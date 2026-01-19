import os
from llama_index.core import SimpleDirectoryReader
from backend.rag_engine import get_index

def ingest_document(file_path: str):
    """
    Ingests a single document into the Supabase vector store.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load data
    reader = SimpleDirectoryReader(input_files=[file_path])
    documents = reader.load_data()

    # Metadata Extraction
    hutton_metadata = get_hutton_metadata(file_path)
    print(f"DEBUG: Extracted Metadata: {hutton_metadata}")
    
    # Dynamic Chunking Strategy
    # Spec documents get smaller chunks for precision
    chunk_size = 512
    if hutton_metadata["document_type"] == "Technical Spec":
        chunk_size = 256
        
    chunk_overlap = 50 # maintain context
    
    from llama_index.core.node_parser import SentenceSplitter
    
    parser = SentenceSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    nodes = parser.get_nodes_from_documents(documents)
    
    # Enrich nodes with metadata
    for node in nodes:
        node.metadata.update(hutton_metadata)
        
    # Verification: Print first 5 chunks
    print("\n--- CHUNK VERIFICATION (First 5) ---")
    for i, node in enumerate(nodes[:5]):
        print(f"Chunk {i+1} (Size: {len(node.get_content())} chars) | Metadata: {node.metadata}")
        print(f"Preview: {node.get_content()[:100]}...")
        print("-" * 50)
    print("------------------------------------\n")
    
    # Store nodes
    index = get_index()
    index.insert_nodes(nodes)
    
    return len(nodes)

def get_hutton_metadata(file_path: str) -> dict:
    """
    Extracts metadata from filename/path using simple rules (MVP).
    In production, this would use an LLM for classification.
    """
    filename = os.path.basename(file_path).lower()
    
    # 1. Project Year
    # Basic regex-like check for years 2010-2025
    year = 2023 # Default
    for y in range(2010, 2026):
        if str(y) in filename:
            year = y
            break
            
    # 2. Document Type
    doc_type = "General"
    if "safety" in filename or "log" in filename:
        doc_type = "Safety Log"
    elif "spec" in filename or "technical" in filename:
        doc_type = "Technical Spec"
    elif "closeout" in filename:
        doc_type = "Closeout"
        
    # 3. Facility Type
    # Random extraction for MVP, logic could be expanded
    facility_type = "Commercial" # Default
    if "hosp" in filename or "med" in filename or "clinic" in filename:
        facility_type = "Healthcare"
    elif "fact" in filename or "ind" in filename or "plant" in filename:
        facility_type = "Industrial"
        
    return {
        "project_year": year,
        "facility_type": facility_type,
        "document_type": doc_type
    }
