# Gender Transformation Feature for i2v

## Overview

The i2v (image-to-video) pipeline now supports gender presentation transformation to customize movement quality and styling in generated videos.

## How It Works

When the `--gender` flag is provided, the system transforms the i2v prompt by:

1. **Adding Movement Style Cues**: Injects gender-appropriate movement descriptions:
   - **Masculine (M)**: "Presenting a masculine look and movement quality (confident posture, strong chest/shoulder isolations)."
   - **Feminine (F)**: "Presenting a feminine look and movement quality (fluid lines, hip emphasis, graceful arm styling)."

2. **Harmonizing Pronouns**: Replaces neutral or mismatched pronouns with gender-appropriate ones:
   - M: they→he, them→him, their→his, she→he, her→his
   - F: they→she, them→her, their→her, he→she, him→her, his→her

3. **Ensuring Visibility**: Adds framing constraints if not already present:
   - "Entire body is always in frame."
   - "Head is always in the frame."

4. **Preserving Identity**: The transformation is inserted strategically before identity-lock statements to ensure the original person's features are maintained while adjusting presentation style.

## Usage

```bash
# Masculine presentation
python src/batch_media.py i2v \\
  --input path/to/images \\
  --output outputs/videos \\
  --prompts prompts/kling_prompts.txt \\
  --gender M \\
  --workers 5

# Feminine presentation
python src/batch_media.py i2v \\
  --input path/to/images \\
  --output outputs/videos \\
  --prompts prompts/kling_prompts.txt \\
  --gender F \\
  --workers 5
```

## Examples

### Original Prompt (Peanuts style)
```
Animate the uploaded person in a hand-drawn Peanuts newspaper-strip style. 
Identity lock: keep hair color/part, skin tone, outfit colors/patterns...
```

### With Masculine Transformation (--gender M)
```
Animate the uploaded person in a hand-drawn Peanuts newspaper-strip style. 
Presenting a masculine look and movement quality (confident posture, strong 
chest/shoulder isolations). Identity lock: keep hair color/part, skin tone, 
outfit colors/patterns... Entire body is always in frame. Head is always in 
the frame.
```

### With Feminine Transformation (--gender F)
```
Animate the uploaded person in a hand-drawn Peanuts newspaper-strip style. 
Presenting a feminine look and movement quality (fluid lines, hip emphasis, 
graceful arm styling). Identity lock: keep hair color/part, skin tone, 
outfit colors/patterns... Entire body is always in frame. Head is always in 
the frame.
```

## Compatible With All i2v Options

The gender transformation works alongside all other i2v features:
- ✅ Named prompts (`--prompt-name`)
- ✅ Camera directions (`--use-camera-directions`)
- ✅ Backgrounds (`--use-i2v-backgrounds`)
- ✅ Negative prompts (`--use-negative-prompt`)
- ✅ CFG scale adjustment (`--cfg-scale`)
- ✅ Both Kling and Veo3 models

## Design Principles

1. **Non-Destructive**: Choreography and existing constraints remain intact
2. **Subtle**: Movement quality cues are gentle suggestions, not rigid rules
3. **Identity-Preserving**: Face and body features from the input image are maintained
4. **Flexible**: Works with any prompt style (dance, puppet, cartoon, etc.)

## Technical Implementation

The transformation is handled by the `genderize_prompt()` function in `src/batch_media.py`, which:
- Uses regex for pronoun replacement with word boundaries
- Strategically injects style tags before identity anchors
- Tidies up spacing and formatting
- Maintains original choreography instructions

## Output

When gender transformation is enabled, you'll see these indicators in the output:

```
⚧️  Using gender transformation: M
🎬 Worker 0: Starting video generation for IMG_0404_anime.png
⚧️  Worker 0: Applied gender transformation (M)
🎨 Worker 0: Genderized prompt: Animate the uploaded person...
```

## Notes

- Gender parameter accepts: `M`, `F`, `m`, or `f` (case-insensitive)
- If no gender is specified, prompts are used unchanged
- The transformation is applied BEFORE backgrounds and camera directions
- Works with all existing i2v styles (peanuts, antiquepuppet, claymation, etc.)
