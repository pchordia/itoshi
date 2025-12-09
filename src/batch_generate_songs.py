#!/usr/bin/env python3
"""
Generate multiple custom rap songs in parallel using concurrent workers
"""

import os
import sys
import argparse
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv
from openai import OpenAI
from elevenlabs.client import ElevenLabs
from tqdm import tqdm

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY", "")

# Reference tracks for each genre
REFERENCE_TRACKS = {
    "1": ("Trap", '"SICKO MODE" by Travis Scott'),
    "2": ("Boom-Bap", '"N.Y. State of Mind" by Nas'),
    "3": ("West Coast", '"Nuthin\' but a \'G\' Thang" by Dr. Dre'),
    "4": ("Drill", '"Dior" by Pop Smoke'),
    "5": ("Cloud Rap", '"Yonkers" by Tyler, The Creator'),
    "6": ("East Coast", '"Juicy" by The Notorious B.I.G.'),
    "7": ("Dirty South", '"In Da Club" by 50 Cent'),
    "8": ("Alternative", '"Ms. Jackson" by OutKast'),
    "9": ("Conscious", '"Alright" by Kendrick Lamar'),
    "10": ("Mumble Rap", '"Lifestyle" by Young Thug')
}

def generate_one_song(description_path: str, genre: str, output_base: str, worker_id: int) -> dict:
    """
    Generate one complete song (lyrics + music)
    
    Returns:
        dict with status, files, and any errors
    """
    
    try:
        client_openai = OpenAI(api_key=OPENAI_API_KEY)
        client_elevenlabs = ElevenLabs(api_key=ELEVENLABS_API_KEY)
        
        # Read description
        with open(description_path, 'r') as f:
            description = f.read().strip()
        
        genre_name, reference = REFERENCE_TRACKS[genre]
        base_name = Path(description_path).stem
        
        print(f"🎤 Worker {worker_id}: Starting {base_name} + {genre_name}")
        
        # Step 1: Generate lyrics with ChatGPT 5.1
        lyrics_prompt = f"""Compose rap lyrics that match this intent. Target: 40-55 words for 10 seconds.

Description: {description}

Requirements:
- AABB rhyme scheme
- Include 1-2 ad-libs: (Yeah), (Uh)
- Keep it clean
- 4 lines that flow well

Output only lyrics, no explanations."""
        
        response_lyrics = client_openai.responses.create(
            model="gpt-5.1",
            input=lyrics_prompt,
            reasoning={"effort": "medium"}
        )
        
        lyrics = response_lyrics.output_text.strip().replace("```", "")
        
        # Step 2: Generate simple music prompt
        music_prompt_request = f"""Create a short ElevenLabs music prompt inspired by {reference}.

Style: {genre_name}
Keep it under 150 words.
Include: instruments, BPM, vocal style.
Must say: "Start vocals immediately, no intro"
End with: "Rapping: {lyrics}"

Output only the prompt."""
        
        response_music = client_openai.responses.create(
            model="gpt-5.1",
            input=music_prompt_request,
            reasoning={"effort": "medium"}
        )
        
        music_prompt = response_music.output_text.strip()
        
        # Step 3: Generate song with ElevenLabs
        song_response = client_elevenlabs.music.stream(
            prompt=music_prompt,
            music_length_ms=10000
        )
        
        # Save files
        output_mp3 = f"{output_base}/{base_name}_{genre_name.lower().replace(' ', '')}.mp3"
        output_lyrics = f"{output_base}/{base_name}_{genre_name.lower().replace(' ', '')}_lyrics.txt"
        
        os.makedirs(output_base, exist_ok=True)
        
        with open(output_mp3, "wb") as f:
            for chunk in song_response:
                f.write(chunk)
        
        with open(output_lyrics, "w") as f:
            f.write(lyrics)
        
        print(f"✅ Worker {worker_id}: Completed {base_name} + {genre_name}")
        
        return {
            "status": "success",
            "description": base_name,
            "genre": genre_name,
            "output": output_mp3,
            "lyrics_file": output_lyrics,
            "lyrics": lyrics[:80] + "..."
        }
        
    except Exception as e:
        print(f"❌ Worker {worker_id}: Failed {description_path} - {str(e)[:100]}")
        return {
            "status": "failed",
            "description": description_path,
            "genre": genre,
            "error": str(e)[:200]
        }

def main():
    parser = argparse.ArgumentParser(
        description='Generate multiple rap songs in parallel'
    )
    parser.add_argument('--descriptions-dir', required=True, 
                       help='Directory with song description text files')
    parser.add_argument('--genres', nargs='+', required=True,
                       help='List of genre numbers (1-10) matching number of descriptions')
    parser.add_argument('--output-dir', required=True,
                       help='Output directory for generated songs')
    parser.add_argument('--workers', type=int, default=5,
                       help='Number of parallel workers (default: 5)')
    
    args = parser.parse_args()
    
    if not OPENAI_API_KEY or not ELEVENLABS_API_KEY:
        print("❌ Missing API keys in .env")
        sys.exit(1)
    
    # Get all description files
    desc_dir = Path(args.descriptions_dir)
    desc_files = sorted(desc_dir.glob("*.txt"))
    
    if len(desc_files) != len(args.genres):
        print(f"❌ Mismatch: {len(desc_files)} descriptions but {len(args.genres)} genres")
        sys.exit(1)
    
    print("=" * 70)
    print(f"🎵 BATCH SONG GENERATION ({len(desc_files)} songs)")
    print("=" * 70)
    print(f"Workers: {args.workers}")
    print(f"Output: {args.output_dir}")
    print()
    
    # Create tasks
    tasks = []
    for i, (desc_file, genre) in enumerate(zip(desc_files, args.genres)):
        genre_name = REFERENCE_TRACKS.get(genre, ("Unknown", ""))[0]
        print(f"{i+1}. {desc_file.stem} → {genre_name}")
        tasks.append((desc_file, genre, i))
    
    print()
    print("🚀 Starting parallel generation...")
    print()
    
    # Run in parallel
    results = []
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {}
        
        for desc_file, genre, worker_id in tasks:
            future = executor.submit(
                generate_one_song,
                str(desc_file),
                genre,
                args.output_dir,
                worker_id
            )
            futures[future] = (desc_file.stem, genre)
        
        # Collect results with progress bar
        pbar = tqdm(total=len(futures), desc="Songs", unit="song")
        
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            pbar.update(1)
            
            if result["status"] == "success":
                pbar.set_postfix_str(f"✅ {result['description']}")
            else:
                pbar.set_postfix_str(f"❌ {result['description']}")
        
        pbar.close()
    
    # Summary
    print()
    print("=" * 70)
    print("📊 SUMMARY")
    print("=" * 70)
    
    success = [r for r in results if r["status"] == "success"]
    failed = [r for r in results if r["status"] == "failed"]
    
    print(f"✅ Success: {len(success)}/{len(results)}")
    print(f"❌ Failed: {len(failed)}/{len(results)}")
    
    if success:
        print()
        print("Generated songs:")
        for r in success:
            print(f"  • {r['description']} ({r['genre']}): {Path(r['output']).name}")
    
    if failed:
        print()
        print("Failed:")
        for r in failed:
            print(f"  • {r['description']}: {r['error'][:100]}")
    
    print()
    print(f"📁 Output: {args.output_dir}")
    print("=" * 70)

if __name__ == "__main__":
    main()

