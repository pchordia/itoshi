#!/usr/bin/env python3
"""
GUI App for Interactive Anime Video Generator
A standalone Mac application with file picker for selfie selection
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, scrolledtext, messagebox
from tkinter import ttk
import threading
from pathlib import Path
from datetime import datetime
from interactive_prompt_builder import InteractivePromptBuilder
from end_to_end_test import save_prompts, run_i2i, run_i2v
from secure_config import SecureConfig

class AnimeVideoGeneratorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Anime Video Generator")
        self.root.geometry("800x900")
        
        # Check API keys
        if not self._check_api_keys():
            return
        
        # State
        self.selected_image = None
        self.builder = None
        self.prompts = None
        self.activity_name = None
        self.conversation_active = False
        
        # Create UI
        self.create_ui()
    
    def _check_api_keys(self) -> bool:
        """Check if API keys are configured"""
        openai_key = SecureConfig.get_key("OPENAI_API_KEY")
        
        if not openai_key:
            result = messagebox.askyesno(
                "API Keys Required",
                "API keys are not configured.\n\n"
                "Would you like to set them up now?\n\n"
                "(Keys will be stored securely in macOS Keychain)",
                icon='warning'
            )
            
            if result:
                # Run setup in terminal
                messagebox.showinfo(
                    "Setup Instructions",
                    "Please run the following command in Terminal:\n\n"
                    "python src/secure_config.py\n\n"
                    "Then restart this app."
                )
            
            self.root.destroy()
            return False
        
        return True
        
    def create_ui(self):
        """Create the main UI"""
        # Main container with padding
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Title
        title = ttk.Label(main_frame, text="🎬 Interactive Anime Video Generator", 
                         font=("Helvetica", 18, "bold"))
        title.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Step 1: Image Selection
        step1_frame = ttk.LabelFrame(main_frame, text="Step 1: Select Your Selfie", padding="10")
        step1_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.image_label = ttk.Label(step1_frame, text="No image selected")
        self.image_label.grid(row=0, column=0, padx=(0, 10))
        
        self.select_btn = ttk.Button(step1_frame, text="Choose Image...", 
                                     command=self.select_image)
        self.select_btn.grid(row=0, column=1)
        
        # Step 2: Activity Input
        step2_frame = ttk.LabelFrame(main_frame, text="Step 2: What do you want your character to do?", 
                                     padding="10")
        step2_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        examples = ttk.Label(step2_frame, 
                           text="Examples: eat ramen, play guitar, drink coffee, dance, read book...",
                           font=("Helvetica", 10), foreground="gray")
        examples.grid(row=0, column=0, columnspan=2, sticky=tk.W, pady=(0, 5))
        
        self.activity_entry = ttk.Entry(step2_frame, width=50)
        self.activity_entry.grid(row=1, column=0, padx=(0, 10))
        
        self.start_btn = ttk.Button(step2_frame, text="Start →", 
                                    command=self.start_conversation, state="disabled")
        self.start_btn.grid(row=1, column=1)
        
        # Step 3: Conversation Area
        step3_frame = ttk.LabelFrame(main_frame, text="Step 3: Interactive Q&A (GPT-5)", 
                                     padding="10")
        step3_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        
        # Conversation display
        self.conversation_text = scrolledtext.ScrolledText(step3_frame, height=20, width=90, 
                                                          wrap=tk.WORD, state="disabled")
        self.conversation_text.grid(row=0, column=0, columnspan=2, pady=(0, 10))
        
        # User input
        self.user_input = ttk.Entry(step3_frame, width=70, state="disabled")
        self.user_input.grid(row=1, column=0, padx=(0, 10))
        self.user_input.bind("<Return>", lambda e: self.send_message())
        
        self.send_btn = ttk.Button(step3_frame, text="Send", 
                                   command=self.send_message, state="disabled")
        self.send_btn.grid(row=1, column=1)
        
        # Step 4: Generation
        step4_frame = ttk.LabelFrame(main_frame, text="Step 4: Generate Video", padding="10")
        step4_frame.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.generate_btn = ttk.Button(step4_frame, text="🎬 Generate Anime Video", 
                                       command=self.generate_video, state="disabled")
        self.generate_btn.pack()
        
        # Status bar
        self.status = ttk.Label(main_frame, text="Ready. Select an image to begin.", 
                               relief=tk.SUNKEN, anchor=tk.W)
        self.status.grid(row=5, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(3, weight=1)
    
    def select_image(self):
        """Open file dialog to select an image"""
        filename = filedialog.askopenfilename(
            title="Select Selfie Image",
            filetypes=[
                ("Image files", "*.jpg *.jpeg *.png *.webp"),
                ("All files", "*.*")
            ]
        )
        
        if filename:
            self.selected_image = filename
            self.image_label.config(text=f"✓ {Path(filename).name}")
            self.start_btn.config(state="normal")
            self.update_status(f"Image selected: {Path(filename).name}")
    
    def start_conversation(self):
        """Start the GPT-5 conversation"""
        activity = self.activity_entry.get().strip()
        if not activity:
            messagebox.showwarning("Input Required", "Please enter what you want your character to do.")
            return
        
        if not self.selected_image:
            messagebox.showwarning("Image Required", "Please select an image first.")
            return
        
        # Disable start button
        self.start_btn.config(state="disabled")
        self.activity_entry.config(state="disabled")
        self.select_btn.config(state="disabled")
        
        # Enable conversation UI
        self.user_input.config(state="normal")
        self.send_btn.config(state="normal")
        self.conversation_text.config(state="normal")
        
        # Clear conversation
        self.conversation_text.delete(1.0, tk.END)
        
        # Initialize builder
        self.builder = InteractivePromptBuilder(max_questions=5)
        self.conversation_active = True
        
        # Add user message to display
        self.add_to_conversation(f"You: {activity}\n\n", "user")
        self.update_status("Waiting for GPT-5 response...")
        
        # Get response in background thread
        def get_response():
            try:
                response, response_time = self.builder.start_conversation(activity)
                self.root.after(0, lambda: self.handle_response(response, response_time))
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def send_message(self):
        """Send user message to GPT-5"""
        user_msg = self.user_input.get().strip()
        if not user_msg:
            return
        
        # Add to display
        self.add_to_conversation(f"You: {user_msg}\n\n", "user")
        self.user_input.delete(0, tk.END)
        
        # Disable input while waiting
        self.user_input.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.update_status("Waiting for GPT-5 response...")
        
        # Get response in background
        def get_response():
            try:
                response, prompts, response_time = self.builder.send_message(user_msg)
                self.root.after(0, lambda: self.handle_response(response, response_time, prompts))
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
        
        threading.Thread(target=get_response, daemon=True).start()
    
    def handle_response(self, response, response_time, prompts=None):
        """Handle GPT-5 response"""
        # Add response to display
        self.add_to_conversation(f"Assistant ({response_time:.2f}s): {response}\n\n", "assistant")
        
        if prompts:
            # Prompts generated!
            self.prompts = prompts
            self.activity_name = prompts.get("activity_name", "custom_scene")
            self.conversation_active = False
            
            self.add_to_conversation(f"\n✅ Prompts generated! Ready to create video.\n", "system")
            
            # Disable conversation, enable generate
            self.user_input.config(state="disabled")
            self.send_btn.config(state="disabled")
            self.generate_btn.config(state="normal")
            self.update_status("✅ Ready to generate video")
        else:
            # Continue conversation
            self.user_input.config(state="normal")
            self.send_btn.config(state="normal")
            remaining = self.builder.get_questions_remaining()
            self.update_status(f"Your turn ({remaining} questions remaining)")
    
    def handle_error(self, error_msg):
        """Handle errors"""
        self.add_to_conversation(f"\n❌ Error: {error_msg}\n", "error")
        self.update_status(f"Error: {error_msg}")
        messagebox.showerror("Error", error_msg)
        
        # Re-enable UI
        self.start_btn.config(state="normal")
        self.activity_entry.config(state="normal")
        self.select_btn.config(state="normal")
    
    def generate_video(self):
        """Generate the anime video"""
        if not self.prompts or not self.selected_image:
            return
        
        # Disable generate button
        self.generate_btn.config(state="disabled")
        self.update_status("🎨 Generating anime image (i2i)...")
        
        def generate():
            try:
                # Save prompts to temp files
                i2i_prompts_file, i2v_prompts_file = save_prompts(self.prompts, self.activity_name)
                
                # Run i2i
                self.root.after(0, lambda: self.update_status("🎨 Generating anime image (this may take 1-2 minutes)..."))
                i2i_output = "outputs/images/gui_app"
                generated_image = run_i2i(self.selected_image, i2i_output, 
                                        i2i_prompts_file, self.activity_name)
                
                # Run i2v
                self.root.after(0, lambda: self.update_status("🎬 Generating video (this may take 2-3 minutes)..."))
                i2v_output = "outputs/videos/gui_app"
                run_i2v(generated_image, i2v_output, i2v_prompts_file, self.activity_name)
                
                # Cleanup temp files
                os.remove(i2i_prompts_file)
                os.remove(i2v_prompts_file)
                
                # Success!
                self.root.after(0, lambda: self.generation_complete(generated_image, i2v_output))
                
            except Exception as e:
                self.root.after(0, lambda: self.handle_error(str(e)))
                self.root.after(0, lambda: self.generate_btn.config(state="normal"))
        
        threading.Thread(target=generate, daemon=True).start()
    
    def generation_complete(self, image_path, video_dir):
        """Handle successful generation"""
        self.add_to_conversation(f"\n🎉 Generation complete!\n", "system")
        self.add_to_conversation(f"📁 Anime image: {image_path}\n", "system")
        self.add_to_conversation(f"📁 Video: {video_dir}/\n", "system")
        
        self.update_status("✅ Video generation complete!")
        
        # Show success dialog
        result = messagebox.askquestion(
            "Success!",
            "Video generated successfully!\n\nWould you like to create another video?",
            icon='info'
        )
        
        if result == 'yes':
            self.reset()
        else:
            self.root.quit()
    
    def reset(self):
        """Reset the app for a new generation"""
        self.selected_image = None
        self.builder = None
        self.prompts = None
        self.activity_name = None
        self.conversation_active = False
        
        self.image_label.config(text="No image selected")
        self.activity_entry.delete(0, tk.END)
        self.conversation_text.config(state="normal")
        self.conversation_text.delete(1.0, tk.END)
        self.conversation_text.config(state="disabled")
        
        self.select_btn.config(state="normal")
        self.start_btn.config(state="disabled")
        self.activity_entry.config(state="normal")
        self.user_input.config(state="disabled")
        self.send_btn.config(state="disabled")
        self.generate_btn.config(state="disabled")
        
        self.update_status("Ready. Select an image to begin.")
    
    def add_to_conversation(self, text, tag):
        """Add text to conversation display"""
        self.conversation_text.config(state="normal")
        
        # Configure tags
        self.conversation_text.tag_config("user", foreground="blue")
        self.conversation_text.tag_config("assistant", foreground="green")
        self.conversation_text.tag_config("system", foreground="purple", font=("Helvetica", 10, "bold"))
        self.conversation_text.tag_config("error", foreground="red")
        
        self.conversation_text.insert(tk.END, text, tag)
        self.conversation_text.see(tk.END)
        self.conversation_text.config(state="disabled")
    
    def update_status(self, message):
        """Update status bar"""
        self.status.config(text=message)
        self.root.update_idletasks()

def main():
    root = tk.Tk()
    app = AnimeVideoGeneratorApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()

