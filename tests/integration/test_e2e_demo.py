from unittest.mock import patch

from langchain_core.documents import Document

from app.data_source.vector_store import VectorStoreManager


def test_e2e_ingestion_and_retrieval():
    """
    Testa o fluxo completo: Ingestão de arquivo -> Persistência -> Retrieval.
    Nota: Usamos mocks para evitar chamadas reais à API da OpenAI e persistência em disco.
    """

    # 1. Configuração do Mock para Embeddings e Chroma
    with (
        patch("app.data_source.vector_store.OpenAIEmbeddings"),
        patch("app.data_source.vector_store.Chroma"),
        patch("app.data_source.loaders.TextLoader") as mock_loader,
        patch("os.path.exists") as mock_exists,
        patch("os.stat"),
        patch("app.data_source.vector_store.HybridRetriever"),
    ):
        mock_exists.return_value = True

        # Simula o conteúdo do arquivo
        mock_loader_instance = mock_loader.return_value
        mock_loader_instance.load.return_value = [
            Document(
                page_content="O Projeto Grifo é uma arquitetura de agente 3-tier.",
                metadata={"source": "test.txt"},
            )
        ]

        # Simula o comportamento do Chroma
        vector_manager = VectorStoreManager()

        # Mock da busca por similaridade
        vector_manager.vector_store.similarity_search.return_value = [
            Document(
                page_content="O Projeto Grifo é uma arquitetura de agente 3-tier.",
                metadata={"source": "test.txt"},
            )
        ]

        # 2. Execução: Ingestão
        print("\nPasso 1: Ingerindo arquivo...")
        vector_manager.ingest_file("test.txt")

        # 3. Execução: Retrieval
        print("Passo 2: Realizando busca (Retrieval)...")
        query = "O que é o Projeto Grifo?"
        context = vector_manager.search_context(query)

        # 4. Validação
        assert "Projeto Grifo" in context
        assert "3-tier" in context

        print(
            "\nResultado: O fluxo de Ingestão e Retrieval está funcionando corretamente (validado via mocks)."
        )


if __name__ == "__main__":
    test_e2e_ingestion_and_retrieval()
