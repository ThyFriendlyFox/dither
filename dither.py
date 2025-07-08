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
        self.root.geometry("1200x800")
        self.root.configure(bg="#222")
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
        style = ttk.Style()
        style.configure('Toolbutton', font=('Arial', 12, 'bold'))
        # Main image display
        self.canvas = tk.Canvas(self.root, bg="#222", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Bottom dock frame
        dock = tk.Frame(self.root, bg="#222", height=120)
        dock.pack(side=tk.BOTTOM, fill=tk.X)

        # File menu dropdown
        file_menu_btn = ttk.Menubutton(dock, text="File ▼")
        file_menu = tk.Menu(file_menu_btn, tearoff=0)
        file_menu.add_command(label="Load Image", command=self.load_image)
        file_menu.add_command(label="Save Image", command=self.save_image)
        file_menu.add_command(label="Apply to Folder", command=self.apply_to_folder)
        file_menu_btn['menu'] = file_menu
        file_menu_btn.pack(side=tk.RIGHT, padx=10, pady=10)

        # Collapsible: Image Adjustments
        adj_section = CollapsibleSection(dock, "Image Adjustments")
        adj_section.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        self.add_slider_entry(adj_section.body, "Brightness", self.brightness, 0.2, 2.0, 1.0)
        self.add_slider_entry(adj_section.body, "Contrast", self.contrast, 0.5, 2.0, 1.0)
        self.add_slider_entry(adj_section.body, "Black Clip", self.black_clip, 0, 128, 0, is_int=True)

        # Collapsible: Dither Style
        style_section = CollapsibleSection(dock, "Dither Style")
        style_section.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        algo_label = ttk.Label(style_section.body, text="Algorithm:")
        algo_label.pack(anchor=tk.W)
        algo_combo = ttk.Combobox(style_section.body, textvariable=self.dither_algorithm, values=self.dither_algorithms, state="readonly", width=15)
        algo_combo.pack(fill=tk.X, pady=2)
        algo_combo.bind("<Button-1>", self.show_dropup)
        algo_combo.bind("<<ComboboxSelected>>", lambda e: self.debounced_update_preview())
        self.add_slider_entry(style_section.body, "Brightness Threshold", self.dither_strength, 0, 255, 128, is_int=True)
        self.add_slider_entry(style_section.body, "Dot Size", self.dot_size, 1, 12, 4, is_int=True)
        self.add_slider_entry(style_section.body, "Detail", self.detail, 1, 64, 8, is_int=True)
        shape_label = ttk.Label(style_section.body, text="Shape/Orientation:")
        shape_label.pack(anchor=tk.W, pady=(6,0))
        shape_combo = ttk.Combobox(style_section.body, textvariable=self.shape, values=self.shape_options, state="readonly", width=18)
        shape_combo.pack(fill=tk.X, pady=2)
        shape_combo.bind("<<ComboboxSelected>>", lambda e: self.debounced_update_preview())

        # Collapsible: Output
        out_section = CollapsibleSection(dock, "Output")
        out_section.pack(side=tk.LEFT, fill=tk.Y, padx=5, pady=2)
        self.add_slider_entry(out_section.body, "Zoom", self.zoom, 0.5, 3.0, 1.0)
        color_toggle = ttk.Checkbutton(out_section.body, text="Color", variable=self.color_mode, onvalue="color", offvalue="grayscale", command=self.debounced_update_preview)
        color_toggle.pack(anchor=tk.W, pady=(6,0))
        hue_label = ttk.Label(out_section.body, text="Mono Hue:")
        hue_label.pack(anchor=tk.W)
        hue_slider = ttk.Scale(out_section.body, from_=0, to=1, variable=self.hue, orient=tk.HORIZONTAL, command=lambda e: self.debounced_update_preview(), length=100)
        hue_slider.pack(fill=tk.X)

    def add_slider_entry(self, parent, label, var, minv, maxv, default, is_int=False):
        frame = ttk.Frame(parent)
        frame.pack(fill=tk.X, pady=2)
        ttk.Label(frame, text=label+":").pack(side=tk.LEFT)
        slider = ttk.Scale(frame, from_=minv, to=maxv, variable=var, orient=tk.HORIZONTAL, command=lambda e: self.debounced_update_preview(), length=80)
        slider.pack(side=tk.LEFT, padx=4)
        entry = ttk.Entry(frame, textvariable=var, width=5)
        entry.pack(side=tk.LEFT)
        def validate_entry(*_):
            try:
                v = int(var.get()) if is_int else float(var.get())
                if v < minv: v = minv
                if v > maxv: v = maxv
                var.set(int(v) if is_int else round(v,2))
            except:
                var.set(default)
            self.debounced_update_preview()
        entry.bind('<Return>', validate_entry)

    def show_dropup(self, event):
        widget = event.widget
        widget.tk.call("ttk::combobox::PopdownWindow", widget)
        popdown = widget.tk.call("ttk::combobox::PopdownWindow", widget)
        widget.tk.call("wm", "geometry", popdown, "+%d+%d" % (widget.winfo_rootx(), widget.winfo_rooty() - 100))

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