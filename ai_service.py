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


SUGGEST_SYSTEM_PROMPT = """You are an expert mixologist. You are given a list of available ingredients, glassware, and accessories from someone's home bar. Suggest 2-4 classic or creative cocktails they can make right now using ONLY the items listed.

For each suggestion, provide:
- name: The cocktail name
- base_spirit: The main spirit category (e.g., "Gin", "Whiskey", "Rum")
- ingredients: Array of {name: string, amount: number, unit: "ml"} — use ONLY ingredient names from the available list
- glass: The glassware name from the available list (or suggest "Rocks Glass" / "Coupe" if the bar has it)
- method: Detailed preparation steps (in Portuguese, numbered, with specific technique details)
- garnish: Garnish suggestion
- tags: Array of 3-5 strings describing the cocktail (in Portuguese)

Return ONLY a JSON array of cocktail objects. No intro, no outro, no markdown fences.

Example format:
[{"name":"Negroni","base_spirit":"Gin","ingredients":[{"name":"London Dry Gin","amount":30,"unit":"ml"},{"name":"Sweet Vermouth","amount":30,"unit":"ml"},{"name":"Campari","amount":30,"unit":"ml"}],"glass":"Rocks Glass","method":"1. Fill a mixing glass with ice.\\n2. Add all ingredients.\\n3. Stir for 20 seconds.\\n4. Strain into a rocks glass over a large ice cube.\\n5. Express an orange peel over the surface and drop it in.","garnish":"Orange peel","tags":["amargo","clássico","boozy","italiano"]}]"""


def suggest_cocktails(available_items: list[dict]) -> list[dict]:
    ingredients_list = []
    glasses_list = []
    accessories_list = []

    for item in available_items:
        name = item.get("name", "unknown")
        category = item.get("category", "")
        it_name = (item.get("ingredient_type") or {}).get("name", "")
        label = it_name or name

        if category == "glass":
            glasses_list.append(name)
        elif category == "accessory":
            accessories_list.append(name)
        else:
            ingredients_list.append(f"- {label} ({name})")

    user_prompt = f"""Available ingredients:
{chr(10).join(ingredients_list) if ingredients_list else '(none)'}

Available glassware:
{chr(10).join(f'- {g}' for g in glasses_list) if glasses_list else '(none)'}

Available accessories:
{chr(10).join(f'- {a}' for a in accessories_list) if accessories_list else '(none)'}

Suggest cocktails I can make right now."""

    result = _call_ai(SUGGEST_SYSTEM_PROMPT, user_prompt)
    try:
        suggestions = json.loads(result)
        if isinstance(suggestions, list):
            return suggestions
    except json.JSONDecodeError:
        pass

    cleaned = result.strip()
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        cleaned = "\n".join(lines)
    try:
        suggestions = json.loads(cleaned)
        if isinstance(suggestions, list):
            return suggestions
    except json.JSONDecodeError:
        pass

    raise RuntimeError(f"AI returned unparseable response: {result[:200]}...")


FILTER_SYSTEM_PROMPT = """You are given a list of suggested cocktails and a list of cocktails that already exist in someone's collection. Remove any suggestion that is essentially the same drink as an existing one — same name (including translations and variants), or same core ingredient combination.

Return ONLY a JSON array of the remaining suggestions (the unique ones). If all are duplicates, return an empty array [].

Do NOT modify the cocktail objects — just remove duplicates. Do NOT add any explanation."""


def filter_duplicates(suggestions: list[dict], existing_names: list[str]) -> list[dict]:
    if not existing_names:
        return suggestions

    suggestions_json = json.dumps(suggestions, ensure_ascii=False, indent=2)
    existing_str = "\n".join(f"- {n}" for n in existing_names)

    user_prompt = f"""Existing cocktails:
{existing_str}

Suggested cocktails:
{suggestions_json}

Return only the unique suggestions (those not already in the existing list)."""

    result = _call_ai(FILTER_SYSTEM_PROMPT, user_prompt)
    try:
        filtered = json.loads(result)
        if isinstance(filtered, list):
            return filtered
    except json.JSONDecodeError:
        pass

    return suggestions
