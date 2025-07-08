# Dither Dock

A Python GUI application for creating artistic dithering effects on images. Dither Dock allows you to apply various dithering algorithms and shape-based patterns to transform your images into stylized, pixelated artwork.

## Features

- **Multiple Dithering Algorithms**: Floyd-Steinberg, Ordered, and Atkinson dithering
- **Shape-Based Dithering**: Create patterns using circles, squares, or triangles
- **Real-time Preview**: See changes instantly as you adjust parameters
- **Image Adjustments**: Control brightness, contrast, and black clipping
- **Batch Processing**: Apply effects to entire folders of images
- **Color Options**: Grayscale or monochromatic color output
- **Zoom Support**: Scale images up or down during processing

## Requirements

- Python 3.6 or higher
- Required packages:
  - `tkinter` (usually included with Python)
  - `PIL` (Pillow)
  - `numpy`

## Installation

1. Clone or download this repository
2. Install the required dependencies:

```bash
pip install Pillow numpy
```

## Usage

### Starting the Application

Run the script from the command line:

```bash
python dither.py
```

### Loading an Image

1. Click the **File ▼** button in the bottom dock
2. Select **Load Image** from the dropdown menu
3. Choose an image file (supports PNG, JPG, JPEG, BMP, TIFF)

### Image Adjustments

The **Image Adjustments** section allows you to modify the base image before dithering:

- **Brightness**: Adjust overall image brightness (0.2 - 2.0)
- **Contrast**: Control image contrast (0.5 - 2.0)
- **Black Clip**: Set minimum brightness threshold (0 - 128)

### Dither Style

The **Dither Style** section controls the dithering effect:

- **Algorithm**: Choose between three dithering methods:
  - **Floyd-Steinberg**: Classic error diffusion dithering
  - **Ordered**: Pattern-based dithering using Bayer matrices
  - **Atkinson**: Apple's dithering algorithm with reduced artifacts
- **Brightness Threshold**: Set the threshold for black/white conversion (0 - 255)
- **Dot Size**: Control the maximum size of shape elements (1 - 12)
- **Detail**: Adjust the density of shape placement (1 - 64)
- **Shape/Orientation**: Choose the shape and alignment:
  - **Circles**: Circular dots
  - **Squares (aligned)**: Square dots aligned to grid
  - **Triangles (aligned)**: Triangular dots aligned to grid
  - **Squares (random)**: Square dots with random rotation
  - **Triangles (random)**: Triangular dots with random rotation

### Output Settings

The **Output** section controls the final appearance:

- **Zoom**: Scale the output image (0.5x - 3.0x)
- **Color**: Toggle between grayscale and monochromatic color
- **Mono Hue**: When color is enabled, set the hue for monochromatic output (0.0 - 1.0)

### Saving Images

1. Click **File ▼** → **Save Image**
2. Choose a save location and filename
3. The image will be processed at full resolution with current settings

### Batch Processing

To apply the current settings to multiple images:

1. Click **File ▼** → **Apply to Folder**
2. Select the input folder containing your images
3. Select an output folder for the processed images
4. The application will process all supported image files and save them with "_dithered" suffix

## Tips for Best Results

- **Start with moderate settings**: Begin with default values and adjust gradually
- **Experiment with algorithms**: Each dithering method produces different effects
- **Use appropriate detail levels**: Higher detail values create finer patterns but may be slower
- **Consider your output size**: Larger zoom factors will create bigger, more visible patterns
- **Try different shapes**: Each shape type creates a unique aesthetic
- **Adjust brightness/contrast**: These can dramatically affect the final appearance

## Supported File Formats

- **Input**: PNG, JPG, JPEG, BMP, TIFF
- **Output**: PNG (recommended for best quality)

## Troubleshooting

- **Slow performance**: Reduce the detail level or use a smaller preview image
- **Memory issues**: Process images in smaller batches or reduce zoom factor
- **No preview**: Make sure an image is loaded and the canvas is visible
- **Missing dependencies**: Ensure all required packages are installed

## License

This project is licensed under the MIT License - see the LICENSE file for details. 