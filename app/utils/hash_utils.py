import hashlib
import cv2
import numpy as np
import imagehash
from PIL import Image

def normalize_image(image_path: str) -> np.ndarray:
    """
    Normalize image before hashing:
    - Convert to grayscale
    - Resize to fixed 512x512
    - Apply slight blur to reduce noise
    """
    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(f"Cannot read image at path: {image_path}")

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize to fixed dimension
    resized = cv2.resize(gray, (512, 512))

    # Apply slight blur for noise reduction
    blurred = cv2.GaussianBlur(resized, (3, 3), 0)

    return blurred


def generate_sha256(image_path: str) -> str:
    """
    Generate SHA-256 hash from normalized image.
    Used for EXACT integrity check.
    """
    normalized = normalize_image(image_path)

    # Convert numpy array to bytes
    img_bytes = normalized.tobytes()

    # Generate SHA-256
    sha256 = hashlib.sha256(img_bytes).hexdigest()

    return sha256


def generate_phash(image_path: str) -> str:
    """
    Generate Perceptual Hash (pHash).
    Used for SIMILARITY check (handles rescans, minor quality changes).
    """
    # Open with PIL for imagehash
    img = Image.open(image_path).convert("L")  # L = grayscale

    # Resize to 512x512 for consistency
    img = img.resize((512, 512))

    # Generate perceptual hash
    phash = imagehash.phash(img)

    return str(phash)


def hamming_distance(hash1: str, hash2: str) -> int:
    """
    Calculate Hamming distance between two pHash strings.
    Lower distance = more similar images.
    Threshold: 0-10 = same, 10-20 = minor changes, 20+ = tampered
    """
    # Convert hex strings to imagehash objects
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)

    return h1 - h2  # imagehash subtraction = hamming distance