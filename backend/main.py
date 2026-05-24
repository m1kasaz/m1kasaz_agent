from __future__ import annotations

import argparse
import json

from app.agent.orchestrator import invoke_agent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the m1kasaz agent graph once.")
    parser.add_argument("message", nargs="*", help="User input to send to the graph")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    user_input = " ".join(args.message).strip()

    if not user_input:
        user_input = input("message> ").strip()

    result = invoke_agent(user_input)
    print(f"Intent: {result['intent']}")
    print(f"Response: {result['response']}")

    artifacts = result.get("artifacts") or {}
    if artifacts:
        print("Artifacts:")
        print(json.dumps(artifacts, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
