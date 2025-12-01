#!/usr/bin/env python3
"""
Extract 10-second verse excerpts from rap songs
1. Get lyrics from Genius
2. Transcribe with ElevenLabs Speech-to-Text
3. Find best verse section (not hook)
4. Extract 10s starting on beat
"""

import os
import sys
import re
import string
import librosa
import soundfile as sf
import numpy as np
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs
import requests
from bs4 import BeautifulSoup

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")
GENIUS_ACCESS_TOKEN = os.getenv("GENIUS_ACCESS_TOKEN", "")  # Get from https://genius.com/api-clients

def search_genius_lyrics(song_title: str, artist: str = None) -> dict:
    """Search for song on Genius and get lyrics using direct API"""
    
    if not GENIUS_ACCESS_TOKEN:
        print("⚠️  GENIUS_ACCESS_TOKEN not found, skipping lyrics lookup")
        return None
    
    try:
        # Search for song
        query = f"{artist} {song_title}" if artist else song_title
        print(f"🔍 Searching Genius: {query}")
        
        headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
        search_url = "https://api.genius.com/search"
        params = {"q": query}
        
        response = requests.get(search_url, headers=headers, params=params, timeout=10)
        
        if response.status_code != 200:
            print(f"❌ Search failed: {response.status_code}")
            return None
        
        data = response.json()
        hits = data.get("response", {}).get("hits", [])
        
        if not hits:
            print(f"❌ No results found")
            return None
        
        result = hits[0]["result"]
        song_url = result["url"]
        song_title = result["title"]
        artist_name = result["primary_artist"]["name"]
        song_id = result.get("id")
        
        print(f"📝 Found: {song_title} by {artist_name}")
        print(f"🔗 {song_url}")
        
        # Scrape lyrics from page
        page = requests.get(song_url, timeout=10)
        soup = BeautifulSoup(page.content, 'html.parser')
        
        # Find lyrics containers
        lyrics_divs = soup.find_all('div', {'data-lyrics-container': 'true'})
        
        if not lyrics_divs:
            print("❌ Could not extract lyrics")
            return None
        
        # Extract text from all lyrics containers
        lyrics_parts = []
        for div in lyrics_divs:
            # Get text but preserve line breaks
            for br in div.find_all('br'):
                br.replace_with('\n')
            lyrics_parts.append(div.get_text())
        
        lyrics = '\n'.join(lyrics_parts)
        
        return {
            'title': song_title,
            'artist': artist_name,
            'url': song_url,
            'id': song_id,
            'lyrics': lyrics
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def transcribe_audio(audio_path: str) -> dict:
    """Transcribe audio using ElevenLabs Speech-to-Text"""
    
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY required")
    
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    print(f"🎤 Transcribing audio...")
    
    # Note: ElevenLabs doesn't have speech-to-text in their main API
    # We'll use Whisper (OpenAI) instead which is better for this
    from openai import OpenAI
    
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    with open(audio_path, 'rb') as audio_file:
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json"
        )
    
    return {
        'text': transcript.text,
        'words': transcript.words if hasattr(transcript, 'words') else []
    }

def find_verse_sections(lyrics: str) -> list:
    """Identify verse sections (not hooks/choruses)"""
    
    sections = []
    lines = lyrics.split('\n')
    
    current_section = []
    section_type = 'verse'
    seen_section_header = False
    
    for line in lines:
        line_lower = line.lower().strip()
        
        # Detect section markers like [Verse 1], [Chorus], etc.
        if line_lower.startswith('[') and ']' in line_lower:
            seen_section_header = True
            # Save previous section
            if current_section:
                sections.append({
                    'type': section_type,
                    'lines': current_section.copy()
                })
                current_section = []
            
            # Determine new section type
            if any(word in line_lower for word in ['chorus', 'hook', 'refrain']):
                section_type = 'chorus'
            elif any(word in line_lower for word in ['verse', 'rap']):
                section_type = 'verse'
            elif any(word in line_lower for word in ['bridge', 'outro', 'intro']):
                section_type = 'other'
            else:
                section_type = 'other'
            
            continue
        
        # Skip metadata / headers before the first section header
        if not seen_section_header:
            continue
        
        if line.strip():
            current_section.append(line)
    
    # Add final section
    if current_section:
        sections.append({
            'type': section_type,
            'lines': current_section.copy()
        })
    
    # Filter to verses only
    verses = [s for s in sections if s['type'] == 'verse']
    
    return verses


