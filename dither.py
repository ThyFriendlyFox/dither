import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk, ImageEnhance, ImageDraw
import numpy as np
import colorsys
import threading
import os
import math

class CollapsibleSection(ttk.Frame):
    def __init__(self, parent, title, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.show = tk.BooleanVar(value=True)
        self.header = ttk.Checkbutton(self, text=title, variable=self.show, command=self.toggle, style='Toolbutton')
        self.header.pack(fill=tk.X, pady=2)
        self.body = ttk.Frame(self)
        self.body.pack(fill=tk.X, expand=True)
    def toggle(self):
        if self.show.get():
            self.body.pack(fill=tk.X, expand=True)
        else:
            self.body.forget()

class DitherDockApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dither Dock")
        self.root.geometry("1400x900")
        self.root.configure(bg="#2b2b2b")
        self.image = None
        self.preview_image = None
        self.display_image = None
        self.processed_image = None
        self.image_path = None
        self.dither_algorithms = ["Floyd-Steinberg", "Ordered", "Atkinson"]
        self.dither_algorithm = tk.StringVar(value=self.dither_algorithms[0])
        self.dither_strength = tk.IntVar(value=128)
        self.brightness = tk.DoubleVar(value=1.0)
        self.contrast = tk.DoubleVar(value=1.0)
        self.black_clip = tk.IntVar(value=0)
        self.dot_size = tk.IntVar(value=4)
        self.shape_options = ["Circles", "Squares (aligned)", "Triangles (aligned)", "Squares (random)", "Triangles (random)"]
        self.shape = tk.StringVar(value=self.shape_options[0])
        self.zoom = tk.DoubleVar(value=1.0)
        self.color_mode = tk.StringVar(value="grayscale")
        self.hue = tk.DoubleVar(value=0.0)
        self.debounce_timer = None
        self.detail = tk.IntVar(value=8)
        self.setup_ui()

    def setup_ui(self):
        # Configure styles for a modern look
        style = ttk.Style()
        style.theme_use('clam')
        style.configure('Toolbutton', font=('Segoe UI', 10, 'bold'), background='#3c3c3c')
        style.configure('TFrame', background='#2b2b2b')
        style.configure('TLabel', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 9))
        style.configure('TButton', font=('Segoe UI', 9))
        style.configure('TCheckbutton', background='#2b2b2b', foreground='#ffffff', font=('Segoe UI', 9))
        
        # Main container with padding
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Top toolbar
        toolbar = ttk.Frame(main_container)
        toolbar.pack(fill=tk.X, pady=(0, 10))
        
        # File operations
        file_frame = ttk.LabelFrame(toolbar, text="File Operations", padding="8")
        file_frame.pack(side=tk.LEFT, padx=(0, 10))
        
        load_btn = ttk.Button(file_frame, text="📁 Load Image", command=self.load_image, width=15)
        load_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        save_btn = ttk.Button(file_frame, text="💾 Save Image", command=self.save_image, width=15)
        save_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        batch_btn = ttk.Button(file_frame, text="📂 Batch Process", command=self.apply_to_folder, width=15)
        batch_btn.pack(side=tk.LEFT)
        
        # Image info
        self.info_label = ttk.Label(toolbar, text="No image loaded", font=('Segoe UI', 9, 'italic'))
        self.info_label.pack(side=tk.RIGHT, padx=10)
        
        # Main content area
        content_frame = ttk.Frame(main_container)
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left panel - Controls
        left_panel = ttk.Frame(content_frame, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_panel.pack_propagate(False)
        
        # Right panel - Image display
        right_panel = ttk.Frame(content_frame)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Image canvas with border
        canvas_frame = ttk.LabelFrame(right_panel, text="Preview", padding="5")
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg="#1e1e1e", highlightthickness=0, relief=tk.FLAT)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Create scrollable control panel
        control_canvas = tk.Canvas(left_panel, bg="#2b2b2b", highlightthickness=0)
        scrollbar = ttk.Scrollbar(left_panel, orient="vertical", command=control_canvas.yview)
        scrollable_frame = ttk.Frame(control_canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: control_canvas.configure(scrollregion=control_canvas.bbox("all"))
        )
        
        control_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        control_canvas.configure(yscrollcommand=scrollbar.set)
        
        control_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Image Adjustments Section
        adj_section = self.create_section(scrollable_frame, "Image Adjustments", "🎨")
        self.add_slider_entry(adj_section, "Brightness", self.brightness, 0.2, 2.0, 1.0, "Adjust overall image brightness")
        self.add_slider_entry(adj_section, "Contrast", self.contrast, 0.5, 2.0, 1.0, "Control image contrast")
        self.add_slider_entry(adj_section, "Black Clip", self.black_clip, 0, 128, 0, "Set minimum brightness threshold", is_int=True)
        
        # Dither Algorithm Section
        algo_section = self.create_section(scrollable_frame, "Dither Algorithm", "🔧")
        
        # Algorithm selection
        algo_frame = ttk.Frame(algo_section)
        algo_frame.pack(fill=tk.X, pady=5)
        ttk.Label(algo_frame, text="Method:").pack(anchor=tk.W)
        algo_combo = ttk.Combobox(algo_frame, textvariable=self.dither_algorithm, 
                                 values=self.dither_algorithms, state="readonly", 
                                 font=('Segoe UI', 9))
        algo_combo.pack(fill=tk.X, pady=(2, 0))
        algo_combo.bind("<<ComboboxSelected>>", lambda e: self.debounced_update_preview())
        
        # Algorithm descriptions
        desc_frame = ttk.Frame(algo_section)
        desc_frame.pack(fill=tk.X, pady=5)
        desc_text = tk.Text(desc_frame, height=3, wrap=tk.WORD, bg="#3c3c3c", fg="#ffffff", 
                           font=('Segoe UI', 8), relief=tk.FLAT, state=tk.DISABLED)
        desc_text.pack(fill=tk.X)
        
        # Update description based on selection
        def update_desc(*args):
            desc_text.config(state=tk.NORMAL)
            desc_text.delete(1.0, tk.END)
            algo = self.dither_algorithm.get()
            if algo == "Floyd-Steinberg":
                desc_text.insert(1.0, "Classic error diffusion dithering that distributes quantization errors to neighboring pixels.")
            elif algo == "Ordered":
                desc_text.insert(1.0, "Pattern-based dithering using Bayer matrices for structured noise distribution.")
            elif algo == "Atkinson":
                desc_text.insert(1.0, "Apple's dithering algorithm with reduced artifacts and smoother gradients.")
            desc_text.config(state=tk.DISABLED)
        
        self.dither_algorithm.trace('w', update_desc)
        update_desc()
        
        self.add_slider_entry(algo_section, "Threshold", self.dither_strength, 0, 255, 128, 
                             "Brightness threshold for black/white conversion", is_int=True)
        
        # Shape Settings Section
        shape_section = self.create_section(scrollable_frame, "Shape Settings", "🔷")
        
        # Shape selection
        shape_frame = ttk.Frame(shape_section)
        shape_frame.pack(fill=tk.X, pady=5)
        ttk.Label(shape_frame, text="Pattern Type:").pack(anchor=tk.W)
        shape_combo = ttk.Combobox(shape_frame, textvariable=self.shape, 
                                  values=self.shape_options, state="readonly", 
                                  font=('Segoe UI', 9))
        shape_combo.pack(fill=tk.X, pady=(2, 0))
        shape_combo.bind("<<ComboboxSelected>>", lambda e: self.debounced_update_preview())
        
        self.add_slider_entry(shape_section, "Dot Size", self.dot_size, 1, 12, 4, 
                             "Maximum size of shape elements", is_int=True)
        self.add_slider_entry(shape_section, "Detail Level", self.detail, 1, 64, 8, 
                             "Density of shape placement (higher = finer detail)", is_int=True)
        
        # Output Settings Section
        output_section = self.create_section(scrollable_frame, "Output Settings", "📤")
        
        self.add_slider_entry(output_section, "Zoom Factor", self.zoom, 0.5, 3.0, 1.0, 
                             "Scale the output image")
        
        # Color options
        color_frame = ttk.Frame(output_section)
        color_frame.pack(fill=tk.X, pady=10)
        
        color_toggle = ttk.Checkbutton(color_frame, text="Enable Color Output", 
                                      variable=self.color_mode, onvalue="color", 
                                      offvalue="grayscale", command=self.debounced_update_preview)
        color_toggle.pack(anchor=tk.W, pady=(0, 5))
        
        hue_frame = ttk.Frame(color_frame)
        hue_frame.pack(fill=tk.X)
        ttk.Label(hue_frame, text="Hue (when color enabled):").pack(anchor=tk.W)
        hue_slider = ttk.Scale(hue_frame, from_=0, to=1, variable=self.hue, 
                              orient=tk.HORIZONTAL, command=lambda e: self.debounced_update_preview())
        hue_slider.pack(fill=tk.X, pady=(2, 0))
        
        # Quick Presets Section
        presets_section = self.create_section(scrollable_frame, "Quick Presets", "⚡")
        
        presets_frame = ttk.Frame(presets_section)
        presets_frame.pack(fill=tk.X, pady=5)
        
        ttk.Button(presets_frame, text="Classic B&W", 
                  command=lambda: self.apply_preset("classic")).pack(fill=tk.X, pady=2)
        ttk.Button(presets_frame, text="Retro Gaming", 
                  command=lambda: self.apply_preset("retro")).pack(fill=tk.X, pady=2)
        ttk.Button(presets_frame, text="Modern Art", 
                  command=lambda: self.apply_preset("modern")).pack(fill=tk.X, pady=2)
        ttk.Button(presets_frame, text="Reset to Defaults", 
                  command=self.reset_to_defaults).pack(fill=tk.X, pady=2)

    def create_section(self, parent, title, icon):
        """Create a styled section with title and icon"""
        section = ttk.LabelFrame(parent, text=f"{icon} {title}", padding="10")
        section.pack(fill=tk.X, pady=5)
        return section

    def add_slider_entry(self, parent, label, var, minv, maxv, default, tooltip="", is_int=False):
        """Create a slider with entry field and tooltip"""
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=5)
        
        # Label and tooltip
        label_frame = ttk.Frame(frame)
        label_frame.pack(fill=tk.X, pady=(0, 5))
        ttk.Label(label_frame, text=label, font=('Segoe UI', 9, 'bold')).pack(side=tk.LEFT)
        
        if tooltip:
            tooltip_label = ttk.Label(label_frame, text="ⓘ", font=('Segoe UI', 8), foreground='#888888')
            tooltip_label.pack(side=tk.RIGHT)
            self.create_tooltip(tooltip_label, tooltip)
        
        # Slider and entry
        control_frame = ttk.Frame(frame)
        control_frame.pack(fill=tk.X)
        
        slider = ttk.Scale(control_frame, from_=minv, to=maxv, variable=var, 
                          orient=tk.HORIZONTAL, command=lambda e: self.debounced_update_preview())
        slider.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        entry = ttk.Entry(control_frame, textvariable=var, width=8, font=('Segoe UI', 9))
        entry.pack(side=tk.RIGHT)
        
        def validate_entry(*_):
            try:
                v = int(var.get()) if is_int else float(var.get())
                if v < minv: v = minv
                if v > maxv: v = maxv
                var.set(int(v) if is_int else round(v, 2))
            except:
                var.set(default)
            self.debounced_update_preview()
        
        entry.bind('<Return>', validate_entry)
        entry.bind('<FocusOut>', validate_entry)

    def create_tooltip(self, widget, text):
        """Create a tooltip for a widget"""
        def show_tooltip(event):
            tooltip = tk.Toplevel()
            tooltip.wm_overrideredirect(True)
            tooltip.wm_geometry(f"+{event.x_root+10}+{event.y_root+10}")
            
            label = ttk.Label(tooltip, text=text, background="#ffffe0", relief=tk.SOLID, borderwidth=1, 
                             font=('Segoe UI', 8), wraplength=200)
            label.pack()
            
            def hide_tooltip(event):
                tooltip.destroy()
            
            widget.tooltip = tooltip
            widget.bind('<Leave>', hide_tooltip)
        
        widget.bind('<Enter>', show_tooltip)

    def apply_preset(self, preset_name):
        """Apply a preset configuration"""
        if preset_name == "classic":
            self.brightness.set(1.0)
            self.contrast.set(1.2)
            self.black_clip.set(20)
            self.dither_algorithm.set("Floyd-Steinberg")
            self.dither_strength.set(128)
            self.dot_size.set(3)
            self.detail.set(6)
            self.shape.set("Circles")
            self.zoom.set(1.0)
            self.color_mode.set("grayscale")
        elif preset_name == "retro":
            self.brightness.set(1.1)
            self.contrast.set(1.5)
            self.black_clip.set(30)
            self.dither_algorithm.set("Ordered")
            self.dither_strength.set(150)
            self.dot_size.set(5)
            self.detail.set(4)
            self.shape.set("Squares (aligned)")
            self.zoom.set(2.0)
            self.color_mode.set("grayscale")
        elif preset_name == "modern":
            self.brightness.set(0.9)
            self.contrast.set(1.8)
            self.black_clip.set(10)
            self.dither_algorithm.set("Atkinson")
            self.dither_strength.set(100)
            self.dot_size.set(6)
            self.detail.set(12)
            self.shape.set("Triangles (random)")
            self.zoom.set(1.5)
            self.color_mode.set("color")
            self.hue.set(0.6)
        
        self.debounced_update_preview()

    def reset_to_defaults(self):
        """Reset all controls to default values"""
        self.brightness.set(1.0)
        self.contrast.set(1.0)
        self.black_clip.set(0)
        self.dither_algorithm.set("Floyd-Steinberg")
        self.dither_strength.set(128)
        self.dot_size.set(4)
        self.detail.set(8)
        self.shape.set("Circles")
        self.zoom.set(1.0)
        self.color_mode.set("grayscale")
        self.hue.set(0.0)
        self.debounced_update_preview()

    def load_image(self):
        file_path = filedialog.askopenfilename(title="Select Image", filetypes=[("Image files", "*.png *.jpg *.jpeg *.bmp *.tiff")])
        if file_path:
            self.image_path = file_path
            self.image = Image.open(file_path).convert("RGB")
            # Create a downscaled preview image for UI (max 512x512)
            preview_size = 512
            img_w, img_h = self.image.size
            scale = min(preview_size / img_w, preview_size / img_h, 1.0)
            self.preview_image = self.image.resize((int(img_w * scale), int(img_h * scale)), Image.LANCZOS)
            self.update_preview()

    def save_image(self):
        if self.image is None:
            messagebox.showwarning("Warning", "No image to save.")
            return
        file_path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])
        if file_path:
            # Process the full-res image with current settings and zoom
            img_w, img_h = self.image.size
            zoom_factor = self.zoom.get()
            new_w = int(img_w * zoom_factor)
            new_h = int(img_h * zoom_factor)
            save_img = self.image.resize((new_w, new_h), Image.LANCZOS)
            enhancer = ImageEnhance.Brightness(save_img)
            bright_img = enhancer.enhance(self.brightness.get())
            dithered = self.apply_dither(bright_img)
            dithered.save(file_path)
            messagebox.showinfo("Saved", f"Image saved to {file_path}")

    def update_preview(self):
        if self.preview_image is None:
            return
        # Resize preview image with zoom
        canvas_w = self.canvas.winfo_width()
        canvas_h = self.canvas.winfo_height()
        img_w, img_h = self.preview_image.size
        zoom_factor = self.zoom.get()
        new_w = int(img_w * zoom_factor)
        new_h = int(img_h * zoom_factor)
        preview_img = self.preview_image.resize((new_w, new_h), Image.LANCZOS)
        # Apply brightness, contrast, black clip
        enhancer = ImageEnhance.Brightness(preview_img)
        bright_img = enhancer.enhance(self.brightness.get())
        enhancer2 = ImageEnhance.Contrast(bright_img)
        contrast_img = enhancer2.enhance(self.contrast.get())
        arr = np.array(contrast_img.convert("L"))
        arr[arr < self.black_clip.get()] = 0
        contrast_img = Image.fromarray(arr).convert("RGB")
        # Dither with shape
        dithered = self.apply_shape_dither(contrast_img)
        self.display_image = ImageTk.PhotoImage(dithered)
        self.canvas.delete("all")
        self.canvas.create_image(canvas_w // 2, canvas_h // 2, anchor=tk.CENTER, image=self.display_image)

    def apply_dither(self, img):
        arr = np.array(img.convert("L"))
        algo = self.dither_algorithm.get()
        threshold = self.dither_strength.get()
        if algo == "Floyd-Steinberg":
            arr = self.floyd_steinberg(arr, threshold)
        elif algo == "Ordered":
            arr = self.ordered_dither(arr)
        elif algo == "Atkinson":
            arr = self.atkinson_dither(arr, threshold)
        out_img = Image.fromarray(arr).convert("L")
        if self.color_mode.get() == "color":
            # Apply mono hue
            hue = self.hue.get()
            rgb_img = Image.new("RGB", out_img.size)
            arr = np.array(out_img)
            for y in range(out_img.size[1]):
                for x in range(out_img.size[0]):
                    v = arr[y, x] / 255.0
                    r, g, b = colorsys.hsv_to_rgb(hue, 1, v)
                    rgb_img.putpixel((x, y), (int(r*255), int(g*255), int(b*255)))
            return rgb_img
        return out_img

    def floyd_steinberg(self, arr, threshold):
        arr = arr.astype(float)
        h, w = arr.shape
        for y in range(h):
            for x in range(w):
                old = arr[y, x]
                new = 255 if old > threshold else 0
                arr[y, x] = new
                err = old - new
                if x+1<w: arr[y, x+1] += err*7/16
                if x-1>=0 and y+1<h: arr[y+1, x-1] += err*3/16
                if y+1<h: arr[y+1, x] += err*5/16
                if x+1<w and y+1<h: arr[y+1, x+1] += err*1/16
        return np.clip(arr,0,255).astype(np.uint8)

    def ordered_dither(self, arr):
        bayer = np.array([[0,2],[3,1]])
        bayer = np.kron(bayer, np.ones((arr.shape[0]//2, arr.shape[1]//2)))
        bayer = bayer[:arr.shape[0], :arr.shape[1]]
        threshold_map = (bayer+0.5)*255/4
        return np.where(arr>threshold_map,255,0).astype(np.uint8)

    def atkinson_dither(self, arr, threshold):
        arr = arr.astype(float)
        h, w = arr.shape
        for y in range(h):
            for x in range(w):
                old = arr[y, x]
                new = 255 if old > threshold else 0
                arr[y, x] = new
                err = (old - new)/8
                for dx, dy in [(1,0),(2,0),(-1,1),(0,1),(1,1),(0,2)]:
                    nx, ny = x+dx, y+dy
                    if 0<=nx<w and 0<=ny<h:
                        arr[ny, nx] += err
        return np.clip(arr,0,255).astype(np.uint8)

    def apply_shape_dither(self, img):
        arr = np.array(img.convert("L"))
        shape = self.shape.get()
        dot_size = self.dot_size.get()
        detail = self.detail.get()
        threshold = self.dither_strength.get()
        h, w = arr.shape
        out = Image.new("RGB", (w, h), (0,0,0))
        draw = ImageDraw.Draw(out)
        rng = np.random.default_rng(42)
        for y in range(0, h, detail):
            for x in range(0, w, detail):
                block = arr[y:y+detail, x:x+detail]
                avg = np.mean(block)
                if avg < threshold:
                    continue
                # Dot size proportional to brightness (larger = brighter)
                rel = (avg - threshold) / (255 - threshold) if avg > threshold else 0
                rel = max(0, min(1, rel))
                size = int(1 + rel * (dot_size-1))
                cx, cy = x + detail//2, y + detail//2
                if shape.startswith("Circle"):
                    draw.ellipse([cx-size//2, cy-size//2, cx+size//2, cy+size//2], fill=(255,255,255))
                elif shape.startswith("Square"):
                    angle = 0
                    if "random" in shape.lower():
                        angle = rng.uniform(0, 360)
                    self.draw_square(draw, cx, cy, size, angle)
                elif shape.startswith("Triangle"):
                    angle = 0
                    if "random" in shape.lower():
                        angle = rng.uniform(0, 360)
                    self.draw_triangle(draw, cx, cy, size, angle)
        if self.color_mode.get() == "color":
            # Apply mono hue
            hue = self.hue.get()
            arr = np.array(out.convert("L"))
            rgb_img = Image.new("RGB", out.size)
            for y in range(out.size[1]):
                for x in range(out.size[0]):
                    v = arr[y, x] / 255.0
                    r, g, b = colorsys.hsv_to_rgb(hue, 1, v)
                    rgb_img.putpixel((x, y), (int(r*255), int(g*255), int(b*255)))
            return rgb_img
        return out

    def draw_square(self, draw, cx, cy, size, angle):
        rad = math.radians(angle)
        half = size/2
        corners = [
            (cx + half*math.cos(rad + math.pi/4*i), cy + half*math.sin(rad + math.pi/4*i))
            for i in range(4)
        ]
        draw.polygon(corners, fill=(255,255,255))

    def draw_triangle(self, draw, cx, cy, size, angle):
        rad = math.radians(angle)
        half = size/2
        corners = [
            (cx + half*math.cos(rad + 2*math.pi/3*i), cy + half*math.sin(rad + 2*math.pi/3*i))
            for i in range(3)
        ]
        draw.polygon(corners, fill=(255,255,255))

    def apply_to_folder(self):
        input_dir = filedialog.askdirectory(title="Select Input Folder")
        if not input_dir:
            return
        output_dir = filedialog.askdirectory(title="Select Output Folder")
        if not output_dir:
            return
        # Gather all image files
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        files = [f for f in os.listdir(input_dir) if os.path.splitext(f)[1].lower() in image_exts]
        if not files:
            messagebox.showwarning("No Images", "No image files found in the selected folder.")
            return
        # Progress window
        progress_win = tk.Toplevel(self.root)
        progress_win.title("Batch Dithering")
        progress_win.geometry("400x120")
        progress_label = ttk.Label(progress_win, text="Processing images...")
        progress_label.pack(pady=10)
        progress_bar = ttk.Progressbar(progress_win, length=350, mode='determinate', maximum=len(files))
        progress_bar.pack(pady=10)
        status_label = ttk.Label(progress_win, text="0 / {}".format(len(files)))
        status_label.pack(pady=5)
        self.root.update()
        def batch_process():
            for i, fname in enumerate(files):
                try:
                    img_path = os.path.join(input_dir, fname)
                    img = Image.open(img_path).convert("RGB")
                    # Apply zoom
                    img_w, img_h = img.size
                    zoom_factor = self.zoom.get()
                    new_w = int(img_w * zoom_factor)
                    new_h = int(img_h * zoom_factor)
                    proc_img = img.resize((new_w, new_h), Image.LANCZOS)
                    # Apply brightness
                    enhancer = ImageEnhance.Brightness(proc_img)
                    bright_img = enhancer.enhance(self.brightness.get())
                    # Apply contrast
                    enhancer2 = ImageEnhance.Contrast(bright_img)
                    contrast_img = enhancer2.enhance(self.contrast.get())
                    # Apply black clip
                    arr = np.array(contrast_img.convert("L"))
                    arr[arr < self.black_clip.get()] = 0
                    contrast_img = Image.fromarray(arr).convert("RGB")
                    # Apply shape dither
                    dithered = self.apply_shape_dither(contrast_img)
                    name, ext = os.path.splitext(fname)
                    out_path = os.path.join(output_dir, f"{name}_dithered{ext}")
                    dithered.save(out_path)
                except Exception as e:
                    print(f"Error processing {fname}: {e}")
                progress_bar['value'] = i+1
                status_label.config(text=f"{i+1} / {len(files)}")
                self.root.update()
            progress_win.destroy()
            messagebox.showinfo("Done", f"Processed {len(files)} images.")
        threading.Thread(target=batch_process).start()

    def debounced_update_preview(self, delay=100):
        if hasattr(self, 'debounce_timer') and self.debounce_timer:
            self.root.after_cancel(self.debounce_timer)
        self.debounce_timer = self.root.after(delay, self.update_preview)

def main():
    root = tk.Tk()
    app = DitherDockApp(root)
    def on_resize(event):
        app.debounced_update_preview()
    root.bind('<Configure>', on_resize)
    root.mainloop()

if __name__ == "__main__":
    main() 