#!/usr/bin/env python3
"""
Generate rap vocal track from lyrics using ElevenLabs Music API
"""

import os
import sys
import time
import argparse
from pathlib import Path
from dotenv import load_dotenv
from elevenlabs.client import ElevenLabs

load_dotenv()

ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

def read_lyrics(lyrics_path: str) -> str:
    """Read lyrics from file"""
    with open(lyrics_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def read_vocal_prompt_template(template_path: str) -> str:
    """Read vocal prompt template"""
    with open(template_path, 'r', encoding='utf-8') as f:
        return f.read().strip()

def generate_vocal_track(lyrics: str, vocal_prompt_template: str, output_path: str, duration: int = 10) -> str:
    """
    Generate acapella rap vocal track using ElevenLabs Music API
    
    Args:
        lyrics: The rap lyrics text
        vocal_prompt_template: Template with {LYRICS} placeholder
        output_path: Where to save the generated MP3
        duration: Track duration in seconds (default 10)
    
    Returns:
        Path to generated vocal track
    """
    
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in .env")
    
    # Initialize ElevenLabs client
    client = ElevenLabs(api_key=ELEVENLABS_API_KEY)
    
    # Build full prompt
    full_prompt = vocal_prompt_template.replace("{LYRICS}", lyrics)
    
    print("=" * 70)
    print("🎤 Generating Rap Vocal Track with ElevenLabs Music API")
    print("=" * 70)
    print(f"Lyrics: {lyrics[:80]}...")
    print(f"Duration: {duration}s")
    print(f"Output: {output_path}")
    print()
    
    print("🎵 Sending to ElevenLabs Music API...")
    print(f"Prompt: {full_prompt[:150]}...")
    print()
    
    try:
        # Generate music using ElevenLabs Music API
        # Note: This uses the music generation endpoint
        response = client.text_to_sound_effects.convert(
            text=full_prompt,
            duration_seconds=duration,
            prompt_influence=0.3
        )
        
        # Save the audio
        os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
        
        with open(output_path, "wb") as f:
            for chunk in response:
                f.write(chunk)
        
        file_size_mb = Path(output_path).stat().st_size / (1024 * 1024)
        print(f"✅ Vocal track generated successfully!")
        print(f"📦 Size: {file_size_mb:.2f} MB")
        print(f"📁 Saved to: {output_path}")
        
        return output_path
        
    except Exception as e:
        print(f"❌ Error generating vocal track: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(
        description='Generate rap vocal track from lyrics using ElevenLabs'
    )
    parser.add_argument('--lyrics', required=True, help='Path to lyrics text file')
    parser.add_argument('--vocal-prompt', required=True, help='Path to vocal prompt template file')
    parser.add_argument('--output', required=True, help='Output MP3 path for vocal track')
    parser.add_argument('--duration', type=int, default=10, help='Duration in seconds (default: 10)')
    
    args = parser.parse_args()
    
    # Read inputs
    lyrics = read_lyrics(args.lyrics)
    vocal_prompt = read_vocal_prompt_template(args.vocal_prompt)
    
    # Generate vocal track
    generate_vocal_track(lyrics, vocal_prompt, args.output, args.duration)
    
    print()
    print("=" * 70)
    print("✅ Vocal generation complete!")
    print("=" * 70)

if __name__ == "__main__":
    main()

