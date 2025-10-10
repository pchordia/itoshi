#!/usr/bin/env python3
"""
Delete tracks marked with 'x' from S3 and CSV.
"""

import boto3
import os
import csv
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# The 11 tracks to delete
TRACKS_TO_DELETE = [
    'funkcw_express_yourself',
    'funkcw_express_yourself2',
    'funkcw_get_down',
    'funkcy1',
    'funkcy3',
    'heyson_rap',
    'rockam_choruspt2',
    'rockws',
    'roclkill2',
    'roclkill3',
    'roclkill5'
]

def main():
    import argparse
    parser = argparse.ArgumentParser(description='Delete marked tracks from S3 and CSV')
    parser.add_argument('--bucket', default='twerkai-storage',
                        help='S3 bucket name')
    parser.add_argument('--prefix', default='__music__/',
                        help='S3 key prefix')
    parser.add_argument('--csv', default='outputs/music_excerpts/master_with_filenames_with_s3_safe_name_nohyphen.csv',
                        help='CSV file path')
    parser.add_argument('--dry-run', action='store_true',
                        help='Show what would be done without making changes')
    
    args = parser.parse_args()
    
    # Load AWS credentials
    aws_access_key = os.getenv('AWS_ACCESS_KEY_ID')
    aws_secret_key = os.getenv('AWS_SECRET_ACCESS_KEY')
    aws_region = os.getenv('AWS_REGION', 'us-east-1')
    
    if not aws_access_key or not aws_secret_key:
        print("❌ Error: AWS credentials not found in environment")
        return
    
    s3_client = boto3.client(
        's3',
        aws_access_key_id=aws_access_key,
        aws_secret_access_key=aws_secret_key,
        region_name=aws_region
    )
    
    print(f"🗑️  Deleting {len(TRACKS_TO_DELETE)} tracks from S3 and CSV\n")
    
    if args.dry_run:
        print("🔍 DRY RUN - No changes will be made\n")
    
    # Delete from S3
    deleted_s3 = 0
    failed_s3 = 0
    
    for s3_name in TRACKS_TO_DELETE:
        s3_key = args.prefix + s3_name + '.mp3'
        
        if args.dry_run:
            print(f"Would delete from S3: {s3_key}")
            deleted_s3 += 1
        else:
            try:
                s3_client.delete_object(Bucket=args.bucket, Key=s3_key)
                print(f"✅ Deleted from S3: {s3_name}.mp3")
                deleted_s3 += 1
            except Exception as e:
                print(f"❌ Failed to delete from S3: {s3_name}.mp3 - {e}")
                failed_s3 += 1
    
    # Remove from CSV
    csv_path = Path(args.csv)
    rows = []
    removed_csv = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        header = reader.fieldnames
        for row in reader:
            s3_safe_name = row.get('s3_safe_name', '').strip()
            if s3_safe_name not in TRACKS_TO_DELETE:
                rows.append(row)
            else:
                removed_csv += 1
                if not args.dry_run:
                    print(f"📝 Removed from CSV: {row.get('title', s3_safe_name)}")
    
    if not args.dry_run:
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=header)
            writer.writeheader()
            writer.writerows(rows)
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 Deletion Summary:")
    print(f"   S3 deletions:  {deleted_s3}")
    if failed_s3 > 0:
        print(f"   S3 failures:   {failed_s3}")
    print(f"   CSV removals:  {removed_csv}")
    print(f"   CSV remaining: {len(rows)}")
    print(f"{'='*80}\n")
    
    if not args.dry_run and deleted_s3 > 0:
        print(f"✨ Cleanup complete!")
        print(f"   Removed {deleted_s3} files from S3")
        print(f"   Removed {removed_csv} entries from CSV")

if __name__ == '__main__':
    main()



