import os
import shutil
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
import json
from llama_index.core.vector_stores.types import MetadataFilters, ExactMatchFilter
from backend.models import IngestResponse, QueryRequest, QueryResponse, RiskScoutRequest, RiskScoutResponse
from backend.ingestion import ingest_document
from backend.rag_engine import get_index, llm_flash
from backend.risk_scouter import analyze_risk

app = FastAPI(title="The Foreman API")

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, replace ["*"] with your Streamlit URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.post("/query")
async def query_index(request: QueryRequest):
    try:
        index = get_index()
        
        # Build Metadata Filters
        filters = []
        if request.filters:
            if request.filters.facility_type:
                for f_type in request.filters.facility_type:
                    filters.append(ExactMatchFilter(key="facility_type", value=f_type))
            if request.filters.project_year:
                for year in request.filters.project_year:
                    filters.append(ExactMatchFilter(key="project_year", value=year))
        
        metadata_filters = MetadataFilters(filters=filters) if filters else None
        
        # Use Flash for standard semantic search queries (faster, sufficient for retrieval synthesis)
        query_engine = index.as_query_engine(
            similarity_top_k=request.top_k, 
            llm=llm_flash,
            streaming=True,
            filters=metadata_filters
        )
        
        def stream_generator():
            # Initial status
            yield json.dumps({"type": "status", "content": "Reading Project Docs..."}) + "\n"
            
            response = query_engine.query(request.query)
            
            # Stream the answer tokens
            for text in response.response_gen:
                yield json.dumps({"type": "answer", "content": text}) + "\n"
            
            # Stream the sources at the end
            sources = [
                {
                    "content": node.node.get_content(),
                    "metadata": node.node.metadata,
                    "score": node.score
                }
                for node in response.source_nodes
            ]
            yield json.dumps({"type": "source", "content": sources}) + "\n"

        return StreamingResponse(stream_generator(), media_type="application/x-ndjson")
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
