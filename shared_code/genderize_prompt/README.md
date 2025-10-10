# Gender Transformation for Video Generation Prompts

A Python module that transforms video generation prompts to match a specified gender presentation (masculine or feminine) while preserving the original choreography, style, and identity constraints.

## Features

- ✅ **Non-destructive transformation** - Preserves all original choreography and style instructions
- ✅ **Gender-appropriate movement cues** - Adds subtle movement quality descriptions
- ✅ **Pronoun harmonization** - Converts they/them/their → he/him/his or she/her/her
- ✅ **Identity preservation** - Maintains character identity and appearance constraints
- ✅ **Visibility enforcement** - Ensures full body and head are always in frame
- ✅ **Smart injection** - Strategically places style cues before identity anchors

## Installation

Simply copy the `genderize_prompt.py` file to your project:

```bash
# Download the standalone module
curl -O https://your-repo/genderize_prompt.py

# Or copy it directly
cp genderize_prompt.py /path/to/your/project/
```

No external dependencies required - uses only Python standard library (`re` module).

## Quick Start

```python
from genderize_prompt import genderize_prompt

# Original gender-neutral prompt
original = """The character dances confidently to a 160 BPM beat. 
They move with energy. The character matches the uploaded reference 
exactly—same face, complexion, hair, outfit, and accessories."""

# Transform for masculine presentation
masculine = genderize_prompt(original, "M")
# Output: "The character dances confidently to a 160 BPM beat. 
# He moves with energy. Presenting a masculine look and movement 
# quality (confident posture, strong chest/shoulder isolations). 
# The character matches the uploaded reference exactly—same face, 
# complexion, hair, outfit, and accessories."

# Transform for feminine presentation
feminine = genderize_prompt(original, "F")
# Output: "The character dances confidently to a 160 BPM beat. 
# She moves with energy. Presenting a feminine look and movement 
# quality (fluid lines, hip emphasis, graceful arm styling). 
# The character matches the uploaded reference exactly—same face, 
# complexion, hair, outfit, and accessories."
```

## API Reference

### `genderize_prompt(original: str, gender: str) -> str`

Transform a single prompt to match the specified gender.

**Parameters:**
- `original` (str): The original prompt text
- `gender` (str): Either `"M"` (masculine) or `"F"` (feminine)

**Returns:**
- Transformed prompt with gender-appropriate styling and pronouns

**Example:**
```python
prompt = "The character breakdances. They perform toprocks and freezes."
result = genderize_prompt(prompt, "M")
```

### `genderize_prompts(prompts: list[str], gender: str) -> list[str]`

Transform multiple prompts at once.

**Parameters:**
- `prompts` (list): List of prompt texts
- `gender` (str): Either `"M"` (masculine) or `"F"` (feminine)

**Returns:**
- List of transformed prompts

**Example:**
```python
prompts = [
    "The character dances hip-hop. They move energetically.",
    "The character performs ballet. They move gracefully."
]
results = genderize_prompts(prompts, "F")
```

## How It Works

The transformation process follows these steps:

1. **Style Tag Injection**: Adds gender-appropriate movement quality cues
   - Masculine: "confident posture, strong chest/shoulder isolations"
   - Feminine: "fluid lines, hip emphasis, graceful arm styling"

2. **Pronoun Mapping**: Harmonizes all pronouns
   - M: they→he, them→him, their→his, she→he, her→his
   - F: they→she, them→her, their→her, he→she, his→her

3. **Visibility Enforcement**: Ensures framing constraints
   - Adds "Entire body is always in frame" if not present
   - Adds "Head is always in the frame" if not present

4. **Space Cleanup**: Removes accidental double spaces

## Configuration

You can customize the transformation behavior by modifying the module constants:

### `STYLE_TAGS`

Gender-specific movement quality descriptions:

```python
STYLE_TAGS = {
    "M": "Presenting a masculine look and movement quality (confident posture, strong chest/shoulder isolations).",
    "F": "Presenting a feminine look and movement quality (fluid lines, hip emphasis, graceful arm styling).",
}
```

### `PRONOUN_MAPS`

