# i2i to i2v Style Linking

## Overview

Certain i2i (anime/image-to-image) styles are designed to work best with specific i2v (image-to-video) styles. The system automatically detects when you use a linked i2i style and recommends the matching i2v style.

## How It Works

When you run an i2i conversion using a linked style, the system will:
1. ✅ Display which i2v style is recommended
2. ✅ Show you the exact command to run for i2v conversion
3. ✅ Use the matched i2v style automatically (in future updates)

## Linked Styles

The following i2i styles are linked to specific i2v styles:

| i2i Style | → | i2v Style | Description |
|-----------|---|-----------|-------------|
| `cartoonSaloon` | → | `cartoonSaloon` | Hand-drawn 2D, Song of the Sea style |
| `demonslayer` | → | `demonslayer` | Shōnen battle anime, dramatic cel shading |
| `demonslayer2` | → | `demonslayer` | Alternative demon slayer portrait |
| `demonhunter` | → | `demonhunter` | Glossy K-pop idol 3D character |
| `claymation` | → | `claymation` | Aardman/Wallace & Gromit stop-motion |
| `lego` | → | `lego` | LEGO movie minifigure style |
| `peanuts` | → | `peanuts` | Hand-drawn newspaper comic strip |
| `antiquepuppet` | → | `antiquepuppet` | Antique marionette theatre puppet |
| `antiquepuppetcreepy` | → | `antiquepuppet` | Creepy puppet maps to same i2v |
| `corpsebride` | → | `corpsebride` | Tim Burton stop-motion gothic |
| `french` | → | `french` | French caricature animation |
| `japaneseNoodleShop` | → | `japaneseNoodleShop` | Cozy ramen shop scene |

## Usage Examples

### Automatic Recommendation

When you run an i2i conversion with a linked style:

```bash
python src/batch_media.py anime \
  --input source_images/selfie_test \
  --output outputs/images \
  --prompts prompts/anime_prompts.txt \
  --prompt-name claymation \
  --workers 10
```

**Output:**
```
🎨 Anime: processing 10 images with up to 10 workers...
📁 Output: outputs/images/251006_143022
🔗 Style 'claymation' is linked to i2v style 'claymation'
   💡 Recommended i2v command:
   python src/batch_media.py i2v --input outputs/images/251006_143022 --output outputs/videos \
      --prompts prompts/kling_prompts.txt --prompt-name claymation --workers 20
```

### Following the Recommendation

Simply copy and run the recommended command:

```bash
python src/batch_media.py i2v \
  --input outputs/images/251006_143022 \
  --output outputs/videos \
  --prompts prompts/kling_prompts.txt \
  --prompt-name claymation \
  --workers 20
```

## Why Style Linking?

Different i2i styles have unique visual characteristics that work best with matching i2v animation styles:

- **`claymation`** → Needs stop-motion animation rules (animate on twos, stepped poses, no motion blur)
- **`lego`** → Requires minifigure joint constraints and toy-like movement
- **`corpsebride`** → Gothic puppet aesthetics need specific lighting and movement
- **`peanuts`** → Limited animation style with wobbly lines and simple poses
- **`demonslayer`** → Shōnen anime requires speedlines, cel-shaded consistency

Using the wrong i2v style can result in:
- ❌ Visual inconsistency between image and video
- ❌ Loss of the intended aesthetic
- ❌ Animation that doesn't match the character style

## Advanced Usage

### Override the Recommendation

If you want to use a different i2v style despite the recommendation:

```bash
# Generate claymation images
python src/batch_media.py anime --input ... --prompt-name claymation

# Use a different i2v style (not recommended but possible)
python src/batch_media.py i2v \
  --input outputs/images/[timestamp] \
  --prompts prompts/kling_prompts.txt \
  --prompt-name default \
  --workers 20
```

### Check Available Styles

**i2i styles:**
```bash
grep "^[a-z]" prompts/anime_prompts.txt | cut -d: -f1
```

**i2v styles:**
```bash
grep "^[a-z]" prompts/kling_prompts.txt | cut -d: -f1
```

## Adding New Style Links

To add a new style link, edit `src/batch_media.py`:

```python
I2I_TO_I2V_STYLE_MAP = {
    # ... existing mappings ...
    "yourNewStyle": "matchingI2vStyle",
}
```

**Requirements:**
1. The i2i style must exist in `prompts/anime_prompts.txt`
2. The i2v style must exist in `prompts/kling_prompts.txt`
3. Both styles should be visually and thematically compatible

## Tips for Best Results

1. **Always use linked styles together** - They're designed as a pair
2. **Check the recommendation** - Copy the exact command shown
3. **Add appropriate flags** - Consider `--gender`, `--use-negative-prompt`, `--use-camera-directions`
4. **Adjust workers** - Use 10-20 workers for i2v for faster processing

### Complete Example with All Options

```bash
# Step 1: Generate claymation images
python src/batch_media.py anime \
  --input source_images/selfie_test \
  --output outputs/images \
  --prompts prompts/anime_prompts.txt \
  --prompt-name claymation \
  --workers 10

# Step 2: Generate claymation videos (copy from recommendation)
python src/batch_media.py i2v \
  --input outputs/images/251006_143022 \
  --output outputs/videos \
  --prompts prompts/kling_prompts.txt \
  --prompt-name claymation \
  --gender M \
  --use-negative-prompt \
  --workers 20

# Step 3: Add music
python src/add_music_to_videos.py \
  --input-videos outputs/videos/251006_143522 \
  --music-folder outputs/music_excerpts \
  --output-folder outputs/videos_with_music \
  --replace-audio
```

## Troubleshooting

**Q: The recommendation doesn't show up**
- Make sure you're using `--prompt-name` with a linked style
- Check that the style name is spelled correctly

**Q: I want to use a style that isn't linked**
- You can still use any i2i and i2v combination you want
- The linking is just a recommendation, not a requirement

**Q: Can I use default i2v with linked i2i styles?**
- Yes, but results may not match the intended aesthetic
- The default i2v style uses generic hip-hop dance movements

**Q: How do I know which styles are linked?**
- Check the table above
- Or look at `I2I_TO_I2V_STYLE_MAP` in `src/batch_media.py`

## Future Enhancements

Planned improvements:
- [ ] Automatic i2v style selection (no need to specify `--prompt-name`)
- [ ] Batch processing that automatically chains i2i → i2v
- [ ] Style compatibility warnings
- [ ] Metadata in output files tracking which styles were used

---

**Last Updated:** October 2025  
**Related Docs:** `GENDER_TRANSFORMATION.md`, `PHOTO_ANALYSIS.md`



