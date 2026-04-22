# app/core/exceptions.py
"""
Custom exception hierarchy for the application.
Router layer catches these and maps to HTTP responses via exception handlers.
This keeps business logic free of HTTP concerns (status codes, response format).
"""


class AppException(Exception):
    """Base exception for all application errors."""

    def __init__(self, message: str, status_code: int = 500, detail: str = None):
        self.message = message
        self.status_code = status_code
        self.detail = detail or message
        super().__init__(self.message)


# ── Resource Not Found ──

class CollectionNotFound(AppException):
    def __init__(self, collection_id: int):
        super().__init__(
            message=f"Collection {collection_id} not found",
            status_code=404,
        )


class ConversationNotFound(AppException):
    def __init__(self, conversation_id: int):
        super().__init__(
            message=f"Conversation {conversation_id} not found",
            status_code=404,
        )


class UserNotFound(AppException):
    def __init__(self, username: str):
        super().__init__(
            message=f"User '{username}' not found",
            status_code=404,
        )


# ── External Service Errors ──

class LLMServiceError(AppException):
    """LLM API call failed (OpenRouter, etc.)."""

    def __init__(self, detail: str):
        super().__init__(
            message="LLM service is temporarily unavailable",
            status_code=503,
            detail=detail,
        )


class VectorStoreError(AppException):
    """FAISS / vector store operation failed."""

    def __init__(self, detail: str):
        super().__init__(
            message="Vector store error",
            status_code=500,
            detail=detail,
        )


# ── Auth / Validation ──

class InvalidCredentials(AppException):
    def __init__(self):
        super().__init__(
            message="Invalid username or password",
            status_code=401,
        )


class DuplicateUser(AppException):
    def __init__(self, username: str):
        super().__init__(
            message=f"Username '{username}' is already registered",
            status_code=409,
        )


class InvalidFileFormat(AppException):
    def __init__(self, expected: str, received: str):
        super().__init__(
            message=f"Expected {expected} file, got {received}",
            status_code=400,
        )
