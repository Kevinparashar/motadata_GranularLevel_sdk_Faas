"""
Document Processing

Handles document loading, chunking, preprocessing, and metadata handling for RAG.
"""


# Standard library imports
import hashlib
import re
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# Third-party imports
from pydantic import BaseModel, Field, validator

# Local application/library specific imports
from .exceptions import (
    ChunkingError,
    DocumentProcessingError,
    ValidationError,
)
from .multimodal_loader import MultiModalLoader, create_multimodal_loader


class ChunkingStrategy(str, Enum):
    """Chunking strategy enumeration."""

    FIXED = "fixed"
    SENTENCE = "sentence"
    PARAGRAPH = "paragraph"
    SEMANTIC = "semantic"  # Chunk by semantic boundaries (headers, sections)


class MetadataSchema(BaseModel):
    """Schema for document metadata validation."""

    title: Optional[str] = None
    author: Optional[str] = None
    source: Optional[str] = None
    language: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    document_type: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    category: Optional[str] = None
    custom: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"  # Allow additional fields


class DocumentChunk(BaseModel):
    """Represents a chunk of a document."""

    chunk_id: str
    document_id: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    chunk_index: int = 0
    start_char: Optional[int] = None
    end_char: Optional[int] = None
    token_count: Optional[int] = None  # Estimated token count

    @validator("content")
    def content_not_empty(cls, v):
        """
        Validate that content is not empty.
        
        Args:
            v (Any): Input parameter for this operation.
        
        Returns:
            Any: Result of the operation.
        
        Raises:
            ValidationError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        if not v or not v.strip():
            raise ValidationError(message="Chunk content cannot be empty", field="content", value=v)
        return v.strip()


class ChunkingPipeline:
    """
    Pipeline for preprocessing and chunking documents.

    Supports multiple preprocessing steps and chunk validation.
    """

    def __init__(
        self,
        preprocessing_steps: Optional[List[Callable[[str], str]]] = None,
        chunk_validators: Optional[List[Callable[[DocumentChunk], bool]]] = None,
    ):
        """
        Initialize chunking pipeline.
        
        Args:
            preprocessing_steps (Optional[List[Callable[[str], str]]]): Input parameter for this operation.
            chunk_validators (Optional[List[Callable[[DocumentChunk], bool]]]): Input parameter for this operation.
        """
        self.preprocessing_steps = preprocessing_steps or []
        self.chunk_validators = chunk_validators or []

    def preprocess(self, content: str) -> str:
        """
        Apply preprocessing steps to content.
        
        Args:
            content (str): Content text.
        
        Returns:
            str: Returned text value.
        """
        processed = content
        for step in self.preprocessing_steps:
            processed = step(processed)
        return processed

    def validate_chunk(self, chunk: DocumentChunk) -> bool:
        """
        Validate a chunk using all validators.
        
        Args:
            chunk (DocumentChunk): Input parameter for this operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        for validator in self.chunk_validators:
            if not validator(chunk):
                return False
        return True


