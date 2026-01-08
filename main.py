import io
import os
import uvicorn
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from fastapi import FastAPI, Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from llama_cpp import Llama
from huggingface_hub import hf_hub_download
from contextlib import asynccontextmanager

# --- Global Handler ---
llm = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global llm
    print("🚀 Local Engine Starting...")
    # This downloads the AI model to your computer automatically
    model_path = hf_hub_download(
        repo_id="bartowski/SmolLM2-135M-Instruct-GGUF", 
        filename="SmolLM2-135M-Instruct-Q8_0.gguf"
    )
    llm = Llama(model_path=model_path, n_ctx=2048)
    yield

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

def deep_document_parse(file_bytes, extension):
    text_content = []
    if extension == ".pdf":
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        for page in doc:
            page_text = page.get_text().strip()
            if len(page_text) < 50:
                pix = page.get_pixmap(dpi=300)
                img = Image.open(io.BytesIO(pix.tobytes("png")))
                page_text = pytesseract.image_to_string(img)
            text_content.append(page_text)
    elif extension in [".png", ".jpg", ".jpeg"]:
        img = Image.open(io.BytesIO(file_bytes))
        text_content.append(pytesseract.image_to_string(img))
    return "\n\n".join(text_content)

@app.get("/")
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/process-file")
async def process_file(file: UploadFile = File(...)):
    file_bytes = await file.read()
    ext = "." + file.filename.split(".")[-1].lower()
    return {"extracted_text": deep_document_parse(file_bytes, ext)}

@app.post("/generate")
async def generate(request: Request):
    data = await request.json()
    prompt = f"<|im_start|>user\n{data['topic']}<|im_end|>\n<|im_start|>assistant\n"
    response = llm(prompt, max_tokens=500)
    return {"result": response["choices"][0]["text"]}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)