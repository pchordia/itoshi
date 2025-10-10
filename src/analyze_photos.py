#!/usr/bin/env python3
"""
Analyze photos using GPT-5 to extract metadata.

For each photo, determines:
1. Gender of person/people
2. Number of people
3. Background description
4. Brief caption

Usage:
    python analyze_photos.py --input path/to/photos --output metadata.json
    python analyze_photos.py --input folder1 folder2 folder3 --output metadata.json
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import List, Dict, Any
from tqdm import tqdm
from dotenv import load_dotenv
import json
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor, as_completed

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

ANALYSIS_SCHEMA = {
    "type": "object",
    "properties": {
        "gender": {
            "type": "string",
            "description": "Gender presentation of the person/people (e.g., Male, Female, Mixed, Unclear)"
        },
        "num_people": {
            "type": "integer",
            "description": "Number of people visible in the photo"
        },
        "age": {
            "type": "string",
            "description": "Estimated age or age range of the person/people (e.g., '25-30', 'Early 20s', 'Mid 30s', 'Teenager', 'Child', 'Multiple ages' if mixed)"
        },
        "background": {
            "type": "string",
            "description": "Brief description of the background/setting (e.g., indoor office, outdoor park, beach at sunset, plain wall)"
        },
        "caption": {
            "type": "string",
            "description": "Brief 1-2 sentence caption describing what's happening in the photo"
        }
    },
    "required": ["gender", "num_people", "age", "background", "caption"],
    "additionalProperties": False
}

ANALYSIS_PROMPT = """Analyze this photo and provide the following information:

1. Gender: What is the gender presentation of the person/people? (e.g., "Male", "Female", "Mixed", "Unclear")
2. Number of people: How many people are visible in the photo? (as an integer)
3. Age: Estimate the age or age range of the person/people (e.g., "25-30", "Early 20s", "Mid 30s", "Teenager", "Child", "Multiple ages" if mixed)
4. Background: Briefly describe the background/setting (e.g., "indoor office", "outdoor park", "beach at sunset", "plain wall")
5. Caption: Provide a brief 1-2 sentence caption describing what's happening in the photo

Be concise and factual."""


def encode_image_to_base64(image_path: str) -> str:
    """Read image file and encode to base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')


def analyze_image_with_gpt(image_path: str, client: OpenAI, model: str = "gpt-4o") -> Dict[str, Any]:
    """
    Send image to GPT for analysis using Responses API.
    
    Returns dict with keys: gender, num_people, background, caption
    """
    # Encode image
    base64_image = encode_image_to_base64(image_path)
    
    # Use the Responses API with structured output
    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": ANALYSIS_PROMPT
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "photo_metadata",
                "strict": True,
                "schema": ANALYSIS_SCHEMA
            }
        },
        max_tokens=500
    )
    
    # Parse the JSON response
    content = completion.choices[0].message.content
    metadata = json.loads(content)
    
    return metadata


def list_image_files(directories: List[str]) -> List[str]:
    """List all image files in the given directories."""
    image_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.tiff'}
    image_files = []
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            print(f"⚠️  Warning: Directory not found: {directory}")
            continue
        
        for file_path in dir_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in image_extensions:
                image_files.append(str(file_path))
    
    return sorted(image_files)




def load_existing_results(output_path: str) -> Dict[str, Any]:
    """Load existing results from JSON file if it exists."""
    if not os.path.exists(output_path):
        return {"photos": [], "errors": []}
    
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except Exception as e:
        print(f"⚠️  Warning: Could not load existing results: {e}")
        return {"photos": [], "errors": []}


def get_analyzed_paths(existing_data: Dict[str, Any]) -> set:
    """Get set of file paths that have already been analyzed."""
    analyzed = set()
    
    # Add successful analyses
    for photo in existing_data.get("photos", []):
        analyzed.add(photo.get("file_path", ""))
    
    # Also track errors to avoid re-trying immediately
    for error in existing_data.get("errors", []):
        analyzed.add(error.get("file_path", ""))
    
    return analyzed


