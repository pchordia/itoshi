#!/usr/bin/env python3
"""
One-Shot End-to-End: Activity → Prompts → i2i → i2v
Fast mode with activity menu and instant prompt generation.
"""

import os
import sys
import random
import subprocess
import shutil
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))
from oneshot_prompt_builder import OneShotPromptBuilder

def get_random_image(directory: str) -> str:
    """Get a random image from the directory"""
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = [
        f for f in Path(directory).iterdir()
        if f.is_file() and f.suffix.lower() in image_extensions
    ]
    
    if not images:
        raise ValueError(f"No images found in {directory}")
    
    selected = random.choice(images)
    print(f"📸 Selected random image: {selected.name}")
    return str(selected)

def save_prompts(prompts: dict, activity_name: str) -> tuple:
    """Save prompts to temporary files and return paths"""
    i2i_path = f"prompts/temp_oneshot_i2i_{activity_name}.txt"
    i2v_path = f"prompts/temp_oneshot_i2v_{activity_name}.txt"
    
    # Write i2i prompt
    with open(i2i_path, "w", encoding="utf-8") as f:
        f.write(f"{activity_name}: {prompts['i2i_prompt']}")
    
    # Write i2v prompt
    with open(i2v_path, "w", encoding="utf-8") as f:
        f.write(f"{activity_name}: {prompts['i2v_prompt']}")
    
    return i2i_path, i2v_path

def run_i2i(input_image: str, output_dir: str, prompts_file: str, prompt_name: str) -> str:
    """Run i2i using OpenAI gpt-image"""
    print()
    print("=" * 70)
    print("🎨 STEP 2: Running i2i (Image-to-Image)")
    print("=" * 70)
    print(f"Input: {input_image}")
    print(f"Output: {output_dir}")
    print(f"Style: {prompt_name}")
    print()
    
    # Create temp directory with just this image
    temp_input_dir = "temp_oneshot_input"
    os.makedirs(temp_input_dir, exist_ok=True)
    
    # Copy image to temp directory
    image_name = Path(input_image).name
    temp_image_path = os.path.join(temp_input_dir, image_name)
    shutil.copy2(input_image, temp_image_path)
    
    try:
        cmd = [
            "python", "src/batch_media.py", "anime",
            "--input", temp_input_dir,
            "--output", output_dir,
            "--prompts", prompts_file,
            "--prompt-name", prompt_name
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ i2i failed:")
            print(result.stderr)
            raise RuntimeError(f"i2i failed with exit code {result.returncode}")
        
        print(result.stdout)
        
        # Find the generated image
        output_path = Path(output_dir)
        latest_dir = max(output_path.glob("*/"), key=os.path.getmtime)
        generated_images = list(latest_dir.glob("*.png"))
        
        if not generated_images:
            raise RuntimeError("No generated images found")
        
        generated_image = str(generated_images[0])
        print(f"✅ i2i complete: {generated_image}")
        return generated_image
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_input_dir, ignore_errors=True)

