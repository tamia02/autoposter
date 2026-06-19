import re
from typing import List


def extract_sentences(text: str, count: int = 3) -> List[str]:
    """Extract key sentences from text (simple heuristic: longest sentences first)."""
    sents = re.split(r'(?<=[\.\?!])\s+', text)
    sents = [s.strip() for s in sents if s.strip() and len(s.split()) > 3]
    # Sort by length (longer = more informative heuristic)
    sents.sort(key=len, reverse=True)
    return sents[:count]


def summarize_extractive(texts: List[str], max_sentences: int = 5) -> str:
    """Extract key sentences from a list of text snippets."""
    all_sents = []
    for text in texts:
        sents = extract_sentences(text, count=2)
        all_sents.extend(sents)
    
    # Remove duplicates (simple string match)
    unique = []
    for s in all_sents:
        if s not in unique:
            unique.append(s)
    
    return ' '.join(unique[:max_sentences])


def research_to_snippet(research_text: str) -> str:
    """Convert research output to a short snippet for content generation."""
    lines = research_text.split('\n')
    snippet_lines = [l for l in lines if l.strip() and not l.startswith('Research on')]
    return ' '.join(snippet_lines)[:300]
