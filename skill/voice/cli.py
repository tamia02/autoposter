import argparse
from skill.voice.ingest import create_profile_from_audio


def main():
    p = argparse.ArgumentParser()
    p.add_argument('audio', help='Path to audio file to ingest')
    p.add_argument('--model', default='small', help='Whisper model to use')
    args = p.parse_args()

    res = create_profile_from_audio(args.audio, model=args.model)
    print('Transcript saved and voice profile written to:', res['path'])


if __name__ == '__main__':
    main()
