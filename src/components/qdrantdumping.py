import os
import uuid
import logging
from typing import List, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct
import pdfplumber
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class QdrantDumper:
    def __init__(self, collection_name: str, embedding_model: str = "text-embedding-ada-002"):
        self.collection_name = collection_name
        self.embedding_model = embedding_model

        qdrant_url = os.getenv("QDRANT_URL")
        qdrant_api_key = os.getenv("QDRANT_API_KEY")
        self.qdrant_client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)

        self.text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)

        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        self._ensure_collection_exists()

    def _ensure_collection_exists(self):
        try:
            collection_info = self.qdrant_client.get_collection(self.collection_name)
            self.logger.info(f"Collection `{self.collection_name}` already exists.")
        except Exception:
            self.logger.info(f"Collection `{self.collection_name}` not found. Creating it now.")
            self.qdrant_client.recreate_collection(
                collection_name=self.collection_name,
                vectors_config={"size": 1536, "distance": "Cosine"}
            )

    def _get_embeddings(self, texts):
        response = client.embeddings.create(model=self.embedding_model, input=texts)
        return [data.embedding for data in response.data]
    

    def dump_documents(self, documents: List[Dict]):
        for document in documents:
            try:
                content = document.get("page_content")
                metadata = document.get("metadata", {})
                document_id = metadata.get("_id")
                token = metadata.get("token")
                source = metadata.get("source")

                if not content or not document_id or not token or not source:
                    self.logger.warning(f"Skipping document due to missing required fields: {document}")
                    continue

                payload = {
                    "id": document_id,
                    "content": content,
                    "token": token,
                    "source": source
                }

                embedding = self._get_embeddings([content])[0]

                point = PointStruct(
                    id=document_id,  
                    vector=embedding,
                    payload=payload
                )

                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )

                self.logger.info(f"Inserted document with ID: {document_id}")
            except Exception as e:
                self.logger.error(f"Error inserting document: {str(e)}")

    def dump_pdf(self, pdf_path, token):
        try:
            documents = []
            with pdfplumber.open(pdf_path) as pdf:
                for page_number, page in enumerate(pdf.pages, start=1):
                    text = page.extract_text() or ""
                    text = " ".join(text.split())
                    metadata = {
                        "_id": str(uuid.uuid4()),
                        "source": os.path.basename(pdf_path),
                        "page": page_number,
                        "token": token,
                    }

                    chunks = self.text_splitter.split_text(text)
                    for chunk in chunks:
                        documents.append(Document(page_content=chunk, metadata=metadata))

            for document in documents:
                embedding = self._get_embeddings([document.page_content])[0]
                payload = {
                    "_id": document.metadata["_id"],
                    "source": document.metadata["source"],
                    "page": document.metadata["page"],
                    "token": document.metadata["token"],
                    "content": document.page_content, 
                }
                point = PointStruct(
                    id=document.metadata["_id"],
                    vector=embedding,
                    payload=payload
                )
                self.qdrant_client.upsert(
                    collection_name=self.collection_name,
                    points=[point]
                )
                self.logger.info(f"Inserted chunk with ID: {document.metadata['_id']}")

            return {"message": "PDF processed and inserted into Qdrant successfully."}
        except Exception as e:
            self.logger.error(f"Error processing PDF: {str(e)}")
            return {"message": f"Error processing PDF: {str(e)}"}
