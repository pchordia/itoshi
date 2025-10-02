#!/usr/bin/env python3
"""
Interactive Prompt Builder - Dynamic i2i and i2v prompt generation using GPT-5
Uses conversational AI to gather user preferences and generate custom prompts.
"""

import os
import sys
import time
from typing import Optional, Tuple, List, Dict
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
GPT_MODEL = os.getenv("PROMPT_BUILDER_MODEL", "gpt-5")
REASONING_EFFORT = os.getenv("REASONING_EFFORT", "medium")  # low, medium, high
TEXT_VERBOSITY = os.getenv("TEXT_VERBOSITY", "low")  # low, medium, high
MAX_QUESTIONS = 5  # Maximum number of questions before generating prompts

SYSTEM_PROMPT = """You are an expert anime video generation assistant. Your job is to help users create custom i2i (image-to-image) and i2v (image-to-video) prompts through a conversational interview.

## Your Role:
- Ask targeted questions to understand what the user wants their character to do
- **ASK ONLY ONE QUESTION AT A TIME** - wait for the user's answer before asking the next question
- Ask **UP TO {max_questions} questions** - you decide how many are needed (could be 2, 3, 4, or 5)
- Stop asking when you have enough detail to create compelling prompts
- Be conversational, friendly, and efficient
- **For EVERY question, provide a numbered list of 3-4 specific options, ALWAYS ending with "Type your own"**
- After gathering enough information, generate TWO prompts: one for i2i (static anime frame) and one for i2v (video animation)

## CRITICAL: This is Image-to-Image (i2i)
- The user will provide a reference selfie/photo
- **DO NOT ask about character appearance** (face, hair, eyes, skin tone, gender, age, etc.)
- The character's identity will be preserved exactly from the input image
- **DO NOT ask about camera angles or camera motion** - you will determine the best framing and camera movement automatically based on the activity
- Only ask about: scene, setting, activity, props, lighting, specific actions, mood/vibe

## CRITICAL: i2i is the FIRST FRAME (Opening Pose)
- The i2i prompt generates the **opening/starting frame** of the video, NOT the climax or mid-action
- Think of it as the "before" or "setup" moment
- Examples:
  - Eating ramen: Character seated at counter, bowl in front, chopsticks ready (NOT mid-slurp)
  - Playing guitar: Character holding guitar, fingers positioned (NOT mid-strum)
  - Dancing: Character in starting pose, ready to move (NOT mid-jump)
  - Drinking coffee: Character holding cup near face (NOT mid-sip)
- The i2v prompt will describe the motion FROM this starting frame
- Keep the i2i pose natural, anticipatory, and ready for the action to begin

## CRITICAL: 5-Second Video Constraint
- The entire action sequence must fit within **5 seconds** (from first frame to climax/ending)
- Design the starting pose and action to reach a satisfying climax within this time limit
- **When asking questions, suggest activities/movements that work within 5 seconds:**
  - ✅ GOOD: Single action (one slurp, one strum, quick wink, small sip, brief smile)
  - ✅ GOOD: Short sequence (lift noodles → blow → slurp, or pick up guitar → strike chord)
  - ❌ BAD: Complex multi-step sequences, long elaborate choreography, extended narratives
- The starting pose should be close enough to the climax that it can be reached in 5s
- Examples of good 5-second arcs:
  - Ramen: Chopsticks ready (0s) → lift noodles (1-2s) → slurp (3-4s) → smile (5s)
  - Guitar: Hands positioned (0s) → strum begins (1-2s) → full chord (3-4s) → hold/smile (5s)
  - Coffee: Cup near lips (0s) → sip (2-3s) → exhale contentment (4s) → smile (5s)

## Question Format (MANDATORY):
Every question MUST follow this exact format:
```
[Brief friendly question text]

1. [Specific option A with details]
2. [Specific option B with details]
3. [Specific option C with details]
4. Type your own
```

Example:
```
What's the setting vibe?

1. Cozy wooden ramen shop (warm lanterns, rainy window)
2. Neon-lit street stall (cyberpunk, reflections)
3. Minimalist modern cafe (clean lines, natural light)
4. Type your own
```

## Question Strategy (ONE AT A TIME, up to 5 total):
- Decide how many questions you actually need (2-5)
- More complex activities may need 4-5 questions
- Simple activities may only need 2-3 questions
- Typical questions cover:
  1. **Scene/vibe** - setting, atmosphere, lighting
  2. **Key details** - props, specific elements
  3. **Motion style** - energy, movement type (if needed)
  4. **Ending beat** - conclusion moment (if needed)

## Handling Non-Responses:
- If the user ignores a question or gives a vague/short answer (like "idk", "whatever", "sure", or just presses enter)
- **DO NOT repeat the question**
- Instead, **make a tasteful creative decision** based on what works best for the activity
- Move on to the next question or generate the prompts if you have enough information

## When to Stop Asking:
- You have enough detail to create compelling prompts (don't ask unnecessary questions)
- User says "generate", "done", "that's enough", or similar
- User has ignored 2+ questions (make decisions and generate)
- You've reached {max_questions} questions maximum

## Output Format (when ready):
When you have enough information, respond with EXACTLY this JSON structure (and nothing else):
```json
{{
  "i2i_prompt": "The complete i2i prompt text here...",
  "i2v_prompt": "The complete i2v prompt text here...",
  "activity_name": "short_activity_name"
}}
```

## Prompt Guidelines:

### i2i Prompt Requirements:
- Preserve character identity exactly (face, hair, skin tone, outfit, accessories)
- Specify framing, pose, and composition
- Include lighting and atmosphere details
- Mention background elements
- Specify aspect ratio preference (usually 9:16)
- Include constraints (no logos, single subject, etc.)

### i2v Prompt Requirements:
- Use the i2i output as the character base
- Preserve identity from input
- Specify action sequence with timing
- Include camera movement (if any)
- Describe motion details (speed, style, rhythm)
- Specify ending state
- Include environmental effects (steam, lighting, etc.)
- Keep body/head in frame constraints

## Activity Suggestions to Offer:
dance, eat ramen, street fashion shoot, play guitar, basketball moves, karaoke, samurai cosplay, cute pet walk, cooking, reading in cafe, skateboarding, gaming setup, yoga/stretching, painting/drawing, taking photos

Remember: Be efficient, friendly, and creative. Help users bring their vision to life!"""

