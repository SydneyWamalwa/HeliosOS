import re
from flask import request, jsonify

def validate_json(required_fields=None):
    """
    Validates if request contains valid JSON with required fields.
    :param required_fields: list of field names that must be present in the JSON body
    :return: (data, error_response)
    """
    if not request.is_json:
        return None, jsonify({"error": "Invalid or missing JSON"}), 400

    data = request.get_json()

    if required_fields:
        missing = [field for field in required_fields if field not in data]
        if missing:
            return None, jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    return data, None


def sanitize_input(value):
    """
    Sanitizes string inputs to prevent injection attacks.
    Removes suspicious patterns such as shell operators, SQL keywords, etc.
    """
    if not isinstance(value, str):
        return value

    # Remove dangerous characters and SQL keywords
    dangerous_patterns = [
        r"[;&|`$<>]",           # shell operators
        r"(--|\b(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|CREATE)\b)",  # SQL injection
        r"(\bUNION\b.*\bSELECT\b)"  # UNION SELECT injection
    ]

    sanitized = value
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, "", sanitized, flags=re.IGNORECASE)

    return sanitized.strip()
