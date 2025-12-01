#!/usr/bin/env python3
"""
Kling AI Lip Sync - Two-step process:
1. Identify face in video using video_id
2. Apply lip sync with audio
"""

import os
import sys
import time
import base64
import requests
import jwt
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

KLING_ACCESS_KEY = os.getenv("KLING_ACCESS_KEY", "")
KLING_SECRET_KEY = os.getenv("KLING_SECRET_KEY", "")
KLING_IDENTIFY_FACE_URL = "https://api-singapore.klingai.com/v1/videos/identify-face"
KLING_LIP_SYNC_URL = "https://api-singapore.klingai.com/v1/videos/advanced-lip-sync"
KLING_POLL_URL = "https://api-singapore.klingai.com/v1/videos/advanced-lip-sync/"

def get_jwt_token():
    """Generate JWT token for Kling API"""
    payload = {
        "iss": KLING_ACCESS_KEY,
        "exp": int(time.time()) + 1800,  # 30 minutes
        "nbf": int(time.time()) - 5
    }
    return jwt.encode(payload, KLING_SECRET_KEY, algorithm="HS256")

def get_headers():
    token = get_jwt_token()
    return {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

def identify_face(video_id: str):
    """Step 1: Identify face in video"""
    print(f"🔍 Step 1: Identifying face in video {video_id}")
    
    payload = {"video_id": video_id}
    
    response = requests.post(
        KLING_IDENTIFY_FACE_URL,
        headers=get_headers(),
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Face identification failed: {response.status_code} - {response.text}")
    
    data = response.json()
    
    if data.get("code") != 0:
        raise Exception(f"Face identification error: {data.get('message')}")
    
    result = data.get("data", {})
    session_id = result.get("session_id")
    face_data = result.get("face_data")
    
    if not session_id or not face_data:
        raise Exception("Missing session_id or face_data in response")
    
    print(f"✅ Face identified - session_id: {session_id}")
    
    return session_id, face_data

def create_lip_sync_task(session_id: str, face_data: str, audio_path: str, audio_duration_ms: int = None):
    """Step 2: Create lip sync task"""
    print(f"🎤 Step 2: Creating lip sync task with audio: {Path(audio_path).name}")
    
    # Read and encode audio
    with open(audio_path, 'rb') as f:
        audio_bytes = f.read()
    
    audio_base64 = base64.b64encode(audio_bytes).decode('utf-8')
    
    # face_data is already a list of face objects
    import json
    
    if isinstance(face_data, list) and len(face_data) > 0:
        first_face = face_data[0]
        face_id = first_face.get("face_id", "0")
        face_start_time = first_face.get("start_time", 0)
        face_end_time = first_face.get("end_time", 10000)
        print(f"✅ Using face_id: {face_id} (from {len(face_data)} detected faces)")
        print(f"   Face time range: {face_start_time}ms - {face_end_time}ms")
    else:
        face_id = "0"
        face_start_time = 0
        face_end_time = 10000
        print(f"⚠️  No faces detected, using defaults")
    
    if audio_duration_ms is None:
        audio_duration_ms = min(10000, face_end_time - face_start_time)
    
    print(f"🎵 Audio duration: {audio_duration_ms}ms")
    
    # Build face_choose object according to Kling API spec
    face_choose_obj = {
        "face_id": face_id,
        "sound_file": audio_base64,
        "sound_start_time": 0,
        "sound_end_time": audio_duration_ms,
        "sound_insert_time": face_start_time,
        "sound_volume": 1.0,
        "original_audio_volume": 0.5
    }
    
    payload = {
        "session_id": session_id,
        "face_choose": [face_choose_obj]
    }
    
    response = requests.post(
        KLING_LIP_SYNC_URL,
        headers=get_headers(),
        json=payload,
        timeout=30
    )
    
    if response.status_code != 200:
        raise Exception(f"Lip sync creation failed: {response.status_code} - {response.text}")
    
    data = response.json()
    
    if data.get("code") != 0:
        raise Exception(f"Lip sync error: {data.get('message')}")
    
    task_id = data.get("data", {}).get("task_id")
    
    if not task_id:
        raise Exception("Missing task_id in response")
    
    print(f"✅ Lip sync task created - task_id: {task_id}")
    
    return task_id

def poll_lip_sync(task_id: str, max_attempts=60, poll_interval=5):
    """Poll for lip sync completion"""
    print(f"⏳ Polling for completion (max {max_attempts * poll_interval}s)...")
    
    for attempt in range(max_attempts):
        response = requests.get(
            f"{KLING_POLL_URL}{task_id}",
            headers=get_headers(),
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"⚠️  Poll attempt {attempt + 1} failed: {response.status_code}")
            time.sleep(poll_interval)
            continue
        
        data = response.json()
        
        if data.get("code") != 0:
            print(f"⚠️  Poll attempt {attempt + 1} error: {data.get('message')}")
            time.sleep(poll_interval)
            continue
        
        task_data = data.get("data", {})
        status = task_data.get("task_status")
        
        print(f"📊 Attempt {attempt + 1}/{max_attempts}: status={status}")
        
        if status == "succeed":
            videos = task_data.get("task_result", {}).get("videos", [])
            if videos and len(videos) > 0:
                video_url = videos[0].get("url")
                if video_url:
                    print(f"✅ Lip sync complete!")
                    return video_url
            raise Exception("No video URL in successful response")
        
        elif status == "failed":
            error_msg = task_data.get("task_status_msg", "Unknown error")
            raise Exception(f"Lip sync failed: {error_msg}")
        
        time.sleep(poll_interval)
    
    raise Exception(f"Lip sync timed out after {max_attempts * poll_interval}s")

def download_video(video_url: str, output_path: str):
    """Download the lip-synced video"""
    print(f"⬇️  Downloading video...")
    
    response = requests.get(video_url, timeout=60)
    
    if response.status_code != 200:
        raise Exception(f"Download failed: {response.status_code}")
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'wb') as f:
        f.write(response.content)
    
    print(f"✅ Saved: {output_path}")
    print(f"📦 Size: {len(response.content) / 1024 / 1024:.2f} MB")

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Kling AI Lip Sync')
    parser.add_argument('--video-id', required=True, help='Kling video ID from i2v')
    parser.add_argument('--audio', required=True, help='Path to audio file (MP3/WAV)')
    parser.add_argument('--audio-duration-ms', type=int, default=10000, help='Audio duration in milliseconds')
    parser.add_argument('--output', required=True, help='Output video path')
    
    args = parser.parse_args()
    
    if not KLING_ACCESS_KEY or not KLING_SECRET_KEY:
        print("❌ KLING_ACCESS_KEY or KLING_SECRET_KEY not found in .env")
        sys.exit(1)
    
    print("=" * 70)
    print("🎬 Kling AI Lip Sync")
    print("=" * 70)
    print(f"Video ID: {args.video_id}")
    print(f"Audio: {args.audio}")
    print(f"Output: {args.output}")
    print()
    
    try:
        # Step 1: Identify face
        session_id, face_data = identify_face(args.video_id)
        print()
        
        # Step 2: Create lip sync task
        task_id = create_lip_sync_task(session_id, face_data, args.audio, args.audio_duration_ms)
        print()
        
        # Step 3: Poll for completion
        video_url = poll_lip_sync(task_id)
        print()
        
        # Step 4: Download
        download_video(video_url, args.output)
        print()
        
        print("=" * 70)
        print("✅ Lip sync complete!")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error: {e}")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()

