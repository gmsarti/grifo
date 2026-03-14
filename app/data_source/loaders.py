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


from app.core.logging import get_logger

logger = get_logger(__name__)

class FileIngestionService:
    """
    Service responsible for loading and splitting files of different formats.
    """
    ALLOWED_EXTENSIONS = {".pdf", ".docx", ".csv", ".txt", ".md"}

    def __init__(self):
        self.text_splitter = get_text_splitter()

    def _get_loader(self, file_path: str, ext: str):
        """Returns the appropriate loader for the given extension."""
        if ext == ".pdf":
            return PyPDFLoader(file_path)
        elif ext == ".docx":
            return Docx2txtLoader(file_path)
        elif ext == ".csv":
            return CSVLoader(file_path)
        elif ext in [".txt", ".md"]:
            return TextLoader(file_path)
        return None

    def validate_file(self, file_path: str):
        """Validates file existence, size, and extension."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")
        
        stat = os.stat(file_path)
        if stat.st_size == 0:
            raise ValueError(f"O arquivo está vazio: {file_path}")
            
        ext = os.path.splitext(file_path)[1].lower()
        if ext not in self.ALLOWED_EXTENSIONS:
            raise ValueError(f"Extensão não suportada: {ext}. Permitidas: {self.ALLOWED_EXTENSIONS}")
        
        return ext

    def process_file(self, file_path: str) -> List[Document]:
        """
        Loads a file based on its extension and returns a list of split documents.
        """
        ext = self.validate_file(file_path)
        loader = self._get_loader(file_path, ext)
        
        if not loader:
            raise ValueError(f"Falha ao instanciar loader para: {ext}")

        try:
            logger.info(f"Carregando arquivo: {file_path}")
            documents = loader.load()
            
            if not documents:
                logger.warning(f"Loader não retornou documentos para: {file_path}")
                return []
                
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Erro ao processar arquivo {file_path}: {str(e)}")
            raise RuntimeError(f"Falha no parsing do arquivo {ext}: {str(e)}")


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
        try:
            logger.info(f"Ingerindo URL: {url}")
            loader = WebBaseLoader(url)
            documents = loader.load()
            
            if not documents:
                logger.warning(f"Nenhum conteúdo extraído da URL: {url}")
                return []
                
            return self.text_splitter.split_documents(documents)
        except Exception as e:
            logger.error(f"Erro ao processar URL {url}: {str(e)}")
            raise RuntimeError(f"Falha ao carregar conteúdo da URL: {str(e)}")
