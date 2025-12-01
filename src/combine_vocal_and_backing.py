#!/usr/bin/env python3
"""
Combine vocal track with backing track using FFmpeg
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

def combine_tracks(vocal_path: str, backing_path: str, output_path: str, 
                   vocal_volume: float = 1.0, backing_volume: float = 0.7) -> str:
    """
    Combine vocal and backing tracks using FFmpeg
    
    Args:
        vocal_path: Path to acapella vocal track
        backing_path: Path to instrumental/backing track
        output_path: Where to save combined track
        vocal_volume: Volume multiplier for vocals (0.0-2.0, default 1.0)
        backing_volume: Volume multiplier for backing (0.0-2.0, default 0.7)
    
    Returns:
        Path to combined track
    """
    
    print("=" * 70)
    print("🎚️  Combining Vocal + Backing Track")
    print("=" * 70)
    print(f"Vocal: {vocal_path}")
    print(f"Backing: {backing_path}")
    print(f"Output: {output_path}")
    print(f"Vocal volume: {vocal_volume}")
    print(f"Backing volume: {backing_volume}")
    print()
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    
    # FFmpeg command to mix tracks
    # Use amix filter to combine audio streams with volume control
    cmd = [
        'ffmpeg',
        '-i', vocal_path,
        '-i', backing_path,
        '-filter_complex',
        f'[0:a]volume={vocal_volume}[a0];[1:a]volume={backing_volume}[a1];[a0][a1]amix=inputs=2:duration=shortest:normalize=0',
        '-codec:a', 'libmp3lame',
        '-b:a', '320k',
        '-y',  # Overwrite output
        output_path
    ]
    
    print("🎵 Running FFmpeg...")
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True
        )
        
        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"✅ Tracks combined successfully!")
        print(f"📦 Size: {file_size_mb:.2f} MB")
        print(f"📁 Saved to: {output_path}")
        
        return output_path
        
    except subprocess.CalledProcessError as e:
        print(f"❌ FFmpeg error: {e.stderr}")
        raise
    except Exception as e:
        print(f"❌ Error combining tracks: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Combine vocal and backing tracks using FFmpeg'
    )
    parser.add_argument('--vocal', required=True, help='Path to vocal track (MP3)')
    parser.add_argument('--backing', required=True, help='Path to backing/instrumental track (MP3)')
    parser.add_argument('--output', required=True, help='Output path for combined track')
    parser.add_argument('--vocal-volume', type=float, default=1.0, 
                       help='Vocal volume multiplier (default: 1.0)')
    parser.add_argument('--backing-volume', type=float, default=0.7,
                       help='Backing volume multiplier (default: 0.7)')
    
    args = parser.parse_args()
    
    # Combine tracks
    combine_tracks(
        args.vocal, 
        args.backing, 
        args.output,
        args.vocal_volume,
        args.backing_volume
    )
    
    print()
    print("=" * 70)
    print("✅ Audio mixing complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

