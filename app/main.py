from fastapi import FastAPI, UploadFile, File, HTTPException, Response # <-- Add Response
from app.services.document_parser import extract_text_from_pdf
from app.services.semantic_pipeline import chunk_text, store_embeddings
from app.services.llm_engine import generate_agentic_blueprint
from app.services.code_generator import generate_crewai_script # <-- New import
import traceback

app = FastAPI(
    title="AgentifyX Middleware",
    description="API for transforming conventional solutions into Agentic AI frameworks.",
    version="1.0.0"
)

@app.post("/api/v1/process-document")
async def process_document(file: UploadFile = File(...)):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Currently, only PDF files are supported.")
    
    try:
        # Phase 1: Parsing
        contents = await file.read()
        raw_text = extract_text_from_pdf(contents)
        
        #Phase 2: Vectorize
        text_chunks = chunk_text(raw_text)
        chunks_stored = store_embeddings(file.filename, text_chunks)
        
        # Phase 3: Reason & Generate Blueprint
        blueprint = generate_agentic_blueprint(file.filename)
        
        return {
            "filename": file.filename,
            "status": "success",
            "pipeline_metrics": {
                "chunks_stored": chunks_stored
            },
            "Agent Architecture File": "Successfully generated! Use the /download-blueprint endpoint to get the Python code.",
            "agentifyx_analysis": blueprint  
        }
        
    except Exception as e:
        print("=== ERROR ===")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/api/v1/download-blueprint")
async def download_blueprint(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        raw_text = extract_text_from_pdf(contents)
        text_chunks = chunk_text(raw_text)
        store_embeddings(file.filename, text_chunks)
        blueprint_json_str = generate_agentic_blueprint(file.filename)

        python_code = generate_crewai_script(blueprint_json_str)

        return Response(
            content=python_code,
            media_type="text/x-python",
            headers={"Content-Disposition": 'attachment; filename="agentic_architecture.py"'}
        )
        
    except Exception as e:
        print("=== ERROR ===")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))