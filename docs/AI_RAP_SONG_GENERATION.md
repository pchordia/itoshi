# AI-Generated Custom Rap Songs

Generate complete rap songs (vocals + beat) from a simple text description using ChatGPT + ElevenLabs.

## Overview

```
User Description → ChatGPT (Lyrics) → User Selects Genre → ChatGPT (Music Prompt) → ElevenLabs (Complete Song)
```

**Result:** 10-second rap song with vocals and instrumental ready for video production.

---

## Quick Start

### 1. Setup

```bash
# Install dependencies
pip install openai elevenlabs python-dotenv

# Create .env file
cat > .env << 'EOF'
OPENAI_API_KEY=your_openai_key_here
ELEVENLABS_API_KEY=your_elevenlabs_key_here
EOF
```

### 2. Describe Your Song

Create a text file with your song idea:

```bash
# my_song_description.txt
I want a song about overcoming obstacles and believing in yourself 
when everyone doubts you. Rising from nothing to success.
```

### 3. Generate Song

```bash
python src/create_custom_rap_song.py \
  --description my_song_description.txt \
  --output outputs/audio/my_custom_rap.mp3 \
  --save-lyrics outputs/audio/my_lyrics.txt \
  --duration 10
```

**Interactive Mode:** Select genre when prompted (1-10)

**Non-Interactive Mode:**
```bash
python src/create_custom_rap_song.py \
  --description my_song_description.txt \
  --genre 1 \
  --output my_song.mp3 \
  --duration 10
```

---

## Song Description Examples

Use `prompts/song_description_examples.txt` for inspiration:

### Motivational
```
I want a song about overcoming obstacles and believing in yourself 
when everyone doubts you. Rising from nothing to success.
```

### Party/Fun
```
A fun party anthem about living in the moment, celebrating with friends, 
and not worrying about tomorrow.
```

### Hustle/Grind
```
About working hard every day, late nights grinding, chasing dreams 
while others sleep. Making it from the bottom.
```

### Confidence/Swagger
```
Feeling unstoppable, knowing my worth, walking into any room with 
confidence. Nobody can tell me nothing.
```

---

## Available Genres

| # | Genre | Description | BPM |
|---|-------|-------------|-----|
| 1 | **Trap** | Modern trap with 808s, hi-hats, heavy bass | 140-160 |
| 2 | **Boom-Bap** | Classic 90s sampled drums, jazzy loops | 85-95 |
| 3 | **West Coast** | G-Funk synths, funky bass, laid-back | 90-100 |
| 4 | **Drill** | Dark, aggressive, sliding 808s | 140-150 |
| 5 | **Cloud Rap** | Dreamy, atmospheric, spacey | 120-140 |
| 6 | **East Coast** | Gritty, sample-heavy, hard drums | 90-100 |
| 7 | **Dirty South** | Crunk-influenced, heavy bass | 140-150 |
| 8 | **Alternative** | Experimental, jazzy, unconventional | Variable |
| 9 | **Conscious** | Socially aware, jazzy/soulful | 85-95 |
| 10 | **Mumble Rap** | Melodic, autotuned trap | 130-150 |

---

## Complete Workflow

### Step 1: ChatGPT Generates Lyrics

**Input:** Song description
**Output:** 40-60 word rap lyrics with rhyme scheme and ad-libs

**Example Output:**
```
Started from the bottom now I'm climbing to the peak,
Every single day I'm out here putting in the work week,
Doubters tried to stop me but I'm never feeling weak,
Now I'm at the top and my future looking sleek. (Yeah)
```

### Step 2: User Selects Genre

Choose from 10 popular hip-hop subgenres (interactive or command-line)

### Step 3: ChatGPT Creates Music Prompt

**Input:** Genre + Lyrics
**Output:** Detailed prompt for ElevenLabs with:
- Instrument specifications
- BPM and tempo details
- Vocal style and delivery
- Production elements
- The lyrics

