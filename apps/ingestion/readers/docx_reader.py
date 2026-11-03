# OWNER: Dev B
from docx import Document

def read(path) -> str:
    return "\n".join(p.text for p in Document(path).paragraphs)