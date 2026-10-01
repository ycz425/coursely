import os
from pathlib import Path

import dotenv
from google import genai
from pypdf import PdfReader

from app.models import Course

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


def read_pdf(path: str | Path) -> str:
    reader = PdfReader(path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def read_syllabus_file(path: str | Path) -> str:
    path = Path(path)
    return read_pdf(path) if path.suffix.lower() == ".pdf" else path.read_text()


class SyllabusExtractor:
    """Turns raw syllabus text (or a syllabus file) into a structured Course via Gemini."""

    def __init__(self, api_key: str | None = None, model: str = "gemini-3.1-flash-lite"):
        if api_key is None:
            dotenv.load_dotenv()
            api_key = os.getenv("GEMINI_API_KEY")
        self._client = genai.Client(api_key=api_key)
        self._model = model

    def extract(self, syllabus_text: str) -> Course:
        interaction = self._client.interactions.create(
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

    def extract_from_file(self, path: str | Path) -> Course:
        return self.extract(read_syllabus_file(path))
