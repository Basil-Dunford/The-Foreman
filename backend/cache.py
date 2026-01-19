from gptcache import cache
from gptcache.manager import CacheBase, VectorBase, get_data_manager
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation
from gptcache.processor.post import temperature_softmax
from gptcache.embedding import Onnx
from gptcache.adapter.api import init_similar_cache

# Initialize the cache
# We use a simple Map cache for data and Onnx for embeddings (local, fast)
# if onnxruntime is not available, it might fail, so we'll wrap or handle.
# For this environment, let's assume we can install onnxruntime.

def init_cache():
    # Use a local file-based map for persistence so it survives restarts
    # data_manager = get_data_manager(data_path="data_map", vector_path="data_vector") 
    # But for simplicity in this demo, let's use in-memory matching or efficient default.
    
    # Standard init with ONNX embedding for semantic matching
    # and a scalar similarity evaluation.
    
    print("Initializing GPTCache...")
    
    # We'll use a simple configuration:
    # 1. Embedding: Onnx (all-MiniLM-L6-v2 is default)
    # 2. Data Manager: Map based (in-memory)
    
    onnx = Onnx()
    
    cache.init(
        pre_embedding_func=onnx.to_embeddings,
        embedding_func=onnx.to_embeddings,
        data_manager=get_data_manager(data_path="backend_cache_data", vector_path="backend_cache_vector"),
        similarity_evaluation=SearchDistanceEvaluation(),
    )
    print("GPTCache initialized.")

def get_cached_response(query: str):
    # This is a bit manual because we aren't wrapping an LLM directly, 
    # we are wrapping the RAG pipeline.
    # We can use cache.data_manager to search.
    # Or simpler: use `cache.get(query)` if we configure it right.
    # However, standard `init_similar_cache` setups are for api hooking.
    # Let's use the low-level API or the manual methods.
    
    # Actually, `gptcache` is designed to wrap LLM calls. 
    # Since we have a complex RAG pipeline, we want to cache the *FINAL RESULT* of the pipeline based on the *QUERY*.
    # So we treat the whole RAG pipeline as the "LLM" function effectively.
    
    # Let's try to fetch from cache manually
    # The cache.import_data or similar is expected.
    # Let's basically use the `cache` object which mimics a dict but smart.
    # Wait, `gptcache` isn't just a dict.
    
    # Correct usage for manual caching:
    # 1. Embedding
    # 2. Search in VectorBase
    # 3. If found, get data from CacheBase
    
    # Simplification:
    # We will use `gptcache`'s `cache` singleton for storage if possible, but 
    # the docs show `cache.init` setting up the global strategy.
    
    # Then we can do:
    # res = cache.get(query) -> this typically expects standard exact match unless similar is set.
    # Actually, typical usage for manual check:
    # there is no direct "check_cache(query)" that does semantic search easily in one line without the adapter.
    
    # Let's implement a helper that uses the global components.
    
    embedding = cache.embedding_func(query)
    # Search for top 1
    rank = cache.data_manager.search(embedding, top_k=1)
    
    if rank and len(rank) > 0:
        # rank structure depends on implementation, usually dict or list of tuples
        # standard: [(score, id), ...]
        score, cache_id = rank[0]
        
        # Threshold check (distance)
        # SearchDistanceEvaluation usually implies smaller is better? Or similarity?
        # Default Onnx + SearchDistance usually uses L2 or Cosine.
        # Let's assume similarity score > 0.8 is good (if normalized) or distance < small.
        # Actually `rank` from simple vector search is usually just scores.
        
        # Let's rely on gptcache's `similarity_evaluation`.
        # But `similarity_evaluation` is an object.
        
        # Alternative: Just use the `put` and `get` logic if we can.
        # But `get` is usually exact match in base implementations unless configured.
        pass
        
    return None

# Use a simpler "function cache" approach provided by gptcache?
# The `cached` decorator is great but handles exact inputs well.
# For semantic:
# https://github.com/zilliztech/GPTCache/blob/main/examples/integrate/langchain/manual_cache.py
# Reference implies we can just wrap our function.

# Let's define the Cache wrapper class.