Pronoun replacement rules:

```python
PRONOUN_MAPS = {
    "M": [
        (r"\bthey\b", "he"),
        (r"\bthem\b", "him"),
        # ... more mappings
    ],
    "F": [
        (r"\bthey\b", "she"),
        (r"\bthem\b", "her"),
        # ... more mappings
    ],
}
```

### `IDENTITY_ANCHORS`

Phrases used to identify where to inject style tags:

```python
IDENTITY_ANCHORS = [
    "The anime character matches the uploaded reference exactly",
    "The character matches the uploaded reference exactly",
    "Preserve identity",
]
```

## Testing

Run the built-in examples:

```bash
python genderize_prompt.py
```

This will output transformation examples for several test prompts.

## Use Cases

### Video Generation APIs

```python
from genderize_prompt import genderize_prompt

# Generate masculine version
api.generate_video(
    image=user_image,
    prompt=genderize_prompt(base_prompt, "M")
)

# Generate feminine version
api.generate_video(
    image=user_image,
    prompt=genderize_prompt(base_prompt, "F")
)
```

### Batch Processing

```python
from genderize_prompt import genderize_prompts

dance_styles = [
    "The character performs hip-hop. They move energetically.",
    "The character does ballet. They move gracefully.",
    "The character breakdances. They perform power moves.",
]

# Generate all masculine versions
masculine_prompts = genderize_prompts(dance_styles, "M")

# Generate all feminine versions
feminine_prompts = genderize_prompts(dance_styles, "F")
```

### CLI Integration

```python
import argparse
from genderize_prompt import genderize_prompt

parser = argparse.ArgumentParser()
parser.add_argument("--prompt", required=True)
parser.add_argument("--gender", choices=["M", "F"], required=True)

args = parser.parse_args()
result = genderize_prompt(args.prompt, args.gender)
print(result)
```

## Best Practices

1. **Start gender-neutral**: Write prompts using "they/them/their" pronouns
2. **Include identity anchors**: Use phrases like "The character matches the uploaded reference exactly"
3. **Be specific about choreography**: The transformation preserves all movement details
4. **Test both genders**: Verify output for both M and F transformations
5. **Combine with other techniques**: Works well with negative prompts and camera directions

## Limitations

- Pronoun mapping is regex-based and may occasionally have edge cases
- Style tags are generic - you may want to customize them for specific dance styles
- Works best with English prompts
- Does not modify actual video generation - only transforms text prompts

## Examples

### Example 1: Hip-Hop Dance

```python
original = "The character dances hip-hop. They perform sharp isolations."

masculine = genderize_prompt(original, "M")
# "The character dances hip-hop. He performs sharp isolations. 
# Presenting a masculine look and movement quality..."

feminine = genderize_prompt(original, "F")
# "The character dances hip-hop. She performs sharp isolations. 
# Presenting a feminine look and movement quality..."
```

### Example 2: Breakdance

```python
original = """The character breakdances like an expert. They perform 
toprocks, 6-step footwork, and freezes. The character matches the 
uploaded reference exactly."""

result = genderize_prompt(original, "M")
# Pronouns changed to he/him, masculine style cues added before 
# "The character matches..."
```

### Example 3: Batch Processing Multiple Styles

```python
styles = {
    "kpop": "The character performs K-pop choreography...",
    "ballet": "The character dances ballet...",
    "breakdance": "The character breakdances...",
}

masculine_versions = {
    name: genderize_prompt(prompt, "M") 
    for name, prompt in styles.items()
}

feminine_versions = {
    name: genderize_prompt(prompt, "F") 
    for name, prompt in styles.items()
}
```

## Contributing

Feel free to customize and extend the module for your needs:

- Add new gender options (non-binary, etc.)
- Customize style tags for specific use cases
- Add support for other languages
- Extend pronoun mapping rules

## License

MIT License - feel free to use, modify, and distribute.

## Author

Parag Chordia

## Support

For issues, questions, or suggestions, please open an issue or contact the author.

---

**Version**: 1.0.0  
**Last Updated**: October 2025  
**Python Version**: 3.9+

