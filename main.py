from fastapi import FastAPI
from routes import pdf_dump_route, chatbot_route
import os
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

app.include_router(pdf_dump_route.router)
app.include_router(chatbot_route.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the PDF Dump API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
