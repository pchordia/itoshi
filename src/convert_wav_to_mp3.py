#!/usr/bin/env python3
"""
Convert WAV files to 320kbps MP3 format.
"""

import subprocess
from pathlib import Path
from tqdm import tqdm
import sys

def convert_wav_to_mp3(wav_path: Path, mp3_path: Path, bitrate: str = '320k'):
    """
    Convert WAV to MP3 using ffmpeg.
    
    Args:
        wav_path: Input WAV file path
        mp3_path: Output MP3 file path
        bitrate: MP3 bitrate (default: 320k)
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Use ffmpeg to convert
        cmd = [
            'ffmpeg',
            '-i', str(wav_path),
            '-codec:a', 'libmp3lame',
            '-b:a', bitrate,
            '-q:a', '0',  # Highest quality VBR
            '-y',  # Overwrite output file
            str(mp3_path)
        ]
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"  ❌ Error converting {wav_path.name}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error converting {wav_path.name}: {e}")
        return False

def get_file_size_mb(path: Path):
    """Get file size in MB."""
    return path.stat().st_size / (1024 * 1024)

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Convert WAV files to 320kbps MP3')
    parser.add_argument('--input-dir', required=True,
                        help='Directory containing WAV files')
    parser.add_argument('--output-dir', required=True,
                        help='Directory for MP3 output')
    parser.add_argument('--bitrate', default='320k',
                        help='MP3 bitrate (default: 320k)')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite existing MP3 files')
    
    args = parser.parse_args()
    
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    
    if not input_dir.exists():
        print(f"❌ Error: Input directory not found: {input_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all WAV files
    wav_files = list(input_dir.glob("*.wav")) + list(input_dir.glob("*.WAV"))
    
    if not wav_files:
        print(f"No WAV files found in {input_dir}")
        sys.exit(0)
    
    print(f"🎵 Found {len(wav_files)} WAV files in {input_dir}")
    print(f"📁 Output directory: {output_dir}")
    print(f"🎚️  Bitrate: {args.bitrate}\n")
    
    converted = 0
    skipped = 0
    failed = 0
    
    total_wav_size = 0
    total_mp3_size = 0
    
    for wav_file in tqdm(wav_files, desc="Converting"):
        mp3_file = output_dir / f"{wav_file.stem}.mp3"
        
        # Check if output already exists
        if mp3_file.exists() and not args.overwrite:
            tqdm.write(f"⏭️  Skipped (exists): {wav_file.name}")
            skipped += 1
            continue
        
        # Get original size
        wav_size = get_file_size_mb(wav_file)
        total_wav_size += wav_size
        
        # Convert
        success = convert_wav_to_mp3(wav_file, mp3_file, args.bitrate)
        
        if success:
            mp3_size = get_file_size_mb(mp3_file)
            total_mp3_size += mp3_size
            compression = ((wav_size - mp3_size) / wav_size) * 100
            
            tqdm.write(f"✅ {wav_file.name} → {mp3_file.name}")
            tqdm.write(f"   {wav_size:.1f} MB → {mp3_size:.1f} MB (saved {compression:.1f}%)")
            converted += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 Conversion Summary:")
    print(f"   ✅ Converted: {converted}")
    if skipped > 0:
        print(f"   ⏭️  Skipped:   {skipped}")
    if failed > 0:
        print(f"   ❌ Failed:    {failed}")
    
    if converted > 0:
        total_saved = total_wav_size - total_mp3_size
        compression_pct = (total_saved / total_wav_size) * 100
        print(f"\n💾 Space Savings:")
        print(f"   Original WAV: {total_wav_size:.1f} MB")
        print(f"   320k MP3:     {total_mp3_size:.1f} MB")
        print(f"   Saved:        {total_saved:.1f} MB ({compression_pct:.1f}%)")
    
    print(f"{'='*80}\n")
    
    if converted > 0:
        print(f"✨ MP3 files are in: {output_dir}")

if __name__ == '__main__':
    main()



