import json
import re
from pathlib import Path


def load_json(path: Path):
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as exc:  # noqa: BLE001 - surface any parse errors
        return None, exc


def validate_flow(data: dict) -> list[str]:
    issues: list[str] = []
    states = data.get("states", []) or []
    state_names = [s.get("name") for s in states]
    name_set = set(state_names)

    # initial_state exists
    initial_state = data.get("initial_state")
    if initial_state not in name_set:
        issues.append(f"initial_state '{initial_state}' not found in states")

    # transitions point to existing states
    for state in states:
        for transition in (state.get("transitions") or []):
            next_state = transition.get("next")
            if next_state and next_state not in name_set:
                issues.append(
                    f"transition from '{state.get('name')}' points to missing state '{next_state}'"
                )

    # split-based-on must have properties.input
    for state in states:
        if state.get("type") == "split-based-on":
            props = state.get("properties") or {}
            if not props.get("input"):
                issues.append(f"split state '{state.get('name')}' missing properties.input")

    # compile any matches_regex conditions
    for state in states:
        if state.get("type") == "split-based-on":
            for tr in (state.get("transitions") or []):
                for cond in (tr.get("conditions") or []):
                    if cond.get("type") == "matches_regex":
                        pattern = cond.get("value")
                        try:
                            re.compile(pattern)
                        except re.error as exc:
                            issues.append(
                                f"regex invalid in state '{state.get('name')}' condition "
                                f"'{cond.get('friendly_name')}': {exc}"
                            )

    return issues


def main() -> None:
    json_path = Path("/workspace/AlexChatBot.json")
    data, err = load_json(json_path)
    if err is not None:
        print("ALEX_SYNTAX_ERR", repr(err))
        return
    print("ALEX_SYNTAX_OK")

    issues = validate_flow(data)
    print("ISSUE_COUNT", len(issues))
    for issue in issues:
        print("ISSUE", issue)


if __name__ == "__main__":
    main()

