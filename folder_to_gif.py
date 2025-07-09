import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image
import os

class FolderToGifApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Folder to GIF")
        self.root.geometry("420x320")  # Larger default size
        self.input_folder = None
        self.output_file = None
        self.duration = tk.IntVar(value=100)
        self.setup_ui()

    def setup_ui(self):
        frame = ttk.Frame(self.root, padding=20)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Button(frame, text="Select Image Folder", command=self.select_folder).pack(fill=tk.X, expand=True, pady=(0, 8))
        self.folder_label = ttk.Label(frame, text="No folder selected", foreground="gray", anchor="w")
        self.folder_label.pack(fill=tk.X, expand=True, pady=(0, 12))

        ttk.Label(frame, text="Frame Duration (ms):").pack(anchor=tk.W, pady=(0, 2))
        duration_entry = ttk.Entry(frame, textvariable=self.duration, width=10)
        duration_entry.pack(fill=tk.X, expand=True, pady=(0, 12))

        ttk.Label(frame, text="(GIF will loop infinitely)", foreground="gray").pack(anchor=tk.W, pady=(0, 12))

        ttk.Button(frame, text="Select Output GIF", command=self.select_output).pack(fill=tk.X, expand=True, pady=(0, 8))
        self.output_label = ttk.Label(frame, text="No output file selected", foreground="gray", anchor="w")
        self.output_label.pack(fill=tk.X, expand=True, pady=(0, 12))

        ttk.Button(frame, text="Create GIF", command=self.create_gif).pack(fill=tk.X, expand=True, pady=(10, 0))

    def select_folder(self):
        folder = filedialog.askdirectory(title="Select Folder of Images")
        if folder:
            self.input_folder = folder
            self.folder_label.config(text=folder, foreground="black")

    def select_output(self):
        file = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF files", "*.gif")], title="Save GIF As")
        if file:
            self.output_file = file
            self.output_label.config(text=file, foreground="black")

    def create_gif(self):
        if not self.input_folder or not self.output_file:
            messagebox.showwarning("Missing Info", "Please select both an input folder and output file.")
            return
        image_exts = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}
        files = [f for f in os.listdir(self.input_folder) if os.path.splitext(f)[1].lower() in image_exts]
        if not files:
            messagebox.showwarning("No Images", "No image files found in the selected folder.")
            return
        files.sort()  # Sort by filename
        images = []
        for fname in files:
            path = os.path.join(self.input_folder, fname)
            img = Image.open(path).convert("RGBA")
            images.append(img)
        # Resize all to the first image's size
        base_size = images[0].size
        images = [img.resize(base_size, Image.LANCZOS) for img in images]
        duration = self.duration.get()
        try:
            images[0].save(self.output_file, save_all=True, append_images=images[1:], duration=duration, loop=0, disposal=2, optimize=False)
            messagebox.showinfo("Success", f"GIF saved to {self.output_file}\n(It will loop infinitely)")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create GIF: {e}")

def main():
    root = tk.Tk()
    app = FolderToGifApp(root)
    root.mainloop()

if __name__ == "__main__":
    main() 