class MetadataHandler:
    """
    Handles metadata extraction, validation, and enrichment.
    """

    def __init__(
        self,
        schema: Optional[MetadataSchema] = None,
        extractors: Optional[List[Callable[[str, Dict[str, Any]], Dict[str, Any]]]] = None,
    ):
        """
        Initialize metadata handler.
        
        Args:
            schema (Optional[MetadataSchema]): Input parameter for this operation.
            extractors (Optional[List[Callable[[str, Dict[str, Any]], Dict[str, Any]]]]): Input parameter for this operation.
        """
        self.schema = schema
        self.extractors = extractors or []

    def extract_metadata(
        self, content: str, existing_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Extract metadata from document content.
        
        Args:
            content (str): Content text.
            existing_metadata (Optional[Dict[str, Any]]): Input parameter for this operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        metadata = existing_metadata.copy() if existing_metadata else {}

        # Apply extractors
        for extractor in self.extractors:
            extracted = extractor(content, metadata)
            if extracted:
                metadata.update(extracted)

        # Add default metadata if missing
        if "language" not in metadata:
            metadata["language"] = self._detect_language(content)

        if "created_at" not in metadata:
            metadata["created_at"] = datetime.now().isoformat()

        return metadata

    def validate_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate metadata against schema.
        
        Args:
            metadata (Dict[str, Any]): Extra metadata for the operation.
        
        Returns:
            bool: True if the operation succeeds, else False.
        """
        if not self.schema:
            return True

        try:
            # Validate against schema
            MetadataSchema(**metadata)
            return True
        except (ValueError, TypeError, KeyError) as e:
            # Schema validation failed - expected for invalid metadata
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"Metadata validation failed: {e}")
            return False

    def enrich_chunk_metadata(
        self, chunk: DocumentChunk, document_metadata: Dict[str, Any]
    ) -> DocumentChunk:
        """
        Enrich chunk metadata with document-level metadata.
        
        Args:
            chunk (DocumentChunk): Input parameter for this operation.
            document_metadata (Dict[str, Any]): Input parameter for this operation.
        
        Returns:
            DocumentChunk: Result of the operation.
        """
        # Merge document metadata with chunk metadata
        enriched_metadata = {
            **document_metadata,
            **chunk.metadata,
            "chunk_index": chunk.chunk_index,
            "chunk_id": chunk.chunk_id,
            "document_id": chunk.document_id,
        }

        chunk.metadata = enriched_metadata
        return chunk

    def _detect_language(self, content: str) -> str:
        """
        Simple language detection (can be enhanced).
        
        Args:
            content (str): Content text.
        
        Returns:
            str: Returned text value.
        """
        # Basic detection - can be improved with langdetect library
        if re.search(r"[àáâãäåæçèéêë]", content, re.IGNORECASE):
            return "fr"
        elif re.search(r"[äöüß]", content, re.IGNORECASE):
            return "de"
        elif re.search(r"[ñáéíóúü]", content, re.IGNORECASE):
            return "es"
        else:
            return "en"  # Default to English


class DocumentProcessor:
    """
    Processes documents for RAG system.

    Handles loading, preprocessing, chunking, and metadata management.
    """

    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        chunking_strategy: str = "fixed",
        min_chunk_size: int = 50,  # Minimum chunk size to keep
        max_chunk_size: int = 2000,  # Maximum chunk size
        enable_preprocessing: bool = True,
        enable_metadata_extraction: bool = True,
        metadata_schema: Optional[MetadataSchema] = None,
        enable_multimodal: bool = True,
        multimodal_loader: Optional[MultiModalLoader] = None,
        gateway: Optional[Any] = None,  # For image description generation
    ):
        """
        Initialize document processor.
        
        Args:
            chunk_size (int): Input parameter for this operation.
            chunk_overlap (int): Input parameter for this operation.
            chunking_strategy (str): Input parameter for this operation.
            min_chunk_size (int): Input parameter for this operation.
            max_chunk_size (int): Input parameter for this operation.
            enable_preprocessing (bool): Flag to enable or disable preprocessing.
            enable_metadata_extraction (bool): Flag to enable or disable metadata extraction.
            metadata_schema (Optional[MetadataSchema]): Input parameter for this operation.
            enable_multimodal (bool): Flag to enable or disable multimodal.
            multimodal_loader (Optional[MultiModalLoader]): Input parameter for this operation.
            gateway (Optional[Any]): Gateway client used for LLM calls.
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunking_strategy = chunking_strategy
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.gateway = gateway

        # Initialize multimodal loader if enabled
        self.multimodal_loader: Optional[MultiModalLoader] = (
            (multimodal_loader or create_multimodal_loader()) if enable_multimodal else None
        )

        # Initialize preprocessing pipeline
        preprocessing_steps = []
        if enable_preprocessing:
            preprocessing_steps = [
                self._normalize_whitespace,
                self._remove_control_characters,
                self._normalize_unicode,
            ]

        # Initialize chunk validators
        chunk_validators = [
            lambda c: len(c.content) >= self.min_chunk_size,
            lambda c: len(c.content) <= self.max_chunk_size,
        ]

        self.pipeline = ChunkingPipeline(
            preprocessing_steps=preprocessing_steps or None,
            chunk_validators=chunk_validators,
        )

        # Initialize metadata handler
        extractors = []
        if enable_metadata_extraction:
            extractors = [self._extract_title, self._extract_dates, self._extract_tags]

        self.metadata_handler = MetadataHandler(
            schema=metadata_schema,
            extractors=extractors if extractors else None,
        )

    def _read_text_file(self, path: Path) -> str:
        """
        Read text file synchronously (helper for async wrapper).
        
        Args:
            path (Path): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        with open(path, "r", encoding="utf-8") as f:
            return f.read()

    async def load_document(self, file_path: str) -> tuple[str, Dict[str, Any]]:
        """
        Load document from file with metadata extraction asynchronously.
        
        Supports multiple formats:
                                        - Text: .txt, .md, .markdown, .html, .json
                                        - Documents: .pdf, .doc, .docx, .rtf
                                        - Audio: .mp3, .wav, .m4a, .ogg (with transcription)
                                        - Video: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
                                        - Images: .jpg, .png, .gif, .bmp (with OCR and description)
        
        Args:
            file_path (str): Path of the input file.
        
        Returns:
            tuple[str, Dict[str, Any]]: Dictionary result of the operation.
        
        Raises:
            DocumentProcessingError: Raised when this function detects an invalid state or when an underlying call fails.
            FileNotFoundError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        import asyncio

        path = Path(file_path)

        # Check file existence asynchronously
        exists = await asyncio.to_thread(path.exists)
        if not exists:
            raise FileNotFoundError(f"Document not found: {file_path}")

        # Use multimodal loader if available and file is not basic text
        suffix = path.suffix.lower()
        basic_text_formats = [".txt", ".md", ".markdown", ".html", ".json"]

        if self.multimodal_loader and suffix not in basic_text_formats:
            # Use multimodal loader for complex formats (async)
            content, file_metadata = await self.multimodal_loader.load(str(path), self.gateway)
        else:
            # Use basic text loading for simple formats
            # Get file stats asynchronously
            stat_result = await asyncio.to_thread(path.stat)
            file_metadata = {
                "source": str(path),
                "file_name": path.name,
                "file_extension": suffix,
                "file_size": stat_result.st_size,
                "updated_at": datetime.fromtimestamp(stat_result.st_mtime).isoformat(),
            }

            if suffix in [".txt", ".md", ".markdown"]:
                content = await asyncio.to_thread(self._read_text_file, path)
            elif suffix == ".html":
                content = await self._load_html(path)
            elif suffix == ".json":
                content = await self._load_json(path)
            else:
                # Try as text file
                try:
                    content = await asyncio.to_thread(self._read_text_file, path)
                except UnicodeDecodeError as e:
                    raise DocumentProcessingError(
                        message=f"Unsupported file format: {suffix}. Enable multimodal loader for advanced formats.",
                        file_path=str(file_path),
                        operation="load_document",
                        original_error=e,
                    )

        # Extract metadata from content
        extracted_metadata = self.metadata_handler.extract_metadata(
            content, existing_metadata=file_metadata
        )

        return content, extracted_metadata

    async def _load_html(self, path: Path) -> str:
        """
        Load HTML file and extract text content asynchronously.
        
        Args:
            path (Path): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        import asyncio

        try:
            from html.parser import HTMLParser

            class TextExtractor(HTMLParser):
                def __init__(self):
                    super().__init__()
                    self.text = []
                    self.in_script = False
                    self.in_style = False

                def handle_starttag(self, tag, attrs):
                    if tag.lower() in ["script", "style"]:
                        self.in_script = tag.lower() == "script"
                        self.in_style = tag.lower() == "style"

                def handle_endtag(self, tag):
                    if tag.lower() in ["script", "style"]:
                        self.in_script = False
                        self.in_style = False

                def handle_data(self, data):
                    if not self.in_script and not self.in_style:
                        self.text.append(data)

            # Read file asynchronously
            html_content = await asyncio.to_thread(self._read_text_file, path)

            # Parse HTML (CPU-bound, but lightweight)
            parser = TextExtractor()
            parser.feed(html_content)
            return " ".join(parser.text)
        except (AttributeError, UnicodeDecodeError, OSError) as e:
            # Fallback: try as plain text
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"HTML parsing failed for {path}, falling back to plain text: {e}")
            return await asyncio.to_thread(self._read_text_file, path)

    async def _load_json(self, path: Path) -> str:
        """
        Load JSON file and convert to text asynchronously.
        
        Args:
            path (Path): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        import asyncio
        import json

        # Read and parse JSON asynchronously
        def _read_and_parse_json(p: Path) -> str:
            with open(p, "r", encoding="utf-8") as f:
                data = json.load(f)
                # Convert to readable text
                if isinstance(data, dict):
                    return json.dumps(data, indent=2)
                return str(data)

        return await asyncio.to_thread(_read_and_parse_json, path)

    def chunk_document(
        self, content: str, document_id: str, metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Chunk a document into smaller pieces with preprocessing and validation.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            List[DocumentChunk]: List result of the operation.
        
        Raises:
            ChunkingError: Raised when this function detects an invalid state or when an underlying call fails.
        """
        # Preprocess content
        processed_content = self.pipeline.preprocess(content)

        # Extract and validate metadata
        if metadata is None:
            metadata = {}

        extracted_metadata = self.metadata_handler.extract_metadata(
            processed_content, existing_metadata=metadata
        )

        # Validate metadata if schema is set
        if not self.metadata_handler.validate_metadata(extracted_metadata):
            # Log warning but continue
            pass

        # Chunk document based on strategy
        if self.chunking_strategy == "fixed":
            chunks = self._chunk_fixed(processed_content, document_id, extracted_metadata)
        elif self.chunking_strategy == "sentence":
            chunks = self._chunk_sentence(processed_content, document_id, extracted_metadata)
        elif self.chunking_strategy == "paragraph":
            chunks = self._chunk_paragraph(processed_content, document_id, extracted_metadata)
        elif self.chunking_strategy == "semantic":
            chunks = self._chunk_semantic(processed_content, document_id, extracted_metadata)
        else:
            raise ChunkingError(
                message=f"Unknown chunking strategy: {self.chunking_strategy}",
                document_id=document_id,
                chunking_strategy=self.chunking_strategy,
            )

        # Enrich chunks with metadata and validate
        validated_chunks = []
        for chunk in chunks:
            # Enrich with document metadata
            enriched_chunk = self.metadata_handler.enrich_chunk_metadata(chunk, extracted_metadata)

            # Add token count estimate
            enriched_chunk.token_count = self._estimate_tokens(enriched_chunk.content)

            # Validate chunk
            if self.pipeline.validate_chunk(enriched_chunk):
                validated_chunks.append(enriched_chunk)

        return validated_chunks

    def _chunk_fixed(
        self, content: str, document_id: str, metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk document into fixed-size pieces.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            List[DocumentChunk]: List result of the operation.
        """
        chunks = []
        start = 0
        chunk_index = 0

        while start < len(content):
            end = min(start + self.chunk_size, len(content))
            chunk_content = content[start:end]

            # Try to break at word boundary
            if end < len(content):
                # Look for space or newline near the end
                for i in range(end, max(start, end - 50), -1):
                    if content[i] in [" ", "\n", "\t"]:
                        end = i + 1
                        chunk_content = content[start:end]
                        break

            chunk_id = self._generate_chunk_id(document_id, chunk_index)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata=metadata.copy() if metadata else {},
                chunk_index=chunk_index,
                start_char=start,
                end_char=end,
            )
            chunks.append(chunk)

            start = end - self.chunk_overlap
            chunk_index += 1

        return chunks

    def _chunk_sentence(
        self, content: str, document_id: str, metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk document by sentences.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            List[DocumentChunk]: List result of the operation.
        """
        # Improved sentence splitting
        sentence_pattern = r"(?<=[.!?])\s+(?=[A-Z])|(?<=\n)\s*"
        sentences = re.split(sentence_pattern, content)
        sentences = [s.strip() for s in sentences if s.strip()]

        chunks = []
        current_chunk: List[str] = []
        current_size = 0
        chunk_index = 0

        for sentence in sentences:
            sentence_size = len(sentence)

            if current_size + sentence_size > self.chunk_size and current_chunk:
                # Create chunk
                chunk_content = " ".join(current_chunk)
                chunk_id = self._generate_chunk_id(document_id, chunk_index)
                chunk = DocumentChunk(
                    chunk_id=chunk_id,
                    document_id=document_id,
                    content=chunk_content,
                    metadata=metadata.copy() if metadata else {},
                    chunk_index=chunk_index,
                )
                chunks.append(chunk)

                # Start new chunk with overlap
                overlap_sentences = current_chunk[-self._get_overlap_sentence_count() :]
                current_chunk = overlap_sentences + [sentence]
                current_size = sum(len(s) for s in current_chunk)
                chunk_index += 1
            else:
                current_chunk.append(sentence)
                current_size += sentence_size

        # Add remaining chunk
        if current_chunk:
            chunk_content = " ".join(current_chunk)
            chunk_id = self._generate_chunk_id(document_id, chunk_index)
            chunk = DocumentChunk(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_content,
                metadata=metadata.copy() if metadata else {},
                chunk_index=chunk_index,
            )
            chunks.append(chunk)

        return chunks

    def _create_chunk(
        self,
        content: str,
        document_id: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]],
    ) -> DocumentChunk:
        """
        Helper to create a DocumentChunk.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            chunk_index (int): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            DocumentChunk: Result of the operation.
        """
        chunk_id = self._generate_chunk_id(document_id, chunk_index)
        return DocumentChunk(
            chunk_id=chunk_id,
            document_id=document_id,
            content=content,
            metadata=metadata.copy() if metadata else {},
            chunk_index=chunk_index,
        )

    def _finalize_current_chunk(
        self,
        current_chunk: List[str],
        document_id: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]],
        chunks: List[DocumentChunk],
        separator: str = "\n\n",
    ) -> None:
        """
        Helper to finalize and append current chunk to chunks list.
        
        Args:
            current_chunk (List[str]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
            chunk_index (int): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            chunks (List[DocumentChunk]): Input parameter for this operation.
            separator (str): Input parameter for this operation.
        
        Returns:
            None: Result of the operation.
        """
        if current_chunk:
            chunk_content = separator.join(current_chunk)
            chunk = self._create_chunk(chunk_content, document_id, chunk_index, metadata)
            chunks.append(chunk)

    def _chunk_paragraph(
        self, content: str, document_id: str, metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk document by paragraphs.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            List[DocumentChunk]: List result of the operation.
        """
        # Split by double newlines or single newline followed by whitespace
        paragraphs = re.split(r"\n\s*\n|\n{2,}", content)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]

        chunks = []
        current_chunk: List[str] = []
        current_size = 0
        chunk_index = 0

        for paragraph in paragraphs:
            paragraph_size = len(paragraph)

            # If paragraph is too large, split it
            if paragraph_size > self.chunk_size:
                # Split large paragraph
                sub_paragraphs = self._split_large_paragraph(paragraph, self.chunk_size)
                for sub_para in sub_paragraphs:
                    if current_size + len(sub_para) > self.chunk_size and current_chunk:
                        self._finalize_current_chunk(
                            current_chunk, document_id, chunk_index, metadata, chunks
                        )
                        current_chunk = []
                        current_size = 0
                        chunk_index += 1

                    current_chunk.append(sub_para)
                    current_size += len(sub_para)
            elif current_size + paragraph_size > self.chunk_size and current_chunk:
                self._finalize_current_chunk(
                    current_chunk, document_id, chunk_index, metadata, chunks
                )
                # Start new chunk
                current_chunk = [paragraph]
                current_size = paragraph_size
                chunk_index += 1
            else:
                current_chunk.append(paragraph)
                current_size += paragraph_size

        # Add remaining chunk
        self._finalize_current_chunk(
            current_chunk, document_id, chunk_index, metadata, chunks
        )

        return chunks

    def _finalize_section(
        self,
        current_section: List[str],
        document_id: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]],
        chunks: List[DocumentChunk],
    ) -> int:
        """
        Finalize current section and add to chunks.
        
        Returns updated chunk_index.
        
        Args:
            current_section (List[str]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
            chunk_index (int): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            chunks (List[DocumentChunk]): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        if not current_section:
            return chunk_index
        
        chunk_content = "\n".join(current_section)
        chunk = self._create_chunk(chunk_content, document_id, chunk_index, metadata)
        chunks.append(chunk)
        return chunk_index + 1

    def _handle_oversized_section(
        self,
        current_section: List[str],
        document_id: str,
        chunk_index: int,
        metadata: Optional[Dict[str, Any]],
        chunks: List[DocumentChunk],
    ) -> int:
        """
        Handle section that exceeds chunk size.
        
        Returns updated chunk_index.
        
        Args:
            current_section (List[str]): Input parameter for this operation.
            document_id (str): Input parameter for this operation.
            chunk_index (int): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
            chunks (List[DocumentChunk]): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        section_content = "\n".join(current_section)
        
        if len(section_content) > self.chunk_size:
            # Use paragraph chunking for large sections
            sub_chunks = self._chunk_paragraph(section_content, document_id, metadata)
            for sub_chunk in sub_chunks:
                sub_chunk.chunk_index = chunk_index
                sub_chunk.chunk_id = self._generate_chunk_id(document_id, chunk_index)
                chunks.append(sub_chunk)
                chunk_index += 1
        else:
            chunk = self._create_chunk(section_content, document_id, chunk_index, metadata)
            chunks.append(chunk)
            chunk_index += 1
        
        return chunk_index

    def _chunk_semantic(
        self, content: str, document_id: str, metadata: Optional[Dict[str, Any]]
    ) -> List[DocumentChunk]:
        """
        Chunk document by semantic boundaries (headers, sections).
        
        Falls back to paragraph chunking if no semantic markers found.
        
        Args:
            content (str): Content text.
            document_id (str): Input parameter for this operation.
            metadata (Optional[Dict[str, Any]]): Extra metadata for the operation.
        
        Returns:
            List[DocumentChunk]: List result of the operation.
        """
        # Look for markdown headers or HTML-like headers
        header_pattern = r"^(#{1,6}\s+.+)$|^(<h[1-6]>.+</h[1-6]>)$"

        lines = content.split("\n")
        chunks = []
        current_section: List[str] = []
        current_size = 0
        chunk_index = 0

        for line in lines:
            line_size = len(line)

            # Check if line is a header
            if re.match(header_pattern, line.strip(), re.MULTILINE):
                # If we have content, create a chunk
                if current_section and current_size > 0:
                    chunk_index = self._finalize_section(
                        current_section, document_id, chunk_index, metadata, chunks
                    )
                    current_section = []
                    current_size = 0

                # Start new section with header
                current_section.append(line)
                current_size += line_size
            else:
                current_section.append(line)
                current_size += line_size

                # If section gets too large, split it
                if current_size > self.chunk_size:
                    chunk_index = self._handle_oversized_section(
                        current_section, document_id, chunk_index, metadata, chunks
                    )
                    current_section = []
                    current_size = 0

        # Add remaining section
        self._finalize_section(
            current_section, document_id, chunk_index, metadata, chunks
        )

        # If no semantic chunks found, fall back to paragraph chunking
        if not chunks:
            return self._chunk_paragraph(content, document_id, metadata)

        return chunks

    def _split_large_paragraph(self, paragraph: str, max_size: int) -> List[str]:
        """
        Split a large paragraph into smaller pieces.
        
        Args:
            paragraph (str): Input parameter for this operation.
            max_size (int): Input parameter for this operation.
        
        Returns:
            List[str]: List result of the operation.
        """
        if len(paragraph) <= max_size:
            return [paragraph]

        # Try to split by sentences first
        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
        if len(sentences) > 1:
            parts = []
            current_part: List[str] = []
            current_size = 0

            for sentence in sentences:
                sentence_size = len(sentence)
                if current_size + sentence_size > max_size and current_part:
                    parts.append(" ".join(current_part))
                    current_part = [sentence]
                    current_size = sentence_size
                else:
                    current_part.append(sentence)
                    current_size += sentence_size

            if current_part:
                parts.append(" ".join(current_part))

            return parts

        # Fall back to fixed-size splitting
        parts = []
        start = 0
        while start < len(paragraph):
            end = min(start + max_size, len(paragraph))
            parts.append(paragraph[start:end])
            start = end

        return parts

    def _get_overlap_sentence_count(self) -> int:
        """
        Calculate number of sentences for overlap.
        
        Returns:
            int: Result of the operation.
        """
        avg_sentence_length = 100
        return max(1, self.chunk_overlap // avg_sentence_length)

    def _generate_chunk_id(self, document_id: str, chunk_index: int) -> str:
        """
        Generate unique chunk ID.
        
        Args:
            document_id (str): Input parameter for this operation.
            chunk_index (int): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        content = f"{document_id}_{chunk_index}"
        return hashlib.md5(content.encode()).hexdigest()[:16]

    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count (rough approximation: 1 token ≈ 4 characters).
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            int: Result of the operation.
        """
        return len(text) // 4

    # Preprocessing functions
    def _normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        # Replace multiple spaces with single space
        text = re.sub(r" +", " ", text)
        # Replace multiple newlines with double newline
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    def _remove_control_characters(self, text: str) -> str:
        """
        Remove control characters except newlines and tabs.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        # Keep newlines (\n), carriage returns (\r), and tabs (\t)
        return re.sub(r"[\x00-\x08\x0B-\x0C\x0E-\x1F\x7F]", "", text)

    def _normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters.
        
        Args:
            text (str): Input parameter for this operation.
        
        Returns:
            str: Returned text value.
        """
        try:
            import unicodedata

            # Normalize to NFC form
            return unicodedata.normalize("NFC", text)
        except ImportError:
            return text

    # Metadata extraction functions
    def _extract_title(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract title from content.
        
        Args:
            content (str): Content text.
            metadata (Dict[str, Any]): Extra metadata for the operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        if "title" in metadata and metadata["title"]:
            return {}

        # Look for title in first line or markdown header
        lines = content.split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            if line:
                # Check for markdown header
                if line.startswith("#"):
                    title = line.lstrip("#").strip()
                    return {"title": title}
                # Use first non-empty line as title
                if len(line) < 200:  # Reasonable title length
                    return {"title": line}
                break

        return {}

    def _extract_dates(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract dates from content.
        
        Args:
            content (str): Content text.
            metadata (Dict[str, Any]): Extra metadata for the operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        extracted = {}

        # Look for date patterns
        date_patterns = [
            r"\b(\d{4}-\d{2}-\d{2})\b",  # YYYY-MM-DD
            r"\b(\d{2}/\d{2}/\d{4})\b",  # MM/DD/YYYY
            r"\b(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\b",  # DD Mon YYYY
        ]

        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                extracted["dates_found"] = matches[:5]  # Keep first 5 dates
                break

        return extracted

    def _extract_tags(self, content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract tags/keywords from content.
        
        Args:
            content (str): Content text.
            metadata (Dict[str, Any]): Extra metadata for the operation.
        
        Returns:
            Dict[str, Any]: Dictionary result of the operation.
        """
        extracted = {}

        # Look for hashtags or tag patterns
        hashtags = re.findall(r"#(\w+)", content)
        if hashtags:
            existing_tags = metadata.get("tags", [])
            extracted["tags"] = list(set(existing_tags + hashtags[:10]))  # Limit to 10 tags

        return extracted
