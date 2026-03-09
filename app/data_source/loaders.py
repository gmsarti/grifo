import os
from typing import List
from langchain_community.document_loaders import (
    PyPDFLoader,
    Docx2txtLoader,
    TextLoader,
    CSVLoader,
    WebBaseLoader,
)
from langchain_core.documents import Document
from app.utils.text_processor import get_text_splitter


class FileIngestionService:
    """
    Service responsible for loading and splitting files of different formats.
    """

    def __init__(self):
        self.text_splitter = get_text_splitter()

    def process_file(self, file_path: str) -> List[Document]:
        """
        Loads a file based on its extension and returns a list of split documents.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = os.path.splitext(file_path)[1].lower()

        if ext == ".pdf":
            loader = PyPDFLoader(file_path)
        elif ext == ".docx":
            loader = Docx2txtLoader(file_path)
        elif ext == ".csv":
            loader = CSVLoader(file_path)
        elif ext in [".txt", ".md"]:
            loader = TextLoader(file_path)
        else:
            raise ValueError(f"Unsupported file extension: {ext}")

        documents = loader.load()
        return self.text_splitter.split_documents(documents)


class WebIngestionService:
    """
    Service responsible for loading and splitting content from web URLs.
    """

    def __init__(self):
        self.text_splitter = get_text_splitter()

    def process_url(self, url: str) -> List[Document]:
        """
        Ingests content from a URL and returns a list of split documents.
        """
        loader = WebBaseLoader(url)
        documents = loader.load()
        return self.text_splitter.split_documents(documents)
