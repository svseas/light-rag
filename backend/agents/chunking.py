from chonkie import TokenChunker

from backend.models.chunks import ChunkingRequest


class ChunkingAgent:
    def __init__(self, default_chunk_size: int = 512, default_overlap: int = 50):
        self.default_chunk_size = default_chunk_size
        self.default_overlap = default_overlap
    
    def chunk_document(self, content: str, request: ChunkingRequest) -> list[str]:
        """Chunk a document using chonkie library.
        
        Args:
            content: The document content to chunk
            request: Chunking parameters
            
        Returns:
            List of chunk texts
        """
        chunk_size = request.chunk_size or self.default_chunk_size
        overlap = request.overlap or self.default_overlap
        
        chunker = TokenChunker(chunk_size=chunk_size, chunk_overlap=overlap)
        raw_chunks = chunker.chunk(content)
        
        return [chunk.text for chunk in raw_chunks]