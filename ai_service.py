import os
import json
from urllib.request import Request, urlopen
from urllib.error import HTTPError


def _get_config():
    return {
        "base_url": os.getenv("AI_BASE_URL", "https://api.deepseek.com"),
        "api_key": os.getenv("AI_API_KEY", ""),
        "model": os.getenv("AI_MODEL", "deepseek-chat"),
    }


def _call_ai(system_prompt: str, user_prompt: str) -> str:
    cfg = _get_config()
    if not cfg["api_key"]:
        raise RuntimeError("AI_API_KEY not configured")

    body = json.dumps({
        "model": cfg["model"],
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }).encode()

    req = Request(
        f"{cfg['base_url']}/v1/chat/completions",
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {cfg['api_key']}",
        },
    )

    try:
        with urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read())
    except HTTPError as e:
        detail = e.read().decode()
        raise RuntimeError(f"AI request failed: {e.code} — {detail}")

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("AI returned no choices")

    for i, choice in enumerate(choices):
        content = (choice.get("message", {}) or {}).get("content", "")
        if content and content.strip():
            finish_reason = choice.get("finish_reason", "unknown")
            if finish_reason == "length":
                raise RuntimeError("AI response was truncated — try again.")
            return content.strip()

    finish_reasons = [c.get("finish_reason", "?") for c in choices]
    raise RuntimeError(
        f"AI returned empty content in all {len(choices)} choice(s) "
        f"(finish_reasons={finish_reasons}). "
        "Try again — the model may have refused or the response was filtered."
    )


METHOD_SYSTEM_PROMPT = """You are an expert mixologist and cocktail writer. When given a cocktail recipe, write detailed, professional preparation steps. Follow these guidelines strictly:

- Write in Portuguese, in the style of a craft cocktail bar.
- Be specific about technique: specify "stir for 15 seconds", "shake vigorously for 12 seconds", "build in the glass over a large ice cube", etc.
- Mention glass preparation: "chill a coupe glass", "rinse the glass with absinthe", etc.
- Specify ice type when relevant: "large ice cube", "cracked ice", "ice-filled mixing glass".
- Specify straining method: "double strain into a chilled glass", "fine strain", "single strain over fresh ice".
- Include garnish placement: "express lemon peel over the surface and discard", "place the lime wheel on the rim".
- Mention the mixing vessel when relevant: "in a mixing glass", "in a shaker tin", "in the serving glass".
- List steps as numbered, concise instructions — one technique per step.
- Do NOT include ingredient amounts (they are already listed separately). Refer to ingredients by name.
- Output ONLY the preparation steps, no intro, no outro, no commentary."""


TAGS_SYSTEM_PROMPT = """You are a cocktail categorization expert. Given a cocktail recipe, generate 3-5 concise, lowercase tags that describe its flavor profile, style, and character. Return ONLY the tags as a JSON array of strings.

Examples: ["refreshing", "citrusy", "bitter"], ["boozy", "stirred", "spirit-forward"], ["tropical", "sweet", "fruity"]

- Write in Portuguese

Do NOT include any explanation, just the JSON array."""


def generate_method(cocktail_data: dict) -> str:
    ingredients_text = "\n".join(
        f"- {ing.get('name', ing.get('ingredient_type_name', 'unknown'))}: {ing.get('amount', '')} {ing.get('unit', 'ml')}"
        for ing in cocktail_data.get("ingredients", [])
    )

    glasses_text = ", ".join(
        g.get("name", g.get("inventory_item_name", "appropriate glass"))
        for g in cocktail_data.get("glasses", [])
    ) or "appropriate glassware"

    user_prompt = f"""Cocktail name: {cocktail_data.get('name', 'Unknown')}

Ingredients:
{ingredients_text}

Garnish: {cocktail_data.get('garnish', 'none specified')}
Glass: {glasses_text}
Base spirit: {cocktail_data.get('base_spirit', 'not specified')}

Write the preparation method."""

    return _call_ai(METHOD_SYSTEM_PROMPT, user_prompt)


def generate_tags(cocktail_data: dict) -> list[str]:
    ingredients_text = ", ".join(
        ing.get("name", ing.get("ingredient_type_name", "unknown"))
        for ing in cocktail_data.get("ingredients", [])
    )

    user_prompt = f"""Cocktail name: {cocktail_data.get('name', 'Unknown')}
Base spirit: {cocktail_data.get('base_spirit', '')}
Ingredients: {ingredients_text}

Generate tags."""

    result = _call_ai(TAGS_SYSTEM_PROMPT, user_prompt)
    try:
        tags = json.loads(result)
        if isinstance(tags, list):
            return tags
    except json.JSONDecodeError:
        pass
    return [t.strip().strip('"').strip("'") for t in result.strip("[]").split(",") if t.strip()]
