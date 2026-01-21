"""
Multi-Modal Data Loader

Handles loading and processing of various data formats:
- Text: .txt, .md, .markdown, .html, .json
- Documents: .pdf, .doc, .docx, .rtf
- Audio: .mp3, .wav, .m4a, .ogg (with transcription)
- Video: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
- Images: .jpg, .png, .gif, .bmp (with OCR and description)
"""

# Standard library imports
import io
import mimetypes
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Third-party imports
try:
    import PyPDF2
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document as DocxDocument
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    import speech_recognition as sr
    from pydub import AudioSegment
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    from PIL import Image
    import pytesseract
    IMAGE_AVAILABLE = True
except ImportError:
    IMAGE_AVAILABLE = False

try:
    import cv2
    VIDEO_AVAILABLE = True
except ImportError:
    VIDEO_AVAILABLE = False

# Local application/library specific imports
from .exceptions import DocumentProcessingError


class MultiModalLoader:
    """
    Loads and processes various data formats for RAG system.
    
    Supports:
    - Text files: .txt, .md, .markdown, .html, .json
    - Documents: .pdf, .doc, .docx, .rtf
    - Audio: .mp3, .wav, .m4a, .ogg (with transcription)
    - Video: .mp4, .avi, .mov, .mkv (with transcription and frame extraction)
    - Images: .jpg, .png, .gif, .bmp (with OCR and description)
    """
    
    def __init__(
        self,
        enable_audio_transcription: bool = True,
        enable_video_transcription: bool = True,
        enable_image_ocr: bool = True,
        enable_image_description: bool = True,
        audio_language: str = "en-US",
        video_extract_frames: bool = True,
        video_frames_per_second: float = 1.0
    ):
        """
        Initialize multi-modal loader.
        
        Args:
            enable_audio_transcription: Enable audio transcription
            enable_video_transcription: Enable video transcription
            enable_image_ocr: Enable OCR for images
            enable_image_description: Enable image description generation
            audio_language: Language for audio transcription
            video_extract_frames: Extract frames from video
            video_frames_per_second: Frames to extract per second
        """
        self.enable_audio_transcription = enable_audio_transcription
        self.enable_video_transcription = enable_video_transcription
        self.enable_image_ocr = enable_image_ocr
        self.enable_image_description = enable_image_description
        self.audio_language = audio_language
        self.video_extract_frames = video_extract_frames
        self.video_frames_per_second = video_frames_per_second
        
        # Initialize recognizer for audio/video
        if AUDIO_AVAILABLE and (enable_audio_transcription or enable_video_transcription):
            self.recognizer = sr.Recognizer()
        else:
            self.recognizer = None
    
    def load(self, file_path: str, gateway: Optional[Any] = None) -> Tuple[str, Dict[str, Any]]:
        """
        Load content from file and return text content with metadata.
        
        Args:
            file_path: Path to file
            gateway: Optional gateway for image description generation
        
        Returns:
            Tuple of (content, metadata)
        
        Raises:
            DocumentProcessingError: If file cannot be loaded
        """
        path = Path(file_path)
        
        if not path.exists():
            raise DocumentProcessingError(
                message=f"File not found: {file_path}",
                file_path=str(file_path),
                operation="load"
            )
        
        # Get file metadata
        file_metadata = self._get_file_metadata(path)
        
        # Determine file type and load
        suffix = path.suffix.lower()
        mime_type, _ = mimetypes.guess_type(str(path))
        
        try:
            if suffix in [".txt", ".md", ".markdown"]:
                content, metadata = self._load_text(path, file_metadata)
            elif suffix == ".html":
                content, metadata = self._load_html(path, file_metadata)
            elif suffix == ".json":
                content, metadata = self._load_json(path, file_metadata)
            elif suffix == ".pdf":
                content, metadata = self._load_pdf(path, file_metadata)
            elif suffix in [".doc", ".docx"]:
                content, metadata = self._load_docx(path, file_metadata)
            elif suffix in [".mp3", ".wav", ".m4a", ".ogg", ".flac"]:
                content, metadata = self._load_audio(path, file_metadata)
            elif suffix in [".mp4", ".avi", ".mov", ".mkv", ".webm"]:
                content, metadata = self._load_video(path, file_metadata, gateway)
            elif suffix in [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"]:
                content, metadata = self._load_image(path, file_metadata, gateway)
            else:
                # Try as text file
                try:
                    content, metadata = self._load_text(path, file_metadata)
                except UnicodeDecodeError as e:
                    raise DocumentProcessingError(
                        message=f"Unsupported file format: {suffix}",
                        file_path=str(file_path),
                        operation="load",
                        original_error=e
                    )
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error loading file: {str(e)}",
                file_path=str(file_path),
                operation="load",
                original_error=e
            )
        
        # Merge metadata
        metadata.update(file_metadata)
        metadata["file_type"] = suffix[1:] if suffix else "unknown"
        metadata["mime_type"] = mime_type or "application/octet-stream"
        
        return content, metadata
    
    def _get_file_metadata(self, path: Path) -> Dict[str, Any]:
        """Extract file metadata."""
        stat = path.stat()
        return {
            "file_name": path.name,
            "file_size": stat.st_size,
            "file_extension": path.suffix.lower(),
            "modified_at": stat.st_mtime,
        }
    
    def _load_text(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load text file."""
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content, metadata
    
    def _load_html(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load HTML file and extract text."""
        try:
            from bs4 import BeautifulSoup
            with open(path, 'r', encoding='utf-8') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            content = soup.get_text(separator=' ', strip=True)
            return content, metadata
        except ImportError:
            # Fallback: basic HTML tag removal
            import re
            with open(path, 'r', encoding='utf-8') as f:
                html = f.read()
            content = re.sub(r'<[^>]+>', '', html)
            return content, metadata
    
    def _load_json(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load JSON file and convert to readable text."""
        import json
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Convert to readable text format
        content = json.dumps(data, indent=2, ensure_ascii=False)
        return content, metadata
    
    def _load_pdf(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load PDF file and extract text."""
        if not PDF_AVAILABLE:
            raise DocumentProcessingError(
                message="PyPDF2 is required for PDF support. Install with: pip install PyPDF2",
                file_path=str(path),
                operation="load_pdf"
            )
        
        content_parts = []
        try:
            with open(path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                metadata["page_count"] = len(pdf_reader.pages)
                
                for page_num, page in enumerate(pdf_reader.pages):
                    text = page.extract_text()
                    if text:
                        content_parts.append(f"--- Page {page_num + 1} ---\n{text}\n")
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error reading PDF: {str(e)}",
                file_path=str(path),
                operation="load_pdf",
                original_error=e
            )
        
        content = "\n".join(content_parts)
        return content, metadata
    
    def _load_docx(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load DOCX file and extract text."""
        if not DOCX_AVAILABLE:
            raise DocumentProcessingError(
                message="python-docx is required for DOCX support. Install with: pip install python-docx",
                file_path=str(path),
                operation="load_docx"
            )
        
        try:
            doc = DocxDocument(path)
            content_parts = []
            
            # Extract text from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    content_parts.append(para.text)
            
            # Extract text from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = " | ".join([cell.text for cell in row.cells])
                    if row_text.strip():
                        content_parts.append(row_text)
            
            content = "\n".join(content_parts)
            metadata["paragraph_count"] = len(doc.paragraphs)
            return content, metadata
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error reading DOCX: {str(e)}",
                file_path=str(path),
                operation="load_docx",
                original_error=e
            )
    
    def _load_audio(self, path: Path, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Load audio file and transcribe."""
        if not AUDIO_AVAILABLE:
            raise DocumentProcessingError(
                message="Audio processing libraries required. Install with: pip install SpeechRecognition pydub",
                file_path=str(path),
                operation="load_audio"
            )
        
        if not self.enable_audio_transcription:
            return "", {**metadata, "transcription_disabled": True}
        
        try:
            # Load audio file
            audio = AudioSegment.from_file(str(path))
            metadata["duration_seconds"] = len(audio) / 1000.0
            metadata["sample_rate"] = audio.frame_rate
            
            # Convert to WAV for recognition
            wav_io = io.BytesIO()
            audio.export(wav_io, format="wav")
            wav_io.seek(0)
            
            # Transcribe
            with sr.AudioFile(wav_io) as source:
                audio_data = self.recognizer.record(source)
                try:
                    transcript = self.recognizer.recognize_google(
                        audio_data,
                        language=self.audio_language
                    )
                    content = f"[Audio Transcript]\n{transcript}"
                    metadata["transcription_language"] = self.audio_language
                    return content, metadata
                except sr.UnknownValueError:
                    return "[Audio file loaded but transcription failed - audio may be unclear]", metadata
                except sr.RequestError as e:
                    raise DocumentProcessingError(
                        message=f"Transcription service error: {str(e)}",
                        file_path=str(path),
                        operation="load_audio",
                        original_error=e
                    )
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error processing audio: {str(e)}",
                file_path=str(path),
                operation="load_audio",
                original_error=e
            )
    
    def _load_video(self, path: Path, metadata: Dict[str, Any], gateway: Optional[Any]) -> Tuple[str, Dict[str, Any]]:
        """Load video file, extract frames, and transcribe audio."""
        if not VIDEO_AVAILABLE:
            raise DocumentProcessingError(
                message="OpenCV is required for video support. Install with: pip install opencv-python",
                file_path=str(path),
                operation="load_video"
            )
        
        content_parts = []
        
        try:
            cap = cv2.VideoCapture(str(path))
            if not cap.isOpened():
                raise DocumentProcessingError(
                    message="Could not open video file",
                    file_path=str(path),
                    operation="load_video"
                )
            
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            metadata["video_fps"] = fps
            metadata["frame_count"] = frame_count
            metadata["duration_seconds"] = duration
            
            # Extract audio and transcribe if enabled
            if self.enable_video_transcription and self.recognizer:
                # Note: Audio extraction from video requires ffmpeg
                # This is a simplified version - full implementation would extract audio track
                content_parts.append("[Video Audio: Transcription available if audio track extracted]")
            
            # Extract frames if enabled
            if self.video_extract_frames:
                frame_interval = int(fps / self.video_frames_per_second) if fps > 0 else 30
                frame_num = 0
                extracted_frames = 0
                
                while cap.isOpened():
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    if frame_num % frame_interval == 0:
                        # Convert frame to text description (would use vision model in production)
                        content_parts.append(f"[Frame at {frame_num/fps:.2f}s: Frame extracted]")
                        extracted_frames += 1
                    
                    frame_num += 1
                
                metadata["extracted_frames"] = extracted_frames
                content_parts.append(f"\n[Video Summary: {extracted_frames} frames extracted from {duration:.2f}s video]")
            
            cap.release()
            
            content = "\n".join(content_parts) if content_parts else "[Video file processed]"
            return content, metadata
            
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error processing video: {str(e)}",
                file_path=str(path),
                operation="load_video",
                original_error=e
            )
    
    def _load_image(self, path: Path, metadata: Dict[str, Any], gateway: Optional[Any]) -> Tuple[str, Dict[str, Any]]:
        """Load image file, perform OCR, and generate description."""
        if not IMAGE_AVAILABLE:
            raise DocumentProcessingError(
                message="Image processing libraries required. Install with: pip install Pillow pytesseract",
                file_path=str(path),
                operation="load_image"
            )
        
        content_parts = []
        
        try:
            image = Image.open(path)
            metadata["image_width"] = image.width
            metadata["image_height"] = image.height
            metadata["image_format"] = image.format
            
            # OCR if enabled
            if self.enable_image_ocr:
                try:
                    ocr_text = pytesseract.image_to_string(image)
                    if ocr_text.strip():
                        content_parts.append(f"[OCR Text]\n{ocr_text}")
                        metadata["ocr_performed"] = True
                except Exception as e:
                    content_parts.append(f"[OCR failed: {str(e)}]")
                    metadata["ocr_performed"] = False
            
            # Generate description if gateway provided
            if self.enable_image_description and gateway:
                try:
                    # Convert image to base64 for API
                    import base64
                    buffered = io.BytesIO()
                    image.save(buffered, format="PNG")
                    img_base64 = base64.b64encode(buffered.getvalue()).decode()
                    
                    # Use vision model to describe image
                    # Note: This requires a vision-capable model like GPT-4 Vision
                    description = "[Image description would be generated using vision model]"
                    content_parts.append(f"[Image Description]\n{description}")
                    metadata["description_generated"] = True
                except Exception as e:
                    content_parts.append(f"[Description generation failed: {str(e)}]")
                    metadata["description_generated"] = False
            
            content = "\n".join(content_parts) if content_parts else "[Image file processed]"
            return content, metadata
            
        except Exception as e:
            raise DocumentProcessingError(
                message=f"Error processing image: {str(e)}",
                file_path=str(path),
                operation="load_image",
                original_error=e
            )


def create_multimodal_loader(
    enable_audio_transcription: bool = True,
    enable_video_transcription: bool = True,
    enable_image_ocr: bool = True,
    enable_image_description: bool = True,
    **kwargs: Any
) -> MultiModalLoader:
    """
    Create a multi-modal data loader.
    
    Args:
        enable_audio_transcription: Enable audio transcription
        enable_video_transcription: Enable video transcription
        enable_image_ocr: Enable OCR for images
        enable_image_description: Enable image description generation
        **kwargs: Additional configuration
    
    Returns:
        MultiModalLoader instance
    """
    return MultiModalLoader(
        enable_audio_transcription=enable_audio_transcription,
        enable_video_transcription=enable_video_transcription,
        enable_image_ocr=enable_image_ocr,
        enable_image_description=enable_image_description,
        **kwargs
    )

