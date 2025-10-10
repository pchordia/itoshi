"""
Gender Transformation for Video Generation Prompts

This module provides utilities to transform video generation prompts to match
a specified gender presentation (masculine or feminine) while preserving the
original choreography, style, and identity constraints.

Usage:
    from genderize_prompt import genderize_prompt
    
    original_prompt = "The character dances confidently. They move with energy."
    
    # Transform for masculine presentation
    masculine_prompt = genderize_prompt(original_prompt, "M")
    
    # Transform for feminine presentation
    feminine_prompt = genderize_prompt(original_prompt, "F")

Features:
    - Adds gender-appropriate movement quality cues
    - Harmonizes pronouns (they/them/their → he/him/his or she/her/her)
    - Preserves original choreography and constraints
    - Ensures full body and head visibility
    - Non-destructive transformation

Author: Parag Chordia
License: MIT
"""

import re
from typing import Optional


# Pronoun mapping rules for gender transformation
PRONOUN_MAPS = {
    "M": [
        (r"\bthey\b", "he"),
        (r"\bthem\b", "him"),
        (r"\btheir\b", "his"),
        (r"\btheirs\b", "his"),
        (r"\bthemself\b", "himself"),
        (r"\bthemselves\b", "himself"),
        (r"\bshe\b", "he"),
        (r"\bher\b", "his"),   # safe when used as possessive
        (r"\bhers\b", "his"),
    ],
    "F": [
        (r"\bthey\b", "she"),
        (r"\bthem\b", "her"),
        (r"\btheir\b", "her"),
        (r"\btheirs\b", "hers"),
        (r"\bthemself\b", "herself"),
        (r"\bthemselves\b", "herself"),
        (r"\bhe\b", "she"),
        (r"\bhim\b", "her"),
        (r"\bhis\b", "her"),
    ],
}

# Lightweight style cues appended/inserted to tune movement quality
STYLE_TAGS = {
    "M": "Presenting a masculine look and movement quality (confident posture, strong chest/shoulder isolations).",
    "F": "Presenting a feminine look and movement quality (fluid lines, hip emphasis, graceful arm styling).",
}

# Where to inject the style tag: before identity-lock sentence if we can find one
IDENTITY_ANCHORS = [
    "The anime character matches the uploaded reference exactly",
    "The character matches the uploaded reference exactly",
    "Preserve identity",
]


def inject_style_tag(prompt: str, tag: str) -> str:
    """
    Insert a style tag before the identity anchor if found, otherwise append.
    
    Args:
        prompt: The original prompt text
        tag: The style tag to inject
    
    Returns:
        Prompt with style tag injected
    """
    for anchor in IDENTITY_ANCHORS:
        idx = prompt.find(anchor)
        if idx != -1:
            return prompt[:idx].rstrip() + " " + tag + " " + prompt[idx:]
    # fallback: append
    if prompt.strip().endswith("."):
        return prompt.strip() + " " + tag
    return prompt.strip() + ". " + tag


def map_pronouns(prompt: str, gender: str) -> str:
    """
    Apply pronoun replacements based on gender.
    
    Args:
        prompt: The original prompt text
        gender: Either "M" (masculine) or "F" (feminine)
    
    Returns:
        Prompt with harmonized pronouns
    """
    mapped = prompt
    for pat, repl in PRONOUN_MAPS.get(gender, []):
        mapped = re.sub(pat, repl, mapped, flags=re.IGNORECASE)
    return mapped


def tidy_spaces(text: str) -> str:
    """
    Remove accidental double spaces from replacements.
    
    Args:
        text: Text to clean up
    
    Returns:
        Text with normalized whitespace
    """
    return re.sub(r"\s{2,}", " ", text).strip()


def genderize_prompt(original: str, gender: str) -> str:
    """
    Transform a prompt to match a specified gender presentation.
    
    This function:
    1. Injects gender-appropriate movement quality cues
    2. Harmonizes pronouns to match the specified gender
    3. Ensures visibility constraints (full body, head in frame)
    4. Preserves all original choreography and style instructions
    
    Args:
        original: The original prompt text
        gender: Either "M" (masculine) or "F" (feminine)
    
    Returns:
        Transformed prompt with gender-appropriate styling and pronouns
    
    Examples:
        >>> prompt = "The character dances. They move with energy."
        >>> genderize_prompt(prompt, "M")
        'The character dances. He moves with energy. Presenting a masculine look...'
        
        >>> genderize_prompt(prompt, "F")
        'The character dances. She moves with energy. Presenting a feminine look...'
    """
    # Normalize gender input (accept lowercase)
    gender = gender.upper() if gender else None
    
    if gender not in ["M", "F"]:
        # Return original if gender is not specified or invalid
        return original
    
    # Keep original choreography/constraints intact
    out = original

    # Inject gentle gender movement cue (non-destructive)
    out = inject_style_tag(out, STYLE_TAGS.get(gender, ""))

    # Harmonize pronouns if any are present
    out = map_pronouns(out, gender)

    # Optional: ensure face/body visibility constraints
    vis_bits = []
    if "entire body" not in out.lower():
        vis_bits.append("Entire body is always in frame.")
    if "head is always in the frame" not in out.lower() and "face" not in out.lower():
        vis_bits.append("Head is always in the frame.")
    if vis_bits:
        out = out.rstrip(". ") + " " + " ".join(vis_bits)

    return tidy_spaces(out)


# Convenience function for batch processing
def genderize_prompts(prompts: list[str], gender: str) -> list[str]:
    """
    Transform multiple prompts at once.
    
    Args:
        prompts: List of prompt texts
        gender: Either "M" (masculine) or "F" (feminine)
    
    Returns:
        List of transformed prompts
    """
    return [genderize_prompt(p, gender) for p in prompts]


if __name__ == "__main__":
    # Example usage and testing
    test_prompts = [
        "The character dances confidently. They move with energy and grace.",
        "The anime character matches the uploaded reference exactly—same face, complexion, hair, outfit.",
        "She performs hip-hop choreography. Her movements are sharp and precise.",
    ]
    
    print("=" * 80)
    print("GENDER TRANSFORMATION EXAMPLES")
    print("=" * 80)
    
    for i, prompt in enumerate(test_prompts, 1):
        print(f"\n{'─' * 80}")
        print(f"ORIGINAL PROMPT {i}:")
        print(f"{'─' * 80}")
        print(prompt)
        
        print(f"\n{'─' * 80}")
        print(f"MASCULINE (M) TRANSFORMATION:")
        print(f"{'─' * 80}")
        print(genderize_prompt(prompt, "M"))
        
        print(f"\n{'─' * 80}")
        print(f"FEMININE (F) TRANSFORMATION:")
        print(f"{'─' * 80}")
        print(genderize_prompt(prompt, "F"))
        print()
    
    print("=" * 80)

