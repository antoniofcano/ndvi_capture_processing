import os
import sys
import cv2
import argparse
from ndvi_processor import NDVIProcessor

def main(args):
    # Create the output directory if it doesn't exist
    if not os.path.exists(args.output_directory):
        os.makedirs(args.output_directory)

    # Process all RAW (DNG) and JPG images in the input directory
    for filename in os.listdir(args.input_directory):
        input_filepath = os.path.join(args.input_directory, filename)
        file_extension = filename.lower().split('.')[-1]

        # Check if the file is a supported image format (DNG or JPG/JPEG)
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

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='NDVI image processing tool.')
    parser.add_argument('-i', '--input_directory', type=str, required=True, help='Path to the input image directory.')
    parser.add_argument('-o', '--output_directory', type=str, required=True, help='Path to the output image directory.')
    parser.add_argument('-c', '--colormap', type=int, default=cv2.COLORMAP_JET, help='OpenCV colormap to apply. Default is cv2.COLORMAP_JET (2). Recommended colormaps for NDVI representation: 2 (cv2.COLORMAP_JET), 4 (cv2.COLORMAP_RAINBOW), 11 (cv2.COLORMAP_HOT), 12 (cv2.COLORMAP_PARULA).')


    args = parser.parse_args()

    # Print recommended colormaps for NDVI representation
    print("\nRecommended OpenCV colormaps for NDVI representation:")
    print("2: cv2.COLORMAP_JET")
    print("4: cv2.COLORMAP_RAINBOW")
    print("11: cv2.COLORMAP_HOT")
    print("12: cv2.COLORMAP_PARULA")

    main(args)
