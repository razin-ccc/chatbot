import cohere
from core.config import getSettings

class RerankerService:
    def __init__(self):
        settings = getSettings()
        # Initialize the Cohere AsyncClient
        self.client = cohere.AsyncClient(settings.COHERE_API_KEY)
        self.model = "rerank-english-v3.0"

    async def rerank(self, query: str, documents: list[str]) -> list[float]:
        if not documents:
            return []
            
        response = await self.client.rerank(
            model=self.model,
            query=query,
            documents=documents,
            return_documents=False
        )
        
        # Initialize an array of zeros matching the documents length
        scores = [0.0] * len(documents)
        
        # Map the relevance scores back to their original document indices
        for result in response.results:
            scores[result.index] = result.relevance_score

        return scores

    async def close(self) -> None:
        await self.client.__aexit__(None, None, None)
