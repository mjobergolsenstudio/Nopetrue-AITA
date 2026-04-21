import anthropic
import json
import os

def summarize_story(story):
    client = anthropic.Anthropic(api_key=os.environ['ANTHROPIC_API_KEY'])

    prompt = f"""You are creating a YouTube Shorts script for an AITA story.

ORIGINAL STORY:
Title: {story['title']}
{story['body'][:3000]}

TASK: Rewrite this as a compelling 90-110 word script for a YouTube Short.
- Start with a hook like "So this actually happened..." or "I need your opinion on this..."
- Keep it first person, conversational, fast-paced
- Include the key conflict and context
- End with "Am I the asshole? Comment below!"
- NO markdown, NO headers, just plain text
- Exactly 90-110 words

Return ONLY the script text, nothing else."""

    message = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=300,
        messages=[{'role': 'user', 'content': prompt}]
    )

    script = message.content[0].text.strip()
    print(f"Script ({len(script.split())} words):\n{script}\n")
    return script

if __name__ == '__main__':
    story = {'title': 'Test', 'body': 'I did something and my friend got mad. Was I wrong?'}
    print(summarize_story(story))
