#!/usr/bin/env python3
"""
Create custom rap song using reference tracks for style inspiration

Flow:
1. User describes their song
2. ChatGPT generates lyrics
3. User selects genre (maps to reference track)
4. ChatGPT creates music prompt inspired by reference track
5. ElevenLabs generates complete song
"""

import os
import sys
import argparse
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Reference tracks for each genre
REFERENCE_TRACKS = {
    "1": ("Trap", '"SICKO MODE" by Travis Scott - Modern trap with beat switches, 808s, ad-libs'),
    "2": ("Boom-Bap", '"N.Y. State of Mind" by Nas - Classic 90s East Coast, jazzy samples, hard drums'),
    "3": ("West Coast", '"Nuthin\' but a \'G\' Thang" by Dr. Dre & Snoop Dogg - G-funk synths, laid-back groove'),
    "4": ("Drill", '"Dior" by Pop Smoke - Dark UK drill, sliding 808s, aggressive energy'),
    "5": ("Cloud Rap", '"Yonkers" by Tyler, The Creator - Lo-fi, atmospheric, dark and dreamy'),
    "6": ("East Coast", '"Juicy" by The Notorious B.I.G. - Soulful sample, smooth flow, storytelling'),
    "7": ("Dirty South", '"In Da Club" by 50 Cent - Club banger, hard bass, catchy hook'),
    "8": ("Alternative", '"Ms. Jackson" by OutKast - Live instruments, unique sound, experimental'),
    "9": ("Conscious", '"Alright" by Kendrick Lamar - Jazzy, uplifting, socially conscious'),
    "10": ("Mumble Rap", '"Lifestyle" by Young Thug ft. Rich Homie Quan - Melodic, autotuned, triplet flow')
}

def read_file(path: str) -> str:
    """Read text file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def generate_lyrics_with_chatgpt(song_description: str, lyrics_prompt_template: str) -> str:
    """Generate rap lyrics from song description using ChatGPT 5.1"""
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    prompt = lyrics_prompt_template.replace("{SONG_DESCRIPTION}", song_description)
    
    print("=" * 70)
    print("✍️  Step 1: Generating Lyrics with ChatGPT 5.1")
    print("=" * 70)
    print(f"Song description: {song_description[:100]}...")
    print()
    print("🤖 Asking ChatGPT 5.1 to write lyrics...")
    
    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=f"You are a professional rap lyricist. Write lyrics that are catchy, flow well, and match the user's intent.\n\n{prompt}",
            reasoning={"effort": "medium"}
        )
        
        lyrics = response.output_text.strip()
        lyrics = lyrics.replace("```", "").strip()
        
        print()
        print("✅ Lyrics generated!")
        print()
        print("📝 Lyrics:")
        print("-" * 70)
        print(lyrics)
        print("-" * 70)
        print()
        
        return lyrics
        
    except Exception as e:
        print(f"❌ Error generating lyrics: {e}")
        raise

def generate_music_prompt_with_reference(reference_track: str, lyrics: str, prompt_template: str) -> str:
    """Generate music prompt inspired by reference track using ChatGPT 5.1"""
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    prompt = prompt_template.replace("{REFERENCE_TRACK}", reference_track).replace("{LYRICS}", lyrics)
    
    print("=" * 70)
    print("🎼 Step 3: Generating Music Prompt Inspired by Reference")
    print("=" * 70)
    print(f"Reference: {reference_track}")
    print()
    print("🤖 Asking ChatGPT 5.1 to analyze and create prompt...")
    
    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=f"You are a music producer expert with deep knowledge of hip-hop production. Analyze reference tracks and create detailed prompts for AI music generation.\n\n{prompt}",
            reasoning={"effort": "medium"}
        )
        
        music_prompt = response.output_text.strip()
        
        print()
        print("✅ Music prompt generated!")
        print()
        print("🎵 Music Prompt:")
        print("-" * 70)
        print(music_prompt[:300] + "..." if len(music_prompt) > 300 else music_prompt)
        print("-" * 70)
        print()
        
        return music_prompt
        
    except Exception as e:
        print(f"❌ Error generating music prompt: {e}")
        raise

def generate_song_with_elevenlabs(music_prompt: str, output_path: str, duration: int = 10) -> str:
    """Generate complete rap song using ElevenLabs Music API"""
    
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in .env")
    
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    print("=" * 70)
    print("🎵 Step 4: Generating Complete Song with ElevenLabs")
    print("=" * 70)
    print(f"Duration: {duration}s")
    print(f"Output: {output_path}")
    print()
    
    print("🎼 Sending to ElevenLabs Music API...")
    print("   (This may take 30-60 seconds)")
    print()
    
    try:
        response = client.music.stream(
            prompt=music_prompt,
            music_length_ms=duration * 1000
        )
        
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, "wb") as f:
            for chunk in response:
                f.write(chunk)
        
        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"✅ Song generated successfully!")
        print(f"📦 Size: {file_size_mb:.2f} MB")
        print(f"📁 Saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating song: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Create rap song using reference track inspiration'
    )
    
    parser.add_argument('--description', required=True, help='Song description file')
    parser.add_argument('--lyrics-prompt', default='prompts/chatgpt_lyrics_prompt.txt')
    parser.add_argument('--music-prompt-template', default='prompts/chatgpt_music_prompt_simple.txt')
    parser.add_argument('--genre', type=str, help='Genre number (1-10)')
    parser.add_argument('--output', required=True, help='Output MP3 path')
    parser.add_argument('--save-lyrics', help='Save lyrics to file')
    parser.add_argument('--save-music-prompt', help='Save music prompt to file')
    parser.add_argument('--duration', type=int, default=10)
    
    args = parser.parse_args()
    
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        print("❌ Missing API keys in .env")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("🎤 CUSTOM RAP WITH REFERENCE TRACK INSPIRATION")
    print("=" * 70)
    print()
    
    song_description = read_file(args.description)
    lyrics_prompt_template = read_file(args.lyrics_prompt)
    music_prompt_template = read_file(args.music_prompt_template)
    
    # Generate lyrics
    lyrics = generate_lyrics_with_chatgpt(song_description, lyrics_prompt_template)
    
    if args.save_lyrics:
        with open(args.save_lyrics, 'w') as f:
            f.write(lyrics)
        print(f"💾 Lyrics saved to: {args.save_lyrics}\n")
    
    # Select genre/reference
    if args.genre and args.genre in REFERENCE_TRACKS:
        genre_name, reference = REFERENCE_TRACKS[args.genre]
        print("=" * 70)
        print(f"🎸 Step 2: Using Reference Track")
        print("=" * 70)
        print(f"Genre: {genre_name}")
        print(f"Reference: {reference}")
        print("=" * 70)
        print()
    else:
        print("❌ Invalid or missing genre (1-10)")
        sys.exit(1)
    
    # Generate music prompt
    music_prompt = generate_music_prompt_with_reference(reference, lyrics, music_prompt_template)
    
    if args.save_music_prompt:
        with open(args.save_music_prompt, 'w') as f:
            f.write(music_prompt)
        print(f"💾 Music prompt saved to: {args.save_music_prompt}\n")
    
    # Generate song
    output_path = generate_song_with_elevenlabs(music_prompt, args.output, args.duration)
    
    print()
    print("=" * 70)
    print("🎉 SONG GENERATION COMPLETE!")
    print("=" * 70)
    print(f"🎵 Song: {output_path}")
    if args.save_lyrics:
        print(f"📝 Lyrics: {args.save_lyrics}")
    print("=" * 70)

if __name__ == "__main__":
    main()

