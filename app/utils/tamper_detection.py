import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim
from PIL import Image

def load_and_normalize(image_path: str, size=(512, 512)) -> np.ndarray:
    """Load image and normalize for comparison."""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(gray, size)
    return resized


def compute_ssim(original_path: str, uploaded_path: str):
    """
    Compute SSIM score between original and uploaded certificate.
    Returns:
        score       : float (0 to 1, higher = more similar)
        diff_image  : numpy array with difference highlighted
    """
    img1 = load_and_normalize(original_path)
    img2 = load_and_normalize(uploaded_path)

    # Compute SSIM
    score, diff = ssim(img1, img2, full=True)

    # Convert diff to uint8
    diff = (diff * 255).astype("uint8")

    return score, diff


def highlight_tampered_regions(
    original_path: str,
    uploaded_path: str,
    output_path: str
) -> tuple[float, str]:
    """
    Detect and highlight tampered regions.

    Steps:
    1. Compute SSIM difference map
    2. Threshold the diff to find changed areas
    3. Find contours around tampered regions
    4. Draw RED rectangles on original image

    Returns:
        ssim_score  : similarity score (0-1)
        output_path : path to highlighted image
    """
    # Get SSIM score and diff map
    score, diff = compute_ssim(original_path, uploaded_path)

    # Threshold difference map
    _, thresh = cv2.threshold(diff, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # Find contours (tampered regions)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Load uploaded image for visualization (in color)
    uploaded_img = cv2.imread(uploaded_path)
    h, w = uploaded_img.shape[:2]

    # Scale factor (original normalized to 512x512)
    scale_x = w / 512
    scale_y = h / 512

    # Draw RED rectangles around tampered areas
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 100:  # Ignore tiny noise contours
            x, y, cw, ch = cv2.boundingRect(contour)

            # Scale back to original image size
            x = int(x * scale_x)
            y = int(y * scale_y)
            cw = int(cw * scale_x)
            ch = int(ch * scale_y)

            # Draw red rectangle
            cv2.rectangle(
                uploaded_img,
                (x, y),
                (x + cw, y + ch),
                (0, 0, 255),  # RED in BGR
                2
            )

    # Add text label
    cv2.putText(
        uploaded_img,
        f"TAMPERED - SSIM: {score:.2f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        1,
        (0, 0, 255),
        2
    )

    # Save result
    cv2.imwrite(output_path, uploaded_img)

    return score, output_path