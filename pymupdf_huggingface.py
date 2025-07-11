# import pymupdf4llm
# md_texts = pymupdf4llm.to_markdown("quy_dinh_hoc_vu_va_dao_tao.pdf", write_images=True, show_progress=True, page_chunks=True, image_path="images")

from PIL import Image
import re
import torch
import os
import glob
import numpy as np
import torchvision.transforms as T
from torchvision.transforms.functional import InterpolationMode
from transformers import AutoModel, AutoTokenizer

model_id = "5CD-AI/Vintern-1B-v3_5"

# Lấy tất cả file ảnh trong thư mục images
def atoi(text):
    return int(text) if text.isdigit() else text

def natural_keys(text):
    return [atoi(c) for c in re.split(r'(\d+)', text)]

images_folder = "images"
image_files = glob.glob(os.path.join(images_folder, "*.png"))
image_files.sort(key=natural_keys)

print(f"Tìm thấy {len(image_files)} ảnh để xử lý...")

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

def build_transform(input_size):
    MEAN, STD = IMAGENET_MEAN, IMAGENET_STD
    transform = T.Compose([
        T.Lambda(lambda img: img.convert('RGB') if img.mode != 'RGB' else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=MEAN, std=STD)
    ])
    return transform

def find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_ratio_diff = float('inf')
    best_ratio = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_aspect_ratio = ratio[0] / ratio[1]
        ratio_diff = abs(aspect_ratio - target_aspect_ratio)
        if ratio_diff < best_ratio_diff:
            best_ratio_diff = ratio_diff
            best_ratio = ratio
        elif ratio_diff == best_ratio_diff:
            if area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
                best_ratio = ratio
    return best_ratio

def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=False):
    orig_width, orig_height = image.size
    aspect_ratio = orig_width / orig_height

    # calculate the existing image aspect ratio
    target_ratios = set(
        (i, j) for n in range(min_num, max_num + 1) for i in range(1, n + 1) for j in range(1, n + 1) if
        i * j <= max_num and i * j >= min_num)
    target_ratios = sorted(target_ratios, key=lambda x: x[0] * x[1])

    # find the closest aspect ratio to the target
    target_aspect_ratio = find_closest_aspect_ratio(
        aspect_ratio, target_ratios, orig_width, orig_height, image_size)

    # calculate the target width and height
    target_width = image_size * target_aspect_ratio[0]
    target_height = image_size * target_aspect_ratio[1]
    blocks = target_aspect_ratio[0] * target_aspect_ratio[1]

    # resize the image
    resized_img = image.resize((target_width, target_height))
    processed_images = []
    for i in range(blocks):
        box = (
            (i % (target_width // image_size)) * image_size,
            (i // (target_width // image_size)) * image_size,
            ((i % (target_width // image_size)) + 1) * image_size,
            ((i // (target_width // image_size)) + 1) * image_size
        )
        # split the image
        split_img = resized_img.crop(box)
        processed_images.append(split_img)
    assert len(processed_images) == blocks
    if use_thumbnail and len(processed_images) != 1:
        thumbnail_img = image.resize((image_size, image_size))
        processed_images.append(thumbnail_img)
    return processed_images

def load_image(image_file, input_size=448, max_num=12):
    image = Image.open(image_file).convert('RGB')
    transform = build_transform(input_size=input_size)
    images = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    pixel_values = [transform(image) for image in images]
    pixel_values = torch.stack(pixel_values)
    return pixel_values

model = AutoModel.from_pretrained(
    "5CD-AI/Vintern-1B-v3_5",
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
    use_flash_attn=False,
).eval().cuda()

tokenizer = AutoTokenizer.from_pretrained("5CD-AI/Vintern-1B-v3_5", trust_remote_code=True, use_fast=False)

# Xử lý tất cả ảnh trong thư mục images
text_file_md = ""
for i, image_path in enumerate(image_files):
    print(f"\n--- Đang xử lý ảnh {i+1}/{len(image_files)}: {os.path.basename(image_path)} ---")
    
    try:
        pixel_values = load_image(image_path, max_num=6).to(torch.bfloat16).cuda()
        generation_config = dict(max_new_tokens=1024, do_sample=False, num_beams=3, repetition_penalty=2.5)
        
        question = '<image>\nTrích xuất tất cả thông tin trong ảnh và trả về dạng markdown. Tuyệt đối không được bỏ qua bất kỳ thông tin nào trong ảnh, gồm bảng, ảnh, chú thích. Bố cục trình bày theo ảnh và trả về dạng markdown!'
        
        response, history = model.chat(tokenizer, pixel_values, question, generation_config, history=None, return_history=True)
        
        print(f'User: {question}')
        print(f'Assistant: {response}')
        print("-" * 40)

        # Lưu kết quả vào file markdown
        text_file_md += f"{response}\n\n"
        
    except Exception as e:
        print(f"Lỗi khi xử lý ảnh {image_path}: {str(e)}")
        continue

print("\nHoàn thành xử lý tất cả ảnh!")
# Lưu kết quả vào file markdown
with open("tu_tuong_hcm.md", "w", encoding="utf-8") as f:
    f.write(text_file_md)
print("Kết quả đã được lưu vào file output.md")
# End of recent edits
