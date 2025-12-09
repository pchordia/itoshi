# Rap Vocal Generation with ElevenLabs

Generate acapella rap vocals from text lyrics using ElevenLabs Music API.

## Setup

### 1. Install Dependencies
```bash
pip install elevenlabs python-dotenv
```

### 2. Add API Key
Create a `.env` file:
```bash
ELEVENLABS_API_KEY=your_api_key_here
```

Get your key from: https://elevenlabs.io/

## Quick Start

```bash
python generate_rap_vocals.py \
  --lyrics rap_lyrics_example.txt \
  --vocal-prompt rap_vocal_prompt_template.txt \
  --output my_rap_vocals.mp3 \
  --duration 10
```

**Output:** `my_rap_vocals.mp3` (acapella vocals, no beat)

## Files Included

- `generate_rap_vocals.py` - Main script
- `rap_lyrics_example.txt` - Example lyrics (office rap)
- `rap_vocal_prompt_template.txt` - ElevenLabs prompt template

## Usage

### 1. Create Your Lyrics

Create a text file with your rap lyrics (40-60 words for 10 seconds):

**Example (`my_lyrics.txt`):**
```
Stapler in my hand and my Zoom on mute,
Slack blowin' up while I type this loot,
Deadline creepin' in but I play it cute,
Spinnin' in my chair, flirtin' with the new recruit. (Uh)
```

**Guidelines:**
- Target: 40-60 words for 10 seconds (~5 words/second)
- Include ad-libs in parentheses: `(Uh)`, `(Yeah)`, `(Let's go!)`
- Keep it clean (no explicit content)

### 2. Customize Vocal Prompt (Optional)

Edit `rap_vocal_prompt_template.txt` to change BPM or style:

**Default (87 BPM):**
```
acapella rap track with the following lyrics at 87 bpm. no accompaniment at all, only the vocal track:

{LYRICS}
```

**Fast/Technical (150 BPM):**
```
acapella rap track with the following lyrics at 150 bpm. energetic male rapper with fast delivery. no accompaniment, only vocals:

{LYRICS}
```

**Slow/Smooth (80 BPM):**
```
acapella rap track with the following lyrics at 80 bpm. smooth male rapper with laid-back flow. no beat, vocals only:

{LYRICS}
```

### 3. Generate

```bash
python generate_rap_vocals.py \
  --lyrics my_lyrics.txt \
  --vocal-prompt rap_vocal_prompt_template.txt \
  --output my_vocals.mp3 \
  --duration 10
```

## Arguments

| Argument | Required | Description | Default |
|----------|----------|-------------|---------|
| `--lyrics` | Yes | Path to lyrics text file | - |
| `--vocal-prompt` | Yes | Path to prompt template | - |
| `--output` | Yes | Output MP3 path | - |
| `--duration` | No | Duration in seconds | 10 |

## BPM Guide

| BPM Range | Style | Examples |
|-----------|-------|----------|
| 80-95 | G-Funk, Laid-back | Snoop, Dr. Dre |
| 90-110 | Boom-Bap | Biggie, Nas |
| 140-160 | Trap, Modern | Future, Migos |
| 160-180 | Fast, Technical | Eminem, Tech N9ne |

## Output

**Generated File:**
- Format: MP3
- Quality: 128 kbps, 44.1 kHz
- Type: Acapella vocals (no instrumental)
- Size: ~150-200 KB for 10 seconds

## Next Steps

Once you have the vocal track, you can:

1. **Use as-is** for acapella
2. **Mix with backing track** using FFmpeg or DAW
3. **Apply to video** with lip-sync tools

## Example: Mix with Backing Track

If you want to combine with a beat:

```bash
# Using FFmpeg
ffmpeg -i my_vocals.mp3 -i backing_beat.mp3 \
  -filter_complex "[0:a]volume=1.0[a0];[1:a]volume=0.7[a1];[a0][a1]amix=inputs=2:duration=shortest" \
  -codec:a libmp3lame -b:a 320k \
  complete_track.mp3
```

## Troubleshooting

**"ELEVENLABS_API_KEY not found"**
- Create `.env` file with your API key

**"Music API error"**
- Check API key is valid
- Verify you have Music API access (not just TTS)
- Check account credits/quota

**Audio too short/long**
- Adjust word count in lyrics (target ~50 words for 10s)
- Modify BPM in prompt template

## Cost

ElevenLabs Music API: ~$0.50 per 10-second generation

---

**Questions?** Check ElevenLabs Music API docs: https://elevenlabs.io/docs/product-guides/products/music