class InteractivePromptBuilder:
    def __init__(self, max_questions: int = MAX_QUESTIONS):
        if not OPENAI_API_KEY:
            raise ValueError("OPENAI_API_KEY not found in environment")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.max_questions = max_questions
        self.conversation_context = ""  # Build conversation as text for GPT-5 Responses API
        self.questions_asked = 0
        
        # Initialize with system prompt
        system_instruction = SYSTEM_PROMPT.format(max_questions=max_questions)
        self.conversation_context = f"{system_instruction}\n\n"
    
    def start_conversation(self, initial_input: Optional[str] = None) -> Tuple[str, float]:
        """Start the conversation, optionally with user's initial activity idea
        Returns: (assistant_message, time_taken_seconds)
        """
        if initial_input:
            user_message = initial_input
        else:
            user_message = "I want to create an anime video scene."
        
        return self._get_assistant_response(user_message)
    
    def send_message(self, user_message: str) -> Tuple[str, Optional[Dict], float]:
        """
        Send user message and get response.
        Returns: (assistant_message, prompts_dict or None, time_taken_seconds)
        If prompts_dict is not None, the conversation is complete.
        """
        response, time_taken = self._get_assistant_response(user_message)
        
        # Check if response contains the final JSON prompts
        if response.strip().startswith("{") and '"i2i_prompt"' in response:
            try:
                import json
                # Extract JSON from markdown code blocks if present
                if "```json" in response:
                    start = response.find("```json") + 7
                    end = response.find("```", start)
                    json_str = response[start:end].strip()
                elif "```" in response:
                    start = response.find("```") + 3
                    end = response.find("```", start)
                    json_str = response[start:end].strip()
                else:
                    json_str = response.strip()
                
                prompts = json.loads(json_str)
                return response, prompts, time_taken
            except (json.JSONDecodeError, ValueError) as e:
                # Not valid JSON, continue conversation
                pass
        
        return response, None, time_taken
    
    def _get_assistant_response(self, user_message: str) -> Tuple[str, float]:
        """Internal method to get response from GPT-5 using Responses API
        Returns: (assistant_message, time_taken_seconds)
        """
        # Add user message to conversation context
        self.conversation_context += f"User: {user_message}\n\n"
        
        # Call GPT-5 Responses API with timing
        start_time = time.time()
        try:
            response = self.client.responses.create(
                model=GPT_MODEL,
                input=self.conversation_context,
                reasoning={"effort": REASONING_EFFORT},
                text={"verbosity": TEXT_VERBOSITY},
            )
            end_time = time.time()
            time_taken = end_time - start_time
            
            # Extract the assistant's response
            assistant_message = response.output_text
            
            if not assistant_message:
                assistant_message = "[No response]"
                print(f"WARNING: Empty response from GPT-5")
            
            # Add assistant response to conversation context
            self.conversation_context += f"Assistant: {assistant_message}\n\n"
            
            # Increment question counter if this looks like a question
            if "?" in assistant_message and not assistant_message.strip().startswith("{"):
                self.questions_asked += 1
            
            return assistant_message, time_taken
            
        except Exception as e:
            raise RuntimeError(f"Error calling GPT-5 Responses API: {e}")
    
    def get_questions_remaining(self) -> int:
        """Get number of questions remaining"""
        return max(0, self.max_questions - self.questions_asked)


