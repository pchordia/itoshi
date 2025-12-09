#!/usr/bin/env python3
"""
Create custom rap song from user description using ChatGPT + ElevenLabs

Flow:
1. User describes their song
2. ChatGPT generates lyrics
3. User selects genre
4. ChatGPT creates music prompt
5. ElevenLabs generates complete song (vocals + beat)
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

# Hip-hop subgenres ordered by popularity
GENRES = {
    "1": ("Trap", "Modern trap with 808s, hi-hats, and heavy bass (140-160 BPM)"),
    "2": ("Boom-Bap", "Classic 90s style with sampled drums and jazzy loops (85-95 BPM)"),
    "3": ("West Coast", "G-Funk sound with synths, funky bass, and laid-back vibe (90-100 BPM)"),
    "4": ("Drill", "Dark, aggressive beats with sliding 808s (140-150 BPM)"),
    "5": ("Cloud Rap", "Dreamy, atmospheric with reverb and spacey production (120-140 BPM)"),
    "6": ("East Coast", "Gritty, sample-heavy with hard drums (90-100 BPM)"),
    "7": ("Dirty South", "Crunk-influenced with heavy bass and energetic beats (140-150 BPM)"),
    "8": ("Alternative Hip-Hop", "Experimental, jazzy elements, unconventional (Variable BPM)"),
    "9": ("Conscious Rap", "Socially aware with jazzy/soulful backing (85-95 BPM)"),
    "10": ("Mumble Rap", "Melodic, heavily autotuned trap beats (130-150 BPM)")
}

def read_file(path: str) -> str:
    """Read text file"""
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def generate_lyrics_with_chatgpt(song_description: str, lyrics_prompt_template: str) -> str:
    """
    Generate rap lyrics from song description using ChatGPT 5.1
    
    Args:
        song_description: User's description of what they want
        lyrics_prompt_template: Template with {SONG_DESCRIPTION} placeholder
    
    Returns:
        Generated lyrics text
    """
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build prompt
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
            reasoning={"effort": "low"},
            text={"verbosity": "low"}
        )
        
        lyrics = response.output_text.strip()
        
        # Remove any markdown formatting
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

def generate_music_prompt_with_chatgpt(genre_name: str, genre_desc: str, lyrics: str, music_prompt_template: str) -> str:
    """
    Generate ElevenLabs music prompt from genre + lyrics using ChatGPT 5.1
    
    Args:
        genre_name: Name of the genre (e.g., "Trap")
        genre_desc: Description of the genre
        lyrics: The rap lyrics
        music_prompt_template: Template with {GENRE} and {LYRICS} placeholders
    
    Returns:
        Complete music prompt for ElevenLabs
    """
    
    if not OPENAI_API_KEY:
        raise ValueError("OPENAI_API_KEY not found in .env")
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Build prompt
    genre_info = f"{genre_name}: {genre_desc}"
    prompt = music_prompt_template.replace("{GENRE}", genre_info).replace("{LYRICS}", lyrics)
    
    print("=" * 70)
    print("🎼 Step 3: Generating Music Prompt with ChatGPT 5.1")
    print("=" * 70)
    print(f"Genre: {genre_name}")
    print()
    print("🤖 Asking ChatGPT 5.1 to craft music prompt...")
    
    try:
        response = client.responses.create(
            model="gpt-5.1",
            input=f"You are a music producer expert. Create detailed prompts for AI music generation that specify instruments, BPM, vocal style, and production elements.\n\n{prompt}",
            reasoning={"effort": "medium"},
            text={"verbosity": "medium"}
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
    """
    Generate complete rap song using ElevenLabs Music API
    
    Args:
        music_prompt: Complete prompt with genre description + lyrics
        output_path: Where to save the generated MP3
        duration: Duration in seconds (default 10)
    
    Returns:
        Path to generated song
    """
    
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
        # Generate complete song (vocals + instrumentals)
        response = client.music.stream(
            prompt=music_prompt,
            music_length_ms=duration * 1000
        )
        
        # Save the audio
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

def select_genre_interactive() -> tuple:
    """
    Let user select genre interactively
    
    Returns:
        (genre_name, genre_description)
    """
    print("=" * 70)
    print("🎸 Step 2: Select Hip-Hop Genre")
    print("=" * 70)
    print()
    
    for key, (name, desc) in GENRES.items():
        print(f"{key:2}. {name:20} - {desc}")
    
    print()
    choice = input("Select genre (1-10): ").strip()
    
    if choice not in GENRES:
        print(f"❌ Invalid choice: {choice}")
        sys.exit(1)
    
    genre_name, genre_desc = GENRES[choice]
    print(f"✅ Selected: {genre_name}")
    print()
    
    return genre_name, genre_desc

def main():
    parser = argparse.ArgumentParser(
        description='Create custom rap song: Description → ChatGPT → ElevenLabs'
    )
    
    # Input
    parser.add_argument('--description', required=True, 
                       help='Path to song description text file')
    parser.add_argument('--lyrics-prompt', default='prompts/chatgpt_lyrics_prompt.txt',
                       help='Path to ChatGPT lyrics generation prompt')
    parser.add_argument('--music-prompt', default='prompts/chatgpt_music_prompt.txt',
                       help='Path to ChatGPT music prompt generation template')
    
    # Genre selection
    parser.add_argument('--genre', type=str, 
                       help='Genre number (1-10) or skip for interactive selection')
    
    # Output
    parser.add_argument('--output', required=True, 
                       help='Output MP3 path for complete song')
    parser.add_argument('--save-lyrics', help='Optional: Save generated lyrics to file')
    parser.add_argument('--save-music-prompt', help='Optional: Save music prompt to file')
    
    # Settings
    parser.add_argument('--duration', type=int, default=10,
                       help='Song duration in seconds (default: 10)')
    
    args = parser.parse_args()
    
    # Validate API keys
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in .env")
        sys.exit(1)
    
    if not ELEVENLABS_API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in .env")
        sys.exit(1)
    
    print()
    print("=" * 70)
    print("🎤 CUSTOM RAP SONG GENERATION")
    print("=" * 70)
    print()
    
    # Read inputs
    song_description = read_file(args.description)
    lyrics_prompt_template = read_file(args.lyrics_prompt)
    music_prompt_template = read_file(args.music_prompt)
    
    # STEP 1: Generate lyrics with ChatGPT
    lyrics = generate_lyrics_with_chatgpt(song_description, lyrics_prompt_template)
    
    if args.save_lyrics:
        with open(args.save_lyrics, 'w', encoding='utf-8') as f:
            f.write(lyrics)
        print(f"💾 Lyrics saved to: {args.save_lyrics}")
        print()
    
    # STEP 2: Select genre
    if args.genre and args.genre in GENRES:
        genre_name, genre_desc = GENRES[args.genre]
        print("=" * 70)
        print(f"🎸 Step 2: Using Genre: {genre_name}")
        print("=" * 70)
        print()
    else:
        genre_name, genre_desc = select_genre_interactive()
    
    # STEP 3: Generate music prompt with ChatGPT
    music_prompt = generate_music_prompt_with_chatgpt(
        genre_name, genre_desc, lyrics, music_prompt_template
    )
    
    if args.save_music_prompt:
        with open(args.save_music_prompt, 'w', encoding='utf-8') as f:
            f.write(music_prompt)
        print(f"💾 Music prompt saved to: {args.save_music_prompt}")
        print()
    
    # STEP 4: Generate complete song with ElevenLabs
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

