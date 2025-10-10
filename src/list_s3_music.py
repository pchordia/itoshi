#!/usr/bin/env python3
"""
List all music tracks in S3 bucket.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import boto3
from botocore.exceptions import ClientError
import csv

# Load environment variables
load_dotenv()

def format_size(bytes):
    """Format bytes to human readable size."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} TB"

def list_s3_files(bucket, prefix=''):
    """List all files in S3 bucket with given prefix."""
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
    
    try:
        s3_client.head_bucket(Bucket=bucket)
    except ClientError as e:
        print(f"❌ Error accessing bucket '{bucket}': {e}")
        sys.exit(1)
    
    print(f"📦 Listing files in: s3://{bucket}/{prefix}\n")
    
    files = []
    paginator = s3_client.get_paginator('list_objects_v2')
    
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'modified': obj['LastModified']
                })
    
    return files

def main():
    import argparse
    parser = argparse.ArgumentParser(description='List music files in S3')
    parser.add_argument('--bucket', default='twerkai-storage',
                        help='S3 bucket name')
    parser.add_argument('--prefix', default='__music__/',
                        help='S3 key prefix (folder path)')
    parser.add_argument('--output', default='outputs/s3_music_list.csv',
                        help='Output CSV file path')
    parser.add_argument('--format', choices=['table', 'csv', 'list'], default='table',
                        help='Output format')
    
    args = parser.parse_args()
    
    # List files
    files = list_s3_files(args.bucket, args.prefix)
    
    if not files:
        print("No files found!")
        return
    
    # Sort by key
    files.sort(key=lambda x: x['key'])
    
    total_size = sum(f['size'] for f in files)
    
    # Output based on format
    if args.format == 'table':
        print(f"{'#':<5} {'Filename':<70} {'Size':<12} {'Modified':<25}")
        print("="*115)
        
        for i, f in enumerate(files, 1):
            filename = f['key'].replace(args.prefix, '')
            size_str = format_size(f['size'])
            modified_str = f['modified'].strftime('%Y-%m-%d %H:%M:%S %Z')
            print(f"{i:<5} {filename:<70} {size_str:<12} {modified_str:<25}")
        
        print("="*115)
        print(f"\n📊 Summary:")
        print(f"   Total files: {len(files)}")
        print(f"   Total size:  {format_size(total_size)}")
        print(f"   Location:    s3://{args.bucket}/{args.prefix}")
        
    elif args.format == 'list':
        for f in files:
            filename = f['key'].replace(args.prefix, '')
            print(filename)
        print(f"\nTotal: {len(files)} files ({format_size(total_size)})")
        
    elif args.format == 'csv':
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['number', 'filename', 's3_key', 'size_bytes', 'size_readable', 'last_modified'])
            
            for i, file_info in enumerate(files, 1):
                filename = file_info['key'].replace(args.prefix, '')
                writer.writerow([
                    i,
                    filename,
                    file_info['key'],
                    file_info['size'],
                    format_size(file_info['size']),
                    file_info['modified'].strftime('%Y-%m-%d %H:%M:%S')
                ])
        
        print(f"✅ Saved {len(files)} files to: {output_path}")
        print(f"   Total size: {format_size(total_size)}")
        print(f"\nTo view the list:")
        print(f"   cat {output_path}")

if __name__ == '__main__':
    main()



