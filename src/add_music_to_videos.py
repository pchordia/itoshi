#!/usr/bin/env python3
"""
Add music to videos by randomly selecting audio excerpts.

For each video in the input folder, randomly selects an audio file from the music folder
and combines them. The audio is mixed with the original video audio or replaces it.

Usage:
    python add_music_to_videos.py --videos path/to/videos --music path/to/music --output path/to/output
    python add_music_to_videos.py --videos path/to/videos --music path/to/music --output path/to/output --replace-audio
"""

import argparse
import os
import random
import subprocess
from pathlib import Path
from tqdm import tqdm


def list_files(directory, extensions):
    """List all files in directory with given extensions."""
    files = []
    for ext in extensions:
        files.extend(Path(directory).glob(f"*{ext}"))
    return sorted([str(f) for f in files])


def add_music_to_video(video_path, audio_path, output_path, replace_audio=False, audio_volume=0.5):
    """
    Add music to a video using ffmpeg.
    
    Args:
        video_path: Path to input video
        audio_path: Path to audio file
        output_path: Path to output video
        replace_audio: If True, replace video audio; if False, mix with original
        audio_volume: Volume level for the added music (0.0 to 1.0)
    """
    if replace_audio:
        # Replace original audio with music
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-map', '0:v:0',  # video from first input
            '-map', '1:a:0',  # audio from second input
            '-c:v', 'copy',   # copy video codec
            '-c:a', 'aac',    # encode audio as AAC
            '-b:a', '192k',   # audio bitrate
            '-shortest',      # match shortest stream duration
            '-y',             # overwrite output
            output_path
        ]
    else:
        # Mix original audio with music
        cmd = [
            'ffmpeg',
            '-i', video_path,
            '-i', audio_path,
            '-filter_complex',
            f'[0:a]volume=1.0[a0];[1:a]volume={audio_volume}[a1];[a0][a1]amix=inputs=2:duration=shortest[aout]',
            '-map', '0:v:0',  # video from first input
            '-map', '[aout]', # mixed audio
            '-c:v', 'copy',   # copy video codec
            '-c:a', 'aac',    # encode audio as AAC
            '-b:a', '192k',   # audio bitrate
            '-shortest',      # match shortest stream duration
            '-y',             # overwrite output
            output_path
        ]
    
    try:
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error processing {video_path}: {e.stderr.decode()}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Add music to videos by randomly selecting audio excerpts.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Replace video audio with random music
  python add_music_to_videos.py --videos outputs/videos/latest --music outputs/music_excerpts --output outputs/videos_with_music
  
  # Mix music with original audio at 30% volume
  python add_music_to_videos.py --videos outputs/videos/latest --music outputs/music_excerpts --output outputs/videos_with_music --mix --volume 0.3
        """
    )
    parser.add_argument('--videos', required=True, help='Directory containing video files')
    parser.add_argument('--music', required=True, help='Directory containing audio files')
    parser.add_argument('--output', required=True, help='Output directory for videos with music')
    parser.add_argument('--replace-audio', action='store_true',
                        help='Replace original audio (default: mix with original)')
    parser.add_argument('--mix', action='store_true',
                        help='Mix music with original audio (opposite of --replace-audio)')
    parser.add_argument('--volume', type=float, default=0.5,
                        help='Music volume level when mixing (0.0 to 1.0, default: 0.5)')
    parser.add_argument('--seed', type=int, default=None,
                        help='Random seed for reproducible music selection')
    
    args = parser.parse_args()
    
    # Set random seed if provided
    if args.seed is not None:
        random.seed(args.seed)
    
    # Determine audio mixing mode
    replace_audio = args.replace_audio and not args.mix
    
    # Create output directory
    os.makedirs(args.output, exist_ok=True)
    
    # List video and audio files
    video_extensions = ['.mp4', '.mov', '.avi', '.mkv']
    audio_extensions = ['.wav', '.mp3', '.m4a', '.flac']
    
    videos = list_files(args.videos, video_extensions)
    music_files = list_files(args.music, audio_extensions)
    
    if not videos:
        print(f"❌ No video files found in {args.videos}")
        return
    
    if not music_files:
        print(f"❌ No audio files found in {args.music}")
        return
    
    print(f"🎬 Found {len(videos)} videos")
    print(f"🎵 Found {len(music_files)} audio files")
    print(f"🔊 Mode: {'Replace audio' if replace_audio else f'Mix audio (volume: {args.volume})'}")
    print(f"📁 Output: {args.output}")
    print()
    
    # Process each video
    success_count = 0
    for video_path in tqdm(videos, desc="Adding music to videos"):
        # Randomly select a music file
        music_path = random.choice(music_files)
        
        # Generate output filename
        video_name = Path(video_path).stem
        music_name = Path(music_path).stem
        output_filename = f"{video_name}_music.mp4"
        output_path = os.path.join(args.output, output_filename)
        
        # Add music to video
        success = add_music_to_video(
            video_path,
            music_path,
            output_path,
            replace_audio=replace_audio,
            audio_volume=args.volume
        )
        
        if success:
            success_count += 1
            tqdm.write(f"✅ {video_name} + {music_name}")
        else:
            tqdm.write(f"❌ Failed: {video_name}")
    
    print()
    print(f"🎉 Complete! Successfully processed {success_count}/{len(videos)} videos")
    print(f"📁 Output directory: {args.output}")


if __name__ == "__main__":
    main()


