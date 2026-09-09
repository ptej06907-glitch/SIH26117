"""Conservative evidence screening; not a guarantee of injection detection."""
import re
import unicodedata

PATTERNS = (
    r'ignore\s+(?:all\s+)?(?:previous|prior|system|above)\s+instructions',
    r'(?:override|bypass|disable)\s+(?:the\s+)?(?:approval|security|system|safety)\b',
    r'(?:reveal|print|send|exfiltrate)\s+(?:the\s+)?(?:passwords?|secrets?|api\s*keys?|system\s*prompt)',
    r'(?:<\|(?:system|im_start)\|>|\[INST\]|</?system>)',
    r'you\s+are\s+now\s+(?:an?\s+)?(?:administrator|system|unrestricted)',
)

def suspicious(text):
    normalized=unicodedata.normalize('NFKC',text)
    normalized=''.join(c for c in normalized if unicodedata.category(c)!='Cf')
    return any(re.search(pattern,normalized,re.I) for pattern in PATTERNS)

def screen_records(records):
    # Exclude the full page, rather than retaining an adjacent continuation of
    # an attacker instruction. Originals remain available for human inspection.
    return [r for r in records if not suspicious(r['text'])]