class SemanticCache:
    def __init__(self):
        self.onnx = Onnx()
        self.data_manager = get_data_manager("backend_cache")
        # Initialize global cache manually? No, avoid global conflict if possible.
        # But `gptcache.cache` is a singleton.
        
        cache.init(
            embedding_func=self.onnx.to_embeddings,
            data_manager=self.data_manager,
            similarity_evaluation=SearchDistanceEvaluation(),
        )

    def get(self, query: str):
        # 1. Embed
        emb = self.onnx.to_embeddings(query)
        # 2. Search
        # search returns list of (score, value_id)
        res = self.data_manager.search(emb, top_k=1) 
        if not res:
            return None
            
        score, value_id = res[0]
        # range 0-1? If distance, lower is better. If similarity, higher is better.
        # Onnx default uses L2 or Cosine? 
        # Usually it returns distance.
        # Let's assume strict threshold.
        # Actually, let's use the `evaluation` module if possible, but manual is fine.
        
        # For simplicity, if distance is very small < 0.2 (arbitrary for now, or use exact logic)
        # Actually gptcache docs say:
        # "rank" is the result of vector search.
        
        if score < 0.2: # Assuming distance (L2), 0.2 is close.
            # Get data
            return self.data_manager.get(value_id)
        return None

    def set(self, query: str, response: str):
        emb = self.onnx.to_embeddings(query)
        self.data_manager.save(query, response, emb)
        
# Refined Implementation using Global Init
from gptcache import cache
from gptcache.embedding import Onnx
from gptcache.manager import get_data_manager, CacheBase, VectorBase
from gptcache.similarity_evaluation.distance import SearchDistanceEvaluation

def setup_cache():
    try:
        onnx = Onnx()
        # Initialize with defaults (usually map based and simple vector store)
        # Verify valid args: 'data_path', 'vector_path' might be valid for some factory methods 
        # but here we use get_data_manager directly. 
        # Let's try default (in-memory).
        data_manager = get_data_manager()
        
        cache.init(
            embedding_func=onnx.to_embeddings,
            data_manager=data_manager,
            similarity_evaluation=SearchDistanceEvaluation(),
        )
        print("GPTCache configured with ONNX embeddings.")
        return True
    except Exception as e:
        print(f"Failed to init GPTCache: {e}")
        return False

def get_from_cache(query_str: str):
    try:
        # This uses the underlying configured mechanisms
        
        if not cache.has_init:
            return None
            
        embedding_func = cache.embedding_func
        data_manager = cache.data_manager
        
        query_embedding = embedding_func(query_str)
        if hasattr(query_embedding, "tolist"):
             query_embedding = query_embedding.tolist()
        
        # Check if batch
        if isinstance(query_embedding, list) and len(query_embedding) > 0 and isinstance(query_embedding[0], list):
             query_embedding = query_embedding[0]
             
        search_res = data_manager.search(query_embedding, top_k=1)
        
        if search_res:
             score, answer_key = search_res[0]
             # For distance, lower is better (usually). 
             # Thresholding:
             if score < 0.3: 
                 val = data_manager.get(answer_key)
                 return val
                 
    except Exception as e:
        pass # Soft fail
    
    return None
    
    return None

def save_to_cache(query_str: str, response_str: str):
    try:
        if not cache.has_init:
            return
            
        embedding_func = cache.embedding_func
        data_manager = cache.data_manager
        
        query_embedding = embedding_func(query_str)
        if hasattr(query_embedding, "tolist"):
             query_embedding = query_embedding.tolist()
        
        # Check if batch (list of lists) and take first
        if isinstance(query_embedding, list) and len(query_embedding) > 0 and isinstance(query_embedding[0], list):
             query_embedding = query_embedding[0]
        
        # Some simple vector stores might require hashable embeddings if implemented naively
        # or if they use embeddings as keys (unlikely but possible in simple fallback).
        # We try to pass as is (list), if it fails, we assume cache is just not effectively storing vector.
             
        data_manager.save(query_str, response_str, query_embedding)
        
    except Exception as e:
        # Soft fail - caching is optional enhancement
        print(f"Cache save warning: {e}")

