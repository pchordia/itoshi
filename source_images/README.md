# Source Images

This folder contains all source/input images used for testing and processing in the project.

## 📁 Folder Structure

### Wedding Photos
- **`sb_weddding_pics/`** (32 images) - Full wedding photo collection
- **`sb_wedding/`** (8 images) - Selected wedding photos subset

### Selfie Test Sets
- **`selfie_test/`** (10 images) - Primary selfie test set (screenshots)
- **`selfie_test_2/`** (10 images) - Secondary selfie test set (screenshots)
- **`selfie_test_black/`** (20 images) - Diverse representation test set
- **`selfie_test_fb/`** (42 images) - Facebook profile photos
- **`selfie_test_M/`** (8 images) - Male-focused test subset

### Additional Test Sets
- **`selfies_testing_ftux/`** - Testing and FTUX (First Time User Experience) images
  - `organic/` - Organic/natural photos
  - `midjourney/` - AI-generated reference images

### Archives
- **`selfie_test.zip`** - Archived/backup of selfie test set

## 📊 Image Statistics

| Folder | Count | Type | Purpose |
|--------|-------|------|---------|
| sb_weddding_pics | 32 | JPEG | Wedding event photos |
| sb_wedding | 8 | JPEG | Selected wedding subset |
| selfie_test | 10 | PNG | Primary test selfies |
| selfie_test_2 | 10 | PNG | Secondary test selfies |
| selfie_test_black | 20 | JPG/JPEG/WEBP | Diverse representation |
| selfie_test_fb | 42 | JPG | Profile photos |
| selfie_test_M | 8 | JPG | Male test subset |
| selfies_testing_ftux | ~64 | PNG/JPG/JPEG | FTUX testing |

**Total:** ~190+ source images

## 🎯 Usage

These images are used for:

1. **Testing i2i (image-to-image) conversions** - Anime style transformations
2. **Testing i2v (image-to-video) generation** - Video generation from anime images
3. **Photo analysis and metadata extraction** - Gender, age, background detection
4. **Balanced test set creation** - Creating diverse test sets
5. **Quality assurance** - Ensuring models work across different image types

## 🔧 Processing Commands

### Run anime conversion on a folder:
```bash
python src/batch_media.py anime \
  --input source_images/selfie_test \
  --output outputs/images \
  --prompts prompts/anime_prompts.txt \
  --workers 10
```

### Run i2v conversion:
```bash
python src/batch_media.py i2v \
  --input outputs/images/[timestamp] \
  --output outputs/videos \
  --prompts prompts/kling_prompts.txt \
  --workers 20
```

### Analyze photos:
```bash
python src/analyze_photos.py \
  --folders source_images/selfie_test source_images/selfie_test_2 \
  --output outputs/all_photos_metadata.json
```

## 📝 Image Quality Guidelines

**Best results when images have:**
- ✅ Clear, visible face
- ✅ Good lighting
- ✅ Single person (for most tests)
- ✅ Variety of ages, genders, ethnicities
- ✅ Different backgrounds and settings
- ✅ Various expressions and poses

**Avoid:**
- ❌ Blurry or low-resolution images
- ❌ Heavy filters or edits (unless testing)
- ❌ Extreme angles or partial faces
- ❌ Very dark or overexposed images

## 🗂️ Organization Tips

- **Single person tests:** Use `selfie_test`, `selfie_test_2`, `selfie_test_M`
- **Multiple people:** Use `sb_wedding`, `sb_weddding_pics`
- **Diverse representation:** Use `selfie_test_black`, `selfie_test_fb`
- **AI vs real comparison:** Use `selfies_testing_ftux/organic` vs `midjourney`

## 🔄 Adding New Images

When adding new source images:

1. Create a descriptive folder name (e.g., `selfie_test_asian`, `wedding_2024`)
2. Use consistent file naming (e.g., `subject_01.jpg`, `photo_01.png`)
3. Include a mix of different poses, lighting, and settings
4. Update this README with the new folder info
5. Run photo analysis to extract metadata

## 📊 Metadata

Most folders have been analyzed with GPT-4o Vision. See:
- `outputs/all_photos_metadata.json` - Complete analysis results
- Each entry includes: gender, age, number of people, background, caption

## ⚠️ Privacy Note

These images are for testing and development purposes. Ensure you have appropriate permissions for any images you add to this folder.

---

**Last Updated:** October 2025  
**Total Images:** ~190+  
**Used For:** i2i conversion, i2v generation, photo analysis, testing



