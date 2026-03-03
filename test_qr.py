import sys
import os

# Add qr_utils path
sys.path.append(os.path.join(os.path.dirname(__file__), "app", "utils"))

from qr_utils import extract_qr_from_image

# Use the correct full path to your certificate
certificate_path = r"C:\Users\ELCOT\Desktop\Certificate_verification_system\static\uploads\test_cert.jpeg"

result = extract_qr_from_image(certificate_path)
print("QR extraction result:")
print(result)