from fastapi import FastAPI
from routes import pdf_dump_route, chatbot_route
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

origins = ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pdf_dump_route.router)
app.include_router(chatbot_route.router)

@app.get("/")
async def read_root():
    return {"message": "Welcome to the PDF Dump API"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
