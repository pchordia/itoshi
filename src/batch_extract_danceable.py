#!/usr/bin/env python3
"""
Batch extract danceable 5-second segments from music tracks.
For tracks > 15s: extract top 3 segments
For tracks <= 15s: extract top 1 segment
"""

import os
import sys
import argparse
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from tqdm import tqdm
import subprocess
import pickle
import hashlib

# Import the danceability scoring from pick_danceable_segment
def extract_danceability_features(y, sr):
    """Extract features for danceability scoring."""
    # Beat tracking
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Onset strength
    onset_env = librosa.onset.onset_strength(y=y, sr=sr)
    
    # Spectral flux
    S = np.abs(librosa.stft(y))
    spec_flux = np.sqrt(np.sum(np.diff(S, axis=1)**2, axis=0))
    
    # RMS loudness
    rms = librosa.feature.rms(y=y)[0]
    
    # Low-frequency energy
    S_low = S[:int(S.shape[0]*0.2), :]
    low_energy = np.sum(S_low, axis=0)
    
    # Percussive component
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

def robust_zscore(arr):
    """Robust z-score using median and MAD."""
    median = np.median(arr)
    mad = np.median(np.abs(arr - median))
    if mad < 1e-10:
        return np.zeros_like(arr)
    return (arr - median) / (mad * 1.4826)

def score_danceability_windows(features, sr, window_sec=5.0, hop_sec=0.5):
    """Score danceability for sliding windows."""
    hop_length = 512
    window_frames = int(window_sec * sr / hop_length)
    hop_frames = int(hop_sec * sr / hop_length)
    
    onset_env = features['onset_env']
    spec_flux = features['spec_flux']
    rms = features['rms']
    low_energy = features['low_energy']
    perc_ratio = features['perc_ratio']
    
    # Normalize features
    onset_z = robust_zscore(onset_env)
    flux_z = robust_zscore(spec_flux[:len(onset_z)])
    rms_z = robust_zscore(rms[:len(onset_z)])
    low_z = robust_zscore(low_energy[:len(onset_z)])
    
    scores = []
    positions = []
    
    for start_frame in range(0, len(onset_z) - window_frames, hop_frames):
        end_frame = start_frame + window_frames
        
        # Window scores
        onset_score = np.mean(onset_z[start_frame:end_frame])
        flux_score = np.mean(flux_z[start_frame:end_frame])
        rms_score = np.mean(rms_z[start_frame:end_frame])
        low_score = np.mean(low_z[start_frame:end_frame])
        
        # Weighted sum
        total_score = (
            0.35 * onset_score +
            0.25 * flux_score +
            0.20 * rms_score +
            0.15 * low_score +
            0.05 * perc_ratio
        )
        
        scores.append(total_score)
        start_time = librosa.frames_to_time(start_frame, sr=sr, hop_length=hop_length)
        positions.append(start_time)
    
    return np.array(scores), np.array(positions)

def get_cache_path(input_file, cache_dir):
    """Generate cache file path based on input file hash."""
    # Use file path and modification time for cache key
    file_stat = os.stat(input_file)
    cache_key = f"{input_file}_{file_stat.st_mtime}_{file_stat.st_size}"
    cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
    return cache_dir / f"{cache_hash}.pkl"

def load_cached_analysis(input_file, cache_dir):
    """Load cached MIR analysis if available."""
    cache_path = get_cache_path(input_file, cache_dir)
    if cache_path.exists():
        try:
            with open(cache_path, 'rb') as f:
                return pickle.load(f)
        except:
            return None
    return None

def save_cached_analysis(input_file, cache_dir, data):
    """Save MIR analysis to cache."""
    cache_path = get_cache_path(input_file, cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)
    with open(cache_path, 'wb') as f:
        pickle.dump(data, f)

