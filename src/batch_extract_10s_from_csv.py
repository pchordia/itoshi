#!/usr/bin/env python3
"""
Extract 10-second excerpts for all tracks in CSV.
- For 15s pre-extracts (WAV or MP3): Find best 10s segment
- For full tracks (MP3/WAV): Extract top 10s danceable segment
"""

import os
import sys
import csv
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from tqdm import tqdm
import re
import pickle
import hashlib

def extract_danceability_features(y, sr):
    """Extract features for danceability scoring."""
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    S = np.abs(librosa.stft(y))
    spec_flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))
    rms = librosa.feature.rms(y=y)[0]
    
    S_low = S[:int(S.shape[0]*0.2), :]
    low_energy = np.sum(S_low, axis=0)
    
    y_harmonic, y_percussive = librosa.effects.hpss(y)
    perc_ratio = np.sum(np.abs(y_percussive)) / (np.sum(np.abs(y)) + 1e-10)
    
    return {
        'tempo': tempo,
        'beat_times': beat_times,
        'onset_env': onset_env,
        'spec_flux': spec_flux,
        'rms': rms,
        'low_energy': low_energy,
        'perc_ratio': perc_ratio
    }

def score_danceability(features, start_time, duration, sr):
    """Score a segment for danceability."""
    onset_env = features['onset_env']
    rms = features['rms']
    spec_flux = features['spec_flux']
    low_energy = features['low_energy']
    
    start_frame = librosa.time_to_frames(start_time, sr=sr)
    end_frame = librosa.time_to_frames(start_time + duration, sr=sr)
    
    start_frame = max(0, start_frame)
    end_frame = min(len(onset_env), end_frame)
    
    if end_frame <= start_frame:
        return 0.0
    
    segment_onset = onset_env[start_frame:end_frame]
    segment_rms = rms[start_frame:end_frame] if start_frame < len(rms) else rms[-1:]
    segment_flux = spec_flux[start_frame:end_frame] if start_frame < len(spec_flux) else spec_flux[-1:]
    segment_low = low_energy[start_frame:end_frame] if start_frame < len(low_energy) else low_energy[-1:]
    
    beats_in_segment = np.sum((features['beat_times'] >= start_time) & 
                               (features['beat_times'] < start_time + duration))
    beat_regularity = beats_in_segment / (duration + 1e-10)
    
    score = (
        np.mean(segment_onset) * 2.5 +
        np.mean(segment_rms) * 2.0 +
        np.mean(segment_flux) * 1.5 +
        np.mean(segment_low) * 1.5 +
        beat_regularity * 3.0 +
        features['perc_ratio'] * 2.0
    )
    
    return score

def get_file_hash(filepath):
    """Generate a hash of the file for caching."""
    stat = filepath.stat()
    key = f"{filepath.name}_{stat.st_size}_{stat.st_mtime}"
    return hashlib.md5(key.encode()).hexdigest()

def load_cached_features(audio_path, cache_dir):
    """Load cached features if available."""
    if not cache_dir:
        return None
    
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    file_hash = get_file_hash(audio_path)
    cache_file = cache_dir / f"{file_hash}.pkl"
    
    if cache_file.exists():
        try:
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
        except:
            pass
    
    return None

def save_cached_features(audio_path, features, cache_dir):
    """Save features to cache."""
    if not cache_dir:
        return
    
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    file_hash = get_file_hash(audio_path)
    cache_file = cache_dir / f"{file_hash}.pkl"
    
    try:
        with open(cache_file, 'wb') as f:
            pickle.dump(features, f)
    except:
        pass

def find_best_segment(audio_path, segment_duration=10.0, cache_dir=None):
    """Find the most danceable segment of specified duration."""
    print(f"  Loading: {audio_path.name}")
    
    # Load audio
    y, sr = librosa.load(str(audio_path), sr=None, mono=True)
    duration = len(y) / sr
    
    print(f"  Duration: {duration:.1f}s, extracting {segment_duration}s")
    
    if duration < segment_duration:
        print(f"  ⚠️  Track too short ({duration:.1f}s < {segment_duration}s)")
        return None
    
    # Try to load cached features
    features = load_cached_features(audio_path, cache_dir)
    
    if features:
        print(f"  ✓ Using cached analysis")
    else:
        # Extract features
        print(f"  Analyzing danceability...")
        features = extract_danceability_features(y, sr)
        save_cached_features(audio_path, features, cache_dir)
    
    # Score all possible segments (slide by 0.5s)
    best_score = -1
    best_start = 0
    
    for start_time in np.arange(0, max(0.1, duration - segment_duration + 0.1), 0.5):
        if start_time + segment_duration > duration:
            break
        
        score = score_danceability(features, start_time, segment_duration, sr)
        
        if score > best_score:
            best_score = score
            best_start = start_time
    
    print(f"  Best segment: {best_start:.1f}s - {best_start + segment_duration:.1f}s (score: {best_score:.2f})")
    
    # Extract segment
    start_sample = int(best_start * sr)
    end_sample = int((best_start + segment_duration) * sr)
    segment = y[start_sample:end_sample]
    
    return segment, sr

