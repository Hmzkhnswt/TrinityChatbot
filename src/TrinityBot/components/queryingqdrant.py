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
            {
                "role": "system",
                "content": (
                    "You are a knowledgeable assistant specializing in Web3, blockchain, cryptocurrencies, tokens, and related topics. "
                    "You provide clear, short, concise, to the point and human-like answers tailored to the user's query. "
                    "Do not use phrases like 'according to the context' or 'based on my knowledge'; instead, provide direct and informative answers. "
                    "Focus solely on the information available in the context, and avoid unnecessary speculation or verbose explanations. "
                    "Your goal is to educate and assist users in understanding blockchain and cryptocurrency topics."
                )
            },
            {
                "role": "user",
                "content": f"Context:\n{context}\n\nQuestion: {query}\n\nProvide a clear and precise answer based solely on the provided context."
            }
        ]
        
        response = self.openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=150,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
