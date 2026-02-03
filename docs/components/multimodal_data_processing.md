# MOTADATA - MULTI-MODAL DATA PROCESSING

**Documentation of multi-modal data processing capabilities supporting text, documents, audio, video, and images with automatic conversion for AI models.**

## Overview

The SDK supports comprehensive multi-modal data processing, allowing you to work with various data formats including text, documents, audio, video, and images. All data is automatically processed and converted to a format suitable for AI models, agents, and RAG systems.

---

## Supported Data Formats

### Text Files
- **Formats**: `.txt`, `.md`, `.markdown`, `.html`, `.json`
- **Processing**: Direct text extraction with encoding handling
- **Use Cases**: Documentation, articles, structured data

### Document Files
- **Formats**: `.pdf`, `.doc`, `.docx`, `.rtf`
- **Processing**: 
  - PDF: Text extraction from all pages
  - DOCX: Paragraph and table extraction
  - Metadata extraction (page count, structure)
- **Use Cases**: Reports, contracts, manuals

### Audio Files
- **Formats**: `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`
- **Processing**:
  - Automatic transcription using speech recognition
  - Language detection and configuration
  - Duration and sample rate metadata
- **Use Cases**: Podcasts, meetings, voice notes, interviews

### Video Files
- **Formats**: `.mp4`, `.avi`, `.mov`, `.mkv`, `.webm`
- **Processing**:
  - Audio track transcription
  - Frame extraction at configurable intervals
  - Video metadata (duration, FPS, frame count)
- **Use Cases**: Video tutorials, presentations, recordings

### Image Files
- **Formats**: `.jpg`, `.jpeg`, `.png`, `.gif`, `.bmp`, `.webp`
- **Processing**:
  - OCR (Optical Character Recognition) for text extraction
  - Image description generation using vision models
  - Image metadata (dimensions, format)
- **Use Cases**: Screenshots, scanned documents, diagrams, photos

---

## Data Loading Pipeline

### Automatic Format Detection

The system automatically detects file formats and applies appropriate processing:

```
File Input
    ↓
Format Detection (by extension and MIME type)
    ↓
Format-Specific Loader
    ↓
Text Extraction/Conversion
    ↓
Metadata Extraction
    ↓
Content Ready for Processing
```

### Processing Steps

1. **File Loading**: Reads file based on format
2. **Content Extraction**: Extracts text/content from file
3. **Metadata Extraction**: Extracts file and content metadata
4. **Normalization**: Converts to standardized text format
5. **Chunking**: Splits into manageable chunks (for RAG)
6. **Embedding**: Generates vector embeddings (for RAG)

---

## Usage Examples

### Loading Different File Types

```python
from src.core.rag import create_rag_system, create_multimodal_loader
from src.core.litellm_gateway import create_gateway
from src.core.postgresql_database import create_database

# Setup
db = create_database(connection_string="postgresql://...")
gateway = create_gateway(api_keys={"openai": "sk-..."})
rag = create_rag_system(db, gateway, enable_multimodal=True)

# Load and ingest different file types
# PDF document
rag.ingest_document(
    title="User Manual",
    file_path="manual.pdf"
)

# Audio file (will be transcribed)
rag.ingest_document(
    title="Meeting Recording",
    file_path="meeting.mp3"
)

# Video file (will extract audio and frames)
rag.ingest_document(
    title="Tutorial Video",
    file_path="tutorial.mp4"
)

# Image file (will perform OCR and generate description)
rag.ingest_document(
    title="Screenshot",
    file_path="screenshot.png"
)

# Word document
rag.ingest_document(
    title="Report",
    file_path="report.docx"
)
```

### Direct Content vs File Path

```python
# Option 1: Provide content directly
rag.ingest_document(
    title="My Document",
    content="This is the document content..."
)

# Option 2: Provide file path (for multi-modal processing)
rag.ingest_document(
    title="My Document",
    file_path="/path/to/document.pdf"
)
```

### Custom Multi-Modal Loader Configuration

```python
from src.core.rag import create_multimodal_loader, create_document_processor

# Create custom loader
loader = create_multimodal_loader(
    enable_audio_transcription=True,
    enable_video_transcription=True,
    enable_image_ocr=True,
    enable_image_description=True,
    audio_language="en-US",
    video_frames_per_second=1.0
)

# Use with document processor
processor = create_document_processor(
    enable_multimodal=True,
    gateway=gateway  # Required for image description
)

# Load file
content, metadata = processor.load_document("document.pdf")
```