def main():
    # Paths
    csv_path = Path('outputs/music_excerpts/itoshi_music_DB_251007.csv')
    output_dir = Path('outputs/music_excerpts/itoshiBatch1-2_10s_251009')
    cache_dir = Path('outputs/music_analysis_cache')
    
    # Source directories
    batch2_full = Path('/Users/paragchordia/Downloads/itoshiMusic_epidemic_100725')
    batch2_15s = Path('outputs/music_excerpts/itoshiBatch2_fullTracks_100725')
    batch1_15s = Path('outputs/music_excerpts/itoshiBatch1_fullTracks')
    batch1_mp3 = Path('outputs/music_excerpts/itoshiBatch1_5s_mp3')
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    print("="*80)
    print("🎵 BATCH EXTRACT 10-SECOND EXCERPTS FROM CSV")
    print("="*80)
    print()
    
    # Read CSV
    tracks = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('title'):
                tracks.append(row)
    
    print(f"📊 Total tracks in CSV: {len(tracks)}")
    
    # Filter out subfolder tracks
    processable_tracks = []
    for track in tracks:
        filenames = track.get('filenames', '').strip()
        if '(copied from subfolders)' in filenames or not filenames:
            continue
        processable_tracks.append(track)
    
    print(f"✅ Processable tracks: {len(processable_tracks)}")
    print()
    
    # Process each track
    success_count = 0
    error_count = 0
    skip_count = 0
    
    for track in tqdm(processable_tracks, desc="Processing tracks"):
        try:
            title = track['title']
            s3_safe_name = track['s3_safe_name']
            filenames = track.get('filenames', '').strip()
            
            # Determine output filename
            output_filename = f"{s3_safe_name}_10s.mp3"
            output_path = output_dir / output_filename
            
            # Skip if already exists
            if output_path.exists():
                skip_count += 1
                continue
            
            # Extract base filename
            first_file = filenames.split(';')[0].strip()
            base_name = first_file.replace('_5s_seg1.mp3', '').replace('_5s_seg2.mp3', '') \
                                  .replace('_5s_seg3.mp3', '').replace('_5s.mp3', '')
            
            # Find source file
            source_file = None
            
            # Check for 15s WAV in batch2 (add .wav extension)
            wav_15s_batch2 = batch2_15s / f"{base_name}.wav"
            if wav_15s_batch2.exists():
                source_file = wav_15s_batch2
            
            # Check for 15s WAV in batch1 (filename already has .wav)
            if not source_file:
                wav_15s_batch1 = batch1_15s / base_name
                if wav_15s_batch1.exists():
                    source_file = wav_15s_batch1
            
            # Check for 15s MP3
            if not source_file:
                mp3_15s = batch1_mp3 / f"{base_name}.mp3"
                if mp3_15s.exists():
                    source_file = mp3_15s
            
            # Check for full MP3
            if not source_file:
                clean_name = re.sub(r' - \d{5,6}-\d{5,6}', '', base_name)
                mp3_batch2 = batch2_15s / f"{clean_name}.mp3"
                if mp3_batch2.exists():
                    source_file = mp3_batch2
                else:
                    mp3_full = batch2_full / f"{clean_name}.mp3"
                    if mp3_full.exists():
                        source_file = mp3_full
            
            if not source_file:
                print(f"\n❌ No source file found for: {title}")
                error_count += 1
                continue
            
            # Extract 10s segment
            result = find_best_segment(source_file, segment_duration=10.0, cache_dir=cache_dir)
            
            if result is None:
                error_count += 1
                continue
            
            segment, sr = result
            
            # Save as MP3
            print(f"  Saving: {output_filename}")
            sf.write(str(output_path), segment, sr, format='MP3', subtype='MPEG_LAYER_III')
            
            success_count += 1
            
        except Exception as e:
            print(f"\n❌ Error processing {track.get('title', 'unknown')}: {e}")
            error_count += 1
            continue
    
    # Summary
    print()
    print("="*80)
    print("📊 PROCESSING COMPLETE")
    print("="*80)
    print(f"✅ Successfully extracted: {success_count}")
    print(f"⏭️  Skipped (already exists): {skip_count}")
    print(f"❌ Errors: {error_count}")
    print()
    print(f"📁 Output directory: {output_dir}")
    print("="*80)

if __name__ == "__main__":
    main()

