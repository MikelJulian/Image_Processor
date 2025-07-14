# Image Processor App

The Image Processor App is a user-friendly desktop application built with Python's Tkinter library, designed to simplify bulk image processing tasks. It allows users to easily resize, convert formats, and manage various output settings for multiple images or entire folders, including images within ZIP archives.

## Features

* **Batch Image Processing:** Process multiple images or entire folders at once.

* **ZIP Archive Support:** Load images directly from ZIP files, with automatic temporary extraction and cleanup.

* **Flexible Resizing Options:**

    * **Fit:** Resizes images to fit within a target size while maintaining aspect ratio.

    * **Crop:** Resizes and crops images to fill a target square, useful for creating uniform thumbnails or avatars.

    * **Stretch:** Stretches images to exact target dimensions, potentially distorting aspect ratio.

* **Output Format Conversion:** Convert images to JPG, PNG, or TGA formats.

* **JPG Quality Control:** Adjust the compression quality for JPG output.

* **Custom Naming:** Add custom prefixes and suffixes to processed image filenames.

* **Overwrite Management:** Choose how to handle existing files in the output directory:

    * Ask for confirmation.

    * Automatically overwrite.

    * Generate a unique filename.

* **Thumbnail Previews:** View thumbnails of loaded images within the application.

* **Persistent Configuration:** Saves your last used settings (output folder, target size, format, etc.) for convenience.

* **Clean User Interface:** An intuitive and aesthetically pleasing interface with a pastel blue theme.

## Installation

To run this application, you need Python 3 and the Pillow library.

1.  **Clone the repository (or download the files):**

    ```bash
    git clone [https://github.com/MikelJulian/Image_Processor.git](https://github.com/MikelJulian/Image_Processor.git)
    cd Image_Processor
    ```

2.  **Install dependencies:**

    ```bash
    pip install Pillow
    ```

## Usage

1.  **Run the application:**

    ```bash
    python image_processor_app.py
    ```

2.  **Add Images:**

    * Click "Add Folder" to select a directory containing images. The app will recursively find all supported image files.

    * Click "Add Files" to select individual image files.

    * Click "Load ZIP" to select a `.zip` archive. The app will extract supported images to a temporary directory.

3.  **Configure Processing:**

    * **Target Size:** Enter the desired size (in pixels) for the longest side of your output images. Use the preset buttons (1024 px, 2048 px, 4096 px) for quick selection.

    * **Resize Mode:** Choose how images should be resized:

        * `Fit (Maintain Aspect)`: The image will be scaled down (or up) so its longest side matches the target size, preserving the original aspect ratio.

        * `Crop (Fill, Clip)`: The image will be scaled to fill the target square, and any excess will be cropped.

        * `Stretch (Distort)`: The image will be stretched to exactly match the target dimensions, which may distort the original aspect ratio.

    * **Output Format:** Select the desired output format (JPG, PNG, or TGA).

    * **JPG Quality:** If JPG is selected, use the slider to set the output quality (1-100).

    * **Output Naming:**

        * `Prefix`: Text to add to the beginning of the output filename.

        * `Suffix`: Text to add to the end of the output filename.

    * **If file exists:**

        * `Ask`: The app will prompt you if an output file with the same name already exists.

        * `Overwrite`: The app will automatically replace existing files.

        * `Create Unique Name`: The app will append a number (e.g., `image_1.jpg`) to create a unique filename.

4.  **Choose Output Folder:**

    * Click "Choose Output Folder" to select where the processed images will be saved. By default, it saves to a "ProcessedImages" folder in your home directory.

5.  **Start Processing:**

    * Click the "Start Processing" button. The progress bar and status label will update as images are processed.

    * You can clear all loaded images at any time by clicking "Clear All".

## Project Structure

* `image_processor_app.py`: The main application file, handling the Tkinter UI, event handling, and orchestration of processing.

* `image_processing_logic.py`: Contains the core image manipulation functions (resizing, format conversion).

* `utils.py`: Provides utility functions like finding supported image files, checking formats, and generating unique filenames.

## Contributing

Feel free to fork the repository, open issues, or submit pull requests to improve the application.

## License

This project is open-source and available under the [GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html).
