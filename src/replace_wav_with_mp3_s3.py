#!/usr/bin/env python3
"""
Replace WAV files in S3 with MP3 versions.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm

# Load environment variables
load_dotenv()

def delete_s3_file(s3_client, bucket, key):
    """Delete a file from S3."""
    try:
        s3_client.delete_object(Bucket=bucket, Key=key)
        return True
    except ClientError as e:
        print(f"  ❌ Error deleting {key}: {e}")
        return False

def upload_file_to_s3(s3_client, bucket, local_path, s3_key):
    """Upload a file to S3."""
    try:
        s3_client.upload_file(
            str(local_path),
            bucket,
            s3_key,
            ExtraArgs={
                'ContentType': 'audio/mpeg',
                'CacheControl': 'public, max-age=31536000'
            }
        )
        return True
    except ClientError as e:
        print(f"  ❌ Error uploading {s3_key}: {e}")
        return False

def list_s3_wav_files(s3_client, bucket, prefix):
    """List all WAV files in S3 bucket."""
    wav_files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                key = obj['Key']
                if key.lower().endswith('.wav'):
                    wav_files.append({
                        'key': key,
                        'size': obj['Size']
                    })
    
    return wav_files

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Replace WAV files in S3 with MP3 versions')
    parser.add_argument('--bucket', default='twerkai-storage',
                        help='S3 bucket name')
    parser.add_argument('--prefix', default='__music__/',
                        help='S3 key prefix')
    parser.add_argument('--mp3-dir', required=True,
                        help='Local directory containing MP3 files')
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
    
    # Find all WAV files in S3
    print(f"🔍 Finding WAV files in s3://{args.bucket}/{args.prefix}...")
    wav_files = list_s3_wav_files(s3_client, args.bucket, args.prefix)
    
    if not wav_files:
        print("No WAV files found in S3!")
        sys.exit(0)
    
    print(f"📦 Found {len(wav_files)} WAV files in S3\n")
    
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    replaced = 0
    missing_local = 0
    failed = 0
    
    total_wav_size = 0
    total_mp3_size = 0
    
    for wav_info in tqdm(wav_files, desc="Processing"):
        wav_key = wav_info['key']
        wav_size = wav_info['size']
        total_wav_size += wav_size
        
        # Get the filename without extension
        wav_filename = Path(wav_key).name
        mp3_filename = wav_filename.rsplit('.', 1)[0] + '.mp3'
        mp3_path = mp3_dir / mp3_filename
        
        # Check if corresponding MP3 exists
        if not mp3_path.exists():
            tqdm.write(f"⚠️  Missing MP3: {mp3_filename} (for {wav_filename})")
            missing_local += 1
            continue
        
        mp3_size = mp3_path.stat().st_size
        total_mp3_size += mp3_size
        
        # Calculate the new S3 key (replace .wav with .mp3)
        mp3_key = wav_key.rsplit('.', 1)[0] + '.mp3'
        
        if args.dry_run:
            tqdm.write(f"Would replace:")
            tqdm.write(f"  Delete: {wav_key} ({wav_size / 1024 / 1024:.1f} MB)")
            tqdm.write(f"  Upload: {mp3_key} ({mp3_size / 1024 / 1024:.1f} MB)")
            replaced += 1
        else:
            # Delete WAV from S3
            if delete_s3_file(s3_client, args.bucket, wav_key):
                # Upload MP3 to S3
                if upload_file_to_s3(s3_client, args.bucket, mp3_path, mp3_key):
                    tqdm.write(f"✅ {wav_filename} → {mp3_filename}")
                    tqdm.write(f"   {wav_size / 1024 / 1024:.1f} MB → {mp3_size / 1024 / 1024:.1f} MB")
                    replaced += 1
                else:
                    failed += 1
            else:
                failed += 1
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 Replacement Summary:")
    print(f"   ✅ Replaced: {replaced}")
    if missing_local > 0:
        print(f"   ⚠️  Missing local MP3: {missing_local}")
    if failed > 0:
        print(f"   ❌ Failed: {failed}")
    
    if replaced > 0:
        total_saved = total_wav_size - total_mp3_size
        compression_pct = (total_saved / total_wav_size) * 100
        print(f"\n💾 Space Savings:")
        print(f"   Original WAV: {total_wav_size / 1024 / 1024:.1f} MB")
        print(f"   320k MP3:     {total_mp3_size / 1024 / 1024:.1f} MB")
        print(f"   Saved:        {total_saved / 1024 / 1024:.1f} MB ({compression_pct:.1f}%)")
    
    print(f"{'='*80}\n")
    
    if not args.dry_run and replaced > 0:
        print(f"✨ S3 bucket updated: s3://{args.bucket}/{args.prefix}")

if __name__ == '__main__':
    main()



