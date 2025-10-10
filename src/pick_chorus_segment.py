#!/usr/bin/env python3
"""
Extract the best N-second segment from a music track's chorus.

Uses a two-stage approach:
1. Find the chorus region using repetition, vocal presence, energy, and consistency
2. Pick the most danceable N seconds within the chorus

Usage:
    python pick_chorus_segment.py my_song.mp3 --seconds 10
    python pick_chorus_segment.py my_song.mp3 --seconds 5 --tempo_bias 124 15
"""

import argparse
import math
import numpy as np
import soundfile as sf
import librosa


# ============================================================================
# Utility functions
# ============================================================================

def robust_z(x):
    """Compute robust z-scores using median and MAD."""
    x = np.asarray(x, dtype=float)
    med = np.median(x)
    mad = np.median(np.abs(x - med)) + 1e-9
    return (x - med) / (1.4826 * mad)


def _col_norm(X):
    """Normalize columns of a matrix."""
    return X / (np.linalg.norm(X, axis=0, keepdims=True) + 1e-9)


def _robust_z_pertrack(values):
    """Robust z-score per track."""
    med = np.median(values)
    mad = np.median(np.abs(values - med)) + 1e-9
    return (values - med) / (1.4826 * mad)


def time_to_frame(t, sr, hop):
    """Convert time in seconds to frame index."""
    return int(round(t * sr / hop))


def frames_stats(x, start_f, end_f):
    """Compute mean and std of a feature array within a frame window."""
    xw = x[max(0, start_f):min(len(x), end_f)]
    if len(xw) == 0:
        return np.nan, np.nan
    return float(np.mean(xw)), float(np.std(xw))


# ============================================================================
# Danceability features (from original script)
# ============================================================================

def spectral_flux(S):
    """Compute spectral flux (positive changes in spectrum)."""
    d = np.diff(S, axis=1)
    d[d < 0] = 0.0
    flux = np.concatenate([np.zeros((S.shape[0], 1)), d], axis=1).sum(axis=0)
    return flux


def lowband_ratio(S, sr, n_fft, cutoff_hz=150.0):
    """Compute ratio of low-frequency energy to total energy."""
    freqs = np.fft.rfftfreq(n_fft, d=1.0/sr)
    k = np.searchsorted(freqs, cutoff_hz)
    low = S[:k, :].sum(axis=0)
    tot = S.sum(axis=0) + 1e-9
    return low / tot


def percussive_ratio(y, sr, hop):
    """Estimate percussive vs total energy using HPSS."""
    y_h, y_p = librosa.effects.hpss(y)
    rms_tot = librosa.feature.rms(y=y, hop_length=hop).ravel()
    rms_perc = librosa.feature.rms(y=y_p, hop_length=hop).ravel()
    return (rms_perc + 1e-9) / (rms_tot + 1e-9)


def compute_features(y, sr, hop, n_fft):
    """Compute all frame-wise features for the entire track."""
    S = np.abs(librosa.stft(y, n_fft=n_fft, hop_length=hop))
    rms = librosa.feature.rms(S=S).ravel()
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    flux = spectral_flux(S)
    lb = lowband_ratio(S, sr=sr, n_fft=n_fft, cutoff_hz=150.0)
    perc_ratio = percussive_ratio(y, sr=sr, hop=hop)

    T = min(len(rms), len(onset_env), len(flux), len(lb), len(perc_ratio))
    return dict(
        rms=rms[:T],
        onset=onset_env[:T],
        flux=flux[:T],
        lowband=lb[:T],
        perc_ratio=perc_ratio[:T]
    ), T


def beat_track(y, sr, hop):
    """Perform beat tracking to get tempo, beat frames, and beat times."""
    onset_env = librosa.onset.onset_strength(y=y, sr=sr, hop_length=hop)
    tempo, beat_frames = librosa.beat.beat_track(
        onset_envelope=onset_env,
        sr=sr,
        hop_length=hop,
        tightness=100
    )
    beat_times = librosa.frames_to_time(beat_frames, sr=sr, hop_length=hop)
    return float(tempo), beat_frames, beat_times, onset_env


# ============================================================================
# Chorus detection features
# ============================================================================

