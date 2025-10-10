#!/usr/bin/env python3
"""
Upload missing tracks to S3 and update CSV
"""

import boto3
import os
import csv
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()

# Connect to S3
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION', 'us-east-1')
)

bucket = 'twerkai-storage'
prefix = '__music__/'

# Files to upload
files_to_upload = [
    'ES_BALLING - Katori Walker - 17000-32000_5s.mp3',
    'ES_DIAMONDS (Clean Version) - Bhris Drip_5s_seg1.mp3',
    'ES_Flex Up - Tilden Parc - 20000-35000_5s.mp3',
    'ES_No Friend Zone - Tilden Parc - 22000-37000_5s.mp3',
    'ES_PICK A SIDE - Bhris Drip - 36000-51000_5s.mp3',
    'ES_TROPHIES - Cushy_5s_seg1.mp3',
    'ES_Trilling - Azucares - 15000-30000_5s.mp3',
    'ES_blueworld 22 - dreem_5s_seg3.mp3',
    'ES_poison ivy - dreem_5s_seg1_5s.mp3'
]

# Mapping to s3_safe_name (from CSV)
filename_to_s3_safe = {
    'ES_BALLING - Katori Walker - 17000-32000_5s.mp3': 'balling_katori_walker_bah',
    'ES_Flex Up - Tilden Parc - 20000-35000_5s.mp3': 'flex_up_tilden_parc',
    'ES_No Friend Zone - Tilden Parc - 22000-37000_5s.mp3': 'no_friend_zone_tilden_parc',
    'ES_TROPHIES - Cushy_5s_seg1.mp3': 'trophies_cushy',
    'ES_Trilling - Azucares - 15000-30000_5s.mp3': 'trilling_azucares',
    'ES_DIAMONDS (Clean Version) - Bhris Drip_5s_seg1.mp3': 'diamonds_clean_version_bhris_drip_ballpoint',
    'ES_PICK A SIDE - Bhris Drip - 36000-51000_5s.mp3': 'pick_a_side_bhris_drip',
    'ES_blueworld 22 - dreem_5s_seg3.mp3': 'blueworld_22_dreem',
    'ES_poison ivy - dreem_5s_seg1_5s.mp3': 'poison_ivy_dreem'
}

batch2_dir = Path('outputs/music_excerpts/itoshiBatch2_5s_251007')

print('='*70)
print('📤 UPLOADING MISSING TRACKS TO S3')
print('='*70)
print()

uploaded = []
for filename in files_to_upload:
    file_path = batch2_dir / filename
    
    if not file_path.exists():
        print(f'❌ File not found: {filename}')
        continue
    
    s3_safe_name = filename_to_s3_safe.get(filename)
    if not s3_safe_name:
        print(f'⚠️  No S3 safe name for: {filename}')
        continue
    
    s3_key = f'{prefix}{s3_safe_name}.mp3'
    
    try:
        s3_client.upload_file(
            str(file_path),
            bucket,
            s3_key,
            ExtraArgs={
                'ContentType': 'audio/mpeg',
                'CacheControl': 'public, max-age=31536000'
            }
        )
        
        file_size = file_path.stat().st_size / 1024
        s3_url = f'https://{bucket}.s3.amazonaws.com/{s3_key}'
        
        uploaded.append({
            'filename': filename,
            's3_safe_name': s3_safe_name,
            's3_url': s3_url,
            'size_kb': file_size
        })
        
        print(f'✅ {s3_safe_name}.mp3')
        print(f'   Size: {file_size:.1f} KB')
        print(f'   URL: {s3_url}')
        print()
        
    except Exception as e:
        print(f'❌ Failed to upload {filename}: {e}')
        print()

print('='*70)
print(f'📊 UPLOAD COMPLETE: {len(uploaded)}/{len(files_to_upload)} files')
print('='*70)


