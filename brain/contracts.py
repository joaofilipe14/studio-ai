from __future__ import annotations

from typing import Tuple


def validate_plan_contract(plan: dict, allowed_tools: set, forbidden_tools: set) -> Tuple[bool, str]:
    steps = plan.get("steps")
    if not isinstance(steps, list) or not steps:
        return False, "plan.steps must be a non-empty list"

    for si, step in enumerate(steps):
        tcs = step.get("tool_calls", [])
        if not isinstance(tcs, list):
            return False, f"step[{si}].tool_calls must be a list"

        for ti, tc in enumerate(tcs):
            tname = tc.get("tool")
            if not isinstance(tname, str) or not tname:
                return False, f"step[{si}].tool_calls[{ti}].tool must be a non-empty string"

            if forbidden_tools and tname in forbidden_tools:
                return False, f"tool forbidden by contract: {tname}"

            if allowed_tools and tname not in allowed_tools:
                return False, f"tool not allowed by contract: {tname}"

    return True, "ok"