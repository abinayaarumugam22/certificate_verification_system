import qrcode
import json
import cv2
import numpy as np
from PIL import Image
import os

def generate_qr_code(data: dict, save_path: str) -> str:
    """
    Generate QR code from certificate data dict.
    Saves QR image to save_path.
    Returns the path of saved QR image.
    """
    # Convert dict to JSON string
    qr_content = json.dumps(data)

    # QR code configuration
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,  # High error correction
        box_size=10,
        border=4,
    )

    qr.add_data(qr_content)
    qr.make(fit=True)

    # Create QR image
    qr_image = qr.make_image(fill_color="black", back_color="white")

    # Save QR image
    qr_image.save(save_path)

    return save_path


def embed_qr_into_certificate(
    certificate_path: str,
    qr_path: str,
    output_path: str,
    position: str = "top-right"
) -> str:
    """
    Embed QR code into certificate image.
    Position: top-right (default, like real TN certificates)
    Returns path of final certificate with QR embedded.
    """
    # Open certificate
    cert = Image.open(certificate_path).convert("RGBA")
    cert_w, cert_h = cert.size

    # Open QR code and resize
    qr = Image.open(qr_path).convert("RGBA")
    qr_size = int(min(cert_w, cert_h) * 0.15)  # 15% of certificate size
    qr = qr.resize((qr_size, qr_size))

    # Determine position
    margin = 20
    if position == "top-right":
        x = cert_w - qr_size - margin
        y = margin
    elif position == "bottom-right":
        x = cert_w - qr_size - margin
        y = cert_h - qr_size - margin
    elif position == "bottom-left":
        x = margin
        y = cert_h - qr_size - margin
    else:
        x = cert_w - qr_size - margin
        y = margin

    # Paste QR onto certificate
    cert.paste(qr, (x, y), qr)

    # Save final image as RGB (JPEG compatible)
    final = cert.convert("RGB")
    final.save(output_path)

    return output_path


def extract_qr_from_image(image_path: str) -> dict | None:
    """
    Extract QR from certificate image using WeChatQRCode (preferred) 
    with fallback to standard OpenCV QRCodeDetector.
    """
    import cv2, json, numpy as np

    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    h, w = img.shape[:2]

    # Preprocess multiple regions
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    qr_crop = img[0:int(h*0.25), int(w*0.65):w]  # top-right corner
    qr_crop_3x = cv2.resize(qr_crop, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray_crop = cv2.cvtColor(qr_crop_3x, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray_crop, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    images_to_try = [img, gray, qr_crop, qr_crop_3x, gray_crop, thresh]

    # Method 1: WeChatQRCode (best)
    try:
        wechat = cv2.wechat_qrcode_WeChatQRCode()
        for test_img in images_to_try:
            try:
                data, _ = wechat.detectAndDecode(test_img)
                if data:
                    raw = data[0]
                    try:
                        return json.loads(raw)
                    except:
                        return {"raw": raw}
            except:
                continue
    except Exception:
        pass

    # Method 2: standard OpenCV QRCodeDetector
    detector = cv2.QRCodeDetector()
    for test_img in images_to_try:
        try:
            data, bbox, _ = detector.detectAndDecode(test_img)
            if data:
                try:
                    return json.loads(data)
                except:
                    return {"raw": data}
        except:
            continue

    return None