"""
Document Processing

Handles document loading, chunking, and preprocessing for RAG.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import hashlib
from pydantic import BaseModel, Field


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""
    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_index: int = 0
    start_char: Optional[int] = None
    end_char: Optional[int] = None


class DocumentProcessor:
    """
    Processes documents for RAG system.
    
    Handles loading, chunking, and preprocessing of documents.
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "fixed"
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size: Size of each chunk in characters
            chunk_overlap: Overlap between chunks
            chunking_strategy: Chunking strategy ("fixed", "sentence", "paragraph")
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
    
    def load_document(self, file_path: str) -> str:
        """
        Load document from file.
        
        Args:
            file_path: Path to document file
        
        Returns:
            Document content
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        # Determine file type and load accordingly
        suffix = path.suffix.lower()
        
        if suffix in [".txt", ".md"]:
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        else:
            # Try as text file
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
    
    def chunk_document(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Chunk a document into smaller pieces.
        
        Args:
            content: Document content
            document_id: Document identifier
            metadata: Optional document metadata
        
        Returns:
            List of document chunks
        """
        if self.chunking_strategy == "fixed":
            return self._chunk_fixed(content, document_id, metadata)
        elif self.chunking_strategy == "sentence":
            return self._chunk_sentence(content, document_id, metadata)
        elif self.chunking_strategy == "paragraph":
            return self._chunk_paragraph(content, document_id, metadata)
        else:
            raise ValueError(f"Unknown chunking strategy: {self.chunking_strategy}")
    
    def _chunk_fixed(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Chunk document into fixed-size pieces."""
        chunks = []
        start = 0
        chunk_index = 0
        
        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_content = content[start:end]
            
            chunk_id = self._generate_chunk_id(document_id, chunk_index)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata=metadata or {},
                chunk_index=chunk_index,
                start_char=start,
                end_char=end
            )
            chunks.append(chunk)
            
            start = end - self.chunk_overlap
            chunk_index += 1
        
        return chunks
    
    def _chunk_sentence(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Chunk document by sentences."""
        import re
        
        # Simple sentence splitting
        sentences = re.split(r'(?<=[.!?])\s+', content)
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for sentence in sentences:
            sentence_size = len(sentence)
            
            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_content = ' '.join(current_chunk)
                chunk_id = self._generate_chunk_id(document_id, chunk_index)
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    content=chunk_content,
                    metadata=metadata or {},
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                
                # Start new chunk with overlap
                overlap_sentences = current_chunk[-self._get_overlap_sentence_count():]
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_content = ' '.join(current_chunk)
            chunk_id = self._generate_chunk_id(document_id, chunk_index)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata=metadata or {},
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    def _chunk_paragraph(
        self,
        content: str,
        document_id: str,
        metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """Chunk document by paragraphs."""
        paragraphs = content.split('\n\n')
        chunks = []
        current_chunk = []
        current_size = 0
        chunk_index = 0
        
        for paragraph in paragraphs:
            paragraph_size = len(paragraph)
            
            if current_size + paragraph_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_content = '\n\n'.join(current_chunk)
                chunk_id = self._generate_chunk_id(document_id, chunk_index)
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    content=chunk_content,
                    metadata=metadata or {},
                    chunk_index=chunk_index
                )
                chunks.append(chunk)
                
                # Start new chunk
                current_chunk = [paragraph]
                current_size = paragraph_size
                chunk_index += 1
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size
        
        # Add remaining chunk
        if current_chunk:
            chunk_content = '\n\n'.join(current_chunk)
            chunk_id = self._generate_chunk_id(document_id, chunk_index)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata=metadata or {},
                chunk_index=chunk_index
            )
            chunks.append(chunk)
        
        return chunks
    
    def _get_overlap_sentence_count(self) -> int:
        """Calculate number of sentences for overlap."""
        # Rough estimate: assume average sentence length
        avg_sentence_length = 100
        return max(1, self.chunk_overlap // avg_sentence_length)
    
    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """Generate unique chunk ID."""
        content = f"{document_id}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

