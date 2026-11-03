# OWNER: Dev B
from pypdf import PdfReader

def read(path) -> str:
    return "\n".join((page.extract_text() or "") for page in PdfReader(path).pages)