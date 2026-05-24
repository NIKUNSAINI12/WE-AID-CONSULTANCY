import os
import re

dir_path = 'stitch_assets'
files = [f for f in os.listdir(dir_path) if f.endswith('.html')]

for file in files:
    filepath = os.path.join(dir_path, file)
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Change sticky to fixed
    new_content = content.replace('header class="sticky', 'header class="fixed')
    
    # Add top margin to main to avoid overlapping with fixed header
    # but only if we actually changed something to fixed
    if 'header class="fixed' in new_content:
        # Check if already added mt-24 to avoid double adding
        if 'mt-24' not in new_content:
            new_content = re.sub(r'(<main class="[^"]*)(")', r'\1 pt-24\2', new_content)
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Updated {file}")

print("Done updating headers.")
