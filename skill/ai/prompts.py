from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

PLATFORM_INSTRUCTIONS = {
    'linkedin': (
        "Write a LinkedIn post. Follow these rules EXACTLY:\n\n"
        "STRUCTURE:\n"
        "1. HOOK — One punchy first line that stops the scroll. Then a blank line.\n"
        "2. CONTEXT — 2-3 short lines setting up the problem or story. Then blank line.\n"
        "3. VALUE — Numbered list (1. 2. 3.) or arrow bullets (→) with actionable steps/tips.\n"
        "4. TAKEAWAY — 1-2 lines, the 'so what' insight.\n"
        "5. CTA — A conversational question or engagement prompt. NOT 'like and share'.\n\n"
        "FORMATTING:\n"
        "- Short paragraphs (1-3 sentences MAX)\n"
        "- Blank line between EVERY section\n"
        "- Use → arrows or numbers for lists\n"
        "- 200-350 words (the viral sweet spot)\n"
        "- Use 'I' and 'you' — never corporate speak\n"
        "- Be opinionated. Take a stance.\n\n"
        "HOOK FORMULAS (pick one):\n"
        "- 'I [did something unexpected] — here's what happened.'\n"
        "- 'Most people think [X]. They're wrong.'\n"
        "- 'I spent [time] doing [Y]. Here's what I learned.'\n"
        "- '[Number] [things] that [dream outcome] without [obstacle]'\n"
        "- Personal story: '3 years ago I was [struggle]...'\n\n"
        "CTA FORMULAS (pick one):\n"
        "- 'Which one resonates most? Drop a number below.'\n"
        "- 'What would you add to this?'\n"
        "- 'DM me [keyword] and I'll send you the full playbook.'\n"
        "- 'Save this. You'll need it.'\n"
        "- 'Repost if someone in your network needs this ♻️'\n\n"
        "NEVER use hashtags. No #anything. Zero hashtags.\n"
        "NEVER use markdown formatting. No **bold**, no *italic*, no bullet points with -.\n"
        "Use plain text only. Use line breaks and numbers (1. 2. 3.) for structure.\n"
        "Use arrow symbols like → instead of bullet points.\n"
        "Write like Charles Miller — use 'How I' not 'How to'. Share YOUR experience."
    ),
    'x': (
        "Write an X (Twitter) thread. Rules:\n\n"
        "- 5-8 tweets, each STRICTLY under 280 characters\n"
        "- NEVER use markdown. No **bold**, no *italic*. Plain text only.\n"
        "- Number each: 1/ 2/ 3/ etc.\n"
        "- Tweet 1 = HOOK that makes people click 'Show thread'\n"
        "- Each tweet = ONE idea, punchy and direct\n"
        "- Use 'I' not 'you should'\n"
        "- Last tweet = CTA: 'Follow for more' or 'Repost the first tweet'\n"
        "- Be opinionated. No hedging.\n"
        "- NEVER use hashtags. Zero hashtags anywhere."
    ),
    'threads': (
        "Write a Threads post. Rules:\n\n"
        "- 120-200 words\n"
        "- Casual, raw, like texting a friend\n"
        "- Start with a hot take or bold statement\n"
        "- Share a personal mini-story or observation\n"
        "- End with a spicy question that invites replies\n"
        "- NEVER use hashtags. No corporate tone.\n"
        "- NEVER use markdown. No **bold**, no *italic*. Plain text only.\n"
        "- Use line breaks between thoughts"
    ),
}


def _load_style_guide() -> str:
    path = ROOT / 'knowledge' / 'style_guide.md'
    if path.exists():
        return path.read_text(encoding='utf-8')
    return ''


def build_system_prompt(platform: str, voice_profile: str) -> str:
    platform_guide = PLATFORM_INSTRUCTIONS.get(platform, PLATFORM_INSTRUCTIONS['linkedin'])
    style_guide = _load_style_guide()

    parts = [
        "You are an elite LinkedIn ghostwriter who has studied the writing frameworks of "
        "Jasmin Alic, Matt Barker, Lara Acosta, and Charles Miller. You write viral, "
        "educational, value-driven content that gets massive engagement.\n\n"
        "YOUR CLIENT'S VOICE PROFILE:\n"
        f"{voice_profile}\n\n"
        "PLATFORM RULES:\n"
        f"{platform_guide}\n\n"
        "CRITICAL RULES:\n"
        "- Never mention you are AI or that this was generated\n"
        "- Use the research as INSPIRATION — never copy competitor content\n"
        "- Write in first person as if you ARE the client\n"
        "- Be specific with numbers, examples, and real scenarios\n"
        "- Every line must earn the next line. No filler.\n"
        "- Output ONLY the post text. No preamble, no explanation.\n"
    ]

    if style_guide:
        parts.append(
            "STYLE GUIDE (follow this framework):\n"
            f"{style_guide[:2000]}\n"
        )

    return '\n'.join(parts)


def build_user_prompt(topic: str, research: str, competitor_signals: str, platform: str) -> str:
    parts = [f"Write a {platform} post about: {topic}\n"]

    if research.strip():
        parts.append(f"RESEARCH & CONTEXT:\n{research[:1500]}\n")

    if competitor_signals.strip():
        parts.append(
            f"COMPETITOR POSTS ON THIS TOPIC (use as inspiration, rewrite in MY voice):\n"
            f"{competitor_signals[:1000]}\n"
        )

    parts.append(
        "Now write the post. Follow the structure exactly: "
        "Hook → Context → Value (numbered/arrows) → Takeaway → CTA. "
        "Make it educational, actionable, and something that would go viral. "
        "Sound like ME, not like a generic AI post."
    )
    return "\n".join(parts)


def build_image_prompt(topic: str, platform: str) -> str:
    return (
        f"Generate a short, punchy quote (under 12 words) for a social media "
        f"share image about: {topic}\n\n"
        f"Make it bold, memorable, and shareable. Like something you'd see on a "
        f"carousel slide. Output ONLY the quote text, nothing else."
    )
