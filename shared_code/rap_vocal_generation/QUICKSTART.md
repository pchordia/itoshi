# Rap Vocal Generation - Quick Start

Generate acapella rap vocals from text using ElevenLabs Music API.

## Installation (30 seconds)

```bash
pip install elevenlabs python-dotenv
echo "ELEVENLABS_API_KEY=your_key_here" > .env
```

## Usage (1 command)

```bash
python generate_rap_vocals.py \
  --lyrics rap_lyrics_example.txt \
  --vocal-prompt rap_vocal_prompt_template.txt \
  --output my_vocals.mp3 \
  --duration 10
```

## Create Your Own Lyrics

**File: `my_lyrics.txt`**
```
Your first line here with rhyme A,
Second line ending in rhyme A,  
Third line with a different rhyme B,
Fourth line also with rhyme B. (Yeah)
```

**Target:** 40-60 words (≈10 seconds when rapped)

## Customize BPM

Edit `rap_vocal_prompt_template.txt`:

```
Change: at 87 bpm
To:     at 150 bpm (for faster delivery)
Or:     at 80 bpm (for slower flow)
```

## Output

- **Format:** MP3 (128 kbps, 44.1 kHz)
- **Type:** Acapella vocals only (no beat)
- **Size:** ~150 KB
- **Duration:** 9-10 seconds
- **Cost:** ~$0.50 per generation

## What You Get

✅ Professional rap vocals  
✅ No instrumental/beat (acapella)  
✅ Ready to mix with your own backing track  
✅ Ready for lip-sync videos  

## Questions?

See full `README.md` for:
- BPM guide
- Genre recommendations  
- Mixing with backing tracks
- Troubleshooting

---

**API Key:** Get from https://elevenlabs.io/  
**Cost:** ~$0.50 per 10-second vocal track

