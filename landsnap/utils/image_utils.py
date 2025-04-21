import cv2
import numpy as np
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import SuspiciousOperation
from PIL import Image
import os
import logging

logger = logging.getLogger(__name__)

# Configuration constants
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_DIMENSION = 5000  # Maximum width/height in pixels
MIN_DIMENSION = 100   # Minimum width/height in pixels
CHANGE_THRESHOLD = 25  # Threshold for considering a pixel changed

def validate_image_file(image_path):
    """Validate image file before processing"""
    if not os.path.exists(image_path):
        raise SuspiciousOperation("Image file not found")
    
    if os.path.getsize(image_path) > MAX_IMAGE_SIZE:
        raise SuspiciousOperation(f"Image exceeds maximum size of {MAX_IMAGE_SIZE//(1024*1024)}MB")
    
    try:
        with Image.open(image_path) as img:
            if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
                raise SuspiciousOperation(f"Image dimensions exceed maximum of {MAX_DIMENSION}x{MAX_DIMENSION}")
            if img.width < MIN_DIMENSION or img.height < MIN_DIMENSION:
                raise SuspiciousOperation(f"Image dimensions below minimum of {MIN_DIMENSION}x{MIN_DIMENSION}")
    except Exception as e:
        raise SuspiciousOperation(f"Invalid image file: {str(e)}")

def process_image(image_path):
    """Secure image processing with comprehensive validation"""
    validate_image_file(image_path)
    
    try:
        img = cv2.imread(image_path)
        if img is None:
            raise SuspiciousOperation("Failed to read image with OpenCV")
        
        # Convert color space if needed
        if len(img.shape) == 2:  # Grayscale
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        elif img.shape[2] == 4:   # RGBA
            img = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
        elif img.shape[2] == 3:   # BGR (OpenCV default)
            pass
        else:
            raise SuspiciousOperation("Unsupported image color format")
            
        return img
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        raise SuspiciousOperation(f"Image processing error: {str(e)}")

def generate_heatmap(img1_path, img2_path):
    """Generate secure heatmap with validation and optimized processing"""
    try:
        img1 = process_image(img1_path)
        img2 = process_image(img2_path)

        # Resize images to match dimensions if needed
        if img1.shape != img2.shape:
            logger.info(f"Resizing images to match dimensions: {img1.shape} vs {img2.shape}")
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Calculate absolute difference with normalization
        img1_float = img1.astype(np.float32)
        img2_float = img2.astype(np.float32)
        diff = cv2.absdiff(img1_float, img2_float)
        diff = cv2.normalize(diff, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)

        # Apply color map with optimized parameters
        heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)

        # Convert to PNG with compression
        success, buffer = cv2.imencode('.png', heatmap, [cv2.IMWRITE_PNG_COMPRESSION, 9])
        if not success:
            raise SuspiciousOperation("Failed to encode heatmap image")

        return ContentFile(buffer.tobytes(), name='heatmap.png')
    except Exception as e:
        logger.error(f"Heatmap generation failed: {str(e)}")
        raise SuspiciousOperation(f"Heatmap generation error: {str(e)}")

def calculate_changes(img1_path, img2_path):
    """Calculate percentage of changes with improved accuracy"""
    try:
        # Read images as grayscale
        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

        if img1 is None or img2 is None:
            raise SuspiciousOperation("Failed to read images for change calculation")

        # Resize images to match dimensions if needed
        if img1.shape != img2.shape:
            logger.info(f"Resizing images for change calculation: {img1.shape} vs {img2.shape}")
            img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

        # Calculate absolute difference with noise reduction
        diff = cv2.absdiff(img1, img2)
        
        # Apply Gaussian blur to reduce noise
        diff = cv2.GaussianBlur(diff, (5, 5), 0)
        
        # Adaptive thresholding for better change detection
        threshold = cv2.adaptiveThreshold(
            diff, 255, 
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY_INV, 
            11, 2
        )

        # Calculate changed pixels percentage
        changed_pixels = np.count_nonzero(threshold)
        total_pixels = threshold.size
        change_percent = round((changed_pixels / total_pixels) * 100, 2)

        logger.info(f"Change detection completed: {change_percent}% change detected")
        return change_percent
    except Exception as e:
        logger.error(f"Change calculation failed: {str(e)}")
        raise SuspiciousOperation(f"Change calculation error: {str(e)}")