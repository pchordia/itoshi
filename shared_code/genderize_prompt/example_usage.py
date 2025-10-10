"""
Example Usage of Gender Transformation Module

This script demonstrates how to use the genderize_prompt module
to transform video generation prompts.
"""

from genderize_prompt import genderize_prompt, genderize_prompts


def example_1_single_prompt():
    """Example 1: Transform a single prompt"""
    print("="*80)
    print("EXAMPLE 1: Single Prompt Transformation")
    print("="*80)
    
    original = """The character breakdances like a cool, confident, expert 
TikTok breakdance dance star to a 160 BPM breakbeat song. They perform 
toprock crossovers, 6-step footwork, kickouts, and baby freeze. The character 
matches the uploaded reference exactly—same face, complexion, hair, outfit."""
    
    print("\nOriginal Prompt:")
    print("-" * 80)
    print(original)
    
    print("\n\nMasculine Version:")
    print("-" * 80)
    masculine = genderize_prompt(original, "M")
    print(masculine)
    
    print("\n\nFeminine Version:")
    print("-" * 80)
    feminine = genderize_prompt(original, "F")
    print(feminine)
    print()


def example_2_batch_prompts():
    """Example 2: Transform multiple prompts at once"""
    print("="*80)
    print("EXAMPLE 2: Batch Prompt Transformation")
    print("="*80)
    
    dance_styles = {
        "hip-hop": "The character dances hip-hop. They perform sharp isolations and grooves.",
        "ballet": "The character dances ballet. They move with grace and precision.",
        "kpop": "The character performs K-pop choreography. They hit sharp poses and move energetically.",
    }
    
    print("\nTransforming all prompts to MASCULINE...")
    print("-" * 80)
    for style, prompt in dance_styles.items():
        result = genderize_prompt(prompt, "M")
        print(f"\n{style.upper()}:")
        print(result)
    
    print("\n\nTransforming all prompts to FEMININE...")
    print("-" * 80)
    for style, prompt in dance_styles.items():
        result = genderize_prompt(prompt, "F")
        print(f"\n{style.upper()}:")
        print(result)
    print()


def example_3_api_integration():
    """Example 3: How to integrate with a video generation API"""
    print("="*80)
    print("EXAMPLE 3: API Integration Pattern")
    print("="*80)
    
    # Simulated API call (replace with your actual API)
    def generate_video_api(image_path, prompt, gender=None):
        """Simulated video generation API"""
        if gender:
            prompt = genderize_prompt(prompt, gender)
        
        print(f"\nGenerating video with gender={gender}:")
        print(f"Image: {image_path}")
        print(f"Prompt: {prompt[:100]}...")
        print("✅ Video generated successfully!")
        return f"video_{gender}.mp4"
    
    base_prompt = """The character dances to a 160 BPM beat. They move 
confidently with varied steps. The character matches the uploaded 
reference exactly."""
    
    # Generate both versions
    masculine_video = generate_video_api("user_photo.jpg", base_prompt, "M")
    feminine_video = generate_video_api("user_photo.jpg", base_prompt, "F")
    
    print(f"\nGenerated videos:")
    print(f"  - {masculine_video}")
    print(f"  - {feminine_video}")
    print()


def example_4_conditional_usage():
    """Example 4: Conditional usage based on user preference"""
    print("="*80)
    print("EXAMPLE 4: Conditional Usage")
    print("="*80)
    
    base_prompt = "The character performs contemporary dance. They move fluidly."
    
    # Simulate user choices
    test_cases = [
        ("M", "User selected: Masculine"),
        ("F", "User selected: Feminine"),
        (None, "User selected: Default (no gender transformation)"),
    ]
    
    for gender, description in test_cases:
        print(f"\n{description}")
        print("-" * 80)
        
        if gender:
            final_prompt = genderize_prompt(base_prompt, gender)
        else:
            final_prompt = base_prompt
        
        print(final_prompt)
    print()


if __name__ == "__main__":
    print("\n")
    print("╔" + "="*78 + "╗")
    print("║" + " "*20 + "GENDERIZE PROMPT EXAMPLES" + " "*33 + "║")
    print("╚" + "="*78 + "╝")
    print()
    
    example_1_single_prompt()
    example_2_batch_prompts()
    example_3_api_integration()
    example_4_conditional_usage()
    
    print("="*80)
    print("All examples completed!")
    print("="*80)

