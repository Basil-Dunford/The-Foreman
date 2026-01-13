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

    # Get index (which wraps the remote vector store)
    index = get_index()

    # Insert documents into the index (handling chunking automatically via Settings default transformation)
    # LlamaIndex defaults: Chunk size 1024, chunk overlap 20
    # Note: For production, we might want custom splitters, but default is good for MVP.
 
    # Wait, insert_nodes expects nodes. simpler API is just index.insert implicitly or refreshing.
    # Actually, for VectorStoreIndex, we can just do:
    from llama_index.core.node_parser import SentenceSplitter
    
    parser = SentenceSplitter()
    nodes = parser.get_nodes_from_documents(documents)
    
    # Store nodes
    index.insert_nodes(nodes)
    
    return len(nodes)
