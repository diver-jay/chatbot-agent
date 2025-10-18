import json

def parse_json_from_response(response_text: str) -> dict:
    """
    Extracts a JSON object from a model's text response,
    handling markdown code blocks (e.g., ```json ... ```).

    Args:
        response_text: The raw text response from the chat model.

    Returns:
        A dictionary parsed from the JSON string.
        Returns an empty dictionary if parsing fails or the text is empty.
    """
    if not response_text:
        return {}

    text_to_parse = response_text.strip()

    # Clean up markdown code block markers
    if text_to_parse.startswith("```json"):
        text_to_parse = text_to_parse[7:].strip()
        if text_to_parse.endswith("```"):
            text_to_parse = text_to_parse[:-3].strip()
    elif text_to_parse.startswith("```"):
        text_to_parse = text_to_parse[3:].strip()
        if text_to_parse.endswith("```"):
            text_to_parse = text_to_parse[:-3].strip()

    try:
        return json.loads(text_to_parse)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON from response: {e}")
        print(f"Original text for parsing: {text_to_parse}")
        return {}
