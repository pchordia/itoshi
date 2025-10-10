#!/usr/bin/env python3
"""
Extract the most danceable N-second segment from a music track.

Uses multiple audio features to identify the best segment:
- Beat strength and regularity
- Onset/flux (rhythmic activity)
- RMS loudness
- Low-frequency energy (bass/kick)
- Percussive vs harmonic content

Usage:
    python pick_danceable_segment.py my_song.mp3 --seconds 10
    python pick_danceable_segment.py my_song.mp3 --seconds 5 --tempo_bias 124 15
"""

import argparse
import math
import numpy as np
import soundfile as sf
import librosa


def robust_z(x):
    """Compute robust z-scores using median and MAD."""
    x = np.asarray(x, dtype=float)
    med = np.median(x)
    mad = np.median(np.abs(x - med)) + 1e-9  # avoid div by zero
    return (x - med) / (1.4826 * mad)


def time_to_frame(t, sr, hop):
    """Convert time in seconds to frame index."""
    return int(round(t * sr / hop))


def frames_stats(x, start_f, end_f):
    """Compute mean and std of a feature array within a frame window."""
    xw = x[max(0, start_f):min(len(x), end_f)]
    if len(xw) == 0:
        return np.nan, np.nan
    return float(np.mean(xw)), float(np.std(xw))


def spectral_flux(S):
    """
    Compute spectral flux (positive changes in spectrum).
    S: magnitude spectrogram [freq x frames]
    """
    d = np.diff(S, axis=1)
    d[d < 0] = 0.0
    flux = np.concatenate([np.zeros((S.shape[0], 1)), d], axis=1).sum(axis=0)
    return flux


def lowband_ratio(S, sr, n_fft, cutoff_hz=150.0):
    """
    Compute ratio of low-frequency energy (below cutoff_hz) to total energy.
    """
    freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)
    k = np.searchsorted(freqs, cutoff_hz)
    low = S[:k, :].sum(axis=0)
    tot = S.sum(axis=0) + 1e-9
    return low / tot


def percussive_ratio(y, sr, hop):
    """
    Estimate percussive vs total energy using HPSS.
    Returns frame-wise ratio of percussive to total RMS energy.
    """
    y_h, y_p = librosa.effects.hpss(y)
    rms_tot = librosa.feature.rms(y=y, hop_length=hop).ravel()
    rms_perc = librosa.feature.rms(y=y_p, hop_length=hop).ravel()
    return (rms_perc + 1e-9) / (rms_tot + 1e-9)


def compute_features(y, sr, hop, n_fft):
    """
    Compute all frame-wise features for the entire track.
    Returns a dict of feature arrays and the common frame count.
    """
    # Core transforms (shared)
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    rms = librosa.feature.rms(S=S).ravel()
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    flux = spectral_flux(S)
    lb = lowband_ratio(S, sr=sr, n_fft=n_fft, cutoff_hz=150.0)
    perc_ratio = percussive_ratio(y, sr=sr, hop=hop)

    # Make all frame-series the same length
    T = min(len(rms), len(onset_env), len(flux), len(lb), len(perc_ratio))
    rms = rms[:T]
    onset_env = onset_env[:T]
    flux = flux[:T]
    lb = lb[:T]
    perc_ratio = perc_ratio[:T]
    
    return dict(
        rms=rms,
        onset=onset_env,
        flux=flux,
        lowband=lb,
        perc_ratio=perc_ratio
    ), T


def beat_track(y, sr, hop):
    """
    Perform beat tracking to get tempo, beat frames, and beat times.
    """
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop,
        tightness=100
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    return float(tempo), beat_frames, beat_times, onset_env


def window_score(features, start_f, end_f, beats_in_window, beat_onset_env):
    """
    Compute raw feature scores for a single window.
    Returns a dict of unnormalized scores.
    """
    # Per-window statistics
    rms_mu, _ = frames_stats(features['rms'], start_f, end_f)
    onset_mu, _ = frames_stats(features['onset'], start_f, end_f)
    flux_mu, _ = frames_stats(features['flux'], start_f, end_f)
    lb_mu, _ = frames_stats(features['lowband'], start_f, end_f)
    perc_mu, _ = frames_stats(features['perc_ratio'], start_f, end_f)

    # Beat strength: onset envelope sampled at beat frames inside the window
    if len(beats_in_window) > 0:
        beat_strength = float(np.mean(beat_onset_env[beats_in_window]))
    else:
        beat_strength = onset_mu if not np.isnan(onset_mu) else 0.0

    # Beat regularity: coefficient of variation (lower is better) -> invert
    if len(beats_in_window) >= 3:
        ibis = np.diff(beats_in_window).astype(float)  # in frames
        cv = float(np.std(ibis) / (np.mean(ibis) + 1e-9))
        regularity_raw = 1.0 / (1.0 + cv)  # map [0,inf)->(0,1]
    else:
        regularity_raw = 0.5  # unknown; neutral

    # Return raw dict; normalization happens across all windows later
    return dict(
        beat_strength=beat_strength,
        regularity=regularity_raw,
        onset=onset_mu,
        flux=flux_mu,
        rms=rms_mu,
        lowband=lb_mu,
        perc=perc_mu
    )


