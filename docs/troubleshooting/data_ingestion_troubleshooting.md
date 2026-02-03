# MOTADATA - DATA INGESTION SERVICE TROUBLESHOOTING

**Troubleshooting guide for diagnosing and resolving common issues with the Data Ingestion Service.**

## Common Issues and Solutions

### File Upload Failures

#### Problem: File Not Found Error
**Symptoms:**
```
DataIngestionError: File not found: /path/to/file.pdf
```

**Solutions:**
1. Verify file path is correct and absolute
2. Check file permissions (read access required)
3. Ensure file exists before calling `upload_and_process()`

```python
from pathlib import Path

file_path = Path("document.pdf")
if not file_path.exists():
    raise FileNotFoundError(f"File not found: {file_path}")
```

---

#### Problem: Unsupported File Format
**Symptoms:**
```
ValidationError: Unsupported format: .xyz
```

**Solutions:**
1. Check supported formats in documentation
2. Verify file extension matches actual file type
3. Use Data Ingestion Service which supports:
   - Text: `.txt`, `.md`, `.html`, `.json`
   - Documents: `.pdf`, `.doc`, `.docx`
   - Audio: `.mp3`, `.wav`, `.m4a`, `.ogg`
   - Video: `.mp4`, `.avi`, `.mov`, `.mkv`
   - Images: `.jpg`, `.png`, `.gif`, `.bmp`
   - Structured: `.csv`, `.json`, `.xml`, `.xlsx`

---

### Format Validation Errors

#### Problem: File Too Large
**Symptoms:**
```
ValidationError: File too large: 600000000 bytes (max: 524288000)
```

**Solutions:**
1. Reduce file size or split into smaller files
2. Increase `max_file_size` in validator configuration
3. Compress file if possible

```python
from src.core.data_ingestion import DataValidator

validator = DataValidator(
    max_file_size=1024 * 1024 * 1024  # 1 GB
)
```

---

#### Problem: MIME Type Mismatch
**Symptoms:**
```
ValidationError: MIME type mismatch: application/octet-stream for .pdf
```

**Solutions:**
1. Verify file is not corrupted
2. Check file extension matches actual content
3. Re-save file in correct format

---

### Processing Errors

#### Problem: PDF Extraction Fails
**Symptoms:**
```
DocumentProcessingError: Error reading PDF: ...
```

**Solutions:**
1. Install PyPDF2: `pip install PyPDF2`
2. Verify PDF is not password-protected
3. Check if PDF is image-based (may need OCR)
4. Try alternative PDF library

```python
# Check if PDF is readable
try:
    import PyPDF2
    with open("file.pdf", "rb") as f:
        reader = PyPDF2.PdfReader(f)
        print(f"Pages: {len(reader.pages)}")
except Exception as e:
    print(f"PDF error: {e}")
```

---

#### Problem: Audio Transcription Fails
**Symptoms:**
```
DocumentProcessingError: Transcription service error: ...
```

**Solutions:**
1. Install required libraries: `pip install SpeechRecognition pydub`
2. Check audio quality and clarity
3. Verify audio language matches configuration
4. Ensure audio file is not corrupted

```python
# Check audio processing
from src.core.data_ingestion import create_ingestion_service

service = create_ingestion_service(
    gateway=gateway,
    enable_audio_transcription=True
)
```

---

#### Problem: Image OCR Fails
**Symptoms:**
```
DocumentProcessingError: OCR failed: ...
```

**Solutions:**
1. Install Tesseract OCR:
   - Ubuntu: `sudo apt-get install tesseract-ocr`
   - macOS: `brew install tesseract`
   - Windows: Download from GitHub
2. Check image quality and resolution
3. Verify image contains readable text
4. Try image preprocessing (contrast, brightness)

```python
# Test OCR
from PIL import Image
import pytesseract

image = Image.open("screenshot.png")
text = pytesseract.image_to_string(image)
print(f"OCR text: {text}")
```

---

### RAG Ingestion Failures

#### Problem: Document Not Ingested into RAG
**Symptoms:**
```
result["ingested"] = False
result["document_id"] = None
```

**Solutions:**
1. Verify RAG system is provided to ingestion service
2. Check database connection
3. Ensure RAG system is properly initialized
4. Verify `enable_auto_ingest=True`

```python
from src.core.data_ingestion import create_ingestion_service
from src.core.rag import create_rag_system

# Ensure RAG is provided
rag = create_rag_system(db, gateway)
service = create_ingestion_service(
    rag_system=rag,  # Must provide RAG
    enable_auto_ingest=True  # Must be enabled
)
```

---

#### Problem: Embedding Generation Fails
**Symptoms:**
```
Error during RAG ingestion: Embedding generation failed
```

