from unittest.mock import patch

from langchain_core.documents import Document


def test_e2e_ingestion_and_retrieval(vector_manager):
    """
    Testa o fluxo completo: Ingestão de arquivo -> Persistência -> Retrieval.
    Nota: Usamos mocks para evitar chamadas reais à API da OpenAI e persistência em disco.
    """
    with (
        patch("app.data_source.loaders.TextLoader") as mock_loader,
        patch("os.path.exists") as mock_exists,
        patch("os.stat") as mock_stat,
    ):
        mock_exists.return_value = True
        mock_stat.return_value.st_size = 1024

        mock_loader_instance = mock_loader.return_value
        mock_loader_instance.load.return_value = [
            Document(
                page_content="O Projeto Grifo é uma arquitetura de agente 3-tier.",
                metadata={"source": "test.txt"},
            )
        ]

        vector_manager.vector_store.similarity_search.return_value = [
            Document(
                page_content="O Projeto Grifo é uma arquitetura de agente 3-tier.",
                metadata={"source": "test.txt"},
            )
        ]

        vector_manager.ingest_file("test.txt")

        context = vector_manager.search_context("O que é o Projeto Grifo?")

        assert "Projeto Grifo" in context
        assert "3-tier" in context
