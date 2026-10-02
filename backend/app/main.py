import asyncio
import io
from typing import Literal

from fastapi import FastAPI, File, HTTPException, Response, UploadFile

from backend.app.calendar import to_ics
from backend.app.extractor import SyllabusExtractor, read_syllabus
from backend.app.notes import to_notes
from backend.app.spreadsheet import to_workbook

app = FastAPI()
extractor = SyllabusExtractor()

OutputFormat = Literal["json", "md", "ics", "xlsx"]

MEDIA_TYPES = {
    "md": "text/markdown",
    "ics": "text/calendar",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
}


async def _extract_one(file: UploadFile):
    content = await file.read()
    text = read_syllabus(file.filename, io.BytesIO(content))
    return await extractor.extract(text)


@app.post("/extract")
async def extract(format: OutputFormat, files: list[UploadFile] = File(default=[])):
    results = await asyncio.gather(
        *(_extract_one(file) for file in files),
        return_exceptions=True,
    )

    courses = []
    errors = []
    for file, result in zip(files, results):
        if isinstance(result, Exception):
            errors.append({"filename": file.filename, "error": str(result)})
        else:
            courses.append(result)

    if format == "json":
        return {
            "courses": [course.model_dump() for course in courses],
            "errors": errors,
        }

    if not courses:
        raise HTTPException(status_code=422, detail={"errors": errors})

    if format == "md":
        content = to_notes(courses).encode()
    elif format == "ics":
        content = to_ics(courses).encode()
    elif format == "xlsx":
        buf = io.BytesIO()
        to_workbook(courses).save(buf)
        content = buf.getvalue()

    return Response(
        content=content,
        media_type=MEDIA_TYPES[format],
        headers={"Content-Disposition": f"attachment; filename=courses.{format}"},
    )