def choose_best_segment(y, sr, seconds, hop=512, n_fft=2048, tempo_bias=None):
    """
    Analyze the track and choose the best N-second segment for danceability.
    
    Returns:
        start_sec: Start time in seconds
        end_sec: End time in seconds
        tempo: Estimated tempo in BPM
        weights: Dict of feature weights used
    """
    # Compute features
    tempo, beat_frames, beat_times, onset_env_bt = beat_track(y, sr, hop)
    feats, T = compute_features(y, sr, hop, n_fft)

    # Convert seconds to frames
    win_frames = max(1, int(round(seconds * sr / hop)))

    # Generate candidate starts anchored to beats (but evaluate exact-length windows)
    candidates = []
    for bf, bt in zip(beat_frames, beat_times):
        start_f = time_to_frame(bt, sr, hop)
        end_f = start_f + win_frames
        if end_f > T:
            break

        # Which beat frames fall inside this window?
        beat_idx = np.where((beat_frames >= start_f) & (beat_frames < end_f))[0]
        beats_in_window = beat_frames[beat_idx]  # frame indices

        sc = window_score(
            feats, start_f, end_f,
            beats_in_window=beats_in_window,
            beat_onset_env=onset_env_bt if len(onset_env_bt) == T else feats['onset']
        )
        sc['start_f'] = start_f
        sc['end_f'] = end_f
        candidates.append(sc)

    if not candidates:
        # Fallback: scan frame-wise
        for start_f in range(0, T - win_frames, win_frames // 3):
            end_f = start_f + win_frames
            sc = window_score(feats, start_f, end_f, beats_in_window=[], beat_onset_env=feats['onset'])
            sc['start_f'] = start_f
            sc['end_f'] = end_f
            candidates.append(sc)

    # Collect arrays for normalization
    keys = ['beat_strength', 'regularity', 'onset', 'flux', 'rms', 'lowband', 'perc']
    mat = {k: np.array([c[k] for c in candidates]) for k in keys}

    # Robust z-score normalization for each feature
    z = {k: robust_z(v) for k, v in mat.items()}

    # Weighted sum (tune as desired)
    w = dict(
        beat_strength=0.35,
        regularity=0.20,
        onset=0.15,
        flux=0.10,
        rms=0.10,
        lowband=0.05,
        perc=0.05
    )

    score = (
        w['beat_strength'] * z['beat_strength'] +
        w['regularity']    * z['regularity']    +
        w['onset']         * z['onset']         +
        w['flux']          * z['flux']          +
        w['rms']           * z['rms']           +
        w['lowband']       * z['lowband']       +
        w['perc']          * z['perc']
    )

    # Optional gentle tempo bias towards a target BPM (e.g., 120–130)
    # tempo_bias: tuple (target_bpm, sigma_bpm) -> multiplies score by Gaussian weight
    if tempo_bias is not None:
        target, sigma = tempo_bias
        g = math.exp(-0.5 * ((tempo - target) / (sigma + 1e-9))**2)
        score = score * (0.85 + 0.15 * g)  # small effect

    best_i = int(np.nanargmax(score))
    best = candidates[best_i]
    start_sec = best['start_f'] * hop / sr
    end_sec = start_sec + seconds
    return start_sec, end_sec, tempo, dict(weights=w)


def extract_and_save(y, sr, start_sec, end_sec, out_path):
    """
    Extract the audio segment and save to file.
    """
    a = max(0, int(round(start_sec * sr)))
    b = min(len(y), int(round(end_sec * sr)))
    snippet = y[a:b]
    if len(snippet) == 0:
        raise RuntimeError("Empty snippet; indices out of range.")
    sf.write(out_path, snippet, sr)
    return out_path


def main():
    p = argparse.ArgumentParser(
        description="Pick the most danceable N-second segment from a track.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract best 10 seconds
  python pick_danceable_segment.py my_song.mp3 --seconds 10
  
  # Extract best 5 seconds with tempo bias toward 124 BPM
  python pick_danceable_segment.py my_song.mp3 --seconds 5 --tempo_bias 124 15
  
  # Specify output path
  python pick_danceable_segment.py my_song.mp3 -s 5 -o output.wav
        """
    )
    p.add_argument("input", help="Path to audio file (wav/mp3/flac/etc)")
    p.add_argument("--seconds", "-s", type=float, default=10.0,
                   help="Snippet length in seconds (default: 10.0)")
    p.add_argument("--sr", type=int, default=22050,
                   help="Target sample rate (default: 22050)")
    p.add_argument("--out", "-o", default=None,
                   help="Output WAV path; defaults to <input>_bestNs.wav")
    p.add_argument("--tempo_bias", type=float, nargs=2, metavar=("TARGET_BPM", "SIGMA"),
                   help="Optional tempo bias, e.g., --tempo_bias 124 15")
    args = p.parse_args()

    print(f"Loading audio: {args.input}")
    y, sr = librosa.load(args.input, sr=args.sr, mono=True)
    
    print(f"Analyzing track for best {args.seconds}s segment...")
    start, end, tempo, weights = choose_best_segment(
        y, sr, seconds=args.seconds, hop=512, n_fft=2048,
        tempo_bias=tuple(args.tempo_bias) if args.tempo_bias else None
    )
    
    out = args.out or f"{args.input.rsplit('.', 1)[0]}_best{int(args.seconds)}s.wav"
    extract_and_save(y, sr, start, end, out)

    print(f"\n✅ Success!")
    print(f"Estimated tempo: {tempo:.1f} BPM")
    print(f"Best segment: {start:.3f}–{end:.3f} s ({end-start:.2f} s)")
    print(f"Wrote: {out}")
    print(f"Weights used: {weights}")


if __name__ == "__main__":
    main()


