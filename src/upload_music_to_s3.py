#!/usr/bin/env python3
"""
Upload music excerpts to S3 using safe names from CSV.
"""

import os
import csv
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
from tqdm import tqdm

# Load environment variables
load_dotenv()

def load_csv_mapping(csv_path: str) -> List[Tuple[str, str]]:
    """
    Load the CSV and return a list of (filename, s3_safe_name) tuples.
    Only includes rows that have both a filename and s3_safe_name.
    """
    mappings = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filenames = row.get('filenames', '').strip()
            s3_name = row.get('s3_safe_name', '').strip()
            
            if not filenames or not s3_name:
                continue
            
            # Handle multiple filenames separated by semicolon
            file_list = [f.strip() for f in filenames.split(';')]
            
            # For multiple files, use the first one (or you can adjust logic)
            # and append the s3_safe_name with .mp3
            for filename in file_list:
                if filename:
                    mappings.append((filename, f"{s3_name}.mp3"))
                    break  # Only use the first file for each track
    
    return mappings

def upload_to_s3(
    local_file: Path,
    s3_bucket: str,
    s3_key: str,
    s3_client,
    dry_run: bool = False
) -> bool:
    """
    Upload a file to S3.
    
    Args:
        local_file: Path to local file
        s3_bucket: S3 bucket name
        s3_key: S3 object key (path in bucket)
        s3_client: boto3 S3 client
        dry_run: If True, just print what would be uploaded
    
    Returns:
        True if successful, False otherwise
    """
    if dry_run:
        print(f"  [DRY RUN] Would upload: {local_file} -> s3://{s3_bucket}/{s3_key}")
        return True
    
    try:
        s3_client.upload_file(
            str(local_file),
            s3_bucket,
            s3_key,
            ExtraArgs={
                'ContentType': 'audio/mpeg',
                'CacheControl': 'public, max-age=31536000',  # 1 year
            }
        )
        return True
    except ClientError as e:
        print(f"  ❌ Error uploading {local_file.name}: {e}")
        return False
    except Exception as e:
        print(f"  ❌ Unexpected error uploading {local_file.name}: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Upload music excerpts to S3')
    parser.add_argument('--csv', default='outputs/music_excerpts/master_with_filenames_with_s3_safe_name_nohyphen.csv',
                        help='Path to CSV file with mappings')
    parser.add_argument('--music-dir', default='outputs/music_excerpts/itoshiBatch2_5s_251007',
                        help='Directory containing music files')
    parser.add_argument('--bucket', required=True,
                        help='S3 bucket name')
    parser.add_argument('--prefix', default='music/',
                        help='S3 key prefix (folder path in bucket)')
    parser.add_argument('--dry-run', action='store_true',
                        help='Print what would be uploaded without actually uploading')
    parser.add_argument('--skip-existing', action='store_true',
                        help='Skip files that already exist in S3')
    
    args = parser.parse_args()
    
    # Validate AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not args.dry_run:
        if not aws_access_key or not aws_secret_key:
            print("❌ Error: AWS credentials not found in environment")
            print("Please set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY in your .env file")
            sys.exit(1)
    
    # Load CSV mappings
    csv_path = Path(args.csv)
    if not csv_path.exists():
        print(f"❌ Error: CSV file not found: {csv_path}")
        sys.exit(1)
    
    print(f"📄 Loading mappings from: {csv_path}")
    mappings = load_csv_mapping(str(csv_path))
    print(f"   Found {len(mappings)} file mappings\n")
    
    # Validate music directory
    music_dir = Path(args.music_dir)
    if not music_dir.exists():
        print(f"❌ Error: Music directory not found: {music_dir}")
        sys.exit(1)
    
    # Initialize S3 client
    if not args.dry_run:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key,
            region_name=aws_region
        )
        
        # Verify bucket exists
        try:
            s3_client.head_bucket(Bucket=args.bucket)
            print(f"✅ Connected to S3 bucket: {args.bucket}\n")
        except ClientError as e:
            print(f"❌ Error accessing bucket '{args.bucket}': {e}")
            sys.exit(1)
    else:
        s3_client = None
        print(f"🔍 DRY RUN MODE - No files will be uploaded\n")
    
    # Get existing files in S3 if skip_existing is enabled
    existing_keys = set()
    if args.skip_existing and not args.dry_run:
        print("🔍 Checking for existing files in S3...")
        try:
            paginator = s3_client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=args.bucket, Prefix=args.prefix):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        existing_keys.add(obj['Key'])
            print(f"   Found {len(existing_keys)} existing files in S3\n")
        except ClientError as e:
            print(f"⚠️  Warning: Could not list existing files: {e}\n")
    
    # Upload files
    print(f"📤 Starting upload to s3://{args.bucket}/{args.prefix}\n")
    
    uploaded = 0
    skipped = 0
    failed = 0
    missing = 0
    
    for filename, s3_name in tqdm(mappings, desc="Uploading"):
        local_file = music_dir / filename
        s3_key = f"{args.prefix}{s3_name}"
        
        # Check if file exists locally
        if not local_file.exists():
            tqdm.write(f"⚠️  Missing: {filename}")
            missing += 1
            continue
        
        # Check if already exists in S3
        if args.skip_existing and s3_key in existing_keys:
            tqdm.write(f"⏭️  Skipped (exists): {s3_name}")
            skipped += 1
            continue
        
        # Upload
        success = upload_to_s3(local_file, args.bucket, s3_key, s3_client, args.dry_run)
        
        if success:
            if not args.dry_run:
                tqdm.write(f"✅ Uploaded: {filename} -> {s3_name}")
            uploaded += 1
        else:
            failed += 1
    
    # Print summary
    print(f"\n{'='*60}")
    print("📊 Upload Summary:")
    print(f"   ✅ Uploaded: {uploaded}")
    if skipped > 0:
        print(f"   ⏭️  Skipped:  {skipped}")
    if missing > 0:
        print(f"   ⚠️  Missing:  {missing}")
    if failed > 0:
        print(f"   ❌ Failed:   {failed}")
    print(f"{'='*60}\n")
    
    if args.dry_run:
        print("ℹ️  This was a dry run. Run without --dry-run to actually upload files.")
    elif uploaded > 0:
        print(f"✨ Files are now available at: s3://{args.bucket}/{args.prefix}")

if __name__ == '__main__':
    main()



