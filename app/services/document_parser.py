"""
Multimodal PDF extraction — PyMuPDF primary, Docling optional enhancement.
Extracts text, detects headings/tables, and sends image-heavy pages to Gemini Vision.
"""

import os
import re
import base64
import logging
import fitz  # PyMuPDF
from io import BytesIO

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# ── Gemini Vision setup ─────────────────────────────────────────────────────
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
_vision_model = genai.GenerativeModel("gemini-1.5-flash")

# ── Optional Docling import ─────────────────────────────────────────────────
try:
    from docling.document_converter import DocumentConverter  # type: ignore
    DOCLING_AVAILABLE = True
    logger.info("Docling is available — will use for enhanced table/heading extraction.")
except ImportError:
    DOCLING_AVAILABLE = False
    logger.info("Docling not installed — using PyMuPDF only.")


# ═════════════════════════════════════════════════════════════════════════════
#  Public API
# ═════════════════════════════════════════════════════════════════════════════

def extract_structured_pages(file_bytes: bytes) -> list[dict]:
    """
    Parse a PDF and return a list of structured page-dicts.

    Each dict has keys:
        text          – extracted text for that page
        page_number   – 1-indexed page number
        content_type  – "text" | "table" | "heading" | "image_description"
        section_title – nearest heading (best-effort)
        has_images    – bool, whether page contains image blocks
    """
    pages: list[dict] = []

    try:
        with fitz.open(stream=file_bytes, filetype="pdf") as doc:
            current_heading = ""

            for page_idx in range(len(doc)):
                page = doc.load_page(page_idx)
                page_num = page_idx + 1

                # ── Text blocks with structure ──────────────────────────
                blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
                page_text_parts: list[str] = []

                for block in blocks:
                    if block["type"] != 0:  # skip image blocks in text pass
                        continue
                    for line in block.get("lines", []):
                        line_text = "".join(span["text"] for span in line.get("spans", []))
                        if not line_text.strip():
                            continue

                        # Detect headings by font size (>= 14pt) or bold weight
                        spans = line.get("spans", [])
                        if spans:
                            avg_size = sum(s.get("size", 12) for s in spans) / len(spans)
                            is_bold = any("bold" in s.get("font", "").lower() for s in spans)
                            if avg_size >= 14 or (is_bold and avg_size >= 12):
                                current_heading = line_text.strip()
                                pages.append({
                                    "text": current_heading,
                                    "page_number": page_num,
                                    "content_type": "heading",
                                    "section_title": current_heading,
                                    "has_images": False,
                                })

                        page_text_parts.append(line_text)

                full_text = "\n".join(page_text_parts).strip()

                # ── Detect tables (heuristic: lines with multiple tab/pipe separators) ──
                table_text, body_text = _split_tables(full_text)
                if table_text:
                    pages.append({
                        "text": table_text,
                        "page_number": page_num,
                        "content_type": "table",
                        "section_title": current_heading,
                        "has_images": False,
                    })

                if body_text.strip():
                    pages.append({
                        "text": body_text,
                        "page_number": page_num,
                        "content_type": "text",
                        "section_title": current_heading,
                        "has_images": False,
                    })

                # ── Image detection + Gemini Vision ─────────────────────
                image_list = page.get_images(full=True)
                if image_list:
                    try:
                        description = _describe_page_images(page, page_num)
                        if description:
                            pages.append({
                                "text": description,
                                "page_number": page_num,
                                "content_type": "image_description",
                                "section_title": current_heading,
                                "has_images": True,
                            })
                    except Exception as img_err:
                        logger.warning(
                            "Gemini Vision failed for page %d: %s", page_num, img_err
                        )

    except Exception as e:
        raise Exception(f"Failed to parse PDF: {e}") from e

    if not pages:
        raise ValueError("The PDF appears to be empty or contains only unreadable content.")

    return pages


# For backward-compat: legacy callers that expect a plain string
def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Legacy wrapper — returns concatenated text from all pages."""
    pages = extract_structured_pages(file_bytes)
    return "\n\n".join(p["text"] for p in pages if p["content_type"] != "image_description")


# ═════════════════════════════════════════════════════════════════════════════
#  Internal helpers
# ═════════════════════════════════════════════════════════════════════════════

def _split_tables(text: str) -> tuple[str, str]:
    """
    Heuristic split: lines that look tabular (contain | or lots of whitespace
    separating >=3 columns) are pulled into table_text; the rest stays as body.
    """
    table_lines: list[str] = []
    body_lines: list[str] = []

    for line in text.split("\n"):
        stripped = line.strip()
        if "|" in stripped or len(re.findall(r"\s{3,}", stripped)) >= 2:
            table_lines.append(stripped)
        else:
            body_lines.append(line)

    return "\n".join(table_lines), "\n".join(body_lines)


def _describe_page_images(page: fitz.Page, page_num: int) -> str:
    """Render a page to an image and ask Gemini Vision to describe it."""
    pix = page.get_pixmap(dpi=150)
    img_bytes = pix.tobytes("png")

    # Build the Gemini Vision request
    import PIL.Image
    img = PIL.Image.open(BytesIO(img_bytes))

    prompt = (
        "Describe this diagram/image in detail. "
        "What system, workflow, or architecture does it show? "
        "Extract any text visible in it. "
        "Be concise but thorough."
    )

    response = _vision_model.generate_content([prompt, img])
    return response.text.strip() if response.text else ""