"""
Text preprocessing utilities for cleaning text before embedding.
"""
import re
import unicodedata

# Compiled regex patterns for performance
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_MULTI_SPACE_RE = re.compile(r"\s+")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_EMAIL_RE = re.compile(r"\S+@\S+\.\S+")


def strip_html_tags(text: str) -> str:
    """Remove HTML tags from text."""
    return _HTML_TAG_RE.sub(" ", text)


def normalize_unicode(text: str) -> str:
    """Normalize unicode characters to NFC form."""
    return unicodedata.normalize("NFC", text)


def collapse_whitespace(text: str) -> str:
    """Replace multiple whitespace characters with a single space."""
    return _MULTI_SPACE_RE.sub(" ", text).strip()


def remove_urls(text: str) -> str:
    """Remove URLs from text."""
    return _URL_RE.sub("", text)


def remove_emails(text: str) -> str:
    """Remove email addresses from text."""
    return _EMAIL_RE.sub("", text)


def truncate_text(text: str, max_length: int) -> str:
    """Truncate text to max_length characters, breaking at word boundary."""
    if len(text) <= max_length:
        return text
    truncated = text[:max_length]
    last_space = truncated.rfind(" ")
    if last_space > max_length * 0.8:
        truncated = truncated[:last_space]
    return truncated


class TextPreprocessor:
    """
    Pipeline for cleaning and normalizing text before embedding.

    Applies a sequence of transformations to ensure consistent
    and high-quality input for the embedding model.
    """

    def __init__(
        self,
        lowercase: bool = False,
        strip_html: bool = True,
        max_length: int = 10000,
        enable: bool = True
    ):
        self._lowercase = lowercase
        self._strip_html = strip_html
        self._max_length = max_length
        self._enabled = enable

    def preprocess(self, text: str) -> str:
        """Apply the full preprocessing pipeline to a single text."""
        if not self._enabled:
            return text

        if not text or not text.strip():
            return ""

        text = normalize_unicode(text)

        if self._strip_html:
            text = strip_html_tags(text)

        text = remove_urls(text)
        text = remove_emails(text)

        if self._lowercase:
            text = text.lower()

        text = collapse_whitespace(text)
        text = truncate_text(text, self._max_length)

        return text

    def preprocess_batch(self, texts: list) -> list:
        """Apply preprocessing to a batch of texts."""
        return [self.preprocess(t) for t in texts]
