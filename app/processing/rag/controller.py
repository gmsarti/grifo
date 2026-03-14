from app.processing.rag.graph import create_rag_graph

class AgenticRAGController:
    """
    Controller for the Agentic RAG system.
    Exposes a clean interface for the main agent to use.
    """
    def __init__(self):
        self.app = create_rag_graph()

    async def invoke(self, question: str) -> str:
        """
        Runs the full CRAG workflow for a given question.
        Returns the final generated answer.
        """
        inputs = {"question": question}
        result = await self.app.ainvoke(inputs)
        return result.get("generation", "Sorry, I couldn't find an answer.")
