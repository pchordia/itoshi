# 10-Second Music Excerpt Extraction

## Overview
This process extracts 10-second excerpts for all 130 tracks in `itoshi_music_DB_251007.csv` that have source files available.

## Source Files
The script pulls from multiple directories:

1. **15s WAV pre-extracts** (~103 tracks)
   - Location: `outputs/music_excerpts/itoshiBatch2_fullTracks_100725/`
   - Files with timestamp ranges (e.g., `ES_Ring - STRLGHT - 24000-39000.wav`)

2. **15s MP3 pre-extracts** (~16 tracks)
   - Location: `outputs/music_excerpts/itoshiBatch1_5s_mp3/`
   - Previously converted from WAV files

3. **Full MP3 tracks** (~10 tracks)
   - Locations: 
     - `outputs/music_excerpts/itoshiBatch2_fullTracks_100725/`
     - `/Users/paragchordia/Downloads/itoshiMusic_epidemic_100725/`

4. **Skipped** (35 tracks)
   - Tracks copied from S3 subfolders (no local source files)

## Processing Logic

### For 15s Pre-extracts:
- Analyzes the entire 15s file
- Finds the most danceable 10s segment
- Uses sliding window (0.5s increments) to test all positions

### For Full Tracks:
- Analyzes the full track
- Extracts the top 10s most danceable segment

### Danceability Scoring:
The script scores segments based on:
- Beat regularity and tempo
- Onset strength (rhythmic attacks)
- RMS loudness
- Spectral flux (changes in frequency content)
- Low-frequency energy (bass content)
- Percussive-to-harmonic ratio

## Output
- **Directory:** `outputs/music_excerpts/itoshiBatch1-2_10s_251009/`
- **Format:** MP3
- **Naming:** `{s3_safe_name}_10s.mp3`
- **Total files:** 130 tracks

## Progress
The extraction is running in the background. Processing time:
- 15s files: ~8-10 seconds per track
- Full tracks: ~15-20 seconds per track
- **Estimated total time:** ~15-20 minutes for all 130 tracks

## Script
Location: `src/batch_extract_10s_from_csv.py`

## Log File
Progress is being logged to: `outputs/music_excerpts/extract_10s_log.txt`

## Command
```bash
python src/batch_extract_10s_from_csv.py
```

