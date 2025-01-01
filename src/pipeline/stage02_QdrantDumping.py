import os
import json
from typing import List, Dict
from src.components.qdrantdumping import QdrantDumper
from dotenv import load_dotenv

load_dotenv()

artifacts_dir = os.getenv("SCRAPPED_DATA_DIRECTORY", "artifacts/ScrappedData")

qdrant_dumper = QdrantDumper(
    collection_name=os.getenv("QDRANT_COLLECTION_NAME"),
)

def load_scraped_data(directory: str) -> List[Dict]:
    documents = []
    for filename in os.listdir(directory):
        if filename.endswith(".json"):
            filepath = os.path.join(directory, filename)
            with open(filepath, "r", encoding="utf-8") as file:
                data = json.load(file)
                if isinstance(data, list):
                    documents.extend(data)
                else:
                    documents.append(data)
    return documents


def main():
    print("Starting Qdrant dumping process...")
    documents = load_scraped_data(artifacts_dir)
    print(f"Loaded {len(documents)} documents: {documents[:2]}")  
    if documents:
        print(f"Loaded {len(documents)} documents from {artifacts_dir}")
        qdrant_dumper.dump_documents(documents)
        print("All documents have been successfully dumped to Qdrant.")
    else:
        print("No documents found to dump.")


if __name__ == "__main__":
    main()
