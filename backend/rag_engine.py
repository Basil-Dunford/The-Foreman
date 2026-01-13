import os
from dotenv import load_dotenv
from llama_index.core import VectorStoreIndex, StorageContext, Settings
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini
from typing import List, Any, Optional
from llama_index.core.vector_stores.types import (
    BasePydanticVectorStore,
    VectorStoreQuery,
    VectorStoreQueryResult,
)
from llama_index.core.schema import NodeWithScore, TextNode
from llama_index.core.vector_stores.utils import node_to_metadata_dict, metadata_dict_to_node
from supabase import create_client
from pydantic import ConfigDict, PrivateAttr

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

if not all([SUPABASE_URL, SUPABASE_KEY, GOOGLE_API_KEY]):
    raise ValueError("Missing environment variables. Check .env file.")

# Setup Gemini Models
# "Flash" for fast, standard retrieval-based queries
llm_flash = Gemini(model="models/gemini-3-flash-preview", api_key=GOOGLE_API_KEY)
# "Pro" for complex reasoning and risk analysis (Using Gemini 2.0 Flash for stability/quota)
llm_pro = Gemini(model="models/gemini-2.0-flash", api_key=GOOGLE_API_KEY)

# Default embedding model (The actual "Retrieval" engine)
gemini_embedding_model = GeminiEmbedding(model_name="models/text-embedding-004", api_key=GOOGLE_API_KEY)
Settings.embedding = gemini_embedding_model
Settings.embed_model = gemini_embedding_model
Settings.llm = llm_flash

class CustomSupabaseVectorStore(BasePydanticVectorStore):
    stores_text: bool = True
    _client: Any = PrivateAttr()
    
    model_config = ConfigDict(arbitrary_types_allowed=True)
    
    def __init__(self, client: Any, **kwargs: Any):
        super().__init__(**kwargs)
        self._client = client
    
    @property
    def client(self) -> Any:
        return self._client

    def add(self, nodes: List[TextNode], **kwargs: Any) -> List[str]:
        rows = []
        for node in nodes:
            rows.append({
                "id": node.node_id,
                "content": node.get_content(metadata_mode="all"),
                "metadata": node_to_metadata_dict(node),
                "embedding": node.embedding,
            })
        
        if rows:
            self.client.table("documents").upsert(rows).execute()
        return [node.node_id for node in nodes]

    def delete(self, ref_doc_id: str, **kwargs: Any) -> None:
        self.client.table("documents").delete().eq("metadata->>ref_doc_id", ref_doc_id).execute()

    def query(self, query: VectorStoreQuery, **kwargs: Any) -> VectorStoreQueryResult:
        params = {
            "query_embedding": query.query_embedding,
            "match_threshold": 0.01, # Set permissive threshold to ensure results
            "match_count": query.similarity_top_k or 5
        }
        response = self.client.rpc("match_documents", params).execute()
        
        nodes = []
        similarities = []
        ids = []
        
        for record in response.data:
            node = metadata_dict_to_node(record["metadata"])
            node.set_content(record["content"])
            node.node_id = record["id"]
            
            nodes.append(node)
            similarities.append(record["similarity"])
            ids.append(record["id"])
            
        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

def get_vector_store():
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return CustomSupabaseVectorStore(client=supabase_client)

def get_index():
    vector_store = get_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Load index from vector store. If empty, it's just an empty index wrapper around the store.
    return VectorStoreIndex.from_vector_store(vector_store=vector_store, storage_context=storage_context)
