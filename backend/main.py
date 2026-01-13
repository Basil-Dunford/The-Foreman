import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from backend.models import IngestResponse, QueryRequest, QueryResponse, RiskScoutRequest, RiskScoutResponse
from backend.ingestion import ingest_document
from backend.rag_engine import get_index, llm_flash
from backend.risk_scouter import analyze_risk

app = FastAPI(title="The Foreman API")

UPLOAD_DIR = "temp_uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/ingest", response_model=IngestResponse)
async def ingest_file(file: UploadFile = File(...)):
    file_location = f"{UPLOAD_DIR}/{file.filename}"
    try:
        with open(file_location, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        num_chunks = ingest_document(file_location)
        
        # Cleanup
        os.remove(file_location)
        
        return IngestResponse(
            filename=file.filename,
            chunks_processed=num_chunks,
            status="Success"
        )
    except Exception as e:
        if os.path.exists(file_location):
            os.remove(file_location)
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=QueryResponse)
async def query_index(request: QueryRequest):
    try:
        index = get_index()
        # Use Flash for standard semantic search queries (faster, sufficient for retrieval synthesis)
        query_engine = index.as_query_engine(similarity_top_k=request.top_k, llm=llm_flash)
        response = query_engine.query(request.query)
        
        return QueryResponse(
            answer=str(response),
            source_nodes=[node.node.get_content()[:200] + "..." for node in response.source_nodes]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/risk-scout", response_model=RiskScoutResponse)
async def risk_scout(request: RiskScoutRequest):
    try:
        result = analyze_risk(request.project_description)
        return RiskScoutResponse(
            analysis=result["analysis"],
            relevant_past_projects=result["relevant_past_projects"],
            risk_flags=result["risk_flags"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
