# Custom Lyrics to Rap Video Pipeline

Complete pipeline for creating rap videos from user-submitted lyrics using ElevenLabs Music API.

## Overview

This pipeline allows users to input custom rap lyrics and generate a complete lip-synced rap video.

### Pipeline Steps

```
User Lyrics (Text)
    ↓
ElevenLabs Music API (Generate Acapella Vocals)
    ↓
FFmpeg (Combine Vocal + Backing Track)
    ↓
i2i (Create Portrait)
    ↓
i2v (Animate Performance)
    ↓
Kling Lip-Sync (Sync to Combined Audio)
    ↓
Final Video with Custom Lyrics
```

---

## Quick Start

### 1. Prepare Your Lyrics

Create a text file with your rap lyrics:

```bash
# prompts/my_rap_lyrics.txt
Stapler in my hand and my Zoom on mute,
Slack blowin' up while I type this loot,
Deadline creepin' in but I play it cute,
Spinnin' in my chair, flirtin' with the new recruit. (Uh)
```

**Guidelines:**
- Target 40-60 words for 10 seconds
- ~5 words per second delivery
- Include ad-libs in parentheses: (Uh), (Yeah), (Let's go!)
- Keep it clean (no explicit content)

### 2. Choose a Vocal Prompt Template

Use the provided template or customize:

```bash
# prompts/rap_vocal_prompt_template.txt
acapella rap track with the following lyrics at 87 bpm. no accompaniment at all, only the vocal track:

{LYRICS}
```

**Customization Options:**
- Adjust BPM: `at 87 bpm` → `at 95 bpm` (80-180 BPM range)
- Add style: `boom-bap style acapella rap` or `G-funk style acapella rap`
- Specify voice: `male rapper with deep voice` or `energetic young rapper`

### 3. Run Complete Pipeline

```bash
python src/lyrics_to_rap_video.py \
  --selfie source_images/your_selfie.jpg \
  --lyrics prompts/my_rap_lyrics.txt \
  --vocal-prompt prompts/rap_vocal_prompt_template.txt \
  --backing-track outputs/music_excerpts/your_beat_10s.mp3 \
  --i2i-style rapGod \
  --i2v-style rapGod \
  --output-dir outputs/custom_rap/my_video
```

**Time:** ~6-8 minutes total

---

## Step-by-Step Manual Process

### Step 1: Generate Vocal Track

```bash
python src/generate_rap_vocals.py \
  --lyrics prompts/my_rap_lyrics.txt \
  --vocal-prompt prompts/rap_vocal_prompt_template.txt \
  --output outputs/audio/vocals_custom.mp3 \
  --duration 10
```

**Output:** Acapella rap vocals (vocals only, no beat)

### Step 2: Combine with Backing Track

```bash
python src/combine_vocal_and_backing.py \
  --vocal outputs/audio/vocals_custom.mp3 \
  --backing outputs/music_excerpts/boom_bap_beat_10s.mp3 \
  --output outputs/audio/complete_track.mp3 \
  --vocal-volume 1.0 \
  --backing-volume 0.7
```

**Volume Settings:**
- `--vocal-volume 1.0` (full volume)
- `--backing-volume 0.7` (backing at 70%, keeps vocals clear)

**Output:** Complete track (vocals + beat)

### Step 3: Create Portrait (i2i)

```bash
python src/batch_media.py i2i \
  --input source_images/selfie_folder \
  --output outputs/images/custom_rap \
  --prompts prompts/anime_prompts.txt \
  --prompt-name rapGod \
  --model google
```

**Available Styles:**
- `rapGod` - Neon laser background (Eminem style)
- `rap8mile` - 8 Mile street portrait
- `rapSicko` - ASTROWORLD carnival gate
- `rapParty` - '90s house party
- `rapCrown` - Crown and red background

### Step 4: Animate Performance (i2v)

```bash
python src/batch_media.py i2v \
  --input outputs/images/custom_rap/TIMESTAMP \
  --output outputs/videos/custom_rap \
  --prompts prompts/kling_prompts.txt \
  --prompt-name rapGod \
  --model kling \
  --duration 10
```

### Step 5: Apply Lip-Sync

```bash
python src/batch_lip_sync.py \
  --csv outputs/videos/custom_rap/TIMESTAMP/_i2v_metrics.csv \
  --audio outputs/audio/complete_track.mp3 \
  --audio-duration-ms 10000 \
  --output-dir outputs/videos/custom_rap_final \
  --workers 1
```

---

## Style Recommendations

### Fast-Paced / Technical Rap (140-180 BPM)

**Best Styles:**
- **rapGod** (148 BPM) - Neon laser background, rapid hand gestures
- **rap8mile** (171 BPM) - 8 Mile street, focused intensity
- **rap8mile2** (171 BPM) - Refined gesture control

**Example Backing Tracks:**
- Eminem - "Rap God"
- Eminem - "Lose Yourself"
- Logic - "Homicide"

### Medium Tempo / Storytelling (90-110 BPM)

**Best Styles:**
- **rapCrown** (88-96 BPM) - Crown and red background, Biggie style
- **rapParty** (85 BPM) - '90s house party, laid-back

**Example Backing Tracks:**
- The Notorious B.I.G. - "Juicy"
- Dr. Dre & Snoop - "Nuthin' but a 'G' Thang"
- Nas - "NY State of Mind"

### Trap / Modern (120-180 BPM)

**Best Styles:**
- **rapSicko** (172 BPM) - ASTROWORLD carnival, trap bounce
- **rapGod2** (flexible) - Neon lines, modern aesthetic

**Example Backing Tracks:**
- Travis Scott - "SICKO MODE"
- Migos - "Bad and Boujee"
- Future - "Mask Off"

---

## Lyrics Format Guidelines

### Optimal Length

```
For 10-second video:
- Min: 30 words (~6s of rapping)
- Optimal: 40-50 words
- Max: 60 words (~12s, will be trimmed)
```

### Rhyme Schemes

**Example 1: AABB (Couplets)**
```
Line 1 rhyme A
Line 2 rhyme A
Line 3 rhyme B
Line 4 rhyme B
```

**Example 2: ABAB**
```
Line 1 rhyme A
Line 2 rhyme B
Line 3 rhyme A
Line 4 rhyme B
```

**Example 3: AAAA (Mono-rhyme)**
```
Line 1 rhyme A
Line 2 rhyme A
Line 3 rhyme A
Line 4 rhyme A
```

### Ad-Libs

Include ad-libs in parentheses:
```
Line ending here (Uh)
Another line (Yeah)
Final punch (Let's go!)
```

---

## Vocal Prompt Templates

### Boom-Bap (85-100 BPM)

```
boom-bap style acapella rap track with the following lyrics at 90 bpm. male rapper with clear enunciation and confident flow. no accompaniment, only vocals:

{LYRICS}
```

### Trap (140-180 BPM)

```
modern trap style acapella rap with the following lyrics at 150 bpm. energetic male rapper with ad-libs and slight autotune. no beat, vocal track only:

{LYRICS}
```

### G-Funk (80-95 BPM)

```
west coast g-funk acapella rap with the following lyrics at 85 bpm. smooth, laid-back male rapper with melodic flow. no instrumental, vocals only:

{LYRICS}
```

### Drill (140-160 BPM)

```
drill rap acapella with the following lyrics at 145 bpm. aggressive male rapper with rhythmic flow and uk drill delivery. no beat, just vocals:

{LYRICS}
```

---

## Complete Example Workflow

### Office Rap with Boom-Bap Beat

```bash
# 1. Create lyrics file
cat > prompts/office_rap_lyrics.txt << 'EOF'
Stapler in my hand and my Zoom on mute,
Slack blowin' up while I type this loot,
Deadline creepin' in but I play it cute,
Spinnin' in my chair, flirtin' with the new recruit. (Uh)
EOF

# 2. Generate vocals
python src/generate_rap_vocals.py \
  --lyrics prompts/office_rap_lyrics.txt \
  --vocal-prompt prompts/rap_vocal_prompt_template.txt \
  --output outputs/audio/office_vocals.mp3 \
  --duration 10

# 3. Combine with backing track
python src/combine_vocal_and_backing.py \
  --vocal outputs/audio/office_vocals.mp3 \
  --backing "outputs/rap_excerpts_10s_verses_all_annotated/biggie_bigPoppa_10s.mp3" \
  --output outputs/audio/office_complete.mp3 \
  --vocal-volume 1.0 \
  --backing-volume 0.6

# 4. Run i2i
python src/batch_media.py i2i \
  --input source_images/my_selfie \
  --output outputs/images/office_rap \
  --prompts prompts/anime_prompts.txt \
  --prompt-name rapCrown \
  --model google

# 5. Run i2v
python src/batch_media.py i2v \
  --input outputs/images/office_rap/TIMESTAMP \
  --output outputs/videos/office_rap \
  --prompts prompts/kling_prompts.txt \
  --prompt-name rapCrown \
  --model kling \
  --duration 10

# 6. Apply lip-sync
python src/batch_lip_sync.py \
  --csv outputs/videos/office_rap/TIMESTAMP/_i2v_metrics.csv \
  --audio outputs/audio/office_complete.mp3 \
  --audio-duration-ms 10000 \
  --output-dir outputs/videos/office_rap_final \
  --workers 1
```

### OR Use the All-in-One Script:

```bash
python src/lyrics_to_rap_video.py \
  --selfie source_images/my_selfie/me.jpg \
  --lyrics prompts/office_rap_lyrics.txt \
  --vocal-prompt prompts/rap_vocal_prompt_template.txt \
  --backing-track "outputs/rap_excerpts_10s_verses_all_annotated/biggie_bigPoppa_10s.mp3" \
  --i2i-style rapCrown \
  --i2v-style rapCrown \
  --output-dir outputs/custom_rap/office_video \
  --vocal-volume 1.0 \
  --backing-volume 0.6
```

---

## Backing Track Library

Use any of the 24 pre-extracted rap tracks in `outputs/rap_excerpts_10s_verses_all_annotated/`:

**Boom-Bap (85-100 BPM):**
- `biggie_bigPoppa_10s.mp3` (94 BPM)
- `The Notorious B.I.G. - Juicy (Official Video) [4K]_10s_verse.mp3` (92 BPM)
- `Wu-Tang Clan - C.R.E.A.M. (Official HD Video)_10s_verse.mp3` (93 BPM)

**G-Funk (90-100 BPM):**
- `snoopdre_nuthin_10s.mp3` (87 BPM)
- `ginJuice_Snoop_10s.mp3` (95 BPM)
- `Warren G - Regulate (Official Music Video) ft. Nate Dogg_10s_verse.mp3` (94 BPM)

**Modern/Fast (140-180 BPM):**
- `eminem_rapGod_10s.mp3` (148 BPM)
- `eminem_loseYourself_10s.mp3` (171 BPM)
- `Kendrick Lamar - HUMBLE._10s_verse.mp3` (150 BPM)

**Trap:**
- `Travis Scott - SICKO MODE (Official Video) ft. Drake_10s_verse.mp3` (155 BPM)
- `50 Cent - In Da Club (Official Music Video)_10s_verse.mp3` (90 BPM)

---

## Tips for Best Results

### 1. Match BPM

Match your vocal prompt BPM to the backing track:

```bash
# If using 87 BPM backing (G Thang):
acapella rap track with the following lyrics at 87 bpm...

# If using 148 BPM backing (Rap God):
acapella rap track with the following lyrics at 148 bpm...
```

### 2. Vocal/Backing Volume Balance

```bash
# For clear vocals (recommended):
--vocal-volume 1.0 --backing-volume 0.6

# For more prominent beat:
--vocal-volume 0.9 --backing-volume 0.8

# For very quiet backing:
--vocal-volume 1.0 --backing-volume 0.4
```

### 3. Style Matching

Match your lyric style to your visual style:

| Lyric Vibe | i2i/i2v Style | BPM Range |
|------------|---------------|-----------|
| Hustler/Confident | rapCrown | 85-100 |
| Gritty/Street | rap8mile | 160-180 |
| Party/Fun | rapParty | 80-95 |
| Trippy/Psychedelic | rapSicko | 140-180 |
| Technical/Fast | rapGod | 140-180 |

### 4. Lyrics Validation

Validate your lyrics before generation:

```python
def validate_lyrics(text):
    words = text.split()
    word_count = len(words)
    
    if word_count < 30:
        return f"Too short! Add {30 - word_count} more words."
    elif word_count > 60:
        return f"Too long! Remove {word_count - 60} words."
    else:
        return f"Perfect! {word_count} words ≈ {word_count / 5:.1f}s"
```

---

## Troubleshooting

### "Audio duration exceeds video duration"

**Problem:** Combined track is longer than 10s

**Solution:** 
- Trim your lyrics to 40-50 words
- Use `--audio-duration-ms 9900` instead of 10000

### Vocals too quiet or too loud

**Problem:** Imbalanced mix

**Solution:** Adjust volume ratios:
```bash
# Vocals too quiet:
--vocal-volume 1.2 --backing-volume 0.5

# Vocals too loud:
--vocal-volume 0.8 --backing-volume 0.8
```

### ElevenLabs generation failed

**Problem:** API error or rate limit

**Solution:**
- Check your ElevenLabs API key in `.env`
- Wait a few minutes if rate limited
- Try shorter or simpler lyrics

### Lip-sync doesn't match

**Problem:** Vocal timing mismatch

**Solution:**
- Ensure BPM in vocal prompt matches backing track BPM
- Try adjusting `--audio-duration-ms` (use 9900 instead of 10000)

---

## API Costs

**Per 10-second custom rap video:**

| Service | Cost | Notes |
|---------|------|-------|
| ElevenLabs Music (vocals) | ~$0.50 | 10s audio generation |
| Gemini i2i | $0.00125 | Portrait creation |
| Kling i2v (10s) | ~$0.35 | Animation |
| Kling Lip-Sync | ~$0.35 | Sync to audio |
| **Total** | **~$1.20** | Per custom rap video |

**Batch of 10 people with same lyrics:** ~$9.50 (vocals generated once, reused for all)

---

## File Structure

```
prompts/
├── rap_lyrics_example.txt           # Example lyrics
├── rap_vocal_prompt_template.txt    # Vocal generation template
└── my_custom_lyrics.txt             # Your lyrics here

outputs/
├── audio/
│   ├── vocals_TIMESTAMP.mp3         # Generated vocals
│   └── combined_TIMESTAMP.mp3       # Final mix
├── images/
│   └── TIMESTAMP/
│       └── selfie_gemini.png        # Portrait
└── videos/
    └── TIMESTAMP/
        ├── selfie_gemini.mp4        # Animation
        └── selfie_gemini_lipsynced.mp4  # Final video
```

---

## Advanced Usage

### Multiple People, Same Lyrics

Generate one vocal track, use for everyone:

```bash
# 1. Generate vocals once
python src/generate_rap_vocals.py \
  --lyrics prompts/team_rap.txt \
  --vocal-prompt prompts/rap_vocal_prompt_template.txt \
  --output outputs/audio/team_vocals.mp3

# 2. Combine with backing
python src/combine_vocal_and_backing.py \
  --vocal outputs/audio/team_vocals.mp3 \
  --backing outputs/music_excerpts/beat.mp3 \
  --output outputs/audio/team_complete.mp3

# 3. Generate portraits for everyone
python src/batch_media.py i2i \
  --input source_images/team_folder \
  --output outputs/images/team_rap \
  --prompts prompts/anime_prompts.txt \
  --prompt-name rapParty \
  --model google

# 4. Animate all
python src/batch_media.py i2v \
  --input outputs/images/team_rap/TIMESTAMP \
  --output outputs/videos/team_rap \
  --prompts prompts/kling_prompts.txt \
  --prompt-name rapParty \
  --model kling \
  --duration 10

# 5. Lip-sync all (reuse same audio for everyone)
python src/batch_lip_sync.py \
  --csv outputs/videos/team_rap/TIMESTAMP/_i2v_metrics.csv \
  --audio outputs/audio/team_complete.mp3 \
  --audio-duration-ms 10000 \
  --output-dir outputs/videos/team_rap_final \
  --workers 5
```

### Different Styles, Same Lyrics

Test multiple visual styles with the same lyrics:

```bash
# Generate vocals once
python src/generate_rap_vocals.py ... 

# Create 3 different visual versions
for style in rapGod rap8mile rapParty; do
  # i2i
  python src/batch_media.py i2i \
    --input source_images/me \
    --output outputs/images/test_${style} \
    --prompts prompts/anime_prompts.txt \
    --prompt-name ${style} \
    --model google
  
  # i2v  
  python src/batch_media.py i2v \
    --input outputs/images/test_${style}/*/  \
    --output outputs/videos/test_${style} \
    --prompts prompts/kling_prompts.txt \
    --prompt-name ${style} \
    --model kling \
    --duration 10
  
  # lip-sync
  python src/batch_lip_sync.py \
    --csv outputs/videos/test_${style}/*/_i2v_metrics.csv \
    --audio outputs/audio/my_vocals_combined.mp3 \
    --audio-duration-ms 10000 \
    --output-dir outputs/videos/test_${style}_final \
    --workers 1
done
```

---

## Requirements

```bash
# Python packages
pip install elevenlabs requests python-dotenv

# System tools
brew install ffmpeg  # or apt-get install ffmpeg on Linux
```

### .env Configuration

```bash
# Required
ELEVENLABS_API_KEY=your_elevenlabs_key_here
KLING_ACCESS_KEY=your_kling_access_key
KLING_SECRET_KEY=your_kling_secret_key
GOOGLE_API_KEY=your_google_api_key

# Optional
OPENAI_API_KEY=your_openai_key_here
```

---

## Examples

### Example 1: Office Rap

**Lyrics:** Office humor, 90 BPM
**Style:** rapCrown (Biggie style)
**Backing:** Notorious B.I.G. - "Juicy"

### Example 2: Motivational Anthem

**Lyrics:** Inspirational, 150 BPM
**Style:** rapGod (Eminem style)
**Backing:** Eminem - "Lose Yourself"

### Example 3: Party Anthem

**Lyrics:** Fun/party theme, 85 BPM
**Style:** rapParty ('90s party)
**Backing:** Dr. Dre - "Nuthin' but a 'G' Thang"

---

## Next Steps

1. Create your lyrics in `prompts/`
2. Choose or customize a vocal prompt template
3. Select a backing track from the library
4. Run the pipeline!

For questions or issues, see the main [RAP_PIPELINE.md](RAP_PIPELINE.md) documentation.