**Example Output:**
```
A modern trap beat at 150 BPM with rolling hi-hats, heavy 808 bass slides, 
and hard-hitting kick drums. Dark atmospheric pads and minimal melody. 
Male rapper with confident, energetic flow and occasional ad-libs. 
Professional studio mixing with punchy drums and deep sub-bass. 
Rapping the following lyrics:

Started from the bottom now I'm climbing to the peak...
```

### Step 4: ElevenLabs Generates Song

**Input:** Complete music prompt (genre + lyrics)
**Output:** 10-second MP3 with vocals AND instrumental

---

## Command Line Usage

### Interactive (Recommended)

```bash
python src/create_custom_rap_song.py \
  --description prompts/song_description_examples.txt \
  --output outputs/audio/my_song.mp3 \
  --save-lyrics outputs/audio/my_lyrics.txt \
  --save-music-prompt outputs/audio/my_prompt.txt
```

You'll be prompted to select genre (1-10)

### Non-Interactive (Automation)

```bash
# Trap style (genre 1)
python src/create_custom_rap_song.py \
  --description my_description.txt \
  --genre 1 \
  --output my_trap_song.mp3 \
  --duration 10
```

### Save Intermediate Files

```bash
python src/create_custom_rap_song.py \
  --description my_description.txt \
  --genre 2 \
  --output outputs/audio/song.mp3 \
  --save-lyrics outputs/audio/lyrics.txt \
  --save-music-prompt outputs/audio/prompt.txt
```

---

## Complete Video Pipeline

Once you have the song, create a video:

```bash
# 1. Generate custom song
python src/create_custom_rap_song.py \
  --description my_description.txt \
  --genre 1 \
  --output outputs/audio/custom_song.mp3 \
  --save-lyrics outputs/audio/custom_lyrics.txt

# 2. Generate portrait (i2i)
python src/batch_media.py i2i \
  --input source_images/my_selfie \
  --output outputs/images/custom_rap \
  --prompts prompts/anime_prompts.txt \
  --prompt-name rapGod

# 3. Animate (i2v)
python src/batch_media.py i2v \
  --input outputs/images/custom_rap/TIMESTAMP \
  --output outputs/videos/custom_rap \
  --prompts prompts/kling_prompts.txt \
  --prompt-name rapGod \
  --duration 10

# 4. Lip-sync
python src/batch_lip_sync.py \
  --csv outputs/videos/custom_rap/TIMESTAMP/_i2v_metrics.csv \
  --audio outputs/audio/custom_song.mp3 \
  --audio-duration-ms 9500 \
  --output-dir outputs/videos/custom_rap_final \
  --workers 1
```

---

## Style Matching Guide

Match your song theme to visual style:

| Song Theme | Best Genre | Visual Style | i2i/i2v Prompt |
|------------|------------|--------------|----------------|
| Motivational/Success | Trap (1) | Neon modern | rapGod |
| Classic/Street | Boom-Bap (2) | Crown/regal | rapCrown |
| Party/Fun | West Coast (3) | House party | rapParty |
| Gritty/Raw | East Coast (6) | 8 Mile street | rap8mile |
| Psychedelic | Cloud Rap (5) | Carnival gate | rapSicko |

---

## Tips for Best Results

### Song Descriptions

**Good:**
- Clear emotion/theme: "overcoming obstacles"
- Specific scenario: "working late nights in the office"
- Target feeling: "confident and unstoppable"

**Too Vague:**
- "Make me a rap song"
- "Something cool"

### Lyrics Length

- **10 seconds:** ~40-50 words
- **15 seconds:** ~60-75 words
- Keep it tight and punchy!

### Genre Selection

- **Fast delivery?** → Trap (1), Drill (4), Mumble Rap (10)
- **Smooth flow?** → West Coast (3), Boom-Bap (2)
- **Experimental?** → Cloud Rap (5), Alternative (8)

---

## Troubleshooting

### Lyrics too short/long

**Problem:** Generated lyrics don't fit 10 seconds

**Solution:** Edit the ChatGPT prompt to specify word count:
```
Compose rap lyrics... Target: exactly 45-50 words for 10 seconds.
```

