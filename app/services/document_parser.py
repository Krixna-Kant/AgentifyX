import fitz  

def extract_text_from_pdf(file_bytes: bytes) -> str:
    text = ""
    try:
        #Opening the PDF File directly from bytes using fitz (PyMuPDF)
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            for page_num in range(len(doc)):
                page = doc.load_page(page_num)
                # Extract text and if empty, it returns an empty string, preventing NoneType errors
                page_text = page.get_text() 
                if page_text:
                    text += page_text + "\n"
                    
        if not text.strip():
            raise ValueError("The PDF appears to be empty or contains only unreadable images.")
            
        return text
    except Exception as e:
        # Pass the specific error back up so we know what went wrong
        raise Exception(f"Failed to parse PDF: {str(e)}")