# utils.py
from pathlib import Path
from PIL import Image
import os

# List of supported image extensions
SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".tga", ".ico"}

def is_supported_image_format(file_path: Path) -> bool:
    """Checks if a file has a supported image extension.""" # Translated comment
    return file_path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS

def get_image_files_in_folder(folder_path: Path) -> list[Path]:
    """
    Recursively finds all supported image files in a folder.
    """ # Translated comment
    image_files = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            file_path = Path(root) / file
            if is_supported_image_format(file_path):
                image_files.append(file_path)
    return image_files

def generate_unique_filename(original_filepath: Path) -> Path:
    """
    Generates a unique filename by appending a number if the file already exists.
    e.g., image.jpg -> image_1.jpg -> image_2.jpg
    """ # Translated comment
    base_name = original_filepath.stem
    extension = original_filepath.suffix
    directory = original_filepath.parent

    counter = 1
    new_filepath = original_filepath
    while new_filepath.exists():
        new_filepath = directory / f"{base_name}_{counter}{extension}"
        counter += 1
    return new_filepath