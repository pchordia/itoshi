#!/usr/bin/env python3
"""
Monitor i2v completion and automatically start lip sync
"""

import os
import sys
import time
import csv
from pathlib import Path

def wait_for_i2v_completion(i2v_output_dir: str, max_wait_seconds: int = 600):
    """Wait for i2v to complete and return the video_id"""
    
    print(f"⏳ Monitoring {i2v_output_dir} for i2v completion...")
    print(f"   Max wait: {max_wait_seconds}s")
    print()
    
    start_time = time.time()
    
    while time.time() - start_time < max_wait_seconds:
        # Look for the most recent timestamped folder
        output_path = Path(i2v_output_dir)
        
        if not output_path.exists():
            time.sleep(5)
            continue
        
        # Find the most recent subfolder
        subfolders = [f for f in output_path.iterdir() if f.is_dir()]
        
        if not subfolders:
            time.sleep(5)
            continue
        
        latest_folder = max(subfolders, key=lambda f: f.stat().st_mtime)
        csv_path = latest_folder / "_i2v_metrics.csv"
        
        if not csv_path.exists():
            time.sleep(5)
            continue
        
        # Check if CSV has completed entries
        try:
            with open(csv_path, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                
                if rows:
                    row = rows[0]
                    status = row.get('status', '')
                    video_id = row.get('video_id', '')
                    
                    if status == 'ok' and video_id:
                        print(f"✅ i2v complete!")
                        print(f"   Video ID: {video_id}")
                        print(f"   CSV: {csv_path}")
                        return video_id, str(csv_path)
                    
                    print(f"📊 Status: {status}, waiting...")
        
        except Exception as e:
            print(f"⚠️  Error reading CSV: {e}")
        
        time.sleep(5)
    
    raise TimeoutError(f"i2v did not complete within {max_wait_seconds}s")

def run_lip_sync(video_id: str, audio_path: str, output_path: str, audio_duration_ms: int = 10000):
    """Run lip sync using the video_id"""
    
    print()
    print("=" * 70)
    print("🎤 Starting lip sync...")
    print("=" * 70)
    
    import subprocess
    
    cmd = [
        "python",
        "src/kling_lip_sync.py",
        "--video-id", video_id,
        "--audio", audio_path,
        "--audio-duration-ms", str(audio_duration_ms),
        "--output", output_path
    ]
    
    print(f"Running: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Lip sync failed with exit code {result.returncode}")
    
    return output_path

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Auto lip sync when i2v completes')
    parser.add_argument('--i2v-output-dir', required=True, help='i2v output directory to monitor')
    parser.add_argument('--audio', required=True, help='Audio file for lip sync')
    parser.add_argument('--audio-duration-ms', type=int, default=10000, help='Audio duration in ms')
    parser.add_argument('--output', required=True, help='Final lip-synced video output path')
    parser.add_argument('--max-wait', type=int, default=600, help='Max seconds to wait for i2v')
    
    args = parser.parse_args()
    
    try:
        # Step 1: Wait for i2v
        video_id, csv_path = wait_for_i2v_completion(args.i2v_output_dir, args.max_wait)
        
        # Step 2: Run lip sync
        output_path = run_lip_sync(video_id, args.audio, args.output, args.audio_duration_ms)
        
        print()
        print("=" * 70)
        print("✅ Pipeline complete!")
        print(f"📹 Final video: {output_path}")
        print("=" * 70)
        
    except Exception as e:
        print()
        print("=" * 70)
        print(f"❌ Error: {e}")
        print("=" * 70)
        sys.exit(1)

if __name__ == "__main__":
    main()

