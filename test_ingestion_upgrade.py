import os
from backend.ingestion import ingest_document

def create_dummy_file(filename, content):
    with open(filename, "w") as f:
        f.write(content * 100) # Make it long enough to chunk

def test_ingestion():
    # 1. Tech Spec (2024, Industrial) -> Should be chunk_size 256
    file1 = "test_data/2024_Spec_Industrial_Safety.txt"
    create_dummy_file(file1, "This is a technical specification for an industrial facility. " * 50)
    
    # 2. Daily Log (2021, Healthcare) -> Should be chunk_size 512
    file2 = "test_data/2021_Hosp_Daily_Log.txt"
    create_dummy_file(file2, "This is a daily log report for the healthcare wing construction. " * 50)
    
    print(f"--- Ingesting {file1} ---")
    try:
        ingest_document(file1)
    except Exception as e:
        print(f"Error ingesting {file1}: {e}")

    print(f"\n--- Ingesting {file2} ---")
    try:
        ingest_document(file2)
    except Exception as e:
        print(f"Error ingesting {file2}: {e}")

    # Cleanup
    if os.path.exists(file1): os.remove(file1)
    if os.path.exists(file2): os.remove(file2)

if __name__ == "__main__":
    if not os.path.exists("test_data"):
        os.makedirs("test_data")
    test_ingestion()
