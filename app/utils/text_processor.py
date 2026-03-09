from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.core.config import settings


def get_text_splitter() -> RecursiveCharacterTextSplitter:
    """
    Retorna uma instância configurada do RecursiveCharacterTextSplitter.
    Conforme definido na TASK-1.
    """
    return RecursiveCharacterTextSplitter(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ".", " ", ""],
    )