def beat_sync_chroma(y, sr, hop, beat_frames):
    """Return 12xNbeats chroma synchronized to beats."""
    chroma = librosa.feature.chroma_cqt(y=y, sr=sr, hop_length=hop)
    if len(beat_frames) < 2:
        return _col_norm(chroma), None
    C_sync = librosa.util.sync(chroma, beat_frames, aggregate=np.median)
    return _col_norm(C_sync), chroma


def beat_sync_rms(y, sr, hop, beat_frames):
    """Beat-synchronized RMS energy."""
    S = np.abs(librosa.stft(y, n_fft=2048, hop_length=hop))
    rms = librosa.feature.rms(S=S).ravel()
    if len(beat_frames) < 2:
        return rms
    return librosa.util.sync(rms[np.newaxis, :], beat_frames, aggregate=np.mean).ravel()


def beat_sync_vocal_prob(y, sr, hop, beat_frames):
    """Prefer pyin voicing prob; fallback to harmonic midband energy ratio."""
    try:
        f0, vflag, vprob = librosa.pyin(
            y, fmin=librosa.note_to_hz('C2'),
            fmax=librosa.note_to_hz('C6'),
            sr=sr, frame_length=2048, hop_length=hop
        )
        vprob = np.nan_to_num(vprob, nan=0.0)
        vseries = vprob
    except Exception:
        # Fallback: harmonic energy in vocal band
        y_h, _ = librosa.effects.hpss(y)
        S_h = np.abs(librosa.stft(y_h, n_fft=2048, hop_length=hop))
        freqs = np.fft.rfftfreq(2048, 1.0/sr)
        band = (freqs >= 300) & (freqs <= 3400)
        vseries = (S_h[band, :].mean(axis=0)) / (S_h.mean(axis=0) + 1e-9)
    
    if len(beat_frames) < 2:
        return vseries
    return librosa.util.sync(vseries[np.newaxis, :], beat_frames, aggregate=np.mean).ravel()


def _sequence_cosine_topk(Xn, i, L, min_gap=8, topk=2):
    """Average of top-k sequence cosine matches to other positions."""
    N = Xn.shape[1]
    if i + L > N:
        return 0.0
    W = Xn[:, i:i+L]
    scores = []
    for j in range(0, N - L + 1):
        if abs(j - i) < min_gap:
            continue
        s = float(np.mean(np.sum(W * Xn[:, j:j+L], axis=0)))
        scores.append(s)
    if not scores:
        return 0.0
    scores.sort(reverse=True)
    return float(np.mean(scores[:min(topk, len(scores))]))


def _internal_consistency(Xn, i, L):
    """Mean off-diagonal similarity within the window."""
    W = Xn[:, i:i+L]
    S = W.T @ W
    m = S.shape[0]
    mask = np.ones_like(S, dtype=bool)
    np.fill_diagonal(mask, False)
    return float(np.mean(S[mask]))


def find_chorus_region(y, sr, hop, beat_frames, lengths_beats=(16, 24, 32)):
    """
    Find the chorus region using repetition, vocal presence, energy, and consistency.
    Returns (start_frame, end_frame, best_info) or None.
    """
    if len(beat_frames) < min(lengths_beats) + 1:
        return None
    
    Xn, _ = beat_sync_chroma(y, sr, hop, beat_frames)
    Nbeats = Xn.shape[1]

    vbeat = beat_sync_vocal_prob(y, sr, hop, beat_frames)[:Nbeats]
    rmsbeat = beat_sync_rms(y, sr, hop, beat_frames)[:Nbeats]
    vbeat = vbeat / (np.max(vbeat) + 1e-9)
    rmsbeat = rmsbeat / (np.max(rmsbeat) + 1e-9)

    candidates = []
    for L in lengths_beats:
        if Nbeats < L + 1:
            continue
        for i in range(0, Nbeats - L):
            rep = _sequence_cosine_topk(Xn, i, L, min_gap=8, topk=2)
            voc = float(np.mean(vbeat[i:i+L]))
            eng = float(np.mean(rmsbeat[i:i+L]))
            cons = _internal_consistency(Xn, i, L)
            candidates.append(dict(i=i, L=L, rep=rep, voc=voc, eng=eng, cons=cons))

    if not candidates:
        return None

    # Robust z per feature
    for key in ['rep', 'voc', 'eng', 'cons']:
        z = _robust_z_pertrack(np.array([c[key] for c in candidates]))
        for c, val in zip(candidates, z):
            c['z_' + key] = float(val)

    # Weighted chorusness
    for c in candidates:
        c['chorusness'] = (0.50*c['z_rep'] + 0.20*c['z_voc'] +
                           0.15*c['z_eng'] + 0.15*c['z_cons'])

    best = max(candidates, key=lambda x: x['chorusness'])
    start_frame = int(beat_frames[best['i']])
    end_frame = int(beat_frames[best['i'] + best['L']])
    return start_frame, end_frame, best


