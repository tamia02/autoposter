import os
import yaml
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parents[1]


def load_calendar():
    cal = ROOT / 'calendar.yaml'
    if not cal.exists():
        return []
    return yaml.safe_load(cal.read_text())


def render_image(html, out_path):
    from skill.renderer.render_image import render_html_to_image
    render_html_to_image(html, out_path)


def write_draft(platform, content, image_path=None):
    drafts = ROOT / 'drafts'
    drafts.mkdir(exist_ok=True)
    f = drafts / f"{platform}_draft.md"
    with f.open('w', encoding='utf-8') as fh:
        fh.write(content)
        if image_path:
            fh.write(f"\n\nImage: {image_path}\n")
    print('Wrote draft:', f)


def main():
    from skill.orchestrate import main as orchestrate_main
    orchestrate_main()


def ingest_voice(audio_path: str, model: str = 'small'):
    from skill.voice.ingest import create_profile_from_audio
    return create_profile_from_audio(audio_path, model=model)


if __name__ == '__main__':
    main()
