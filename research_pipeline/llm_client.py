import os
import json
import re
import time
from openai import OpenAI
from config import NVIDIA_BASE_URL, LLM_TEMPERATURE, LLM_MAX_TOKENS


def get_client() -> OpenAI:
    api_key = os.getenv("NVIDIA_API_KEY")
    if not api_key:
        raise ValueError("NVIDIA_API_KEY not set in environment")
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)


def extract_json(text: str):
    text = text.strip()
    # Unwrap markdown code block if present
    match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
    if match:
        text = match.group(1).strip()
    # Find the first JSON array or object
    for opener, closer in [('[', ']'), ('{', '}')]:
        start = text.find(opener)
        if start == -1:
            continue
        # Walk to find the matching closer, handling nesting
        depth, in_str, escape = 0, False, False
        for i, ch in enumerate(text[start:], start):
            if escape:
                escape = False
                continue
            if ch == '\\' and in_str:
                escape = True
                continue
            if ch == '"':
                in_str = not in_str
                continue
            if in_str:
                continue
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    return json.loads(text[start:i+1])
    raise ValueError(f"No JSON found in response: {text[:200]}")


def call_llm(client: OpenAI, model: str, system: str, user: str, retries: int = 3) -> str:
    for attempt in range(retries + 1):
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user",   "content": user},
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
            return resp.choices[0].message.content or ""
        except Exception as e:
            if attempt == retries:
                raise
            # Exponential backoff: 5s, 10s, 20s — handles 429 rate limits
            wait = 5 * (2 ** attempt)
            print(f"    [retry {attempt+1}] {e} — waiting {wait}s")
            time.sleep(wait)
    return ""
