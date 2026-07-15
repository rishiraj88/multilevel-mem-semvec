"""Seed the PROBLEM.md demo and ask the cross-perspective question.

Three family members each seed five memories into one shared cluster, then we ask
"Who was at the wedding?" and print the coherent answer.

Usage (headless; requires the API to be running):
    uv run uvicorn main:app --host 0.0.0.0 --port 8000   # in one shell
    uv run python scripts/seed_demo.py                    # in another

Configure the target with BASE_URL (default http://localhost:8000) and the family
with CLUSTER_ID (default "family-1").
"""

from __future__ import annotations

import os
import sys

import httpx

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
CLUSTER_ID = os.getenv("CLUSTER_ID", "family-1")

MEMORIES: dict[str, list[str]] = {
    "Alice": [
        "I watched Sam and Priya exchange vows at the garden wedding in June.",
        "Grandpa told his fishing story again at the wedding reception.",
        "Priya wore our grandmother's necklace at the wedding.",
        "The wedding cake was lemon, and Bob had three slices.",
        "It rained briefly before the wedding ceremony started.",
    ],
    "Bob": [
        "The whole family attended Priya's wedding; even cousin Nina flew in.",
        "I gave the toast at the wedding and forgot half my notes.",
        "We danced until midnight at the wedding.",
        "Uncle Ravi caught the biggest fish on the summer trip.",
        "The wedding was at the Rosewood garden venue.",
    ],
    "Nina": [
        "I flew in from Berlin for Priya and Sam's wedding.",
        "At the wedding I finally met Alice's new puppy.",
        "The garden wedding had fairy lights everywhere.",
        "I photographed the whole wedding party by the fountain.",
        "After the wedding we all had brunch on Sunday.",
    ],
}


def main() -> int:
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as client:
        client.get("/health").raise_for_status()

        count = 0
        for member, texts in MEMORIES.items():
            for text in texts:
                response = client.post(
                    f"/v1/cluster/{CLUSTER_ID}/store",
                    json={"member": member, "text": text, "tags": ["wedding"] if "wedding" in text else []},
                )
                response.raise_for_status()
                count += 1
        print(f"Seeded {count} memories for cluster '{CLUSTER_ID}'.\n")

        answer = client.post(
            f"/v1/cluster/{CLUSTER_ID}/run",
            json={"question": "Who was at the wedding?"},
        )
        answer.raise_for_status()
        body = answer.json()
        print("Q: Who was at the wedding?")
        print(f"A ({'LLM' if body['used_ai'] else 'deterministic'}): {body['answer']}\n")
        members = sorted({memory['member'] for memory in body["memories"]})
        print(f"Perspectives combined: {', '.join(members)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except httpx.HTTPError as error:
        print(f"Demo failed talking to {BASE_URL}: {error}", file=sys.stderr)
        print("Is the API running?  uv run uvicorn main:app --host 0.0.0.0 --port 8000", file=sys.stderr)
        raise SystemExit(1) from error
