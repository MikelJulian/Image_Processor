import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import threading
from pathlib import Path
import zipfile
import shutil
from PIL import ImageTk, Image
import json

# Assuming image_processing_logic and utils are available and correctly implement their functions
from image_processing_logic import process_image_file, get_image_thumbnail
from utils import get_image_files_in_folder, is_supported_image_format, generate_unique_filename

class ImageProcessorApp:
    """
    Main application class that handles the user interface
    and orchestration of image processing.
    """
    def __init__(self, master):
        self.master = master
        self.master.title("Image Processor")
        self.master.geometry("1000x750")

        # All-Blue Pastel Colors
        self.pastel_bg_main = "#E3F2FD"  # Very light blue for overall background (similar to #E0F2F7 but slightly different)
        self.pastel_frame_bg = "#BBDEFB" # Light blue for frames (similar to #E8F5E9 but more distinctly blue)
        self.pastel_accent_btn = "#90CAF9" # Pastel blue for accent button (similar to #A7D9FF)
        self.pastel_dark_blue_text = "#1976D2" # A slightly darker blue for important text/borders
        self.text_color = "#333333"      # Dark gray for general text

        self.master.configure(bg=self.pastel_bg_main) # Set root window background
        
        # Style for the accent button and general ttk widgets
        self.master.style = ttk.Style()
        self.master.style.theme_use('clam') # 'clam' theme provides a good base for customization
        
        # General Button Style (for Add Folder/Files/Load ZIP/Clear All/X buttons)
        self.master.style.configure("TButton",
                                    foreground=self.text_color,
                                    background=self.pastel_frame_bg,
                                    font=("Arial", 10, "bold"),
                                    relief="flat",
                                    borderwidth=1,
                                    bordercolor=self.pastel_accent_btn)
        self.master.style.map("TButton",
                              background=[("active", self.pastel_accent_btn)],
                              foreground=[("active", self.text_color)])

        # Accent Button Style (for Start Processing)
        self.master.style.configure("Accent.TButton",
                                    foreground="white", # White text for better contrast on accent
                                    background=self.pastel_dark_blue_text, # Darker blue for accent
                                    font=("Arial", 10, "bold"),
                                    relief="flat")
        self.master.style.map("Accent.TButton",
                              background=[("active", self.pastel_accent_btn)], # Lighter blue on hover
                              foreground=[("active", self.text_color)]) # Darker text on hover

        # Configure general frame and labelframe backgrounds
        self.master.style.configure("TFrame", background=self.pastel_bg_main) # Default frame is main bg
        self.master.style.configure("TLabelframe", background=self.pastel_frame_bg, bordercolor=self.pastel_accent_btn, relief="solid")
        self.master.style.configure("TLabelframe.Label", background=self.pastel_frame_bg, foreground=self.text_color)
        
        # Labels and Radiobuttons
        self.master.style.configure("TLabel", background=self.pastel_frame_bg, foreground=self.text_color)
        # Specific labels for input buttons frame might need adjustment if parent is different
        self.master.style.configure("TRadiobutton", background=self.pastel_frame_bg, foreground=self.text_color)
        self.master.style.map("TRadiobutton",
                              background=[("active", self.pastel_accent_btn)],
                              foreground=[("active", self.text_color)]) # Text changes on hover

        # Entry (text input) fields
        self.master.style.configure("TEntry", fieldbackground="white", foreground=self.text_color, borderwidth=1, relief="solid", bordercolor=self.pastel_accent_btn)
        
        # Slider
        self.master.style.configure("Horizontal.TScale",
                                    background=self.pastel_frame_bg,
                                    troughcolor=self.pastel_bg_main,
                                    sliderrelief="flat",
                                    sliderthickness=20,
                                    borderwidth=0)
        self.master.style.map("Horizontal.TScale",
                              background=[("active", self.pastel_accent_btn)])

        # Progressbar
        self.master.style.configure("TProgressbar",
                                    background=self.pastel_accent_btn, # Color of the progress bar itself
                                    troughcolor=self.pastel_bg_main, # Color of the track
                                    bordercolor=self.pastel_accent_btn,
                                    lightcolor=self.pastel_accent_btn,
                                    darkcolor=self.pastel_accent_btn,
                                    thickness=15)

        # Custom style for the image item frames to allow background configuration
        self.master.style.configure("ImageItem.TFrame", background=self.pastel_frame_bg)

        # --- Store icon_image as an instance attribute ---
        # This prevents the PhotoImage from being garbage collected
        self.icon_image = None
        icon_path = Path(r"C:\Users\Mikel Julian Villena\Desktop\image_processor_app\Image_Processor\Icono.png")
        try:
            if icon_path.exists():
                self.icon_image = tk.PhotoImage(file=icon_path)
                self.master.iconphoto(True, self.icon_image)
            else:
                print(f"Advertencia: No se encontró el archivo de icono en {icon_path}. La aplicación se ejecutará sin icono persistente.")
        except Exception as e:
            print(f"Error al establecer el icono: {e}")
        # --------------------------------------------------

        self.temp_extract_dir = Path.cwd() / ".temp_extracted_images"

        self.image_paths = []
        self.image_thumbnails = {}
        # Increase thumbnail size to give more space for names
        self.thumbnail_display_size = (150, 112) # Width, Height - Adjust if necessary

        self.output_folder = Path.home() / "ProcessedImages"
        self.config_file = Path.home() / ".image_processor_config.json"
        self._load_config()

        # Create main_frame as the parent for all major UI sections
        self.main_frame = ttk.Frame(self.master, padding=(10, 10))
        self.main_frame.pack(fill="both", expand=True) # Ensure main_frame expands
        # Explicitly set background for main_frame
        self.main_frame.configure(style="TFrame") # Make sure it uses the "TFrame" style

        self._create_widgets()
        self._setup_layout()
        self._bind_events()
        self._update_file_count()
        
        os.makedirs(self.temp_extract_dir, exist_ok=True)
        self._toggle_quality_slider()

        # Bind the resize event of the canvas to recalculate and redraw thumbnails
        self.files_canvas.bind("<Configure>", self._on_canvas_resize)
        # Bind mouse wheel for scrolling on the canvas itself
        self.files_canvas.bind("<MouseWheel>", self._on_mousewheel) # For Windows/macOS
        # For Linux, button 4 and 5 are scroll up/down
        self.files_canvas.bind("<Button-4>", self._on_mousewheel)
        self.files_canvas.bind("<Button-5>", self._on_mousewheel)


    def _load_config(self):
        """Loads user configuration from a JSON file."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    if 'output_folder' in config and Path(config['output_folder']).is_dir():
                        self.output_folder = Path(config['output_folder'])
                    if 'target_size' in config:
                        self.initial_target_size = str(config['target_size'])
                    else:
                        self.initial_target_size = "2048"
                    if 'output_format' in config:
                        self.initial_output_format = config['output_format']
                    else:
                        self.initial_output_format = "JPG"
                    if 'quality' in config:
                        self.initial_quality = config['quality']
                    else:
                        self.initial_quality = 90
                    if 'resize_mode' in config:
                        self.initial_resize_mode = config['resize_mode']
                    else:
                        self.initial_resize_mode = "fit"
                    if 'prefix' in config:
                        self.initial_prefix = config['prefix']
                    else:
                        self.initial_prefix = ""
                    if 'suffix' in config:
                        self.initial_suffix = ""
                    else:
                        self.initial_suffix = ""
                    if 'overwrite_mode' in config:
                        self.initial_overwrite_mode = config['overwrite_mode']
                    else:
                        self.initial_overwrite_mode = "ask"

            except json.JSONDecodeError:
                print("Error reading config file. Using default values.")
                self._set_default_initial_config()
            except Exception as e:
                print(f"Unexpected error loading config: {e}")
                self._set_default_initial_config()
        else:
            self._set_default_initial_config()

    def _set_default_initial_config(self):
        """Sets default initial configuration values."""
        self.initial_target_size = "2048"
        self.initial_output_format = "JPG"
        self.initial_quality = 90
        self.initial_resize_mode = "fit"
        self.initial_prefix = ""
        self.initial_suffix = ""
        self.initial_overwrite_mode = "ask"

    def _save_config(self):
        """Saves the current user configuration to a JSON file."""
        config = {
            'output_folder': str(self.output_folder),
            'target_size': int(self.size_entry.get()) if self.size_entry.get().isdigit() else 2048,
            'output_format': self.output_format_var.get(),
            'quality': int(self.quality_slider.get()),
            'resize_mode': self.resize_mode_var.get(),
            'prefix': self.prefix_entry.get(),
            'suffix': self.suffix_entry.get(),
            'overwrite_mode': self.overwrite_var.get(),
        }
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=4)
        except Exception as e:
            print(f"Error saving configuration: {e}")

    def on_closing(self):
        """Handles window closing event to clean up temporary files."""
        self._save_config()
        self._cleanup_temp_dir()
        self.master.destroy()

    def _cleanup_temp_dir(self):
        """Deletes the temporary ZIP extraction directory."""
        if self.temp_extract_dir.exists():
            try:
                shutil.rmtree(self.temp_extract_dir)
                print(f"Temporary directory '{self.temp_extract_dir}' deleted.")
            except Exception as e:
                print(f"Error deleting temporary directory '{self.temp_extract_dir}': {e}")

    def _create_widgets(self):
        """Creates all user interface widgets."""
        # --- Input Area ---
        # Changed parent from self.master to self.main_frame
        self.input_frame = ttk.Frame(self.main_frame, padding=(10, 10))
        self.btn_select_folder = ttk.Button(self.input_frame, text="Add Folder", command=self._select_folder)
        self.btn_select_files = ttk.Button(self.input_frame, text="Add Files", command=self._select_files)
        self.btn_load_zip = ttk.Button(self.input_frame, text="Load ZIP", command=self._load_zip)
        
        # --- Loaded Files List with Thumbnails ---
        # Changed parent from self.master to self.main_frame
        self.files_frame = ttk.LabelFrame(self.main_frame, text="Loaded Images & Preview", padding=(10, 5))
        # Set canvas background directly for tk.Canvas
        self.files_canvas = tk.Canvas(self.files_frame, bg=self.pastel_bg_main, borderwidth=1, relief="sunken")
        self.files_scrollbar_y = ttk.Scrollbar(self.files_frame, orient="vertical", command=self.files_canvas.yview)
        self.files_canvas.configure(yscrollcommand=self.files_scrollbar_y.set)
        
        self.files_inner_frame = ttk.Frame(self.files_canvas)
        self.canvas_window_id = self.files_canvas.create_window((0, 0), window=self.files_inner_frame, anchor="nw")

        self.files_inner_frame.bind("<Configure>", self._on_inner_frame_configure)

        self.btn_clear_all_images = ttk.Button(self.files_frame, text="Clear All", command=self._clear_loaded_images)
        # Ensure label background is set
        self.file_count_label = ttk.Label(self.files_frame, text="0 files selected", font=("Arial", 9, "bold"), background=self.pastel_frame_bg)

        # --- Processing Configuration ---
        # Changed parent from self.master to self.main_frame
        self.config_frame = ttk.LabelFrame(self.main_frame, text="Processing Configuration", padding=(10, 10))
        
        # Size
        self.size_label = ttk.Label(self.config_frame, text="Target Size (px, longest side):")
        self.size_entry = ttk.Entry(self.config_frame)
        self.size_entry.insert(0, self.initial_target_size)

        self.preset_1k_btn = ttk.Button(self.config_frame, text="1024 px", command=lambda: self.size_entry.delete(0, tk.END) or self.size_entry.insert(0, "1024"))
        self.preset_2k_btn = ttk.Button(self.config_frame, text="2048 px", command=lambda: self.size_entry.delete(0, tk.END) or self.size_entry.insert(0, "2048"))
        self.preset_4k_btn = ttk.Button(self.config_frame, text="4096 px", command=lambda: self.size_entry.delete(0, tk.END) or self.size_entry.insert(0, "4096"))

        # Resize Modes
        self.resize_mode_label = ttk.Label(self.config_frame, text="Resize Mode:")
        self.resize_mode_var = tk.StringVar(value=self.initial_resize_mode)
        self.radio_fit = ttk.Radiobutton(self.config_frame, text="Fit (Maintain Aspect)", variable=self.resize_mode_var, value="fit")
        self.radio_crop = ttk.Radiobutton(self.config_frame, text="Crop (Fill, Clip)", variable=self.resize_mode_var, value="crop")
        self.radio_stretch = ttk.Radiobutton(self.config_frame, text="Stretch (Distort)", variable=self.resize_mode_var, value="stretch")
        
        # Output Format and Quality
        self.output_format_label = ttk.Label(self.config_frame, text="Output Format:")
        self.output_format_var = tk.StringVar(value=self.initial_output_format)
        self.radio_jpg = ttk.Radiobutton(self.config_frame, text="JPG", variable=self.output_format_var, value="JPG", command=self._toggle_quality_slider)
        self.radio_png = ttk.Radiobutton(self.config_frame, text="PNG", variable=self.output_format_var, value="PNG", command=self._toggle_quality_slider)
        self.radio_tga = ttk.Radiobutton(self.config_frame, text="TGA", variable=self.output_format_var, value="TGA", command=self._toggle_quality_slider)

        self.quality_label = ttk.Label(self.config_frame, text="JPG Quality (1-100):")
        self.quality_value_label = ttk.Label(self.config_frame, text=str(self.initial_quality))
        self.quality_slider = ttk.Scale(self.config_frame, from_=1, to=100, orient="horizontal", command=self._update_quality_label_value)
        self.quality_slider.set(self.initial_quality)
        
        # Advanced Naming
        self.naming_frame = ttk.LabelFrame(self.config_frame, text="Output Naming", padding=(5,5))
        self.prefix_label = ttk.Label(self.naming_frame, text="Prefix:")
        self.prefix_entry = ttk.Entry(self.naming_frame)
        self.prefix_entry.insert(0, self.initial_prefix)
        self.suffix_label = ttk.Label(self.naming_frame, text="Suffix:")
        self.suffix_entry = ttk.Entry(self.naming_frame)
        self.suffix_entry.insert(0, self.initial_suffix)

        self.overwrite_var = tk.StringVar(value=self.initial_overwrite_mode)
        self.overwrite_label = ttk.Label(self.naming_frame, text="If file exists:")
        self.radio_overwrite_ask = ttk.Radiobutton(self.naming_frame, text="Ask", variable=self.overwrite_var, value="ask")
        self.radio_overwrite_overwrite = ttk.Radiobutton(self.naming_frame, text="Overwrite", variable=self.overwrite_var, value="overwrite")
        self.radio_overwrite_unique = ttk.Radiobutton(self.naming_frame, text="Create Unique Name", variable=self.overwrite_var, value="unique")

        # Output Folder
        self.output_folder_frame = ttk.Frame(self.config_frame, padding=(5,5))
        self.btn_select_output = ttk.Button(self.output_folder_frame, text="Choose Output Folder", command=self._select_output_folder)
        # Ensure label background is set
        self.output_folder_label = ttk.Label(self.output_folder_frame, text=f"Output: {self.output_folder.name}", wraplength=250, font=("Arial", 9), background=self.pastel_frame_bg)

        # --- Processing Controls ---
        # Changed parent from self.master to self.main_frame
        self.controls_frame = ttk.Frame(self.main_frame, padding=(10, 5))
        self.process_button = ttk.Button(self.controls_frame, text="Start Processing", command=self._start_processing, style="Accent.TButton")
        self.progress_bar = ttk.Progressbar(self.controls_frame, orient="horizontal", mode="determinate")
        # Ensure label background is set
        self.status_label = ttk.Label(self.controls_frame, text="Ready.", font=("Arial", 10, "italic"), background=self.pastel_bg_main)

    def _setup_layout(self):
        """Organizes widgets in the window using pack and grid."""
        # Main layout uses grid for sections within self.main_frame
        self.main_frame.grid_rowconfigure(0, weight=0) # Input frame
        self.main_frame.grid_rowconfigure(1, weight=5) # Files frame (Increased weight from 3 to 5 for more expansion)
        self.main_frame.grid_rowconfigure(2, weight=0) # Config frame
        self.main_frame.grid_rowconfigure(3, weight=0) # Controls frame
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Input Frame
        self.input_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
        self.input_frame.grid_columnconfigure(0, weight=1)
        self.input_frame.grid_columnconfigure(1, weight=1)
        self.input_frame.grid_columnconfigure(2, weight=1)
        self.btn_select_folder.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        self.btn_select_files.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.btn_load_zip.grid(row=0, column=2, padx=5, pady=5, sticky="ew")

        # Files Frame (Left side of a conceptual split, but currently full width)
        self.files_frame.grid(row=1, column=0, padx=10, pady=5, sticky="nsew")
        self.files_frame.grid_rowconfigure(1, weight=1) # Canvas should expand
        self.files_frame.grid_columnconfigure(0, weight=1) # Canvas should expand

        self.btn_clear_all_images.grid(row=0, column=0, padx=5, pady=5, sticky="ne") # Top right
        self.file_count_label.grid(row=0, column=0, padx=5, pady=5, sticky="nw") # Top left

        self.files_canvas.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")
        self.files_scrollbar_y.grid(row=1, column=1, sticky="ns")


        # Configuration Frame
        self.config_frame.grid(row=2, column=0, padx=10, pady=5, sticky="ew")
        # Configure columns for better distribution
        self.config_frame.grid_columnconfigure(0, weight=0) # Labels
        self.config_frame.grid_columnconfigure(1, weight=1) # Entries/Radios
        self.config_frame.grid_columnconfigure(2, weight=1)
        self.config_frame.grid_columnconfigure(3, weight=1)
        self.config_frame.grid_columnconfigure(4, weight=0) # Quality Label
        self.config_frame.grid_columnconfigure(5, weight=2) # Quality Slider
        self.config_frame.grid_columnconfigure(6, weight=0) # Quality Value

        # Size row
        self.size_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.size_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.preset_1k_btn.grid(row=0, column=2, padx=2, pady=5, sticky="ew")
        self.preset_2k_btn.grid(row=0, column=3, padx=2, pady=5, sticky="ew")
        self.preset_4k_btn.grid(row=0, column=4, padx=2, pady=5, sticky="ew")

        # Resize Modes row
        self.resize_mode_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.radio_fit.grid(row=1, column=1, columnspan=2, padx=5, pady=2, sticky="w")
        self.radio_crop.grid(row=1, column=3, columnspan=2, padx=5, pady=2, sticky="w")
        self.radio_stretch.grid(row=1, column=5, columnspan=2, padx=5, pady=2, sticky="w")
        
        # Output Format and Quality row
        self.output_format_label.grid(row=2, column=0, padx=5, pady=5, sticky="w")
        self.radio_jpg.grid(row=2, column=1, padx=5, pady=5, sticky="w")
        self.radio_png.grid(row=2, column=2, padx=5, pady=5, sticky="w")
        self.radio_tga.grid(row=2, column=3, padx=5, pady=5, sticky="w")
        self.quality_label.grid(row=2, column=4, padx=5, pady=5, sticky="w")
        self.quality_slider.grid(row=2, column=5, padx=5, pady=5, sticky="ew")
        self.quality_value_label.grid(row=2, column=6, padx=5, pady=5, sticky="w")
        
        # Naming Frame
        self.naming_frame.grid(row=3, column=0, columnspan=7, padx=5, pady=10, sticky="ew")
        self.naming_frame.grid_columnconfigure(1, weight=1)
        self.naming_frame.grid_columnconfigure(3, weight=1)

        self.prefix_label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.prefix_entry.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        self.suffix_label.grid(row=0, column=2, padx=5, pady=5, sticky="w")
        self.suffix_entry.grid(row=0, column=3, padx=5, pady=5, sticky="ew")

        self.overwrite_label.grid(row=1, column=0, padx=5, pady=5, sticky="w")
        self.radio_overwrite_ask.grid(row=1, column=1, padx=5, pady=5, sticky="w")
        self.radio_overwrite_overwrite.grid(row=1, column=2, padx=5, pady=5, sticky="w")
        self.radio_overwrite_unique.grid(row=1, column=3, padx=5, pady=5, sticky="w")

        self.output_folder_frame.grid(row=4, column=0, columnspan=7, padx=5, pady=5, sticky="ew")
        self.output_folder_frame.grid_columnconfigure(1, weight=1) # Label should expand
        self.btn_select_output.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        self.output_folder_label.grid(row=0, column=1, padx=5, pady=5, sticky="ew")


        self.controls_frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=1) # Allow button/progress to center/fill
        self.process_button.pack(pady=5) # Using pack here for simplicity of single item
        self.progress_bar.pack(fill="x", pady=5)
        self.status_label.pack(side="left", anchor="w", pady=5) # Align status to left

    def _bind_events(self):
        """Configures additional UI events."""
        pass

    def _on_mousewheel(self, event):
        """Handles mouse wheel scrolling for the canvas."""
        if event.delta: # Windows/macOS
            self.files_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
        elif event.num == 4: # Linux scroll up
            self.files_canvas.yview_scroll(-1, "units")
        elif event.num == 5: # Linux scroll down
            self.files_canvas.yview_scroll(1, "units")

    def _add_image_path(self, path):
        """Adds a single image path to the list and updates the UI with thumbnail."""
        if path not in self.image_paths:
            self.image_paths.append(path)
            self._update_file_list_with_thumbnails()
            self._update_file_count()

    def _add_images_from_path(self, folder_path):
        """Adds all supported images from a folder."""
        found_images = get_image_files_in_folder(folder_path)
        if not found_images:
            messagebox.showinfo("Information", f"No supported images found in '{folder_path}'.")
            return
        
        for img_path in found_images:
            if img_path not in self.image_paths:
                self.image_paths.append(img_path)
        
        self._update_file_list_with_thumbnails()
        self._update_file_count()

    def _update_file_list_with_thumbnails(self):
        """Updates the list of loaded files with thumbnails in a grid layout."""
        for widget in self.files_inner_frame.winfo_children():
            widget.destroy()
        self.image_thumbnails.clear() # Clear references to allow garbage collection

        self.files_canvas.update_idletasks() # Ensure canvas has rendered to get correct width
        canvas_width = self.files_canvas.winfo_width()
        if canvas_width == 0:
            canvas_width = self.files_canvas.winfo_reqwidth() or 600
        
        thumbnail_area_width = self.thumbnail_display_size[0]
        padding = 10 # Padding around each item frame
        
        item_total_width = thumbnail_area_width + (padding * 2) + 20 # 20 for some extra buffer

        num_columns = max(1, int(canvas_width / item_total_width))
        
        for i in range(num_columns):
            self.files_inner_frame.grid_columnconfigure(i, weight=1)

        row, col = 0, 0
        for i, path in enumerate(self.image_paths):
            item_frame = ttk.Frame(self.files_inner_frame, relief="ridge", borderwidth=1, style="ImageItem.TFrame")
            item_frame.grid(row=row, column=col, padx=padding, pady=padding, sticky="nsew")
            
            try:
                thumbnail_pil = get_image_thumbnail(path, self.thumbnail_display_size)
                thumbnail_tk = ImageTk.PhotoImage(thumbnail_pil)
                self.image_thumbnails[path] = thumbnail_tk # Keep strong reference

                img_label = ttk.Label(item_frame, image=thumbnail_tk)
                img_label.pack(side="top", pady=(5,0)) # Padding at top only for image
            except Exception as e:
                print(f"Could not generate thumbnail for {path.name}: {e}")
                error_label = ttk.Label(item_frame, text="[Thumbnail Error]",
                                        width=int(self.thumbnail_display_size[0] / 8), # Approx char width
                                        anchor="center", background=self.pastel_frame_bg) # Set background
                error_label.pack(side="top", pady=(5,0), fill="x", expand=True)

            file_name_label = ttk.Label(item_frame, text=path.name,
                                        wraplength=self.thumbnail_display_size[0] + 10, # Give a bit more space than image width
                                        justify="center", # Center text if wrapped
                                        anchor="n", background=self.pastel_frame_bg) # Set background
            file_name_label.pack(side="top", fill="x", expand=True, padx=2, pady=2)

            remove_button = ttk.Button(item_frame, text="X", command=lambda p=path: self._remove_image_from_list(p), width=3)
            remove_button.pack(side="bottom", pady=2)

            col += 1
            if col >= num_columns:
                col = 0
                row += 1
        
        self.files_inner_frame.update_idletasks() 
        self.files_canvas.config(scrollregion=self.files_canvas.bbox("all"))


    def _on_canvas_resize(self, event=None):
        """Called when the canvas is resized to re-render thumbnails."""
        self.files_canvas.itemconfig(self.canvas_window_id, width=event.width)
        self._update_file_list_with_thumbnails()

    def _on_inner_frame_configure(self, event=None):
        """Called when the inner frame changes size (e.g., content added/removed)."""
        self.files_canvas.configure(scrollregion=self.files_canvas.bbox("all"))


    def _remove_image_from_list(self, path_to_remove: Path):
        """Removes a file from the list and its thumbnail."""
        if path_to_remove in self.image_paths:
            self.image_paths.remove(path_to_remove)
            if path_to_remove in self.image_thumbnails:
                del self.image_thumbnails[path_to_remove]
            self._update_file_list_with_thumbnails()
            self._update_file_count()

    def _update_file_count(self):
        """Updates the label with the number of selected files."""
        self.file_count_label.config(text=f"{len(self.image_paths)} images loaded")

    def _select_folder(self):
        """Opens a dialog to select a folder and loads its images."""
        initial_dir_str = str(self.output_folder.parent) if self.output_folder.parent.exists() else str(Path.home())
        folder_selected = filedialog.askdirectory(initialdir=initial_dir_str)
        if folder_selected:
            self._add_images_from_path(Path(folder_selected))
            self.status_label.config(text=f"Added images from '{Path(folder_selected).name}'.")
            if not self.image_paths: # Check if any images were actually added
                self.status_label.config(text="No supported images found in the selected folder.", foreground="orange")


    def _select_files(self):
        """Opens a dialog to select multiple image files."""
        initial_dir_str = str(self.output_folder.parent) if self.output_folder.parent.exists() else str(Path.home())
        file_paths = filedialog.askopenfilenames(
            filetypes=[("Supported Images", "*.jpg *.jpeg *.png *.gif *.bmp *.tiff *.tga *.ico"),
                       ("All Files", "*.*")],
            initialdir=initial_dir_str
        )
        if file_paths:
            added_count = 0
            for f_path in file_paths:
                path_obj = Path(f_path)
                if is_supported_image_format(path_obj):
                    if path_obj not in self.image_paths: # Prevent duplicates if adding files multiple times
                        self._add_image_path(path_obj)
                        added_count += 1
                else:
                    self.status_label.config(text=f"Ignoring unsupported file: {path_obj.name}", foreground="orange")
            self.status_label.config(text=f"Added {added_count} new images. Total: {len(self.image_paths)}.")
            if not self.image_paths:
                self.status_label.config(text="No valid images selected.", foreground="orange")


    def _load_zip(self):
        """Opens a dialog to load a ZIP file and extracts its images."""
        initial_dir_str = str(self.output_folder.parent) if self.output_folder.parent.exists() else str(Path.home())
        zip_path = filedialog.askopenfilename(
            filetypes=[("ZIP Files", "*.zip"), ("All Files", "*.*")],
            initialdir=initial_dir_str
        )
        if zip_path:
            self._clear_loaded_images() 
            self._load_zip_from_path(Path(zip_path))

    def _load_zip_from_path(self, zip_file_path):
        """Extracts images from a ZIP file and adds them to the list."""
        self._cleanup_temp_dir() 
        self._clear_loaded_images() 

        self.loaded_zip_path = zip_file_path
        zip_extract_dir = self.temp_extract_dir / zip_file_path.stem

        os.makedirs(zip_extract_dir, exist_ok=True)
        
        try:
            with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
                extract_count = 0
                for member_name in zip_ref.namelist():
                    member_path = Path(member_name)
                    if is_supported_image_format(member_path) and not member_path.is_dir():
                        try:
                            extracted_file_path = zip_extract_dir / member_path.name
                            with open(extracted_file_path, "wb") as outfile:
                                outfile.write(zip_ref.read(member_name))
                            self._add_image_path(extracted_file_path) 
                            extract_count += 1
                        except Exception as e:
                            print(f"Error extracting '{member_name}' from ZIP: {e}")
                            self.status_label.config(text=f"Error extracting: {member_name}", foreground="red")
            
            self.status_label.config(text=f"Images extracted from '{zip_file_path.name}'. Found: {extract_count}")
            if not self.image_paths:
                messagebox.showinfo("Information", f"No valid images found inside ZIP '{zip_file_path.name}'.")

        except zipfile.BadZipFile:
            messagebox.showerror("ZIP Error", "The ZIP file is invalid or corrupted.")
            self.status_label.config(text="Error: Invalid ZIP file.", foreground="red")
            self._clear_loaded_images()
        except Exception as e:
            messagebox.showerror("ZIP Extraction Error", f"An error occurred while extracting the ZIP: {e}")
            self.status_label.config(text=f"Error extracting ZIP: {e}", foreground="red")
            self._clear_loaded_images()
        finally:
            if not self.image_paths and zip_extract_dir.exists():
                try:
                    shutil.rmtree(zip_extract_dir)
                except Exception as e:
                    print(f"Could not clean up empty temporary directory {zip_extract_dir}: {e}")


    def _clear_loaded_images(self):
        """Clears the list of loaded images and their thumbnails."""
        self.image_paths = []
        self.image_thumbnails.clear()
        for widget in self.files_inner_frame.winfo_children():
            widget.destroy()
        self._update_file_count()
        self.files_canvas.config(scrollregion=(0,0,0,0)) # Reset scroll region
        self._cleanup_temp_dir() # Also clean up temp extraction dir when clearing all

    def _select_output_folder(self):
        """Opens a dialog to select the output folder."""
        # Convert self.output_folder to string for initialdir
        folder_selected = filedialog.askdirectory(initialdir=str(self.output_folder))
        if folder_selected:
            self.output_folder = Path(folder_selected)
            self.output_folder_label.config(text=f"Output: {self.output_folder.name}")
            self.status_label.config(text=f"Output folder set to: '{self.output_folder.name}'.", foreground="black")

    def _toggle_quality_slider(self):
        """Enables/disables the quality slider based on the output format."""
        if hasattr(self, 'quality_label') and hasattr(self, 'quality_slider') and hasattr(self, 'quality_value_label'):
            if self.output_format_var.get() == "JPG":
                self.quality_label.config(state=tk.NORMAL)
                self.quality_slider.config(state=tk.NORMAL)
                self.quality_value_label.config(state=tk.NORMAL)
            else:
                self.quality_label.config(state=tk.DISABLED)
                self.quality_slider.config(state=tk.DISABLED)
                self.quality_value_label.config(state=tk.DISABLED)

    def _update_quality_label_value(self, value):
        """Updates the quality slider value label."""
        if hasattr(self, 'quality_value_label'):
            self.quality_value_label.config(text=f"{int(float(value))}")

    def _start_processing(self):
        """Starts image processing in a separate thread."""
        if not self.image_paths:
            messagebox.showwarning("Warning", "No images to process. Please add images first.")
            return

        try:
            target_size = int(self.size_entry.get())
            if target_size <= 0:
                raise ValueError("Target size must be a positive number.")
        except ValueError:
            messagebox.showerror("Input Error", "Please enter a valid numeric target size (e.g., 2048).")
            return

        resize_mode = self.resize_mode_var.get()
        output_format = self.output_format_var.get()
        quality = int(self.quality_slider.get()) if output_format == "JPG" else 0
        prefix = self.prefix_entry.get()
        suffix = self.suffix_entry.get()
        overwrite_mode = self.overwrite_var.get()

        if not self.output_folder.exists():
            try:
                os.makedirs(self.output_folder)
            except OSError as e:
                messagebox.showerror("Output Folder Error", f"Could not create output folder: {e}")
                return

        self.process_button.config(state=tk.DISABLED)
        self.btn_select_folder.config(state=tk.DISABLED)
        self.btn_select_files.config(state=tk.DISABLED)
        self.btn_load_zip.config(state=tk.DISABLED)
        self.btn_clear_all_images.config(state=tk.DISABLED) 
        self._toggle_config_widgets_state(tk.DISABLED)

        self.progress_bar["value"] = 0
        self.status_label.config(text="Processing images...", foreground="blue")

        processing_thread = threading.Thread(
            target=self._process_images_thread,
            args=(self.image_paths.copy(), target_size, resize_mode, output_format,
                  quality, prefix, suffix, overwrite_mode, self.output_folder)
        )
        processing_thread.start()

    def _toggle_config_widgets_state(self, state):
        """Enables or disables configuration widgets."""
        for frame in [self.config_frame, self.naming_frame, self.output_folder_frame]:
            for child in frame.winfo_children():
                if isinstance(child, (ttk.Entry, ttk.Button, ttk.Radiobutton, ttk.Scale, ttk.Label)):
                    child.config(state=state)
        self._toggle_quality_slider()

    def _process_images_thread(self, image_paths, target_size, resize_mode, output_format,
                                 quality, prefix, suffix, overwrite_mode, output_folder):
        """
        Worker thread function to process images.
        Updates UI elements on the main thread via after().
        """
        processed_count = 0
        total_images = len(image_paths)
        errors_occurred = False
        user_cancelled = False

        for i, input_path in enumerate(image_paths):
            if user_cancelled:
                break
            try:
                self.master.after(0, self.status_label.config,
                                  {"text": f"Processing: {input_path.name} ({i+1}/{total_images})", "foreground": "blue"})
                
                output_filename = input_path.stem
                if prefix:
                    output_filename = prefix + output_filename
                if suffix:
                    output_filename = output_filename + suffix
                
                output_filepath_base = output_folder / f"{output_filename}.{output_format.lower()}"
                output_filepath = output_filepath_base

                if output_filepath_base.exists():
                    if overwrite_mode == "ask":
                        response_container = [None] 
                        response_var = tk.BooleanVar(value=False)
                        
                        def show_dialog_and_set_response():
                            nonlocal user_cancelled 
                            response = messagebox.askyesnocancel(
                                "File Exists",
                                f"The file '{output_filepath_base.name}' already exists.\n\nOverwrite it?",
                                icon="question"
                            )
                            if response is True:
                                response_var.set(True)
                            elif response is False:
                                response_var.set(False)
                            else: 
                                user_cancelled = True 
                                response_var.set(False) 

                        self.master.after(0, show_dialog_and_set_response)
                        self.master.wait_variable(response_var) 
                        
                        if user_cancelled: 
                            self.master.after(0, self.status_label.config, {"text": "Processing cancelled by user.", "foreground": "red"})
                            break 
                        elif not response_var.get(): 
                            self.master.after(0, self.status_label.config, {"text": f"Skipped: {input_path.name}", "foreground": "orange"})
                            continue 

                    elif overwrite_mode == "overwrite":
                        pass
                    elif overwrite_mode == "unique":
                        output_filepath = generate_unique_filename(output_filepath_base)
                
                if not user_cancelled: 
                    process_image_file(input_path, output_filepath, target_size, resize_mode, output_format, quality)
                    processed_count += 1
            except Exception as e:
                errors_occurred = True
                print(f"Error processing {input_path.name}: {e}")
                self.master.after(0, self.status_label.config,
                                  {"text": f"Error with {input_path.name}: {e}", "foreground": "red"})
            
            progress_value = int((i + 1) / total_images * 100)
            self.master.after(0, self.progress_bar.config, {"value": progress_value})

        final_status_text = ""
        if user_cancelled:
            final_status_text = f"Processing cancelled. Processed {processed_count}/{total_images} images."
            final_foreground = "red"
        elif errors_occurred:
            final_status_text = f"Processing finished with errors. Processed {processed_count}/{total_images} images."
            final_foreground = "red"
        elif processed_count == total_images:
            final_status_text = f"Processing completed! Processed {processed_count} images."
            final_foreground = "green"
        else: 
            final_status_text = f"Processing interrupted. Processed {processed_count}/{total_images} images."
            final_foreground = "orange"


        self.master.after(0, self.status_label.config, {"text": final_status_text, "foreground": final_foreground})
        self.master.after(0, self.process_button.config, {"state": tk.NORMAL})
        self.master.after(0, self.btn_select_folder.config, {"state": tk.NORMAL})
        self.master.after(0, self.btn_select_files.config, {"state": tk.NORMAL})
        self.master.after(0, self.btn_load_zip.config, {"state": tk.NORMAL})
        self.master.after(0, self.btn_clear_all_images.config, {"state": tk.NORMAL}) 
        self.master.after(0, self._toggle_config_widgets_state, tk.NORMAL)
        if user_cancelled or errors_occurred:
             self.master.after(0, self.progress_bar.config, {"value": processed_count / total_images * 100})
        else:
            self.master.after(0, self.progress_bar.config, {"value": 100})


if __name__ == "__main__":
    root = tk.Tk()
    
    app = ImageProcessorApp(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()