"""
Script to save hero background image
Run this after uploading the image file to this directory
"""

import os
import shutil
from pathlib import Path

# Source and destination paths
# The image should be placed in the Django folder first
source_paths = [
    'hero-bg.jpg',
    'hero_bg.jpg',
    'hero.jpg',
    'background.jpg',
]

dest_dir = Path('mysite/static/images')
dest_dir.mkdir(parents=True, exist_ok=True)

# Try to find the image
for source in source_paths:
    if os.path.exists(source):
        dest = dest_dir / 'hero-bg.jpg'
        shutil.copy(source, dest)
        print(f"✓ Image saved successfully to {dest}")
        break
else:
    print("❌ Image file not found!")
    print(f"Please place the image file in the Django folder and name it: {source_paths[0]}")
    print(f"It will be saved to: {dest_dir / 'hero-bg.jpg'}")
