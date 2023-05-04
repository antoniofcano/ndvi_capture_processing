import cv2
import numpy as np

class NDVIProcessor:
    """
    Class for processing images and calculating the NDVI (Normalized Difference Vegetation Index).
    """
    def __init__(self, file_path):
        """
        Constructor for the NDVIProcessor class.

        Parameters
        ----------
        file_path : str
            Path to the image file to be processed (raw/dng or jpg format).
        """
        self.file_path = file_path
        self.ndvi_grayscale = None

    def _normalize_ndvi(self, ndvi):
        """
        Normalize the NDVI array to the range [0, 1].

        Parameters
        ----------
        ndvi : ndarray
            The NDVI array.

        Returns
        -------
        ndarray
            The normalized NDVI array.
        """
        return (ndvi - ndvi.min()) / (ndvi.max() - ndvi.min() + 1e-7)

    def _calculate_ndvi(self, red_channel, nir_channel):
        """
        Calculate the NDVI using the red and NIR channels.

        Parameters
        ----------
        red_channel : ndarray
            The red channel array.
        nir_channel : ndarray
            The near-infrared channel array.

        Returns
        -------
        ndarray
            The NDVI array.
        """
        return (nir_channel - red_channel) / (nir_channel + red_channel + 1e-7)

    def _to_grayscale(self, ndvi_normalized):
        """
        Convert the normalized NDVI array to an 8-bit grayscale image.

        Parameters
        ----------
        ndvi_normalized : ndarray
            The normalized NDVI array.

        Returns
        -------
        ndarray
            The 8-bit grayscale NDVI image.
        """
        return (ndvi_normalized * 255).astype(np.uint8)

    def _process_image_data(self, red_channel, nir_channel):
        """
        Process the red and NIR channels to compute the NDVI and normalize it.

        Parameters
        ----------
        red_channel : ndarray
            The red channel array.
        nir_channel : ndarray
            The near-infrared channel array.

        Returns
        -------
        ndarray
            The 8-bit grayscale NDVI image.
        """
        ndvi = self._calculate_ndvi(red_channel, nir_channel)
        ndvi_normalized = self._normalize_ndvi(ndvi)
        ndvi_normalized = np.nan_to_num(ndvi_normalized)

        return self._to_grayscale(ndvi_normalized)

    def process_image(self):
        """
        Process the input image based on its file extension (jpg/jpeg or raw/dng).
        """
        extension = self.file_path.split('.')[-1].lower()
        if extension in ['jpg', 'jpeg']:
            self.ndvi_grayscale = self.process_jpg_image()
        elif extension in ['raw', 'dng']:
            self.ndvi_grayscale = self.process_raw_image()

    def process_jpg_image(self):
        """
        Process a JPG image to compute the NDVI.

        Returns
        -------
        ndarray
            The 8-bit grayscale NDVI image.
        """
        rgb_image = cv2.imread(self.file_path)
        red_channel = rgb_image[:, :, 2].astype(np.float32)
        nir_channel = rgb_image[:, :, 0].astype(np.float32)

        return self._process_image_data(red_channel, nir_channel)

    def process_raw_image(self):
        """
        Process a raw image (Bayer pattern) to compute the NDVI.

        Returns
        -------
        ndarray
        The 8-bit grayscale NDVI image.
        """
        raw_image = cv2.imread(self.file_path, cv2.IMREAD_ANYDEPTH)
        rgb_image = cv2.cvtColor(raw_image, cv2.COLOR_BayerBG2RGB)
        red_channel = rgb_image[:, :, 2].astype(np.float32)
        nir_channel = rgb_image[:, :, 0].astype(np.float32)

        return self._process_image_data(red_channel, nir_channel)

def apply_colormap(self, colormap=cv2.COLORMAP_JET):
    """
    Apply a colormap to the grayscale NDVI image.

    Parameters
    ----------
    colormap : int, optional
        The OpenCV colormap to apply (default is cv2.COLORMAP_JET).

    Returns
    -------
    ndarray
        The NDVI image with the colormap applied.
    """
    return cv2.applyColorMap(self.ndvi_grayscale, colormap)

def save_image(self, output_file_path, colormap=None):
    """
    Save the processed NDVI image to a file.

    Parameters
    ----------
    output_file_path : str
        The path to save the output image file.
    colormap : int, optional
        The OpenCV colormap to apply before saving (default is None, which saves the grayscale image).
    """
    if colormap is not None:
        output_image = self.apply_colormap(colormap)
    else:
        output_image = self.ndvi_grayscale
    cv2.imwrite(output_file_path, output_image)
