import re
from collections import Counter
from pathlib import Path
import json

STOPWORDS = {
    'the','and','is','in','to','of','a','it','that','i','you','we','they','he','she','for','on','with','as','this','was','are'
}

def transcribe(audio_path: str, model: str = 'small') -> str:
    """Transcribe an audio file using local Whisper (openai-whisper).

    Raises RuntimeError with instructions if whisper is not installed.
    """
    try:
        import whisper
    except Exception as e:
        raise RuntimeError('openai-whisper is required. Run the setup script (pip install -r requirements.txt).') from e

    model_obj = whisper.load_model(model)
    result = model_obj.transcribe(audio_path)
    return result.get('text', '').strip()


def analyze_voice(transcript: str) -> dict:
    """Produce a lightweight voice profile from transcript."""
    sentences = re.split(r'[\n\.!?]+', transcript)
    sentences = [s.strip() for s in sentences if s.strip()]

    words = re.findall(r"[A-Za-z']+", transcript.lower())
    words = [w for w in words if w not in STOPWORDS]

    avg_sentence_length = 0
    if sentences:
        avg_sentence_length = sum(len(s.split()) for s in sentences) / len(sentences)

    common_words = [w for w, _ in Counter(words).most_common(20)]

    # simple heuristics for tone
    contractions = len(re.findall(r"\b\w+'\w+\b", transcript))
    informal_score = contractions / (len(words) + 1)

    first_person = 'I' in transcript or 'i ' in transcript.lower()

    sample_phrases = sentences[:6]

    profile = {
        'avg_sentence_length': round(avg_sentence_length, 1),
        'top_words': common_words,
        'informal_score': round(informal_score, 3),
        'uses_first_person': bool(first_person),
        'sample_phrases': sample_phrases,
    }
    return profile


def write_voice_md(profile: dict, transcript: str, out_path: str = None):
    if out_path is None:
        out_path = Path(__file__).resolve().parents[2] / 'knowledge' / 'voice.md'
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    lines.append('# Voice Profile')
    lines.append('')
    lines.append('## Summary')
    tone = 'informal' if profile.get('informal_score', 0) > 0.03 else 'formal'
    lines.append(f'- Tone: {tone}')
    lines.append(f"- Average sentence length: {profile.get('avg_sentence_length')}")
    lines.append(f"- Uses first-person: {profile.get('uses_first_person')}")
    lines.append('')
    lines.append('## Top words')
    lines.append('')
    lines.append(', '.join(profile.get('top_words', [])))
    lines.append('')
    lines.append('## Sample phrases (from transcript)')
    lines.append('')
    for p in profile.get('sample_phrases', []):
        lines.append(f'- {p}')
    lines.append('')
    lines.append('## Full transcript')
    lines.append('')
    lines.append('```')
    lines.append(transcript)
    lines.append('```')

    out_path.write_text('\n'.join(lines), encoding='utf-8')
    return str(out_path)


def create_profile_from_audio(audio_path: str, model: str = 'small') -> dict:
    transcript = transcribe(audio_path, model=model)
    profile = analyze_voice(transcript)
    md_path = write_voice_md(profile, transcript)
    return {'transcript': transcript, 'profile': profile, 'path': md_path}
