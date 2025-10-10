# Music Upload to S3

This guide explains how to upload your curated music excerpts to AWS S3.

## Setup

### 1. Install boto3

```bash
pip install boto3
```

Or install all dependencies:

```bash
pip install -r requirements.txt
```

### 2. Add AWS Credentials to .env

Add these lines to your `.env` file:

```bash
# AWS S3 credentials
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_REGION=us-east-1  # or your preferred region
```

## Usage

### Dry Run (Test First)

Always run a dry run first to see what will be uploaded:

```bash
python src/upload_music_to_s3.py \
  --bucket your-bucket-name \
  --prefix music/ \
  --dry-run
```

### Upload Files

Once you're satisfied with the dry run, upload for real:

```bash
python src/upload_music_to_s3.py \
  --bucket your-bucket-name \
  --prefix music/
```

### Skip Existing Files

If you want to skip files that already exist in S3:

```bash
python src/upload_music_to_s3.py \
  --bucket your-bucket-name \
  --prefix music/ \
  --skip-existing
```

## Options

- `--csv`: Path to CSV file (default: `outputs/music_excerpts/master_with_filenames_with_s3_safe_name_nohyphen.csv`)
- `--music-dir`: Directory with music files (default: `outputs/music_excerpts/itoshiBatch2_5s_251007`)
- `--bucket`: S3 bucket name (required)
- `--prefix`: S3 key prefix/folder (default: `music/`)
- `--dry-run`: Test without uploading
- `--skip-existing`: Skip files already in S3

## What Gets Uploaded

The script will:

1. Read the CSV file to get the mapping of original filenames to S3-safe names
2. Find each music file in your local directory
3. Upload to S3 with the safe name and proper metadata:
   - Content-Type: `audio/mpeg`
   - Cache-Control: `public, max-age=31536000` (1 year cache)

## Example Output

```
📄 Loading mappings from: outputs/music_excerpts/master_with_filenames_with_s3_safe_name_nohyphen.csv
   Found 139 file mappings

✅ Connected to S3 bucket: my-music-bucket

📤 Starting upload to s3://my-music-bucket/music/

Uploading: 100%|██████████| 139/139 [02:15<00:00,  1.03it/s]
✅ Uploaded: ES_Lifelike - STRLGHT - 65000-80000_5s.mp3 -> lifelike_strlght.mp3
✅ Uploaded: ES_Ring - STRLGHT - 24000-39000_5s.mp3 -> ring_strlght.mp3
...

============================================================
📊 Upload Summary:
   ✅ Uploaded: 139
   ⚠️  Missing:  0
   ❌ Failed:   0
============================================================

✨ Files are now available at: s3://my-music-bucket/music/
```

## Notes

- Only files that have both a `filenames` and `s3_safe_name` in the CSV will be uploaded
- The script handles multiple filenames per track (uses the first one)
- Files are uploaded as `audio/mpeg` with a 1-year cache
- The S3 safe names are lowercase, alphanumeric with underscores, no hyphens



