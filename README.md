# TN Certificate Verification System

A hybrid image hash based certificate verification system 
for Tamil Nadu State Board academic certificates.

## Tech Stack
- Python 3.10+
- FastAPI
- PostgreSQL
- OpenCV, Pillow, imagehash
- scikit-image (SSIM)
- JWT Authentication

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/certificate-verification.git
cd certificate-verification
```

### 2. Create Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # Mac/Linux
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Create PostgreSQL Database
```sql
CREATE DATABASE certificate_db;
```

### 5. Create .env File
```env
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/certificate_db
SECRET_KEY=yoursecretkey123
UPLOAD_DIR=static/uploads
QR_DIR=static/qrcodes
```

### 6. Run Server
```bash
uvicorn main:app --reload
```

### 7. Open Browser
```
http://localhost:8000
```

## User Roles
| Role | Access |
|------|--------|
| Institution | Upload & register certificates |
| Student | View own certificate |
| Verifier | Verify certificate authenticity |
| Admin | Monitor all activity |

## Verification Logic
1. SHA-256 exact match → VALID
2. pHash distance ≤ 10 → VALID (rescan)
3. SSIM ≥ 0.85 → POSSIBLY VALID
4. SSIM < 0.85 → TAMPERED (with highlighted image)