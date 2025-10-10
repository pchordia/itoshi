# Gender Transformation Module - Sharing Instructions

## 📦 What You Have

I've extracted and packaged the gender transformation code into a **standalone, reusable module** that can be easily shared with anyone.

## 📂 Package Contents

The `genderize_prompt_package/` folder contains:

1. **`genderize_prompt.py`** (6.7 KB)
   - The main module with all the gender transformation logic
   - Zero dependencies - uses only Python standard library
   - Fully documented with docstrings

2. **`README.md`** (8.4 KB)
   - Complete documentation
   - API reference
   - Configuration options
   - Use cases and examples

3. **`QUICKSTART.md`** (3.2 KB)
   - 5-minute quick start guide
   - Common patterns
   - Troubleshooting tips

4. **`example_usage.py`** (4.3 KB)
   - 4 complete working examples
   - Copy-paste ready code snippets
   - API integration patterns

5. **`requirements.txt`** (285 B)
   - Documents that NO external dependencies are needed
   - Minimum Python version: 3.9+

## 🚀 How to Share

### Option 1: Share the ZIP file

```bash
# The package is already zipped!
# Share this file: genderize_prompt_package.zip (11 KB)
```

**To use:**
```bash
unzip genderize_prompt_package.zip
cd genderize_prompt_package
python example_usage.py  # Try it out!
```

### Option 2: Share via GitHub Gist

1. Go to https://gist.github.com
2. Create a new gist with these files:
   - `genderize_prompt.py`
   - `README.md`
   - `example_usage.py`
3. Share the gist URL

### Option 3: Share individual files

Send just the essential files:
- `genderize_prompt.py` (the module)
- `QUICKSTART.md` (quick instructions)

The recipient can copy `genderize_prompt.py` to their project and use it immediately.

### Option 4: Email-friendly version

The entire package is only **11 KB zipped**, perfect for email attachment!

## 📋 What to Tell the Recipient

### Quick Message Template:

```
Hi [Name],

I'm sharing a Python module for gender transformation of video generation prompts.

**What it does:**
Transforms video prompts to add masculine or feminine movement cues while 
preserving choreography and character identity.

**Example:**
Input:  "The character dances. They move energetically."
Output: "The character dances. He moves energetically. Presenting a 
         masculine look and movement quality..."

**Files included:**
- genderize_prompt.py (the module)
- README.md (full docs)
- QUICKSTART.md (5-min guide)
- example_usage.py (working examples)

**To use:**
1. Unzip the package
2. Copy genderize_prompt.py to your project
3. Import and use:
   from genderize_prompt import genderize_prompt
   result = genderize_prompt("Your prompt", "M")  # or "F"

**Requirements:**
- Python 3.9+
- No external dependencies!

**Quick start:**
Read QUICKSTART.md or run: python example_usage.py

Let me know if you have any questions!
```

## 🔗 Direct Usage (No Installation)

Recipients can use it immediately:

```python
# Just copy genderize_prompt.py to your project folder
from genderize_prompt import genderize_prompt

# Use it!
prompt = "The character dances. They move."
masculine = genderize_prompt(prompt, "M")
feminine = genderize_prompt(prompt, "F")
```

## 🎯 Key Features to Highlight

1. **Zero Dependencies** - Uses only Python standard library
2. **Fully Documented** - Comprehensive docs and examples
3. **Battle-Tested** - Extracted from production code
4. **Customizable** - Easy to modify style tags and pronouns
5. **Small Size** - Only 11 KB total (6.7 KB for the module alone)

## 📝 Testing Instructions

Tell recipients to test it:

```bash
# Test the module
cd genderize_prompt_package
python genderize_prompt.py  # See transformation examples

# Test the usage patterns
python example_usage.py      # See 4 complete examples
```

## 🔧 Customization Guide

If they need to customize it, tell them:

1. **Change style descriptions:**
   - Edit `STYLE_TAGS` dictionary in `genderize_prompt.py`

2. **Add more pronouns:**
   - Edit `PRONOUN_MAPS` dictionary

3. **Change injection points:**
   - Edit `IDENTITY_ANCHORS` list

## 📊 What's Working

✅ Tested and working examples  
✅ Proper pronoun transformation (they→he/she)  
✅ Style tag injection before identity anchors  
✅ Visibility enforcement (body/head in frame)  
✅ Clean output with no double spaces  
✅ Handles edge cases (missing anchors, no pronouns, etc.)

## 🎁 Bonus

The module includes:
- Type hints for better IDE support
- Comprehensive docstrings
- Unit test examples in `__main__`
- Error handling for invalid gender values

## 📧 Support

If the recipient has questions, they can:
1. Read the README.md (comprehensive docs)
2. Check QUICKSTART.md (common issues)
3. Run example_usage.py (see it in action)
4. Contact you for help

---

**Ready to share!** 🚀

Choose your preferred sharing method above and send it over!