# ============================================================================
# Danceability window scoring
# ============================================================================

def window_score(features, start_f, end_f, beats_in_window, beat_onset_env):
    """Compute raw feature scores for a single window."""
    rms_mu, _ = frames_stats(features['rms'], start_f, end_f)
    onset_mu, _ = frames_stats(features['onset'], start_f, end_f)
    flux_mu, _ = frames_stats(features['flux'], start_f, end_f)
    lb_mu, _ = frames_stats(features['lowband'], start_f, end_f)
    perc_mu, _ = frames_stats(features['perc_ratio'], start_f, end_f)

    if len(beats_in_window) > 0:
        beat_strength = float(np.mean(beat_onset_env[beats_in_window]))
    else:
        beat_strength = onset_mu if not np.isnan(onset_mu) else 0.0

    if len(beats_in_window) >= 3:
        ibis = np.diff(beats_in_window).astype(float)
        cv = float(np.std(ibis) / (np.mean(ibis) + 1e-9))
        regularity_raw = 1.0 / (1.0 + cv)
    else:
        regularity_raw = 0.5

    return dict(
        beat_strength=beat_strength,
        regularity=regularity_raw,
        onset=onset_mu,
        flux=flux_mu,
        rms=rms_mu,
        lowband=lb_mu,
        perc=perc_mu
    )


def choose_best_segment(y, sr, seconds, hop=512, n_fft=2048, tempo_bias=None, limit_to_frames=None):
    """
    Analyze the track and choose the best N-second segment for danceability.
    If limit_to_frames is provided, only consider candidates within that range.
    """
    tempo, beat_frames, beat_times, onset_env_bt = beat_track(y, sr, hop)
    feats, T = compute_features(y, sr, hop, n_fft)

    win_frames = max(1, int(round(seconds * sr / hop)))

    candidates = []
    for bf, bt in zip(beat_frames, beat_times):
        start_f = time_to_frame(bt, sr, hop)
        end_f = start_f + win_frames
        if end_f > T:
            break
        
        # Apply frame limit if specified
        if limit_to_frames is not None:
            lo, hi = limit_to_frames
            if not (start_f >= lo and end_f <= hi):
                continue

        beat_idx = np.where((beat_frames >= start_f) & (beat_frames < end_f))[0]
        beats_in_window = beat_frames[beat_idx]

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
            if limit_to_frames is not None:
                lo, hi = limit_to_frames
                if not (start_f >= lo and end_f <= hi):
                    continue
            sc = window_score(feats, start_f, end_f, beats_in_window=[], beat_onset_env=feats['onset'])
            sc['start_f'] = start_f
            sc['end_f'] = end_f
            candidates.append(sc)

    if not candidates:
        raise RuntimeError("No valid candidates found in the specified region.")

    keys = ['beat_strength', 'regularity', 'onset', 'flux', 'rms', 'lowband', 'perc']
    mat = {k: np.array([c[k] for c in candidates]) for k in keys}
    z = {k: robust_z(v) for k, v in mat.items()}

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

    if tempo_bias is not None:
        target, sigma = tempo_bias
        g = math.exp(-0.5 * ((tempo - target) / (sigma + 1e-9))**2)
        score = score * (0.85 + 0.15 * g)

    best_i = int(np.nanargmax(score))
    best = candidates[best_i]
    start_sec = best['start_f'] * hop / sr
    end_sec = start_sec + seconds
    return start_sec, end_sec, tempo, dict(weights=w)