def run_i2v(input_image: str, output_dir: str, prompts_file: str, prompt_name: str):
    """Run i2v using Kling"""
    print()
    print("=" * 70)
    print("🎬 STEP 3: Running i2v (Image-to-Video)")
    print("=" * 70)
    print(f"Input: {input_image}")
    print(f"Output: {output_dir}")
    print(f"Action: {prompt_name}")
    print()
    
    # Create temp directory with just this image
    temp_input_dir = "temp_oneshot_i2v_input"
    os.makedirs(temp_input_dir, exist_ok=True)
    
    # Copy image to temp directory
    image_name = Path(input_image).name
    temp_image_path = os.path.join(temp_input_dir, image_name)
    shutil.copy2(input_image, temp_image_path)
    
    try:
        cmd = [
            "python", "src/batch_media.py", "i2v",
            "--input", temp_input_dir,
            "--output", output_dir,
            "--prompts", prompts_file,
            "--prompt-name", prompt_name,
            "--model", "kling",
            "--duration", "5"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print("❌ i2v failed:")
            print(result.stderr)
            raise RuntimeError(f"i2v failed with exit code {result.returncode}")
        
        print(result.stdout)
        print("✅ i2v complete!")
        
    finally:
        # Cleanup temp directory
        shutil.rmtree(temp_input_dir, ignore_errors=True)

def main():
    """Main one-shot workflow"""
    # Create log file
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"oneshot_session_{timestamp}.txt")
    
    def log(message: str, to_console: bool = True):
        """Write to both console and log file"""
        if to_console:
            print(message)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    
    log("=" * 70)
    log("🎬 One-Shot Anime Video Generator")
    log("=" * 70)
    log("")
    log(f"📝 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📄 Log file: {log_file}")
    log("")
    log("Fast mode: Pick activity → Generate prompts → Create video!")
    log("")
    
    # Step 1: Get GPT-5 suggestions and user choice
    log("=" * 70)
    log("🎯 STEP 1: Activity Suggestions")
    log("=" * 70)
    log("")
    
    # Get GPT-5 suggestions
    log("🤖 Getting personalized activity suggestions from GPT-5...")
    log("")
    
    builder = OneShotPromptBuilder()
    
    try:
        suggestions, suggest_time = builder.suggest_activities()
        
        log(f"✨ Here are 5 activities that would make great videos ({suggest_time:.1f}s):")
        log("")
        
        for i, suggestion in enumerate(suggestions, 1):
            log(f"  {i}. {suggestion}")
        
        log("")
        log("💭 Pick a number (1-5) or describe your own activity:")
        
    except Exception as e:
        log(f"⚠️  Couldn't get suggestions: {e}")
        log("💭 No problem! Just describe what you want:")
    
    log("")
    user_input = input("You: ").strip()
    log(f"You: {user_input}", to_console=False)
    
    if not user_input:
        log("❌ No input provided. Exiting.")
        return
    
    if user_input.lower() in ["quit", "exit", "cancel"]:
        log("👋 Exiting.")
        return
    
    # Handle numbered selection
    if user_input.isdigit():
        choice_num = int(user_input)
        if 1 <= choice_num <= 5 and 'suggestions' in locals():
            user_input = suggestions[choice_num - 1]
            log(f"📝 Selected: {user_input}")
            log("")
    
    # Generate prompts using one-shot builder
    log("")
    log("🤖 Generating optimal prompts with GPT-5...")
    log("")
    
    try:
        prompts, response_time = builder.generate_prompts(user_input)
        
        log(f"✅ Prompts generated in {response_time:.2f}s")
        log("")
        
        # Display prompts
        log("=" * 70)
        log("📋 GENERATED PROMPTS")
        log("=" * 70)
        log("")
        
        activity_name = prompts.get("activity_name", "custom_scene")
        log(f"📝 Activity: {activity_name}")
        log("")
        
        log("🎨 I2I PROMPT (Opening Frame):")
        log("-" * 70)
        log(prompts["i2i_prompt"])
        log("")
        
        log("🎬 I2V PROMPT (5-Second Action):")
        log("-" * 70)
        log(prompts["i2v_prompt"])
        log("")
        
        # Save prompts
        i2i_prompts_file, i2v_prompts_file = save_prompts(prompts, activity_name)
        log(f"💾 Saved prompts to temporary files")
        log("")
        
        # Select random image
        log("📸 Selecting random image from selfie_test_fb/...")
        random_image = get_random_image("selfie_test_fb")
        log("")
        
        # Run i2i
        i2i_output = "outputs/images/oneshot"
        generated_image = run_i2i(random_image, i2i_output, i2i_prompts_file, activity_name)
        log("")
        
        # Run i2v
        i2v_output = "outputs/videos/oneshot"
        run_i2v(generated_image, i2v_output, i2v_prompts_file, activity_name)
        log("")
        
        # Success!
        log("")
        log("=" * 70)
        log("🎉 ONE-SHOT COMPLETE!")
        log("=" * 70)
        log("")
        log(f"📁 Anime image: {generated_image}")
        log(f"📁 Video output: {i2v_output}/")
        log(f"📄 Full session log: {log_file}")
        log("")
        
        # Cleanup temp files
        os.remove(i2i_prompts_file)
        os.remove(i2v_prompts_file)
        log("🧹 Cleaned up temporary files")
        log("")
        
        log(f"📝 Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
    except Exception as e:
        log(f"❌ Error: {e}")
        import traceback
        log(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

