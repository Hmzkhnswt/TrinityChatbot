from fastapi import FastAPI, UploadFile, Form, APIRouter
from fastapi.responses import JSONResponse
from src.components.qdrantdumping import QdrantDumper
import os

router = APIRouter()
CollectionName = os.getenv("QDRANT_COLLECTION_NAME")

qdrant_dumper = QdrantDumper(collection_name=CollectionName)

@router.post("/upload-pdf/")
async def upload_pdf(file: UploadFile, token: str = Form(...)):
    try:
        if file.content_type != "application/pdf":
            return JSONResponse(
                content={"message": "Only PDF files are supported."}, status_code=400
            )

        pdf_path = f"/tmp/{file.filename}"
        with open(pdf_path, "wb") as f:
            f.write(await file.read())

        result = qdrant_dumper.dump_pdf(pdf_path, token)
        os.remove(pdf_path)

        return JSONResponse(content=result, status_code=200)
    except Exception as e:
        return JSONResponse(
            content={"message": f"Error processing PDF: {str(e)}"}, status_code=500
        )