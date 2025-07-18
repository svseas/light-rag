from chonkie import TokenChunker, SemanticChunker

from backend.models.chunks import ChunkingRequest


class ChunkingAgent:
    def __init__(self, default_chunk_size: int = 1024, default_overlap: int = 50, use_semantic: bool = True):
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
        self.use_semantic = use_semantic
    
    def chunk_document(self, content: str, request: ChunkingRequest) -> list[str]:
        """Chunk a document using chonkie library.
        
        Args:
            content: The document content to chunk
            request: Chunking parameters
            
        Returns:
            List of chunk texts
        """
        chunk_size = request.chunk_size or self.default_chunk_size
        
        if self.use_semantic:
            # Use SemanticChunker for better content awareness
            try:
                chunker = SemanticChunker(
                    embedding_model="all-MiniLM-L6-v2",  # More compatible model
                    threshold=0.5,  # Lower threshold for more grouping
                    chunk_size=chunk_size,
                    mode="cumulative",  # Better for document structure
                    min_sentences=3,     # Ensure meaningful chunks
                    similarity_window=5  # Consider more sentences for similarity
                )
                raw_chunks = chunker.chunk(content)
            except Exception as e:
                print(f"SemanticChunker failed: {e}")
                print("Falling back to TokenChunker...")
                # Fallback to TokenChunker
                overlap = request.overlap or self.default_overlap
                chunker = TokenChunker(chunk_size=chunk_size, chunk_overlap=overlap)
                raw_chunks = chunker.chunk(content)
        else:
            # Fallback to TokenChunker
            overlap = request.overlap or self.default_overlap
            chunker = TokenChunker(chunk_size=chunk_size, chunk_overlap=overlap)
            raw_chunks = chunker.chunk(content)
        
        return [chunk.text for chunk in raw_chunks]