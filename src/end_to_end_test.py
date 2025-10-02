#!/usr/bin/env python3
"""
End-to-End Test: Interactive prompt generation → i2i → i2v
1. User provides text describing what they want
2. GPT-5 generates custom i2i and i2v prompts interactively
3. System runs i2i (OpenAI gpt-image) on a random image from selfie_test_fb/
4. System runs i2v (Kling) on the generated anime image
"""

import os
import sys
import random
import subprocess
import shutil
from pathlib import Path
from datetime import datetime
from interactive_prompt_builder import InteractivePromptBuilder

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
    i2i_path = f"prompts/temp_i2i_{activity_name}.txt"
    i2v_path = f"prompts/temp_i2v_{activity_name}.txt"
    
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
    print("🎨 STEP 2: Running i2i (Image-to-Image) with OpenAI gpt-image")
    print("=" * 70)
    print(f"Input: {input_image}")
    print(f"Output: {output_dir}")
    print(f"Prompt: {prompt_name}")
    print()
    
    # Create temp directory with just this image (batch_media.py expects a directory)
    temp_input_dir = "temp_e2e_input"
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
    print("🎬 STEP 3: Running i2v (Image-to-Video) with Kling")
    print("=" * 70)
    print(f"Input: {input_image}")
    print(f"Output: {output_dir}")
    print(f"Prompt: {prompt_name}")
    print()
    
    # Create temp directory with just this image (batch_media.py expects a directory)
    temp_input_dir = "temp_e2e_i2v_input"
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

def interactive_mode():
    """Run in interactive mode with user input"""
    # Create log file
    timestamp = datetime.now().strftime("%y%m%d_%H%M%S")
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, f"e2e_session_{timestamp}.txt")
    
    def log(message: str, to_console: bool = True):
        """Write to both console and log file"""
        if to_console:
            print(message)
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(message + "\n")
    
    log("=" * 70)
    log("🎬 End-to-End Interactive Anime Video Generator")
    log("=" * 70)
    log("")
    log(f"📝 Session started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log(f"📄 Log file: {log_file}")
    log("")
    log("This will:")
    log("1. Use GPT-5 to create custom prompts based on your input")
    log("2. Generate an anime image (i2i) from a random selfie_test_fb/ image")
    log("3. Generate a video (i2v) from the anime image using Kling")
    log("")
    
    # Step 1: Interactive prompt generation
    log("=" * 70)
    log("🤖 STEP 1: Interactive Prompt Generation (GPT-5)")
    log("=" * 70)
    log("")
    log("💭 What would you like your character to do?")
    log("   (Examples: dance, eat ramen, play guitar, street fashion shoot,")
    log("    basketball moves, karaoke, read in a cafe, yoga pose...)")
    log("")
    
    initial_input = input("You: ").strip()
    log(f"You: {initial_input}", to_console=False)  # Already printed by input()
    
    if not initial_input:
        log("❌ No input provided. Exiting.")
        return
    
    # Create prompt builder
    builder = InteractivePromptBuilder(max_questions=5)
    
    log("")
    response, response_time = builder.start_conversation(initial_input)
    log(f"Assistant ({response_time:.2f}s): {response}")
    log("")
    
    # Conversation loop
    prompts = None
    while prompts is None:
        remaining = builder.get_questions_remaining()
        if remaining > 0:
            log(f"   [{remaining} questions remaining]")
        
        user_input = input("You: ").strip()
        log(f"You: {user_input}", to_console=False)  # Already printed by input()
        
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit", "cancel"]:
            log("👋 Exiting.")
            return
        
        log("")
        response, prompts, response_time = builder.send_message(user_input)
        
        if not prompts:
            log(f"Assistant ({response_time:.2f}s): {response}")
            log("")
        else:
            # Final prompt generation - log the time
            log(f"✅ Prompts generated in {response_time:.2f}s")
            log("")
    
    # Prompts generated!
    log("=" * 70)
    log("✅ PROMPTS GENERATED!")
    log("=" * 70)
    log("")
    
    activity_name = prompts.get("activity_name", "custom_scene")
    log(f"📝 Activity: {activity_name}")
    log("")
    
    # Print full i2i prompt
    log("🎨 I2I PROMPT (Full):")
    log("-" * 70)
    log(prompts["i2i_prompt"])
    log("-" * 70)
    log("")
    
    # Print full i2v prompt
    log("🎬 I2V PROMPT (Full):")
    log("-" * 70)
    log(prompts["i2v_prompt"])
    log("-" * 70)
    log("")
    
    # Save prompts
    i2i_prompts_file, i2v_prompts_file = save_prompts(prompts, activity_name)
    log(f"💾 Saved prompts to:")
    log(f"   i2i: {i2i_prompts_file}")
    log(f"   i2v: {i2v_prompts_file}")
    log("")
    
    # Select random image (note: get_random_image already prints to console)
    log("")
    log("📸 Selecting random image from selfie_test_fb/...", to_console=False)
    random_image = get_random_image("selfie_test_fb")
    log(f"📸 Selected: {random_image}", to_console=False)  # Already printed by function
    log("")
    
    # Run i2i (run_i2i already prints its own output)
    i2i_output = "outputs/images/e2e_test"
    log(f"🎨 Running i2i on {random_image}...", to_console=False)
    generated_image = run_i2i(random_image, i2i_output, i2i_prompts_file, activity_name)
    log(f"✅ i2i complete: {generated_image}", to_console=False)
    log("")
    
    # Run i2v (run_i2v already prints its own output)
    i2v_output = "outputs/videos/e2e_test"
    log(f"🎬 Running i2v on {generated_image}...", to_console=False)
    run_i2v(generated_image, i2v_output, i2v_prompts_file, activity_name)
    log(f"✅ i2v complete", to_console=False)
    log("")
    
    log("")
    log("=" * 70)
    log("🎉 END-TO-END TEST COMPLETE!")
    log("=" * 70)
    log("")
    log(f"📁 Generated anime image: {generated_image}")
    log(f"📁 Generated video: {i2v_output}/")
    log(f"📄 Full session log: {log_file}")
    log("")
    
    # Cleanup temp files
    os.remove(i2i_prompts_file)
    os.remove(i2v_prompts_file)
    log("🧹 Cleaned up temporary prompt files")
    log("")
    log(f"📝 Session ended: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    try:
        interactive_mode()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