def extract_top_segments(input_file, output_dir, n_segments=1, segment_duration=5.0, cache_dir=None):
    """Extract top N danceable segments from an audio file."""
    # Try to load from cache
    cached_data = None
    if cache_dir:
        cached_data = load_cached_analysis(input_file, cache_dir)
    
    if cached_data:
        y = cached_data['y']
        sr = cached_data['sr']
        features = cached_data['features']
        scores = cached_data['scores']
        positions = cached_data['positions']
    else:
        # Load audio
        y, sr = librosa.load(input_file, sr=None, mono=True)
        duration = len(y) / sr
        
        # Extract features
        features = extract_danceability_features(y, sr)
        
        # Score windows
        scores, positions = score_danceability_windows(features, sr, window_sec=segment_duration)
        
        # Cache the analysis
        if cache_dir:
            cache_data = {
                'y': y,
                'sr': sr,
                'features': features,
                'scores': scores,
                'positions': positions
            }
            save_cached_analysis(input_file, cache_dir, cache_data)
    
    duration = len(y) / sr
    
    # Get top N non-overlapping positions
    top_positions = []
    top_scores = []
    sorted_indices = np.argsort(scores)[::-1]  # Sort descending
    
    for idx in sorted_indices:
        pos = positions[idx]
        score = scores[idx]
        
        # Check if this position overlaps with any already selected
        overlaps = False
        for selected_pos in top_positions:
            if abs(pos - selected_pos) < segment_duration:
                overlaps = True
                break
        
        if not overlaps:
            top_positions.append(pos)
            top_scores.append(score)
            
            if len(top_positions) >= n_segments:
                break
    
    top_positions = np.array(top_positions)
    top_scores = np.array(top_scores)
    
    # Extract and save segments
    base_name = Path(input_file).stem
    output_files = []
    
    for i, (pos, score) in enumerate(zip(top_positions, top_scores), 1):
        start_sample = int(pos * sr)
        end_sample = int((pos + segment_duration) * sr)
        
        # Ensure we don't go past the end
        if end_sample > len(y):
            end_sample = len(y)
            start_sample = max(0, end_sample - int(segment_duration * sr))
        
        segment = y[start_sample:end_sample]
        
        # Output filename
        if n_segments > 1:
            output_file = output_dir / f"{base_name}_5s_seg{i}.mp3"
        else:
            output_file = output_dir / f"{base_name}_5s.mp3"
        
        # Save as mp3 using soundfile and ffmpeg
        temp_wav = output_dir / f"temp_{base_name}_{i}.wav"
        sf.write(str(temp_wav), segment, sr)
        
        # Convert to mp3
        subprocess.run([
            'ffmpeg', '-i', str(temp_wav), '-acodec', 'libmp3lame',
            '-b:a', '192k', '-y', str(output_file)
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Remove temp file
        temp_wav.unlink()
        
        output_files.append(output_file)
    
    return output_files, duration

def main():
    parser = argparse.ArgumentParser(description='Batch extract danceable segments')
    parser.add_argument('--input-dir', required=True, help='Input directory with mp3 files')
    parser.add_argument('--output-dir', required=True, help='Output directory for segments')
    parser.add_argument('--segment-duration', type=float, default=5.0, help='Segment duration in seconds')
    parser.add_argument('--threshold', type=float, default=15.0, help='Duration threshold for multiple segments')
    parser.add_argument('--cache-dir', default='outputs/music_analysis_cache', help='Directory for MIR analysis cache')
    args = parser.parse_args()
    
    # Setup paths
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)
    cache_dir = Path(args.cache_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all mp3 and wav files
    mp3_files = sorted(input_dir.glob('*.mp3'))
    wav_files = sorted(input_dir.glob('*.wav'))
    audio_files = sorted(mp3_files + wav_files)
    
    if not audio_files:
        print(f"No audio files found in {input_dir}")
        return
    
    print(f"Found {len(audio_files)} audio files ({len(mp3_files)} mp3, {len(wav_files)} wav)")
    print(f"Output directory: {output_dir}")
    print(f"Cache directory: {cache_dir}")
    print(f"Segment duration: {args.segment_duration}s")
    print(f"Threshold for 3 segments: >{args.threshold}s")
    print()
    
    # Process each file
    total_segments = 0
    for audio_file in tqdm(audio_files, desc="Processing tracks"):
        try:
            # Quick duration check
            y_test, sr_test = librosa.load(str(audio_file), sr=None, mono=True, duration=1.0)
            info = sf.info(str(audio_file))
            duration = info.duration
            
            # Determine number of segments
            n_segments = 3 if duration > args.threshold else 1
            
            # Extract segments
            output_files, actual_duration = extract_top_segments(
                str(audio_file),
                output_dir,
                n_segments=n_segments,
                segment_duration=args.segment_duration,
                cache_dir=cache_dir
            )
            
            total_segments += len(output_files)
            tqdm.write(f"✅ {audio_file.name} ({actual_duration:.1f}s) -> {len(output_files)} segment(s)")
            
        except Exception as e:
            tqdm.write(f"❌ Error processing {audio_file.name}: {e}")
            continue
    
    print()
    print(f"🎉 Complete! Generated {total_segments} segments from {len(audio_files)} tracks")
    print(f"📁 Output: {output_dir}")

if __name__ == '__main__':
    main()
