import pdfplumber
import base64
import os

def extract_text_from_image_via_groq(filepath):
    """Uses Groq vision model to extract and describe text from an image."""
    import requests
    from dotenv import load_dotenv
    
    # Force load .env from the root directory
    basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    load_dotenv(os.path.join(basedir, '.env'), override=True)
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "Error: GROQ_API_KEY not set."

    with open(filepath, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    ext = filepath.split('.')[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "bmp": "image/bmp", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/png")

    payload = {
        "model": "meta-llama/llama-4-scout-17b-16e-instruct",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{mime_type};base64,{image_data}"}
                    },
                    {
                        "type": "text",
                        "text": "Please extract and transcribe ALL the text visible in this image exactly as it appears. This appears to be a legal document. Extract every word, number, name, date, and detail carefully."
                    }
                ]
            }
        ],
        "max_tokens": 2048
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    response = requests.post("https://api.groq.com/openai/v1/chat/completions", json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()["choices"][0]["message"]["content"]
    else:
        return f"Error from Groq Vision API: {response.text}"


def extract_text_from_file(filepath):
    """Extracts text from PDF, Image, or Text files."""
    ext = filepath.split('.')[-1].lower()

    try:
        if ext == 'pdf':
            text = ""
            with pdfplumber.open(filepath) as pdf:
                for page in pdf.pages:
                    extracted = page.extract_text()
                    if extracted:
                        text += extracted + "\n"
            return text.strip() if text.strip() else "No readable text found in PDF pages."

        elif ext in ['jpg', 'jpeg', 'png', 'bmp', 'webp']:
            # Use Groq Vision — no Tesseract needed
            return extract_text_from_image_via_groq(filepath)

        elif ext == 'txt':
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read().strip()

        else:
            return f"Unsupported file type: .{ext}. Please upload a PDF, PNG, JPG, or TXT file."

    except Exception as e:
        return f"Error extracting text from {ext}: {str(e)}"
