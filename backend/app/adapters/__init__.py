"""Adapters package initialization."""
from app.adapters.face_provider import FaceProvider, EmbeddingFaceProvider, MockFaceProvider, get_face_provider, FaceComparisonResult
from app.adapters.textract_provider import TextractProvider, AwsTextractProvider, DevOcrFallbackProvider, get_textract_provider, ExtractedDocumentData

__all__ = [
    "FaceProvider",
    "EmbeddingFaceProvider",
    "MockFaceProvider",
    "get_face_provider",
    "FaceComparisonResult",
    "TextractProvider",
    "AwsTextractProvider",
    "DevOcrFallbackProvider",
    "get_textract_provider",
    "ExtractedDocumentData",
]