**Solutions:**
1. Verify gateway is properly configured
2. Check API keys are valid
3. Ensure embedding model is available
4. Check network connectivity

```python
# Test gateway
from src.core.litellm_gateway import create_gateway

gateway = create_gateway(api_keys={"openai": "sk-..."})
test_embedding = await gateway.embed_async("test", model="text-embedding-3-small")
print(f"Embedding dimension: {len(test_embedding.embeddings[0])}")
```

---

### Cache Integration Problems

#### Problem: Content Not Cached
**Symptoms:**
```
result["cached"] = False
```

**Solutions:**
1. Verify cache is provided to ingestion service
2. Check `enable_caching=True`
3. Verify cache backend is working

```python
from src.core.cache_mechanism import create_cache_mechanism

cache = create_cache_mechanism()
service = create_ingestion_service(
    cache=cache,  # Must provide cache
    enable_caching=True  # Must be enabled
)

# Test cache
cache.set("test", "value")
value = cache.get("test")
print(f"Cache working: {value == 'value'}")
```

---

### Batch Processing Errors

#### Problem: Some Files Fail in Batch
**Symptoms:**
```
results = [
    {"success": True, ...},
    {"success": False, "error": "..."},
    {"success": True, ...}
]
```

**Solutions:**
1. Check individual file errors in results
2. Validate all files before batch processing
3. Handle errors per file

```python
from src.core.data_ingestion import batch_upload_and_process

results = batch_upload_and_process(
    ["file1.pdf", "file2.mp3", "file3.jpg"],
    rag_system=rag,
    cache=cache
)

# Check each result
for result in results:
    if not result["success"]:
        print(f"Failed: {result['file_path']} - {result.get('error')}")
```

---

### Multi-Modal Loading Issues

#### Problem: Video Processing Slow
**Symptoms:**
- Video processing takes very long
- Timeout errors

**Solutions:**
1. Reduce `video_frames_per_second` setting
2. Process videos asynchronously
3. Extract audio only if frames not needed
4. Process in background jobs

```python
from src.core.rag.multimodal_loader import create_multimodal_loader

loader = create_multimodal_loader(
    video_frames_per_second=0.5,  # Extract fewer frames
    enable_video_transcription=True
)
```

---

#### Problem: Image Description Not Generated
**Symptoms:**
```
metadata["description_generated"] = False
```

**Solutions:**
1. Verify gateway is provided (required for vision models)
2. Check if vision-capable model is available (GPT-4 Vision, Claude 3 Vision)
3. Ensure `enable_image_description=True`

```python
# Vision models require gateway
service = create_ingestion_service(
    gateway=gateway,  # Required for image description
    enable_image_description=True
)
```

---

## Diagnostic Steps

### Step 1: Verify File
```python
from pathlib import Path

file_path = Path("your_file.pdf")
print(f"Exists: {file_path.exists()}")
print(f"Size: {file_path.stat().st_size} bytes")
print(f"Extension: {file_path.suffix}")
```

### Step 2: Test Validation
```python
from src.core.data_ingestion import DataValidator

validator = DataValidator()
result = validator.validate_file(Path("your_file.pdf"))
print(f"Valid: {result['valid']}")
if not result["valid"]:
    print(f"Error: {result['error']}")
```

### Step 3: Test Processing
```python
from src.core.rag.multimodal_loader import create_multimodal_loader

loader = create_multimodal_loader()
try:
    content, metadata = loader.load("your_file.pdf", gateway=gateway)
    print(f"Content length: {len(content)}")
    print(f"Metadata: {metadata}")
except Exception as e:
    print(f"Processing error: {e}")
```

### Step 4: Test Full Pipeline
```python
from src.core.data_ingestion import upload_and_process

try:
    result = upload_and_process(
        "your_file.pdf",
        rag_system=rag,
        cache=cache
    )
    print(f"Success: {result['success']}")
    print(f"Document ID: {result['document_id']}")
except Exception as e:
    print(f"Error: {type(e).__name__}: {e}")
```

---

## Best Practices

1. **Always Validate Files First**: Check file exists and is readable
2. **Handle Errors Gracefully**: Use try-except for upload operations
3. **Check Dependencies**: Ensure required libraries are installed
4. **Test Format Support**: Verify format is supported before processing
5. **Monitor Processing**: Use async methods for large files
6. **Verify Integration**: Check RAG and cache are properly configured

---

## Related Documentation

- **[Data Ingestion Service](../../src/core/data_ingestion/README.md)** - Component documentation
- **[Multi-Modal Processing](../components/multimodal_data_processing.md)** - Format support
- **[RAG System Troubleshooting](rag_system_troubleshooting.md)** - RAG-specific issues
- **[Cache Mechanism Troubleshooting](cache_mechanism_troubleshooting.md)** - Cache issues

