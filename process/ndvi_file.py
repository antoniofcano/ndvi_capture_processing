import os
import sys
import cv2
import argparse
from ndvi_processor import NDVIProcessor

def main(args):
    # Check if the input file has a supported image format (DNG or JPG/JPEG)
    input_filepath = args.input_file
    filename = os.path.basename(input_filepath)
    file_extension = filename.lower().split('.')[-1]

    if file_extension in ['dng', 'raw', 'jpg', 'jpeg']:
        # Initialize the NDVIProcessor and process the image
        print(f"Processing: {filename}")
        ndvi_processor = NDVIProcessor(input_filepath)
        ndvi_processor.process_image()

        # Apply the specified colormap to the NDVI image
        ndvi_color = ndvi_processor.apply_colormap(args.colormap)

        # Save the NDVI image in the output directory
        output_filename = f"ndvi_{os.path.splitext(filename)[0]}.jpg"
        output_filepath = os.path.join(args.output_directory, output_filename)
        cv2.imwrite(output_filepath, ndvi_color, [cv2.IMWRITE_JPEG_QUALITY, 100])

        print("Image processing completed.")
    else:
        print("Error: Unsupported file format. Please provide a JPG or DNG image.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NDVI single image processing tool.')
    parser.add_argument('-i', '--input_file', type=str, required=True, help='Path to the input image file.')
    parser.add_argument('-o', '--output_directory', type=str, required=True, help='Path to the output image directory.')
    parser.add_argument('-c', '--colormap', type=int, default=cv2.COLORMAP_JET, help='OpenCV colormap to apply. Default is cv2.COLORMAP_JET (2). Recommended colormaps for NDVI representation: 2 (cv2.COLORMAP_JET), 4 (cv2.COLORMAP_RAINBOW), 11 (cv2.COLORMAP_HOT), 12 (cv2.COLORMAP_PARULA).')

    args = parser.parse_args()

    main(args)
