#!/usr/bin/env python3
"""
Complete pipeline: Custom Lyrics → Rap Video with Lip-Sync

Steps:
1. Generate acapella vocal track from lyrics (ElevenLabs Music API)
2. Combine vocal with backing track (FFmpeg)
3. Run i2i to create portrait
4. Run i2v to animate
5. Apply lip-sync with combined audio
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def run_command(cmd, description):
    """Run a command and handle errors"""
    print()
    print("=" * 70)
    print(f"🚀 {description}")
    print("=" * 70)
    print(f"Command: {' '.join(cmd)}")
    print()
    
    result = subprocess.run(cmd, capture_output=False, text=True)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with exit code {result.returncode}")
        sys.exit(1)
    
    print(f"✅ {description} complete!")
    return result

def main():
    parser = argparse.ArgumentParser(
        description='Complete pipeline: Lyrics → Rap Video with Lip-Sync'
    )
    
    # Input files
    parser.add_argument('--selfie', required=True, help='Path to selfie image')
    parser.add_argument('--lyrics', required=True, help='Path to lyrics text file')
    parser.add_argument('--vocal-prompt', required=True, help='Path to vocal prompt template')
    parser.add_argument('--backing-track', required=True, help='Path to backing/instrumental track')
    
    # Style selection
    parser.add_argument('--i2i-style', required=True, 
                       help='i2i style name (e.g., rapGod, rap8mile, rapParty)')
    parser.add_argument('--i2v-style', required=True,
                       help='i2v style name (e.g., rapGod, rap8mile, rapParty)')
    
    # Prompts
    parser.add_argument('--i2i-prompts', default='prompts/anime_prompts.txt',
                       help='Path to i2i prompts file')
    parser.add_argument('--i2v-prompts', default='prompts/kling_prompts.txt',
                       help='Path to i2v prompts file')
    
    # Output
    parser.add_argument('--output-dir', required=True, help='Base output directory')
    
    # Audio settings
    parser.add_argument('--vocal-volume', type=float, default=1.0,
                       help='Vocal volume (default: 1.0)')
    parser.add_argument('--backing-volume', type=float, default=0.7,
                       help='Backing volume (default: 0.7)')
    parser.add_argument('--duration', type=int, default=10,
                       help='Video duration in seconds (default: 10)')
    parser.add_argument('--audio-duration-ms', type=int, default=10000,
                       help='Audio duration in milliseconds for lip-sync (default: 10000)')
    
    args = parser.parse_args()
    
    # Validate inputs
    if not Path(args.selfie).exists():
        print(f"❌ Selfie not found: {args.selfie}")
        sys.exit(1)
    
    if not Path(args.lyrics).exists():
        print(f"❌ Lyrics file not found: {args.lyrics}")
        sys.exit(1)
    
    if not Path(args.vocal_prompt).exists():
        print(f"❌ Vocal prompt not found: {args.vocal_prompt}")
        sys.exit(1)
    
    if not Path(args.backing_track).exists():
        print(f"❌ Backing track not found: {args.backing_track}")
        sys.exit(1)
    
    # Create output directories
    output_base = Path(args.output_dir)
    audio_dir = output_base / "audio"
    images_dir = output_base / "images"
    videos_dir = output_base / "videos"
    
    for d in [audio_dir, images_dir, videos_dir]:
        d.mkdir(parents=True, exist_ok=True)
    
    # Generate unique timestamp for this run
    timestamp = time.strftime("%y%m%d_%H%M%S")
    
    # File paths
    vocal_path = audio_dir / f"vocal_{timestamp}.mp3"
    combined_path = audio_dir / f"combined_{timestamp}.mp3"
    
    print("=" * 70)
    print("🎬 CUSTOM RAP VIDEO PIPELINE")
    print("=" * 70)
    print(f"Selfie: {args.selfie}")
    print(f"Lyrics: {args.lyrics}")
    print(f"i2i Style: {args.i2i_style}")
    print(f"i2v Style: {args.i2v_style}")
    print(f"Output: {output_base}")
    print("=" * 70)
    
    # STEP 1: Generate vocal track
    step1_cmd = [
        'python', 'src/generate_rap_vocals.py',
        '--lyrics', args.lyrics,
        '--vocal-prompt', args.vocal_prompt,
        '--output', str(vocal_path),
        '--duration', str(args.duration)
    ]
    run_command(step1_cmd, "Step 1: Generate Vocal Track")
    
    # STEP 2: Combine vocal + backing
    step2_cmd = [
        'python', 'src/combine_vocal_and_backing.py',
        '--vocal', str(vocal_path),
        '--backing', args.backing_track,
        '--output', str(combined_path),
        '--vocal-volume', str(args.vocal_volume),
        '--backing-volume', str(args.backing_volume)
    ]
    run_command(step2_cmd, "Step 2: Combine Vocal + Backing Track")
    
    # STEP 3: Generate portrait (i2i)
    # Create temp input directory with single image
    temp_input = images_dir / f"temp_input_{timestamp}"
    temp_input.mkdir(exist_ok=True)
    import shutil
    shutil.copy2(args.selfie, temp_input / Path(args.selfie).name)
    
    step3_cmd = [
        'python', 'src/batch_media.py', 'i2i',
        '--input', str(temp_input),
        '--output', str(images_dir),
        '--prompts', args.i2i_prompts,
        '--prompt-name', args.i2i_style,
        '--model', 'google'
    ]
    run_command(step3_cmd, "Step 3: Generate Portrait (i2i)")
    
    # Clean up temp input
    shutil.rmtree(temp_input, ignore_errors=True)
    
    # Find the generated image directory (latest timestamped folder)
    image_output_dirs = sorted([d for d in images_dir.iterdir() if d.is_dir()], 
                               key=lambda x: x.stat().st_mtime)
    if not image_output_dirs:
        print("❌ No i2i output found")
        sys.exit(1)
    
    latest_image_dir = image_output_dirs[-1]
    print(f"📁 Using i2i output: {latest_image_dir}")
    
    # STEP 4: Animate portrait (i2v)
    step4_cmd = [
        'python', 'src/batch_media.py', 'i2v',
        '--input', str(latest_image_dir),
        '--output', str(videos_dir),
        '--prompts', args.i2v_prompts,
        '--prompt-name', args.i2v_style,
        '--model', 'kling',
        '--duration', str(args.duration)
    ]
    run_command(step4_cmd, "Step 4: Animate Portrait (i2v)")
    
    # Find the generated video directory and CSV
    video_output_dirs = sorted([d for d in videos_dir.iterdir() if d.is_dir()],
                               key=lambda x: x.stat().st_mtime)
    if not video_output_dirs:
        print("❌ No i2v output found")
        sys.exit(1)
    
    latest_video_dir = video_output_dirs[-1]
    metrics_csv = latest_video_dir / "_i2v_metrics.csv"
    
    if not metrics_csv.exists():
        print(f"❌ Metrics CSV not found: {metrics_csv}")
        sys.exit(1)
    
    print(f"📁 Using i2v output: {latest_video_dir}")
    
    # STEP 5: Apply lip-sync
    step5_cmd = [
        'python', 'src/batch_lip_sync.py',
        '--csv', str(metrics_csv),
        '--audio', str(combined_path),
        '--audio-duration-ms', str(args.audio_duration_ms),
        '--output-dir', str(latest_video_dir),
        '--workers', '1'
    ]
    run_command(step5_cmd, "Step 5: Apply Lip-Sync")
    
    print()
    print("=" * 70)
    print("🎉 PIPELINE COMPLETE!")
    print("=" * 70)
    print(f"📁 Final videos in: {latest_video_dir}")
    print(f"🎵 Combined audio: {combined_path}")
    print("=" * 70)

if __name__ == "__main__":
    main()

