#!/usr/bin/env python3
"""
Batch lip sync on multiple videos in parallel
"""

import os
import sys
import csv
import subprocess
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

def run_lip_sync_task(video_id, image_name, audio_path, audio_duration_ms, output_dir):
    """Run lip sync for one video"""
    
    output_filename = f"{Path(image_name).stem}_lipsynced.mp4"
    output_path = os.path.join(output_dir, output_filename)
    
    cmd = [
        "python", "src/kling_lip_sync.py",
        "--video-id", video_id,
        "--audio", audio_path,
        "--audio-duration-ms", str(audio_duration_ms),
        "--output", output_path
    ]
    
    print(f"🎬 Starting lip sync for {image_name}")
    print(f"   Video ID: {video_id}")
    print(f"   Output: {output_filename}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        
        if result.returncode == 0:
            print(f"✅ Completed: {image_name}")
            return {"image": image_name, "status": "success", "output": output_path}
        else:
            error = result.stderr[-200:] if result.stderr else "Unknown error"
            print(f"❌ Failed: {image_name} - {error}")
            return {"image": image_name, "status": "failed", "error": error}
    
    except Exception as e:
        print(f"❌ Exception: {image_name} - {e}")
        return {"image": image_name, "status": "error", "error": str(e)}

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Batch lip sync on multiple videos')
    parser.add_argument('--csv', required=True, help='i2v metrics CSV with video_ids')
    parser.add_argument('--audio', required=True, help='Audio file for lip sync')
    parser.add_argument('--audio-duration-ms', type=int, default=9900, help='Audio duration in ms')
    parser.add_argument('--output-dir', required=True, help='Output directory for lip-synced videos')
    parser.add_argument('--workers', type=int, default=5, help='Number of parallel workers')
    
    args = parser.parse_args()
    
    # Read CSV
    print("=" * 70)
    print("🎬 Batch Lip Sync")
    print("=" * 70)
    print(f"CSV: {args.csv}")
    print(f"Audio: {args.audio}")
    print(f"Workers: {args.workers}")
    print()
    
    with open(args.csv, 'r') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    print(f"📊 Found {len(rows)} videos")
    print()
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Run lip sync in parallel
    results = []
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = []
        
        for row in rows:
            video_id = row.get('video_id', '')
            image_name = row.get('image_name', '')
            status = row.get('status', '')
            
            if status == 'ok' and video_id:
                future = executor.submit(
                    run_lip_sync_task,
                    video_id,
                    image_name,
                    args.audio,
                    args.audio_duration_ms,
                    args.output_dir
                )
                futures.append(future)
        
        # Collect results
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
    
    # Summary
    print()
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    
    success = [r for r in results if r['status'] == 'success']
    failed = [r for r in results if r['status'] != 'success']
    
    print(f"✅ Success: {len(success)}")
    print(f"❌ Failed: {len(failed)}")
    
    if failed:
        print()
        print("Failed videos:")
        for r in failed:
            print(f"  - {r['image']}: {r.get('error', 'Unknown')}")
    
    print()
    print(f"📁 Output: {args.output_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()

