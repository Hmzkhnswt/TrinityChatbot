from fastapi import APIRouter, HTTPException
from qdrant_client.models import Filter
from qdrant_client import QdrantClient
from openai import OpenAI
import os
from dotenv import load_dotenv
load_dotenv()


class Chatbot:
    def __init__(self, collection_name: str, embedding_model: str = "text-embedding-ada-002"):
        self.qdrant_client = QdrantClient(
            url=os.getenv("QDRANT_URL"),
            api_key=os.getenv("QDRANT_API_KEY")
        )
        self.collection_name = collection_name
        self.embedding_model = embedding_model
        self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    def _get_embeddings(self, query: str):
        response = self.openai_client.embeddings.create(
            model=self.embedding_model, input=[query]
        )
        return response.data[0].embedding

    def search_qdrant(self, query: str, top_k: int = 5):
        embedding = self._get_embeddings(query)
        results = self.qdrant_client.search(
            collection_name=self.collection_name,
            query_vector=embedding,
            limit=top_k
        )
        return results

    def generate_response(self, query: str, documents: list):
        context = "\n".join([doc.payload.get("content", "") for doc in documents])
        messages = [
            {"role": "system", "content": "You are a helpful assistant that provides short, concise answers based own your knowledge . Focus only on information present in the context and avoid speculation."},
            {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}\n\nProvide a brief, focused answer based solely on the context provided."}
        ]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()