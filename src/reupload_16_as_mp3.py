#!/usr/bin/env python3
"""
Reupload the 16 WAV files as 320kbps MP3 to save space.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from tqdm import tqdm

# Load environment variables
load_dotenv()

# The 16 files and their S3 safe names (from CSV)
FILES_TO_REPLACE = [
    ('ES_PRESSURE! - Nyck Caution - 16000-31000.mp3', 'pressure_nyck_caution.mp3'),
    ('ES_pLaNeT rAvE - Cackie Jhen - 17000-32000.mp3', 'planet_rave_cackie_jhen.mp3'),
    ('ES_Lost Loop - Blue Saga - 143000-158000.mp3', 'lost_loop_blue_saga.mp3'),
    ('ES_After Life - Blue Saga - 28000-43000.mp3', 'after_life_blue_saga.mp3'),
    ('ES_Fire (Instrumental Version) - NIGHTCAP - 56000-71000.mp3', 'fire_instrumental_version_nightcap.mp3'),
    ('ES_Traviesa (Instrumental Version) - Bambi Haze - 21000-36000.mp3', 'traviesa_instrumental_version_bambi_haze.mp3'),
    ('ES_Almost Baked - John Runefelt - 20000-35000.mp3', 'almost_baked_john_runefelt.mp3'),
    ('ES_Special Sauce - Daniel Fridell - 15000-30000.mp3', 'special_sauce_daniel_fridell.mp3'),
    ('ES_Riding High on the Wind - Will Harrison - 31000-46000.mp3', 'riding_high_on_the_wind_will_harrison.mp3'),
    ('ES_surreal - dreem - 57000-72000.mp3', 'surreal_dreem.mp3'),
    ('ES_The Main Event - Matt Large - 7000-22000.mp3', 'the_main_event_matt_large.mp3'),
    ('ES_Our Jam - Sam Kramer - 21000-36000.mp3', 'our_jam_sam_kramer.mp3'),
    ("ES_Don't Test Me (Clean Version) - Iso Indies - 10000-25000.mp3", 'dont_test_me_clean_version_iso_indies.mp3'),
    ('ES_Velvet Disco - FLYIN - 19000-34000.mp3', 'velvet_disco_flyin.mp3'),
    ('ES_Tukan - West & Zander - 69000-84000.mp3', 'tukan_west_and_zander.mp3'),
    ('ES_Try for You - LeDorean - 39000-54000.mp3', 'try_for_you_ledorean.mp3'),
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Reupload 16 files as 320kbps MP3')
    parser.add_argument('--mp3-dir', default='outputs/music_excerpts/itoshiBatch1_mp3',
                        help='Directory containing 320kbps MP3 files')
    parser.add_argument('--bucket', default='twerkai-storage',
                        help='S3 bucket name')
    parser.add_argument('--prefix', default='__music__/',
                        help='S3 key prefix')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Load AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not aws_access_key or not aws_secret_key:
        print("❌ Error: AWS credentials not found in environment")
        sys.exit(1)
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    mp3_dir = Path(args.mp3_dir)
    if not mp3_dir.exists():
        print(f"❌ Error: MP3 directory not found: {mp3_dir}")
        sys.exit(1)
    
    print(f"🎵 Replacing 16 large MP3s (4.1 MB each) with 320kbps versions (~0.5 MB)\n")
    
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    uploaded = 0
    missing = 0
    failed = 0
    
    old_total_size = 0
    new_total_size = 0
    
    for local_filename, s3_safe_name in tqdm(FILES_TO_REPLACE, desc="Processing"):
        local_path = mp3_dir / local_filename
        s3_key = args.prefix + s3_safe_name
        
        if not local_path.exists():
            tqdm.write(f"⚠️  Missing: {local_filename}")
            missing += 1
            continue
        
        local_size = local_path.stat().st_size
        new_total_size += local_size
        old_total_size += 4.1 * 1024 * 1024  # Assume old files were 4.1 MB
        
        if args.dry_run:
            tqdm.write(f"Would upload: {local_filename}")
            tqdm.write(f"  → s3://{args.bucket}/{s3_key}")
            tqdm.write(f"  Size: {local_size / 1024 / 1024:.1f} MB")
            uploaded += 1
        else:
            try:
                s3_client.upload_file(
                    str(local_path),
                    args.bucket,
                    s3_key,
                    ExtraArgs={
                        'ContentType': 'audio/mpeg',
                        'CacheControl': 'public, max-age=31536000'
                    }
                )
                tqdm.write(f"✅ {s3_safe_name} ({local_size / 1024 / 1024:.1f} MB)")
                uploaded += 1
            except Exception as e:
                tqdm.write(f"❌ Failed: {local_filename} - {e}")
                failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 Upload Summary:")
    print(f"   ✅ Uploaded: {uploaded}")
    if missing > 0:
        print(f"   ⚠️  Missing:  {missing}")
    if failed > 0:
        print(f"   ❌ Failed:   {failed}")
    
    if uploaded > 0:
        savings = old_total_size - new_total_size
        savings_pct = (savings / old_total_size) * 100
        print(f"\n💾 Space Savings:")
        print(f"   Old size (4.1 MB MP3s): {old_total_size / 1024 / 1024:.1f} MB")
        print(f"   New size (320k MP3s):    {new_total_size / 1024 / 1024:.1f} MB")
        print(f"   Saved:                   {savings / 1024 / 1024:.1f} MB ({savings_pct:.1f}%)")
    
    print(f"{'='*80}\n")
    
    if not args.dry_run and uploaded > 0:
        print(f"✨ S3 updated: s3://{args.bucket}/{args.prefix}")
        print(f"   The old 4.1 MB files have been replaced with 320kbps versions")

if __name__ == '__main__':
    main()