def _normalize_for_match(text: str) -> str:
    """Normalize text for fuzzy matching between lyrics and transcript."""
    text = text.lower()
    text = text.replace('\n', ' ')
    # Remove bracketed annotations like [Verse 1], [Chorus], etc.
    text = re.sub(r'\[.*?\]', ' ', text)
    # Remove punctuation
    text = text.translate(str.maketrans('', '', string.punctuation))
    # Collapse whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def pick_most_annotated_verse(verses: list, lyrics_data: dict) -> dict:
    """
    Use Genius referents API to find which verse has the most annotations.
    Falls back to the first verse if anything fails.
    """
    if not verses:
        return None
    song_id = lyrics_data.get("id")
    if not song_id or not GENIUS_ACCESS_TOKEN:
        return verses[0]

    headers = {"Authorization": f"Bearer {GENIUS_ACCESS_TOKEN}"}
    url = "https://api.genius.com/referents"
    params = {"song_id": song_id, "text_format": "plain"}

    try:
        resp = requests.get(url, headers=headers, params=params, timeout=10)
        if resp.status_code != 200:
            print(f"⚠️  Referents request failed: {resp.status_code}")
            return verses[0]

        data = resp.json()
        referents = data.get("response", {}).get("referents", [])
        print(f"💬 Found {len(referents)} annotated fragments on Genius")

        # Precompute verse texts
        verse_texts = ["\n".join(v["lines"]) for v in verses]

        best_idx = 0
        best_count = -1

        for i, vtext in enumerate(verse_texts):
            count = 0
            for ref in referents:
                fragment = ref.get("fragment") or ""
                if fragment and fragment in vtext:
                    count += 1
            print(f"   • Verse {i+1} has {count} annotated fragments")
            if count > best_count:
                best_count = count
                best_idx = i

        if best_count <= 0:
            print("ℹ️  No verse had annotated fragments, using first verse")
            return verses[0]

        print(f"🏆 Choosing verse {best_idx+1} as most annotated (count={best_count})")
        return verses[best_idx]

    except Exception as e:
        print(f"⚠️  Error while fetching/using referents: {e}")
        return verses[0]

def find_best_verse_timing(audio_path: str, verse_text: str, transcription: dict) -> tuple:
    """Find where the verse appears in the audio"""
    
    # Normalize verse and transcript for matching
    verse_norm = _normalize_for_match(verse_text)
    transcript_norm = _normalize_for_match(transcription['text'])
    
    verse_tokens = verse_norm.split()
    if len(verse_tokens) < 5:
        print("⚠️  Verse too short after normalization")
        return None, None
    
    # Try sliding windows of different sizes for a robust fuzzy match
    best_pos = -1
    best_len = 0
    for window_size in (12, 10, 8, 6):
        if len(verse_tokens) < window_size:
            continue
        for i in range(0, len(verse_tokens) - window_size + 1):
            snippet = ' '.join(verse_tokens[i:i + window_size])
            pos = transcript_norm.find(snippet)
            if pos != -1:
                best_pos = pos
                best_len = len(snippet)
                break
        if best_pos != -1:
            break
    
    if best_pos == -1:
        print("⚠️  Could not find verse snippet in transcription")
        return None, None
    
    print(f"✅ Matched verse snippet in transcription (window ~{best_len} chars)")
    
    # Estimate timing based on character position ratio
    total_duration = librosa.get_duration(path=audio_path)
    estimated_start = (best_pos / max(1, len(transcript_norm))) * total_duration
    
    return estimated_start, estimated_start + 10.0

def extract_10s_on_beat(audio_path: str, start_time: float, output_path: str):
    """Extract 10s segment starting on nearest beat"""
    
    print(f"🎵 Loading audio for extraction...")
    y, sr = librosa.load(audio_path, sr=None, mono=True)
    
    # Detect beats
    tempo, beat_frames = librosa.beat.beat_track(y=y, sr=sr)
    beat_times = librosa.frames_to_time(beat_frames, sr=sr)
    
    # Find nearest beat to start_time
    nearest_beat_idx = np.argmin(np.abs(beat_times - start_time))
    actual_start = beat_times[nearest_beat_idx]
    
    print(f"🎯 Extracting from {actual_start:.2f}s to {actual_start + 10:.2f}s")
    # tempo can be a scalar or a small ndarray depending on librosa version
    try:
        tempo_scalar = float(np.asarray(tempo).ravel()[0])
        print(f"🥁 Starting on beat (tempo: {tempo_scalar:.1f} BPM)")
    except Exception:
        print(f"🥁 Starting on beat (tempo: {tempo} BPM)")
    
    # Extract segment
    start_sample = int(actual_start * sr)
    end_sample = int((actual_start + 10.0) * sr)
    segment = y[start_sample:end_sample]
    
    # Save
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    sf.write(output_path, segment, sr, format='MP3', subtype='MPEG_LAYER_III')
    
    return actual_start, actual_start + 10.0

