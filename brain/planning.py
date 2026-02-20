from __future__ import annotations

import json
from typing import Optional, Tuple, Dict, Any, List

from brain.ollama_client import chat


def extract_first_json_object(text: str) -> Optional[dict]:
    """Extract first valid JSON object from mixed text/markdown."""
    if not text:
        return None

    # pure JSON fast-path
    try:
        obj = json.loads(text)
        if isinstance(obj, dict):
            return obj
    except Exception:
        pass

    start = text.find("{")
    if start < 0:
        return None

    depth = 0
    in_str = False
    escape = False

    for i in range(start, len(text)):
        ch = text[i]

        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
            continue

        if ch == '"':
            in_str = True
            continue

        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start : i + 1]
                try:
                    obj = json.loads(candidate)
                    if isinstance(obj, dict):
                        return obj
                except Exception:
                    return None

    return None


def build_plan_request(
        *,
        system_prompt: str,
        planner_obj: dict,
        env_data: dict,
        goal: str,
        previous_error: Optional[str] = None,
        previous_plan_raw: Optional[str] = None,
) -> List[dict]:
    os_name = env_data.get("os", "unknown")

    repair_block = ""
    if previous_error:
        repair_block += (
            "\nREPLAN REQUIRED.\n"
            f"Reason: {previous_error}\n"
            "Fix the plan to satisfy the schema and constraints.\n"
        )
    if previous_plan_raw:
        trimmed = previous_plan_raw[:4000]
        repair_block += f"\nPrevious plan (raw, truncated):\n{trimmed}\n"

    constraints = planner_obj.get("constraints", {})
    allowed = constraints.get("allowed_tools", [])
    forbidden = constraints.get("forbidden_tools", [])
    rules = constraints.get("rules", [])

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": (
                f"Detected OS: {os_name}\n"
                f"env_info: {json.dumps(env_data, ensure_ascii=False)}\n\n"
                f"Goal: {goal}\n\n"
                f"{repair_block}\n"
                "You must return ONLY ONE JSON object, no markdown, no explanations.\n\n"
                "Schema:\n"
                f"{json.dumps(planner_obj['schema'])}\n\n"
                "Constraints:\n"
                f"- allowed_tools: {json.dumps(allowed)}\n"
                f"- forbidden_tools: {json.dumps(forbidden)}\n"
                f"- rules: {json.dumps(rules, ensure_ascii=False)}\n"
            ),
        },
    ]


def request_plan(
        *,
        config: dict,
        system_prompt: str,
        planner_obj: dict,
        env_data: dict,
        goal: str,
        log_jsonl,
        log_path: str,
        previous_error: Optional[str] = None,
        previous_plan_raw: Optional[str] = None,
) -> Tuple[Optional[dict], str]:
    messages = build_plan_request(
        system_prompt=system_prompt,
        planner_obj=planner_obj,
        env_data=env_data,
        goal=goal,
        previous_error=previous_error,
        previous_plan_raw=previous_plan_raw,
    )

    resp = chat(
        host=config["ollama"]["host"],
        model=config["ollama"]["model"],
        messages=messages,
        options={
            "temperature": config["ollama"]["temperature"],
            "top_p": config["ollama"]["top_p"],
            "num_ctx": config["ollama"]["num_ctx"],
        },
    )

    content = resp["message"]["content"]
    log_jsonl(log_path, {"event": "llm_plan_raw", "content": content})

    plan = extract_first_json_object(content)
    return plan, content