### Genre doesn't match

**Problem:** Music doesn't sound like selected genre

**Solution:** ChatGPT music prompt may need refinement. Save the prompt (`--save-music-prompt`) and manually edit before sending to ElevenLabs.

### Song incomplete or cut off

**Problem:** ElevenLabs generates less than requested duration

**Solution:** This is normal. Audio is typically 9-9.5 seconds. Use `--audio-duration-ms 9500` for lip-sync.

---

## API Costs

**Per 10-second custom song:**

| Service | Cost | Notes |
|---------|------|-------|
| OpenAI ChatGPT (lyrics) | ~$0.001 | 200 tokens |
| OpenAI ChatGPT (music prompt) | ~$0.002 | 500 tokens |
| ElevenLabs Music (complete song) | ~$0.50 | 10s generation |
| **Total** | **~$0.50** | Per song |

**With video:**
- Song generation: $0.50
- i2i portrait: $0.00125
- i2v animation: $0.35
- Lip-sync: $0.35
- **Total: ~$1.20 per complete video**

---

## Files Structure

```
prompts/
├── song_description_examples.txt      # 8 example descriptions
├── chatgpt_lyrics_prompt.txt          # Lyrics generation prompt
├── chatgpt_music_prompt.txt           # Music prompt creation
└── hiphop_genres.txt                  # 10 genre definitions

src/
└── create_custom_rap_song.py          # Main script

outputs/
└── audio/
    ├── my_song.mp3                    # Complete song
    ├── my_lyrics.txt                  # Generated lyrics (optional)
    └── my_prompt.txt                  # Music prompt (optional)
```

---

## Advanced Usage

### Batch Generation

Generate multiple songs with different genres:

```bash
for genre in 1 2 3; do
  python src/create_custom_rap_song.py \
    --description my_description.txt \
    --genre $genre \
    --output outputs/audio/song_genre_${genre}.mp3
done
```

### Custom Prompts

Modify the ChatGPT prompts for different styles:

**More aggressive lyrics:**
```
Compose aggressive battle rap lyrics that match the intent of this...
```

**More melodic:**
```
Compose melodic rap lyrics with sing-song delivery...
```

---

## Example Session

```bash
$ python src/create_custom_rap_song.py \
    --description prompts/song_description_examples.txt \
    --output my_motivational_rap.mp3

==================================================
🎤 CUSTOM RAP SONG GENERATION
==================================================

✍️  Step 1: Generating Lyrics with ChatGPT
🤖 Asking ChatGPT to write lyrics...

✅ Lyrics generated!

📝 Lyrics:
--------------------------------------------------
Started from the bottom now I'm climbing to the peak,
Every single day I'm out here putting in the work week,
Doubters tried to stop me but I'm never feeling weak,
Now I'm at the top and my future looking sleek. (Yeah)
--------------------------------------------------

🎸 Step 2: Select Hip-Hop Genre

 1. Trap                 - Modern trap with 808s, hi-hats, and heavy bass (140-160 BPM)
 2. Boom-Bap             - Classic 90s style with sampled drums and jazzy loops (85-95 BPM)
 3. West Coast           - G-Funk sound with synths, funky bass, and laid-back vibe (90-100 BPM)
 ...

Select genre (1-10): 1
✅ Selected: Trap

🎼 Step 3: Generating Music Prompt with ChatGPT
🤖 Asking ChatGPT to craft music prompt...

✅ Music prompt generated!

🎵 Step 4: Generating Complete Song with ElevenLabs
🎼 Sending to ElevenLabs Music API...

✅ Song generated successfully!
📦 Size: 0.36 MB

🎉 SONG GENERATION COMPLETE!
🎵 Song: my_motivational_rap.mp3
```

---

## Next Steps

1. **Listen to the song** to verify quality
2. **Use in video pipeline** with i2i + i2v + lip-sync
3. **Iterate** if needed (regenerate with different genre/description)

For full video pipeline, see [CUSTOM_LYRICS_PIPELINE.md](CUSTOM_LYRICS_PIPELINE.md)

