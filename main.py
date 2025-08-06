from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from Pipeline.rag_chain import rag_chain
from PIL import Image
import pytesseract
import pdfplumber
import io

app = FastAPI()

# ✅ Root route for Ngrok base URL access
@app.get("/")
def read_root():
    return {"message": "Welcome to FlashQuery! Use the frontend UI to interact."}

# ✅ Enable frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str
    context: str | None = None

# ✅ Global variable to store extracted PDF content
pdf_text = ""

# ✅ PDF Upload Endpoint
@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global pdf_text
    extracted = ""

    try:
        contents = await file.read()
        with pdfplumber.open(io.BytesIO(contents)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text and text.strip():
                    extracted += text + "\n"
                else:
                    image = page.to_image(resolution=300).original
                    text_ocr = pytesseract.image_to_string(image)
                    if text_ocr.strip():
                        extracted += text_ocr + "\n"

        if not extracted.strip():
            return {
                "error": "❌ PDF seems empty or unreadable.",
                "extracted_text": ""
            }

    except Exception as e:
        return {
            "error": f"❌ Failed to extract PDF: {str(e)}",
            "extracted_text": ""
        }

    pdf_text = extracted.strip()
    rag_chain.load_pdf_text(pdf_text)

    return {
        "message": "✅ PDF uploaded and processed successfully.",
        "extracted_text": pdf_text[:1500]
    }

# ✅ Ask endpoint for model interaction
@app.post("/ask")
async def ask_question(request: QueryRequest):
    answer = rag_chain.run(request.question, request.context)
    return {"answer": answer}