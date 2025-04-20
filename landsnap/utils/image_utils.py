import cv2
import numpy as np
from django.core.files.base import ContentFile
from io import BytesIO
from django.core.exceptions import SuspiciousOperation

MAX_IMAGE_SIZE = 10 * 1024 * 1024

def process_image(image_path):
    """Secure image processing with validation"""
    img = cv2.imread(image_path)
    if img is None:
        raise SuspiciousOperation("Invalid image file")
    if img.size > MAX_IMAGE_SIZE:
        raise SuspiciousOperation("Image size exceeds maximum limit")
    return img

def generate_heatmap(img1_path, img2_path):
    """Generate secure heatmap with validation"""
    img1 = process_image(img1_path)
    img2 = process_image(img2_path)

    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    diff = cv2.absdiff(img1, img2)
    heatmap = cv2.applyColorMap(diff, cv2.COLORMAP_JET)

    buffer = BytesIO()
    _, buffer = cv2.imencode('.png', heatmap)
    return ContentFile(buffer.tobytes(), name='heatmap.png')

def calculate_changes(img1_path, img2_path):
    """Calculate percentage of changes"""
    img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)

    if img1.shape != img2.shape:
        img2 = cv2.resize(img2, (img1.shape[1], img1.shape[0]))

    diff = cv2.absdiff(img1, img2)
    _, threshold = cv2.threshold(diff, 25, 255, cv2.THRESH_BINARY)

    changed_pixels = np.count_nonzero(threshold)
    total_pixels = threshold.size
    return round((changed_pixels / total_pixels) * 100, 2)