def main():
    parser = argparse.ArgumentParser(
        description="Analyze photos using GPT to extract metadata.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze photos in one folder
  python analyze_photos.py --input photos/ --output metadata.json
  
  # Analyze photos in multiple folders (incremental - skips already analyzed)
  python analyze_photos.py --input folder1/ folder2/ folder3/ --output metadata.json
  
  # Force re-analysis of all photos
  python analyze_photos.py --input photos/ --output metadata.json --overwrite
  
  # Use a different model
  python analyze_photos.py --input photos/ --output metadata.json --model gpt-4o
        """
    )
    parser.add_argument('--input', nargs='+', required=True,
                        help='One or more directories containing photos')
    parser.add_argument('--output', required=True,
                        help='Output JSON file for metadata')
    parser.add_argument('--model', default='gpt-4o',
                        help='OpenAI model to use (default: gpt-4o)')
    parser.add_argument('--overwrite', action='store_true',
                        help='Overwrite and re-analyze all photos (default: incremental)')
    parser.add_argument('--workers', type=int, default=50,
                        help='Number of concurrent workers (default: 50)')
    
    args = parser.parse_args()
    
    # Check API key
    if not OPENAI_API_KEY:
        print("❌ OPENAI_API_KEY not found in environment")
        return 1
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Load existing results (unless overwrite is specified)
    existing_data = {"photos": [], "errors": []}
    analyzed_paths = set()
    
    if not args.overwrite and os.path.exists(args.output):
        print(f"📂 Loading existing results from {args.output}...")
        existing_data = load_existing_results(args.output)
        analyzed_paths = get_analyzed_paths(existing_data)
        print(f"   Found {len(existing_data.get('photos', []))} existing analyses")
        print(f"   Found {len(existing_data.get('errors', []))} existing errors")
    
    # List all image files
    print(f"📁 Scanning directories: {', '.join(args.input)}")
    all_image_files = list_image_files(args.input)
    
    if not all_image_files:
        print("❌ No image files found in the specified directories")
        return 1
    
    # Filter out already analyzed files
    image_files = [f for f in all_image_files if f not in analyzed_paths]
    
    print(f"🖼️  Found {len(all_image_files)} total images")
    if len(image_files) < len(all_image_files):
        print(f"✅ {len(all_image_files) - len(image_files)} already analyzed (skipping)")
        print(f"🆕 {len(image_files)} new images to analyze")
    
    if not image_files:
        print("\n✅ All photos already analyzed! Nothing to do.")
        print(f"   Use --overwrite to force re-analysis")
        return 0
    
    print(f"🤖 Using model: {args.model}")
    print(f"👷 Workers: {args.workers}")
    print(f"📝 Output file: {args.output}")
    print()
    
    # Analyze new images with concurrent processing
    new_results = []
    new_errors = []
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # Submit all tasks
        future_to_path = {
            executor.submit(analyze_image_with_gpt, img_path, client, args.model): img_path
            for img_path in image_files
        }
        
        # Process completed tasks with progress bar
        with tqdm(total=len(image_files), desc="Analyzing new photos", unit="photo") as pbar:
            for future in as_completed(future_to_path):
                image_path = future_to_path[future]
                try:
                    metadata = future.result()
                    new_results.append({
                        "file_path": image_path,
                        "file_name": os.path.basename(image_path),
                        **metadata
                    })
                    tqdm.write(f"✅ {os.path.basename(image_path)}: {metadata['num_people']} person(s), {metadata['gender']}, Age: {metadata['age']}")
                except Exception as e:
                    error_msg = f"❌ Failed to analyze {os.path.basename(image_path)}: {str(e)[:100]}"
                    new_errors.append({
                        "file_path": image_path,
                        "file_name": os.path.basename(image_path),
                        "error": str(e)
                    })
                    tqdm.write(error_msg)
                finally:
                    pbar.update(1)
    
    # Combine with existing results
    all_photos = existing_data.get("photos", []) + new_results
    all_errors = existing_data.get("errors", []) + new_errors
    
    # Get unique directories
    all_dirs = list(set(existing_data.get("metadata", {}).get("directories", []) + args.input))
    
    # Write combined results to JSON file
    print()
    print(f"📝 Writing results to {args.output}...")
    
    output_data = {
        "metadata": {
            "model": args.model,
            "total_photos": len(all_image_files),
            "successful": len(all_photos),
            "failed": len(all_errors),
            "directories": sorted(all_dirs)
        },
        "photos": all_photos,
        "errors": all_errors
    }
    
    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    
    # Print summary
    print()
    print(f"✅ Analysis complete!")
    print(f"   New analyses: {len(new_results)}/{len(image_files)} photos")
    if new_errors:
        print(f"   ⚠️  New errors: {len(new_errors)}")
    print(f"   📊 Total in database: {len(all_photos)} photos ({len(all_errors)} errors)")
    print(f"   📄 Results saved to: {args.output}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())

