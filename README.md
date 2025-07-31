# receipt_ai_project
# 📄 Receipt AI Project

A **FastAPI-based API** for automating receipt data extraction using **Gemini AI**, `pdf2image`, and **Tesseract OCR**.  
Includes **Dockerized deployment** for easy setup.

---

## ✅ Features
- Extract text from **PDF receipts** using Poppler + `pdf2image`.
- Perform **OCR on images** using Tesseract.
- Integrate **Gemini AI** for advanced text processing.
- Fully **Dockerized** for portability.
- **FastAPI** for high-performance API endpoints.

---

## 🛠 Tech Stack
- **FastAPI** (Python 3.11)
- **pytesseract** (OCR engine)
- **pdf2image** (PDF to image conversion)
- **Google Gemini AI** SDK
- **Docker & Docker Compose**
- **Poppler + Tesseract OCR** (system dependencies)

---


---

## ⚙️ Setup & Installation

### **1. Clone the Repository**
```bash
git clone https://github.com/your-username/receipt_ai_project.git
cd receipt_ai_project


docker-compose up --build

http://localhost:8000/docs




✅ API Endpoints
POST /process_v5/{id}
Description: Extract text from a receipt (PDF or Image).

Payload: Upload file via multipart/form-data.

Response: Extracted text + AI-processed output.

http://localhost:8000/docs

🐳 Docker Details
Dockerfile
Installs:

poppler-utils (for pdf2image)

tesseract-ocr (for OCR)

Uses:

uvicorn for development

docker-compose.yml
Maps local files to container for hot reload.


✅ Dependencies
Install manually (if not using Docker):

sudo apt-get update && sudo apt-get install -y poppler-utils tesseract-ocr
pip install -r requirements.txt
