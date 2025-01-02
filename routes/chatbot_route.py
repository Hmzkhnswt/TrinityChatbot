import os
from fastapi import APIRouter, HTTPException
from TrinityBot.components.queryingqdrant import Chatbot
from dotenv import load_dotenv
load_dotenv()

collection_name = os.getenv("QDRANT_COLLECTION_NAME")

router = APIRouter()

chatbot = Chatbot(collection_name=collection_name)

@router.post("/chatbot/")
async def chatbot_query(query: str):
    """
    Handle user queries and return concise responses.
    """
    try:
        results = chatbot.search_qdrant(query)
        if not results:
            return {"message": "No relevant information found in the database."}

        response = chatbot.generate_response(query, results)
        return {"answer": response}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing query: {str(e)}")