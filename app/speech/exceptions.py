"""Speech provider domain exceptions."""


class SpeechConfigError(Exception):
    """Raised when speech provider settings are missing or invalid."""


class SpeechAPIError(Exception):
    """Raised when a speech provider API call fails."""