def process_song(audio_path: str, output_dir: str):
    """Process one song through the full pipeline"""
    
    filename = Path(audio_path).stem
    
    print("=" * 70)
    print(f"🎵 Processing: {filename}")
    print("=" * 70)
    print()
    
    # Parse artist and title from filename
    # Format: "Artist - Title.mp3"
    parts = filename.split(' - ', 1)
    if len(parts) == 2:
        artist = parts[0].strip()
        title = parts[1].strip()
        # Remove "(Official Video)" etc
        title = re.sub(r'\(.*?\)', '', title).strip()
    else:
        artist = None
        title = filename
    
    # Step 1: Get lyrics
    lyrics_data = search_genius_lyrics(title, artist)
    
    if not lyrics_data:
        print("⚠️  Proceeding without lyrics")
        verses = []
    else:
        # Find verses
        verses = find_verse_sections(lyrics_data['lyrics'])
        print(f"📖 Found {len(verses)} verse sections")
        if verses:
            # Prefer the verse that has the most Genius annotations
            best_verse = pick_most_annotated_verse(verses, lyrics_data)
        else:
            best_verse = None
    
    # Step 2: Transcribe
    print()
    transcription = transcribe_audio(audio_path)
    print(f"✅ Transcribed: {len(transcription['text'])} chars")
    print()
    
    # Step 3: Find best verse
    if verses and best_verse:
        # Use the selected best verse (by annotations if available)
        verse_text = '\n'.join(best_verse['lines'])
        print(f"📍 Selected verse (first {len(verse_text)} chars):")
        print(verse_text[:200] + "...")
        print()
        
        # Find timing
        start_time, end_time = find_best_verse_timing(audio_path, verse_text, transcription)
        
        if start_time is None:
            print("⚠️  Could not match verse to audio, using high-energy section")
            start_time = None
    else:
        # No lyrics - find high-energy section
        print("📊 Finding high-energy section...")
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        
        # Analyze energy in 10s windows
        duration = len(y) / sr
        best_score = -1
        best_start = 0
        
        for start in np.arange(0, duration - 10, 1.0):
            start_sample = int(start * sr)
            end_sample = int((start + 10) * sr)
            segment = y[start_sample:end_sample]
            
            # Score by RMS energy
            rms = np.sqrt(np.mean(segment**2))
            
            if rms > best_score:
                best_score = rms
                best_start = start
        
        start_time = best_start
    
    # Step 4: Extract 10s on beat
    print()
    output_filename = f"{filename}_10s_verse.mp3"
    output_path = os.path.join(output_dir, output_filename)
    
    # If no start_time, use high-energy section
    if start_time is None:
        print("📊 Using high-energy section instead of verse")
        # Use the high-energy finding code from above
        y, sr = librosa.load(audio_path, sr=None, mono=True)
        duration = len(y) / sr
        best_score = -1
        best_start = 0
        
        for start in np.arange(0, duration - 10, 1.0):
            start_sample = int(start * sr)
            end_sample = int((start + 10) * sr)
            segment = y[start_sample:end_sample]
            rms = np.sqrt(np.mean(segment**2))
            
            if rms > best_score:
                best_score = rms
                best_start = start
        
        start_time = best_start
    
    actual_start, actual_end = extract_10s_on_beat(audio_path, start_time, output_path)
    
    print()
    print(f"✅ Extracted: {output_path}")
    print(f"⏱️  Timing: {actual_start:.2f}s - {actual_end:.2f}s")
    print()

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract 10s verse excerpts from rap songs')
    parser.add_argument('--input-dir', required=True, help='Directory with rap songs')
    parser.add_argument('--output-dir', default='outputs/rap_excerpts_10s', help='Output directory')
    
    args = parser.parse_args()
    
    # Get all MP3 files
    audio_files = list(Path(args.input_dir).glob('*.mp3'))
    
    print(f"📊 Found {len(audio_files)} rap songs")
    print()
    
    for audio_path in audio_files:
        try:
            process_song(str(audio_path), args.output_dir)
        except Exception as e:
            print(f"❌ Error processing {audio_path.name}: {e}")
            print()
    
    print("=" * 70)
    print("✅ Complete!")
    print(f"📁 Output: {args.output_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()

