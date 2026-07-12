"""Arabic shaping for Tk, which has no bidi/shaping engine of its own.

Reshapes Arabic into joined presentation forms and reorders to visual order so
Tk's left-to-right drawing shows correct right-to-left text. Latin text passes
through untouched. Degrades to a no-op if the libraries are missing.
"""
import textwrap

try:
    import arabic_reshaper
    # algorithm.get_display mirrors brackets/parentheses for RTL; the top-level
    # (Rust) get_display reorders but does not mirror them.
    try:
        from bidi.algorithm import get_display
    except ImportError:
        from bidi import get_display
    _reshaper = arabic_reshaper.ArabicReshaper(configuration={"delete_harakat": False})
    _OK = True
except Exception:
    _OK = False


def _has_arabic(text: str) -> bool:
    return any(0x0600 <= ord(c) <= 0x06FF or 0x0750 <= ord(c) <= 0x077F
               or 0xFB50 <= ord(c) <= 0xFDFF or 0xFE70 <= ord(c) <= 0xFEFF
               for c in text)


def shape(text: str) -> str:
    if not _OK or not text or not _has_arabic(text):
        return text
    return get_display(_reshaper.reshape(text))


def shape_wrapped(text: str, width: int = 42) -> str:
    """Wrap the LOGICAL text first, then shape each line, so multi-line RTL keeps
    its line order (shaping the whole paragraph then letting Tk wrap scrambles it)."""
    if not text:
        return text
    lines = textwrap.wrap(text, width=width) or [text]
    if _OK and _has_arabic(text):
        lines = [shape(line) for line in lines]
    return "\n".join(lines)