---

## Integration with RAG System

### Automatic Processing

When you use `file_path` with the RAG system, it automatically:

1. Detects file format
2. Loads content using appropriate loader
3. Extracts metadata
4. Chunks content
5. Generates embeddings
6. Stores in vector database

### Querying Multi-Modal Content

```python
# Query works the same regardless of source format
results = await rag.query("What was discussed in the meeting?", limit=5)

# Results include content from:
# - Text documents
# - PDF pages
# - Audio transcripts
# - Video transcripts
# - Image OCR text
# - Image descriptions
```

---

## Integration with Agents

### Using Multi-Modal Data with Agents

```python
from src.core.agno_agent_framework import create_agent
from src.core.rag import create_rag_system

# Setup RAG with multi-modal support
rag = create_rag_system(db, gateway, enable_multimodal=True)

# Ingest various file types
rag.ingest_document(title="Video", file_path="video.mp4")
rag.ingest_document(title="Audio", file_path="audio.mp3")
rag.ingest_document(title="Image", file_path="image.jpg")

# Create agent that can query multi-modal content
agent = create_agent("assistant", "Multi-Modal Assistant", gateway)

# Agent can now answer questions about all ingested content
response = await agent.execute_task(
    "What information is in the video and image?"
)
```

---

## Configuration Options

### Multi-Modal Loader Options

```python
create_multimodal_loader(
    enable_audio_transcription=True,      # Enable audio transcription
    enable_video_transcription=True,        # Enable video transcription
    enable_image_ocr=True,                 # Enable OCR for images
    enable_image_description=True,         # Enable image description
    audio_language="en-US",                # Audio transcription language
    video_extract_frames=True,             # Extract frames from video
    video_frames_per_second=1.0            # Frames per second to extract
)
```

### Document Processor Options

```python
create_document_processor(
    enable_multimodal=True,                # Enable multi-modal support
    gateway=gateway,                       # Required for image description
    chunk_size=1000,                       # Chunk size for processing
    chunking_strategy="semantic"           # Chunking strategy
)
```

---

## Dependencies

### Required Libraries

For full multi-modal support, install:

```bash
# PDF support
pip install PyPDF2

# DOCX support
pip install python-docx

# Audio support
pip install SpeechRecognition pydub

# Image support
pip install Pillow pytesseract

# Video support
pip install opencv-python

# HTML parsing (optional)
pip install beautifulsoup4
```

### System Requirements

- **Tesseract OCR**: Required for image OCR
  - Ubuntu: `sudo apt-get install tesseract-ocr`
  - macOS: `brew install tesseract`
  - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

- **FFmpeg**: Required for audio/video processing
  - Ubuntu: `sudo apt-get install ffmpeg`
  - macOS: `brew install ffmpeg`
  - Windows: Download from [FFmpeg website](https://ffmpeg.org/download.html)

---

## Best Practices

1. **File Size**: Large files may take time to process. Consider chunking large videos/audios
2. **Language Configuration**: Set appropriate language for audio transcription
3. **Image Description**: Requires vision-capable models (e.g., GPT-4 Vision)
4. **Error Handling**: Some formats may fail - handle exceptions gracefully
5. **Metadata**: Leverage extracted metadata for better search and filtering
6. **Caching**: Cache processed content to avoid reprocessing

---

## Troubleshooting

### Common Issues

**Audio Transcription Fails**:
- Check audio quality and language settings
- Ensure audio file is not corrupted
- Verify SpeechRecognition library is installed

**Image OCR Fails**:
- Install Tesseract OCR
- Check image quality and resolution
- Ensure image contains readable text

**Video Processing Slow**:
- Reduce `video_frames_per_second` setting
- Process videos in background
- Consider extracting audio only

**PDF Extraction Issues**:
- Some PDFs may be image-based (use OCR)
- Complex layouts may require manual processing
- Ensure PyPDF2 is installed

---

## Related Documentation

- **[RAG System](rag_system_explanation.md)** - Complete RAG documentation
- **[Document Processor](../../src/core/rag/README.md)** - Document processing details
- **[Agent Framework](agno_agent_framework_explanation.md)** - Using agents with multi-modal data

