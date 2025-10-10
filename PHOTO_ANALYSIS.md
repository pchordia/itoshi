# Photo Analysis Tool

A script that uses GPT-4o (or other OpenAI vision models) to automatically analyze photos and extract structured metadata.

## Features

For each photo, the tool extracts:
1. **Gender**: Gender presentation of person/people (Male, Female, Mixed, Unclear)
2. **Number of people**: Count of people visible in the photo
3. **Background**: Brief description of the setting
4. **Caption**: 1-2 sentence description of what's happening

## Output Format

Results are saved as JSON with:
- **metadata**: Summary statistics and model info
- **photos**: Array of successfully analyzed photos with their metadata
- **errors**: Array of any failed analyses

## Usage

### Basic Usage

```bash
# Analyze photos in one folder
python src/analyze_photos.py --input photos/ --output metadata.json

# Analyze photos in multiple folders
python src/analyze_photos.py --input folder1/ folder2/ folder3/ --output metadata.json
```

### Options

```bash
--input    One or more directories containing photos (required)
--output   Output JSON file for metadata (required)
--model    OpenAI model to use (default: gpt-4o)
--overwrite Overwrite output file if it exists
```

### Examples

```bash
# Single folder
python src/analyze_photos.py --input selfie_test_M --output outputs/metadata.json

# Multiple folders
python src/analyze_photos.py --input selfie_test_M selfie_test --output outputs/all_metadata.json

# Use a different model
python src/analyze_photos.py --input photos/ --output metadata.json --model gpt-4o-mini

# Overwrite existing output
python src/analyze_photos.py --input photos/ --output metadata.json --overwrite
```

## JSON Output Structure

```json
{
  "metadata": {
    "model": "gpt-4o",
    "total_photos": 18,
    "successful": 18,
    "failed": 0,
    "directories": ["selfie_test_M", "selfie_test"]
  },
  "photos": [
    {
      "file_path": "selfie_test_M/fb_12.jpg",
      "file_name": "fb_12.jpg",
      "gender": "Male",
      "num_people": 1,
      "background": "Outdoor area with trees and buildings",
      "caption": "A man in a suit is standing outside on a sunny day."
    }
  ],
  "errors": [
    {
      "file_path": "broken/photo.jpg",
      "file_name": "photo.jpg",
      "error": "Error message here"
    }
  ]
}
```

## Technical Details

- Uses OpenAI's Responses API with structured output (JSON Schema)
- Supports multiple image formats: jpg, jpeg, png, gif, bmp, webp, tiff
- Images are base64-encoded before sending to API
- Progress bar shows real-time analysis status
- Graceful error handling with detailed error logging

## Requirements

- Python 3.7+
- openai package
- python-dotenv
- tqdm
- OPENAI_API_KEY in environment or .env file

## Performance

- Processing time: ~3-5 seconds per photo
- Costs: Standard GPT-4o vision API pricing applies
- Can process photos in parallel (future enhancement)



