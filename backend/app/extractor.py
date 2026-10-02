import os
from pathlib import Path
from typing import BinaryIO

import dotenv
from docx import Document
from google import genai
from pypdf import PdfReader

from backend.app.models import Course


class EmptySyllabusError(ValueError):
    """Raised when no extractable text was found in a syllabus file (e.g. a scanned PDF with no text layer)."""

PROMPT_TEMPLATE = (
    "You are extracting structured grading information from a university course syllabus.\n\n"
    "Read the syllabus text below and extract the course's name and code, along with its full "
    "grading breakdown: every graded group (e.g. exams, assignments, quizzes) with its weight "
    "toward the final grade, and every individual item within each group with its own weight and "
    "due date. Only include grading information that is explicitly stated in the syllabus -- do "
    "not invent items, dates, or weights that aren't present in the text. If a due date's year "
    "isn't given, infer it from the course term.\n\n"
    "Syllabus:\n{syllabus_text}"
)


def _read_pdf(stream: BinaryIO) -> str:
    reader = PdfReader(stream)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _read_docx(stream: BinaryIO) -> str:
    document = Document(stream)
    paragraphs = [p.text for p in document.paragraphs]
    # Grading breakdowns are often in tables, which .paragraphs doesn't cover.
    table_rows = [
        " | ".join(cell.text for cell in row.cells)
        for table in document.tables
        for row in table.rows
    ]
    return "\n".join(paragraphs + table_rows)


def _read_plain_text(stream: BinaryIO) -> str:
    return stream.read().decode("utf-8")


# Anything not listed here (.md, .txt, etc.) is read as plain UTF-8 text.
_READERS = {
    ".pdf": _read_pdf,
    ".docx": _read_docx,
}


def read_syllabus(filename: str, stream: BinaryIO) -> str:
    """Extracts syllabus text from a binary stream, dispatching on the file's extension."""
    reader = _READERS.get(Path(filename).suffix.lower(), _read_plain_text)
    text = reader(stream)
    if not text.strip():
        raise EmptySyllabusError(
            f"No text could be extracted from '{filename}' -- it may be a scanned/image-only file."
        )
    return text


class SyllabusExtractor:
    """Turns raw syllabus text (or a syllabus file) into a structured Course via Gemini."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.1-flash-lite"):
        if api_key is None:
            dotenv.load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    async def extract(self, syllabus_text: str) -> Course:
        interaction = await self._client.aio.interactions.create(
            model=self._model,
            input=PROMPT_TEMPLATE.format(syllabus_text=syllabus_text),
            generation_config={
                "thinking_level": "low",
                "temperature": 0,
            },
            response_format={
                "mime_type": "application/json",
                "schema": Course.model_json_schema(),
            },
        )
        course = Course.model_validate_json(interaction.output_text)
        course.code = course.code.replace(" ", "").replace("/", "-")
        return course
