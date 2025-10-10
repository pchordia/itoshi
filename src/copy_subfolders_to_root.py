#!/usr/bin/env python3
"""
Copy subfolder files to root __music__/ folder in S3.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from tqdm import tqdm

load_dotenv()

# The 31 files to copy from subfolders to root
FILES_TO_COPY = [
    ('edm/EDM - Fire (Instrumental Version).mp3', 'fire_instrumental_version_edm.mp3'),
    ('edm/EDM - House_MG301.mp3', 'house_mg301.mp3'),
    ('edm/EDM - Lost Loop.mp3', 'lost_loop_edm.mp3'),
    ('edm/EDM - Through - Ooyy.mp3', 'through_ooyy_edm.mp3'),
    ('edm/EDM - Untitled1.mp3', 'untitled1_edm.mp3'),
    ('edm/EDM - Untitled2.mp3', 'untitled2_edm.mp3'),
    ('funk/Funk - FunkCW - Express Yourself.mp3', 'funkcw_express_yourself.mp3'),
    ('funk/Funk - FunkCW - Express Yourself2.mp3', 'funkcw_express_yourself2.mp3'),
    ('funk/Funk - FunkCW - Express Yourself3.mp3', 'funkcw_express_yourself3.mp3'),
    ('funk/Funk - FunkCW - Get Down.mp3', 'funkcw_get_down.mp3'),
    ('funk/Funk - FunkCW - GetDown2.mp3', 'funkcw_getdown2.mp3'),
    ('funk/Funk - FunkCY1.mp3', 'funkcy1.mp3'),
    ('funk/Funk - FunkCY2.mp3', 'funkcy2.mp3'),
    ('funk/Funk - FunkCY3.mp3', 'funkcy3.mp3'),
    ('funk/Funk - Untitled2.mp3', 'untitled2_funk.mp3'),
    ('hip-hop/Hip Hop - Don_t Test Me.mp3', 'dont_test_me_hiphop.mp3'),
    ('hip-hop/Hip Hop - Nyck Caution.mp3', 'nyck_caution.mp3'),
    ('hip-hop/Hip Hop - dhinadhidhina1 - Trap2.mp3', 'dhinadhidhina1_trap2.mp3'),
    ('hip-hop/Rap - Heyson.mp3', 'heyson_rap.mp3'),
    ('pop/Pop - WishYouBest.mp3', 'wishyoubest_pop.mp3'),
    ('pop/Pop - quietrooms Pop House.mp3', 'quietrooms_pop_house.mp3'),
    ('reggaeton/Reggaeton - El Mas Rah - Ratcheton.mp3', 'el_mas_rah_ratcheton.mp3'),
    ('rock/Rock - RockAM - ChorusPt1.mp3', 'rockam_choruspt1.mp3'),
    ('rock/Rock - RockAm - ChorusPt2.mp3', 'rockam_choruspt2.mp3'),
    ('rock/Rock - RockBlur.mp3', 'rockblur.mp3'),
    ('rock/Rock - RockWS.mp3', 'rockws.mp3'),
    ('rock/Rock - RoclKill2.mp3', 'roclkill2.mp3'),
    ('rock/Rock - RoclKill3.mp3', 'roclkill3.mp3'),
    ('rock/Rock - RoclKill4.mp3', 'roclkill4.mp3'),
    ('rock/Rock - RoclKill5.mp3', 'roclkill5.mp3'),
    ('rock/Rock - dhinadhidhina1 - Cover1.mp3', 'dhinadhidhina1_cover1.mp3'),
    # Special rename
    ('hip-hop/track-1.mp3', 'paragHH_og1.mp3'),
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Copy subfolder files to root')
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
    
    print(f"📂 Copying {len(FILES_TO_COPY)} files from subfolders to root\n")
    
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    copied = 0
    failed = 0
    
    for source_path, dest_filename in tqdm(FILES_TO_COPY, desc="Copying"):
        source_key = args.prefix + source_path
        dest_key = args.prefix + dest_filename
        
        if args.dry_run:
            tqdm.write(f"Would copy:")
            tqdm.write(f"  From: {source_path}")
            tqdm.write(f"  To:   {dest_filename}")
            copied += 1
        else:
            try:
                # Copy the file within S3
                s3_client.copy_object(
                    Bucket=args.bucket,
                    CopySource={'Bucket': args.bucket, 'Key': source_key},
                    Key=dest_key,
                    ContentType='audio/mpeg',
                    CacheControl='public, max-age=31536000'
                )
                tqdm.write(f"✅ {dest_filename}")
                copied += 1
            except Exception as e:
                tqdm.write(f"❌ Failed: {source_path} - {e}")
                failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 Copy Summary:")
    print(f"   ✅ Copied: {copied}")
    if failed > 0:
        print(f"   ❌ Failed: {failed}")
    print(f"{'='*80}\n")
    
    if not args.dry_run and copied > 0:
        print(f"✨ Files copied to: s3://{args.bucket}/{args.prefix}")
        print(f"   {copied} files are now available in the root folder")

if __name__ == '__main__':
    main()



