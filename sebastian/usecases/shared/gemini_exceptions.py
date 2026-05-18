class TransientGeminiError(Exception):
    """Raised for transient Gemini failures that should be retried later."""


class NonRetryableGeminiError(Exception):
    """Raised for Gemini failures that should not be retried automatically."""
