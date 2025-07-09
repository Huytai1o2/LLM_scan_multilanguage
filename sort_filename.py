import glob
import os
import re

def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

images_folder = "images"
image_files = glob.glob(os.path.join(images_folder, "*.png"))
image_files.sort(key=natural_keys)

print(f"Tìm thấy {len(image_files)} ảnh để xử lý...")
for file in image_files:
    print(file)
