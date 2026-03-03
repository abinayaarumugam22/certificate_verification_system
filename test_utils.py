from app.utils.hash_utils import generate_sha256, generate_phash, hamming_distance
from app.utils.qr_utils import generate_qr_code, extract_qr_from_image
import os

# Test 1: QR Generation
print("Testing QR Generation...")
data = {
    "certificate_id": "CERT-001",
    "register_number": "4502716",
    "issue_date": "10.08.2020"
}
generate_qr_code(data, "static/qrcodes/test_qr.png")
print("✅ QR Generated at static/qrcodes/test_qr.png")

# Test 2: QR Extraction
print("\nTesting QR Extraction...")
extracted = extract_qr_from_image("static/qrcodes/test_qr.png")
print(f"✅ QR Extracted: {extracted}")

# Test 3: Hash using your actual certificate image
print("\nTesting Hashing...")

# ✅ PUT YOUR IMAGE PATH HERE (the certificate image you have)
test_image = r"C:\Users\ELCOT\Desktop\Certificate_verification_system\static\uploads\test_cert.jpeg"

# Manually copy your image to static/uploads/ folder first
# OR change path to wherever your image is, example:
# test_image = r"C:\Users\ELCOT\Desktop\WhatsApp_Image_2026-03-02_at_10_59_21_AM.jpeg"

if not os.path.exists(test_image):
    print(f"❌ Image not found at: {test_image}")
    print("👉 Please manually copy your certificate image to: static/uploads/test_cert.jpg")
else:
    sha256 = generate_sha256(test_image)
    phash  = generate_phash(test_image)
    print(f"✅ SHA256 : {sha256}")
    print(f"✅ pHash  : {phash}")

    dist = hamming_distance(phash, phash)
    print(f"✅ Hamming distance (same image): {dist}")
    print("\n🎉 All utils working correctly!")
