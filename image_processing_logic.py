# image_processing_logic.py
from PIL import Image

# Translated function names
def process_image_file(input_path, output_path, target_size, resize_mode, output_format, quality):
    """
    Processes a single image file (resize, convert format, apply quality).
    """
    img = Image.open(input_path)
    img = img.convert("RGB") # Ensure consistent mode for resizing and saving

    original_width, original_height = img.size

    if resize_mode == "fit":
        if original_width > original_height:
            new_width = target_size
            new_height = int(original_height * (target_size / original_width))
        else:
            new_height = target_size
            new_width = int(original_width * (target_size / original_height))
        img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
    elif resize_mode == "crop":
        target_aspect = target_size / target_size # Assuming square for simplicity, adjust if target_size means width, height different
        image_aspect = original_width / original_height

        if image_aspect > target_aspect:
            new_height = target_size
            new_width = int(original_width * (target_size / original_height))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            left = (new_width - target_size) / 2
            top = 0
            right = (new_width + target_size) / 2
            bottom = target_size
            img = img.crop((left, top, right, bottom))
        else:
            new_width = target_size
            new_height = int(original_height * (target_size / original_width))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            # Crop
            left = 0
            top = (new_height - target_size) / 2
            right = target_size
            bottom = (new_height + target_size) / 2
            img = img.crop((left, top, right, bottom))
    elif resize_mode == "stretch":
        img = img.resize((target_size, target_size), Image.Resampling.LANCZOS)

    if output_format == "JPG":
        img.save(output_path, quality=quality, optimize=True)
    elif output_format == "PNG":
        img.save(output_path, compress_level=9) # PNG quality is compress_level (0-9)
    elif output_format == "TGA":
        img.save(output_path) # TGA usually doesn't have a 'quality' parameter in PIL

def get_image_thumbnail(image_path, size=(100, 100)):
    """
    Generates a thumbnail for a given image path.
    Returns a PIL Image object.
    """
    try:
        img = Image.open(image_path)
        img.thumbnail(size)
        return img
    except Exception as e:
        print(f"Error creating thumbnail for {image_path}: {e}")
        return Image.new("RGB", size, (200, 200, 200)) 