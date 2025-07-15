import asyncio
import logging
from typing import Any

import google.generativeai as genai

from backend.core.config import get_settings

logger = logging.getLogger(__name__)


class EmbeddingGenerationAgent:
    """Agent for generating embeddings using Google Gemini embedding model."""
    
    def __init__(self):
        self.settings = get_settings()
        genai.configure(api_key=self.settings.google_api_key)
        self.model = self.settings.embedding_model
        self.dimension = 768  # Will be updated after first API call
        self.max_batch_size = 100
        self.max_retries = 3
        
    async def generate_embedding(self, text: str) -> list[float]:
        """Generate embedding for a single text.
        
        Args:
            text: The text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        if not text.strip():
            raise ValueError("Text cannot be empty")
        
        embeddings = await self._generate_embeddings_with_retry([text])
        return embeddings[0]
    
    async def generate_embeddings_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts in batch.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors, one for each input text
            
        Raises:
            Exception: If embedding generation fails after retries
        """
        if not texts:
            return []
        
        # Filter out empty texts
        valid_texts = [text.strip() for text in texts if text.strip()]
        if not valid_texts:
            raise ValueError("No valid texts provided")
        
        # Process in batches if necessary
        if len(valid_texts) <= self.max_batch_size:
            return await self._generate_embeddings_with_retry(valid_texts)
        
        # Split into smaller batches
        embeddings = []
        for i in range(0, len(valid_texts), self.max_batch_size):
            batch = valid_texts[i:i + self.max_batch_size]
            batch_embeddings = await self._generate_embeddings_with_retry(batch)
            embeddings.extend(batch_embeddings)
        
        return embeddings
    
    async def _generate_embeddings_with_retry(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings with retry logic.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return await self._call_gemini_api(texts)
            except Exception as e:
                last_error = e
                logger.warning(f"Embedding generation attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempt)
                else:
                    logger.error(f"All {self.max_retries} attempts failed")
        
        raise last_error
    
    async def _call_gemini_api(self, texts: list[str]) -> list[list[float]]:
        """Make the actual API call to Google Gemini.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors
        """
        try:
            # Run the synchronous Gemini call in a thread pool
            embeddings = []
            for text in texts:
                result = await asyncio.get_event_loop().run_in_executor(
                    None, 
                    lambda t=text: genai.embed_content(
                        model=self.model,
                        content=t
                    )
                )
                embedding = result['embedding']
                embeddings.append(embedding)
                
                # Update dimension on first successful call
                if self.dimension != len(embedding):
                    self.dimension = len(embedding)
                    logger.info(f"Updated embedding dimension to {self.dimension}")
            
            return embeddings
            
        except Exception as e:
            logger.error(f"Unexpected error calling Gemini API: {e}")
            raise
    
    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this agent."""
        return self.dimension
    
    def get_model_name(self) -> str:
        """Get the name of the embedding model being used."""
        return self.model