def extract_and_save(y, sr, start_sec, end_sec, out_path):
    """Extract the audio segment and save to file."""
    a = max(0, int(round(start_sec * sr)))
    b = min(len(y), int(round(end_sec * sr)))
    snippet = y[a:b]
    if len(snippet) == 0:
        raise RuntimeError("Empty snippet; indices out of range.")
    sf.write(out_path, snippet, sr)
    return out_path


def main():
    parser = argparse.ArgumentParser(
        description="Pick the best N-second segment from a track's chorus.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract best 10 seconds from chorus
  python pick_chorus_segment.py my_song.mp3 --seconds 10
  
  # Extract best 5 seconds with tempo bias
  python pick_chorus_segment.py my_song.mp3 --seconds 5 --tempo_bias 124 15
        """
    )
    parser.add_argument("input", help="Path to audio file (wav/mp3/flac/etc)")
    parser.add_argument("--seconds", "-s", type=float, default=10.0,
                        help="Snippet length in seconds (default: 10.0)")
    parser.add_argument("--sr", type=int, default=22050,
                        help="Target sample rate (default: 22050)")
    parser.add_argument("--out", "-o", default=None,
                        help="Output WAV path; defaults to <input>_chorus_Ns.wav")
    parser.add_argument("--tempo_bias", type=float, nargs=2, metavar=("TARGET_BPM", "SIGMA"),
                        help="Optional tempo bias, e.g., --tempo_bias 124 15")
    parser.add_argument("--no-chorus", action="store_true",
                        help="Skip chorus detection, use full track")
    args = parser.parse_args()

    print(f"Loading audio: {args.input}")
    y, sr = librosa.load(args.input, sr=args.sr, mono=True)
    
    hop = 512
    
    if not args.no_chorus:
        print("Detecting chorus region...")
        tempo, beat_frames, beat_times, onset_env_bt = beat_track(y, sr, hop)
        chorus_region = find_chorus_region(y, sr, hop=hop, beat_frames=beat_frames)
        
        if chorus_region is not None:
            chorus_lo, chorus_hi, info = chorus_region
            chorus_duration = (chorus_hi - chorus_lo) * hop / sr
            print(f"✅ Chorus found: beats {info['i']}–{info['i']+info['L']} "
                  f"(~{chorus_duration:.1f}s), chorusness score={info['chorusness']:.2f}")
            print(f"   Repetition: {info['rep']:.3f}, Vocal: {info['voc']:.3f}, "
                  f"Energy: {info['eng']:.3f}, Consistency: {info['cons']:.3f}")
            
            print(f"Finding best {args.seconds}s segment within chorus...")
            start, end, tempo, weights = choose_best_segment(
                y, sr, seconds=args.seconds, hop=hop, n_fft=2048,
                tempo_bias=tuple(args.tempo_bias) if args.tempo_bias else None,
                limit_to_frames=(chorus_lo, chorus_hi)
            )
        else:
            print("⚠️  No clear chorus detected, using full track...")
            start, end, tempo, weights = choose_best_segment(
                y, sr, seconds=args.seconds, hop=hop, n_fft=2048,
                tempo_bias=tuple(args.tempo_bias) if args.tempo_bias else None
            )
    else:
        print(f"Analyzing track for best {args.seconds}s segment (no chorus detection)...")
        start, end, tempo, weights = choose_best_segment(
            y, sr, seconds=args.seconds, hop=hop, n_fft=2048,
            tempo_bias=tuple(args.tempo_bias) if args.tempo_bias else None
        )
    
    out = args.out or f"{args.input.rsplit('.', 1)[0]}_chorus_{int(args.seconds)}s.wav"
    extract_and_save(y, sr, start, end, out)

    print(f"\n✅ Success!")
    print(f"Estimated tempo: {tempo:.1f} BPM")
    print(f"Best segment: {start:.3f}–{end:.3f} s ({end-start:.2f} s)")
    print(f"Wrote: {out}")
    print(f"Weights used: {weights}")


if __name__ == "__main__":
    main()



