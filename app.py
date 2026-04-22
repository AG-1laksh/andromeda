from __future__ import annotations

import json
import re
from typing import Any, Optional, Tuple

from flask import Flask, jsonify, request

app = Flask(__name__)

_INT_RE = re.compile(r"[+-]?\d+")

_NUMBER_WORDS = {
    "zero": 0,
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "seventy": 70,
    "eighty": 80,
    "ninety": 90,
}


def _extract_integer(query: str) -> Optional[int]:
    m = _INT_RE.search(query)
    if m:
        return int(m.group(0))

    text = query.lower().replace("-", " ")
    tokens = re.findall(r"[a-z]+", text)
    for i, tok in enumerate(tokens):
        sign = -1 if tok == "minus" else 1
        start = i + 1 if tok == "minus" else i
        if start >= len(tokens):
            continue

        t0 = tokens[start]
        if t0 in _NUMBER_WORDS:
            value = _NUMBER_WORDS[t0]
            if value >= 20 and start + 1 < len(tokens):
                t1 = tokens[start + 1]
                if t1 in _NUMBER_WORDS and 0 <= _NUMBER_WORDS[t1] <= 9:
                    value += _NUMBER_WORDS[t1]
            return sign * value

    return None


def solve_parity_query(query: str) -> str:
    q = query.lower()
    asks_odd = bool(re.search(r"\bodd\b", q))
    asks_even = bool(re.search(r"\beven\b", q))
    if not asks_odd and not asks_even:
        return "I cannot determine the answer."

    value = _extract_integer(query)
    if value is None:
        return "I cannot determine the answer."

    is_odd = (value % 2) != 0
    if asks_odd and not asks_even:
        return "YES" if is_odd else "NO"
    if asks_even and not asks_odd:
        return "YES" if not is_odd else "NO"

    # If both odd/even appear, default to odd-question interpretation.
    return "YES" if is_odd else "NO"


def validate_payload(payload: object) -> Tuple[bool, Optional[str], Optional[str], Optional[list]]:
    if not isinstance(payload, dict):
        return False, "Request body must be a JSON object.", None, None

    query = payload.get("query")
    assets = payload.get("assets", [])

    if not isinstance(query, str) or not query.strip():
        return False, "'query' must be a non-empty string.", None, None

    if assets is None:
        assets = []

    if not isinstance(assets, list):
        return False, "'assets' must be an array.", None, None

    return True, None, query.strip(), assets


def build_output_payload(text: str) -> dict[str, str]:
    return {"output": text}


def extract_payload() -> Any:
    payload = request.get_json(silent=True)
    if isinstance(payload, dict):
        return payload

    if request.data:
        try:
            payload = json.loads(request.data.decode("utf-8"))
            if isinstance(payload, dict):
                return payload
        except (UnicodeDecodeError, json.JSONDecodeError):
            pass

    if request.form:
        query = request.form.get("query")
        assets_raw = request.form.get("assets")
        assets = []
        if assets_raw:
            try:
                parsed_assets = json.loads(assets_raw)
                if isinstance(parsed_assets, list):
                    assets = parsed_assets
            except json.JSONDecodeError:
                assets = [assets_raw]
        if query is not None:
            return {"query": query, "assets": assets}

    query_arg = request.args.get("query")
    if query_arg is not None:
        assets_arg = request.args.getlist("assets")
        return {"query": query_arg, "assets": assets_arg}

    return payload


@app.route("/v1/answer", methods=["POST", "GET"])
def answer():
    payload = extract_payload()
    is_valid, err, query, _assets = validate_payload(payload)
    if not is_valid:
        return jsonify({"error": err}), 400

    final_output = solve_parity_query(query)
    return jsonify(build_output_payload(final_output)), 200


@app.errorhandler(405)
def method_not_allowed(_):
    return jsonify({"error": "Method not allowed."}), 405


@app.errorhandler(500)
def internal_error(_):
    return jsonify({"error": "Internal server error."}), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
