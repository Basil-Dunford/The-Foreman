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
# "Pro" for complex reasoning and risk analysis (Using Gemini Flash Latest for stability)
llm_pro = Gemini(model="models/gemini-flash-latest", api_key=GOOGLE_API_KEY)

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
        import concurrent.futures
        
        # 1. Define Search Functions
        def run_vector_search():
            params = {
                "query_embedding": query.query_embedding,
                "match_threshold": 0.01,
                "match_count": query.similarity_top_k or 5
            }
            return self.client.rpc("match_documents", params).execute()

        def run_keyword_search():
            # Use 'websearch' config for better English query parsing if available, else 'english'
            # .text_search is a Supabase-js/py helper.
            # We assume a 'plain' or 'phrase' type search depending on needs. 
            # 'websearch' is often best for natural language queries.
            import re
            # Sanitize query for basic tsquery (AND logic, remove punctuation)
            clean_query = re.sub(r'[^\w\s]', '', query.query_str)
            ts_query = " & ".join(clean_query.split())
            if not ts_query:
                # Fallback if query becomes empty (e.g. only symbols)
                ts_query = query.query_str
                
            return self.client.table("documents").select("*").limit(query.similarity_top_k or 5).text_search("content", ts_query).execute()

        # 2. Execute in Parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future_vec = executor.submit(run_vector_search)
            future_kw = executor.submit(run_keyword_search)
            
            vec_response = future_vec.result()
            kw_response = future_kw.result()

        # 3. Process Results for RRF
        # We need a unified dict to hold: {doc_id: {'node': node, 'vec_rank': X, 'kw_rank': Y}}
        
        candidates = {}

        # Process Vector Results
        for rank, record in enumerate(vec_response.data):
            doc_id = record["id"]
            if doc_id not in candidates:
                node = metadata_dict_to_node(record["metadata"])
                node.set_content(record["content"])
                node.node_id = doc_id
                candidates[doc_id] = {"node": node, "vec_rank": rank + 1, "kw_rank": 100} # 100 = default low rank
            else:
                 candidates[doc_id]["vec_rank"] = rank + 1

        # Process Keyword Results
        # Keyword results don't return similarity usually, but they are ranked by relevance
        for rank, record in enumerate(kw_response.data):
             doc_id = record["id"]
             if doc_id not in candidates:
                node = metadata_dict_to_node(record["metadata"])
                node.set_content(record["content"])
                node.node_id = doc_id
                # Fetch embedding if not present? 
                # Ideally we need embedding for the node if we want to return it fully populated,
                # but for search content it might be okay. 
                # The record usually has it if we selected "*".
                if "embedding" in record and record["embedding"]:
                    node.embedding = record["embedding"]
                    
                candidates[doc_id] = {"node": node, "vec_rank": 100, "kw_rank": rank + 1}
             else:
                candidates[doc_id]["kw_rank"] = rank + 1
        
        # 4. Compute RRF Score
        # Score = 1 / (k + rank)
        k = 60
        final_results = []
        for doc_id, data in candidates.items():
            rrf_score = (1 / (k + data["vec_rank"])) + (1 / (k + data["kw_rank"]))
            final_results.append((data["node"], rrf_score))
            
        # 5. Sort by RRF Score Descending
        final_results.sort(key=lambda x: x[1], reverse=True)
        
        # 6. Format Response
        nodes = []
        similarities = []
        ids = []
        
        # Limit to top_k again after fusion
        top_k = query.similarity_top_k or 5
        for node, score in final_results[:top_k]:
            nodes.append(node)
            similarities.append(score) # This is now RRF score, not cosine similarity
            ids.append(node.node_id)
            
        return VectorStoreQueryResult(nodes=nodes, similarities=similarities, ids=ids)

# Initialize Supabase Client globally
supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)

def get_vector_store():
    return CustomSupabaseVectorStore(client=supabase_client)

def get_index():
    vector_store = get_vector_store()
    storage_context = StorageContext.from_defaults(vector_store=vector_store)
    # Load index from vector store. If empty, it's just an empty index wrapper around the store.
    return VectorStoreIndex.from_vector_store(vector_store=vector_store, storage_context=storage_context)
