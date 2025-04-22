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
MAX_IMAGE_SIZE = 10 * 1024 * 1024  
MAX_DIMENSION = 5000  
MIN_DIMENSION = 100 
CHANGE_THRESHOLD = 25

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
        elif img.shape[2] == 3:   # BGR
            pass
        else:
            raise SuspiciousOperation("Unsupported image color format")
            
        return img
    except Exception as e:
        logger.error(f"Error processing image {image_path}: {str(e)}")
        raise SuspiciousOperation(f"Image processing error: {str(e)}")

def generate_heatmap(img1_path, img2_path):
    """Generate heatmap with robust size and type handling"""
    try:
        # Load and validate images
        img1 = process_image(img1_path)
        img2 = process_image(img2_path)

        # Ensure both images have exactly the same dimensions
        if img1.shape != img2.shape:
            height, width = img1.shape[:2]
            img2 = cv2.resize(img2, (width, height))
            logger.info(f"Resized second image to match dimensions: {width}x{height}")

        # Convert to grayscale for comparison
        gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

        # Compute absolute difference
        diff = cv2.absdiff(gray1, gray2)
        
        # Apply threshold to find significant changes
        _, thresh = cv2.threshold(diff, 30, 255, cv2.THRESH_BINARY)
        
        # Find contours of changed regions
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Create empty mask and output image
        mask = np.zeros_like(gray1)
        output = img2.copy()
        
        # Process each contour
        for cnt in contours:
            if cv2.contourArea(cnt) > 100: 
                # Draw filled contour on mask
                cv2.drawContours(mask, [cnt], 0, 255, -1)
                # Draw bounding box
                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(output, (x,y), (x+w,y+h), (0,255,0), 2)

        # Create colored difference visualization, marking the changes in Red
        colored_diff = np.zeros_like(img1)
        colored_diff[mask == 255] = (0, 0, 255)
        
        # Blend with original image (70% original, 30% difference)
        result = cv2.addWeighted(img2, 0.7, colored_diff, 0.3, 0)
        
        # Add the bounding boxes
        for cnt in contours:
            if cv2.contourArea(cnt) > 100:
                x,y,w,h = cv2.boundingRect(cnt)
                cv2.rectangle(result, (x,y), (x+w,y+h), (0,255,0), 2)

        # Encode and return result
        success, buffer = cv2.imencode('.png', result)
        if not success:
            raise Exception("Failed to encode image")
            
        return ContentFile(buffer.tobytes(), name='heatmap.png')
        
    except Exception as e:
        logger.error(f"Heatmap generation error: {str(e)}")
        raise SuspiciousOperation(f"Heatmap generation failed: {str(e)}")
    
def structural_similarity(im1, im2, window_size=7, full=False):
    """
    Compute the mean structural similarity index between two images.
    This is a simplified version of skimage.metrics.structural_similarity
    """
    # Check if the window size is valid
    (win_width, win_height) = (window_size, window_size)
    if win_width > im1.shape[1] or win_height > im1.shape[0]:
        window_size = min(im1.shape[0], im1.shape[1])
        if window_size % 2 == 0:
            window_size -= 1
        (win_width, win_height) = (window_size, window_size)
    
    # Constants
    K1 = 0.01
    K2 = 0.03
    L = 255 
    C1 = (K1 * L) ** 2
    C2 = (K2 * L) ** 2
    
    # Compute means
    im1 = im1.astype(np.float64)
    im2 = im2.astype(np.float64)
    kernel = cv2.getGaussianKernel(win_width, 1.5)
    kernel = np.outer(kernel, kernel.transpose())
    
    mu1 = cv2.filter2D(im1, -1, kernel)
    mu2 = cv2.filter2D(im2, -1, kernel)
    
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    # Compute variances
    sigma1_sq = cv2.filter2D(im1 ** 2, -1, kernel) - mu1_sq
    sigma2_sq = cv2.filter2D(im2 ** 2, -1, kernel) - mu2_sq
    sigma12 = cv2.filter2D(im1 * im2, -1, kernel) - mu1_mu2
    
    # Compute SSIM
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    if full:
        return ssim_map.mean(), ssim_map
    return ssim_map.mean()

def calculate_changes(img1_path, img2_path):
    """Calculate percentage of changes with improved accuracy and noise reduction"""
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

        # Calculate structural similarity
        score, diff = structural_similarity(img1, img2, full=True)
        diff = (diff * 255).astype("uint8")
        
        # Apply adaptive thresholding
        thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
        
        # Morphological operations to clean up the thresholded image
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel, iterations=2)
        thresh = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel, iterations=1)
        
        # Calculate changed pixels percentage
        changed_pixels = np.count_nonzero(thresh)
        total_pixels = thresh.size
        change_percent = round((changed_pixels / total_pixels) * 100, 2)

        logger.info(f"Change detection completed: {change_percent}% change detected (SSIM: {score:.2f})")
        return change_percent
    except Exception as e:
        logger.error(f"Change calculation failed: {str(e)}")
        raise SuspiciousOperation(f"Change calculation error: {str(e)}")