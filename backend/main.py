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
from backend.cache import setup_cache, get_from_cache, save_to_cache
import asyncio

# Initialize Cache on Startup
setup_cache()

app = FastAPI(title="The Foreman API")

from fastapi.middleware.cors import CORSMiddleware

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
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
        # 1. Check Cache
        cached_result = get_from_cache(request.query)
        if cached_result:
            print("CACHE HIT")
            # If cached, we need to yield it in the expected format
            def stream_cached():
                yield json.dumps({"type": "status", "content": "Found in Cache..."}) + "\n"
                # We stored the whole response text, so we can yield it
                # Logic depends on what we stored. Let's assume we stored a JSON or just text.
                # If we stored just text answer, we might miss sources.
                # Ideally, we should cache a JSON string containing answer + sources.
                
                try:
                    data = json.loads(cached_result)
                    answer = data.get("answer", "")
                    sources = data.get("sources", [])
                except:
                    # Fallback if simple string
                    answer = cached_result
                    sources = []

                yield json.dumps({"type": "answer", "content": answer}) + "\n"
                yield json.dumps({"type": "source", "content": sources}) + "\n"

            return StreamingResponse(stream_cached(), media_type="application/x-ndjson")

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
        
        async def stream_generator():
            # Initial status
            yield json.dumps({"type": "status", "content": "Reading Project Docs..."}) + "\n"
            
            response = query_engine.query(request.query)
            
            full_answer_text = ""
            
            # Stream the answer tokens
            for text in response.response_gen:
                full_answer_text += text
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
            
            # Save to Cache
            # We cache a JSON object with answer and sources to reconstruct the full response
            cache_payload = json.dumps({
                "answer": full_answer_text,
                "sources": sources
            })
            save_to_cache(request.query, cache_payload)

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
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
