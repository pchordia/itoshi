# Quick Start Guide

Get started with gender transformation for video prompts in 5 minutes!

## Step 1: Copy the Module

```bash
# Copy genderize_prompt.py to your project
cp genderize_prompt.py /your/project/path/
```

## Step 2: Import and Use

```python
from genderize_prompt import genderize_prompt

# Your original prompt
prompt = "The character dances. They move energetically."

# Transform it!
masculine = genderize_prompt(prompt, "M")
feminine = genderize_prompt(prompt, "F")

print(masculine)
# Output: "The character dances. He moves energetically. 
# Presenting a masculine look and movement quality..."

print(feminine)
# Output: "The character dances. She moves energetically. 
# Presenting a feminine look and movement quality..."
```

## Step 3: Try the Examples

```bash
# Run the example script to see it in action
python example_usage.py
```

That's it! You're ready to go.

## Common Use Cases

### Video Generation API

```python
from genderize_prompt import genderize_prompt

def generate_video(image, prompt, gender=None):
    if gender:
        prompt = genderize_prompt(prompt, gender)
    
    # Call your video API
    return api.create_video(image=image, prompt=prompt)

# Use it
video = generate_video("photo.jpg", "The character dances.", gender="F")
```

### Batch Processing

```python
from genderize_prompt import genderize_prompts

prompts = [
    "The character does hip-hop. They move sharply.",
    "The character does ballet. They move gracefully.",
]

# Transform all at once
masculine_prompts = genderize_prompts(prompts, "M")
feminine_prompts = genderize_prompts(prompts, "F")
```

### User Selection

```python
from genderize_prompt import genderize_prompt

def get_prompt(base_prompt, user_gender_choice):
    """Let users choose their preferred presentation"""
    if user_gender_choice in ["M", "F"]:
        return genderize_prompt(base_prompt, user_gender_choice)
    return base_prompt  # Default, no transformation

# Use it in your app
final_prompt = get_prompt(
    "The character dances.",
    user_gender_choice=user_input  # "M", "F", or None
)
```

## Best Practices

1. **Write gender-neutral base prompts** using "they/them/their"
2. **Include identity anchors** like "The character matches the uploaded reference exactly"
3. **Test both transformations** to ensure good results
4. **Combine with other features** like negative prompts and camera directions

## Need Help?

- Read the full [README.md](README.md) for detailed documentation
- Check [example_usage.py](example_usage.py) for more examples
- Modify the style tags in `genderize_prompt.py` to fit your needs

## Customization

Want different style descriptions? Edit these in `genderize_prompt.py`:

```python
STYLE_TAGS = {
    "M": "Your custom masculine description here.",
    "F": "Your custom feminine description here.",
}
```

## Troubleshooting

**Q: Pronouns aren't changing correctly**
A: Make sure your original prompt uses "they/them/their" pronouns

**Q: Style tags aren't appearing**
A: Check that your prompt includes one of the identity anchor phrases

**Q: Want to add more pronouns**
A: Edit the `PRONOUN_MAPS` dictionary in `genderize_prompt.py`

---

**Ready to dive deeper?** Check out [README.md](README.md) for the complete documentation!

