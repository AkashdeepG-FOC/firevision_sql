#!/usr/bin/env python3
"""
Script to create placeholder icon files for the enhanced fullscreen widget.
Replace these with your actual icon PNG files.
"""

import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(filename, text, bg_color=(60, 60, 60), text_color=(255, 255, 255), size=(32, 32)):
    """Create a simple icon with text"""
    try:
        # Create image
        img = Image.new('RGBA', size, bg_color + (255,))
        draw = ImageDraw.Draw(img)
        
        # Try to use a font, fallback to default
        try:
            font = ImageFont.truetype("arial.ttf", 16)
        except:
            font = ImageFont.load_default()
        
        # Get text size and center it
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        # Draw text
        draw.text((x, y), text, fill=text_color + (255,), font=font)
        
        # Save image
        img.save(filename, 'PNG')
        print(f"Created icon: {filename}")
        
    except Exception as e:
        print(f"Error creating icon {filename}: {e}")

def main():
    # Create icons directory
    icons_dir = "assests/icons"
    os.makedirs(icons_dir, exist_ok=True)
    
    # Define icons to create
    icons = [
        ("play.png", "▶", (0, 150, 0)),      # Green play button
        ("pause.png", "⏸", (255, 165, 0)),   # Orange pause button
        ("stop.png", "⏹", (200, 0, 0)),      # Red stop button
        ("record.png", "⏺", (200, 0, 0)),    # Red record button
        ("previous.png", "⏮", (100, 100, 100)), # Gray previous
        ("next.png", "⏭", (100, 100, 100)),     # Gray next
        ("people.png", "👥", (0, 170, 0)),      # Green people
        ("fire.png", "🔥", (255, 69, 0)),       # Red fire
        ("auto.png", "🤖", (170, 102, 0)),      # Orange auto
        ("zoom_in.png", "+", (100, 100, 100)),  # Gray zoom in
        ("zoom_out.png", "-", (100, 100, 100)), # Gray zoom out
    ]
    
    # Create each icon
    for filename, text, color in icons:
        filepath = os.path.join(icons_dir, filename)
        create_icon(filepath, text, color)
    
    print(f"\nCreated {len(icons)} placeholder icons in {icons_dir}/")
    print("Replace these with your actual icon PNG files for better appearance.")

if __name__ == "__main__":
    main()