def interactive_cli():
    """Simple CLI interface for testing"""
    print("=" * 70)
    print("🎬 Interactive Anime Prompt Builder (powered by GPT-5)")
    print("=" * 70)
    print()
    
    builder = InteractivePromptBuilder(max_questions=MAX_QUESTIONS)
    
    # Get initial activity
    print("💭 What would you like your character to do?")
    print("   (Suggestions: dance, eat ramen, street fashion shoot, play guitar,")
    print("    basketball moves, karaoke, samurai cosplay, cute pet walk...)")
    print()
    
    initial = input("You: ").strip()
    if not initial:
        print("❌ No input provided. Exiting.")
        return
    
    # Start conversation
    print()
    response = builder.start_conversation(initial)
    print(f"Assistant: {response}")
    print()
    
    # Conversation loop
    while True:
        remaining = builder.get_questions_remaining()
        if remaining > 0:
            print(f"   [{remaining} questions remaining]")
        
        user_input = input("You: ").strip()
        if not user_input:
            continue
        
        if user_input.lower() in ["quit", "exit", "cancel"]:
            print("👋 Exiting prompt builder.")
            return
        
        print()
        response, prompts = builder.send_message(user_input)
        
        if prompts:
            # Prompts generated!
            print("✅ Prompts Generated!")
            print("=" * 70)
            print()
            print("📝 Activity Name:", prompts.get("activity_name", "custom_scene"))
            print()
            print("🎨 I2I Prompt (Image Generation):")
            print("-" * 70)
            print(prompts["i2i_prompt"])
            print()
            print("🎬 I2V Prompt (Video Generation):")
            print("-" * 70)
            print(prompts["i2v_prompt"])
            print()
            
            # Ask if user wants to save
            save = input("💾 Save these prompts? (y/n): ").strip().lower()
            if save == 'y':
                activity_name = prompts.get("activity_name", "custom_scene")
                
                # Save to interactive prompt files
                i2i_path = f"prompts/image_prompt_interactive.txt"
                i2v_path = f"prompts/video_prompt_interactive.txt"
                
                try:
                    # Append to i2i prompts
                    with open(i2i_path, "a", encoding="utf-8") as f:
                        f.write(f"\n{activity_name}: {prompts['i2i_prompt']}")
                    
                    # Append to i2v prompts
                    with open(i2v_path, "a", encoding="utf-8") as f:
                        f.write(f"\n{activity_name}: {prompts['i2v_prompt']}")
                    
                    print(f"✅ Saved to {i2i_path} and {i2v_path}")
                    print(f"   Use --prompt-name {activity_name} when running:")
                    print(f"   - i2i: python src/batch_media.py i2i --prompts {i2i_path} --prompt-name {activity_name}")
                    print(f"   - i2v: python src/batch_media.py i2v --prompts {i2v_path} --prompt-name {activity_name}")
                except Exception as e:
                    print(f"❌ Error saving: {e}")
            
            return
        else:
            print(f"Assistant: {response}")
            print()


if __name__ == "__main__":
    try:
        interactive_cli()
    except KeyboardInterrupt:
        print("\n\n👋 Interrupted. Exiting.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

