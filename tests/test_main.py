"""End-to-end API scenarios (see docs/IMPLEMENTATION_PLAN.md §6).

Every test runs offline and deterministically: the client fixture injects a
keyword-only Cortex, so answers never touch the network and `used_ai` is False.
The LLM path is exercised separately with stub synthesizers.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import create_app
from app.services.cortex import KeywordSynthesizer
from app.store.json_store import JsonMemoryStore

# The PROBLEM.md demo: three members, five memories each, in one family cluster.
DEMO_MEMORIES: dict[str, list[str]] = {
    "Alice": [
        "I watched Sam and Priya exchange vows at the garden wedding in June.",
        "Grandpa told his fishing story again at the wedding reception.",
        "Priya wore our grandmother's necklace at the wedding.",
        "The wedding cake was lemon and Bob had three slices.",
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


@pytest.fixture
def store(tmp_path):
    return JsonMemoryStore(tmp_path / "memories.json")


@pytest.fixture
def client(store):
    """A TestClient wired to a deterministic, keyword-only Cortex."""
    app = create_app(store=store, synthesizers=[KeywordSynthesizer()])
    return TestClient(app)


def _seed(client: TestClient, cluster: str, entries: list[tuple[str, str]]) -> None:
    for member, text in entries:
        response = client.post(f"/v1/cluster/{cluster}/store", json={"member": member, "text": text})
        assert response.status_code == 201


# --- health & contract ------------------------------------------------------


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_web_ui_is_served_at_root(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "The Family Chronicle" in response.text


def test_store_returns_created_with_location_header(client):
    response = client.post("/v1/cluster/fam/store", json={"member": "Alice", "text": "A wedding memory."})
    assert response.status_code == 201
    body = response.json()
    assert body["member"] == "Alice"
    assert body["id"] and body["created_at"]
    assert response.headers["Location"] == f"/v1/cluster/fam/memories/{body['id']}"


# --- cross-perspective recall -----------------------------------------------


def test_store_and_recall_across_perspectives(client):
    _seed(
        client,
        "family-1",
        [
            ("Alice", "I watched Sam and Priya exchange vows at the garden wedding."),
            ("Bob", "The whole family attended Priya's wedding in June."),
        ],
    )
    response = client.post("/v1/cluster/family-1/run", json={"question": "Who was at the wedding?"})
    assert response.status_code == 200
    body = response.json()
    assert body["used_ai"] is False
    assert {memory["member"] for memory in body["memories"]} == {"Alice", "Bob"}
    assert "Alice" in body["answer"]


def test_demo_three_members_five_memories(client):
    for member, texts in DEMO_MEMORIES.items():
        _seed(client, "family-1", [(member, text) for text in texts])

    response = client.post("/v1/cluster/family-1/run", json={"question": "Who was at the wedding?", "limit": 20})
    assert response.status_code == 200
    body = response.json()
    assert body["used_ai"] is False
    members = {memory["member"] for memory in body["memories"]}
    # The coherent answer draws on all three perspectives.
    assert members == {"Alice", "Bob", "Nina"}
    # Only wedding memories are retrieved (the fishing/brunch lines are excluded).
    assert all("wedding" in memory["text"].lower() for memory in body["memories"])


# --- empty state & isolation ------------------------------------------------


def test_empty_cluster_returns_helpful_answer(client):
    response = client.post("/v1/cluster/new-family/run", json={"question": "What happened last summer?"})
    assert response.status_code == 200
    body = response.json()
    assert body["memories"] == []
    assert body["used_ai"] is False
    assert "don't have any memories" in body["answer"]


def test_clusters_are_isolated(client):
    client.post("/v1/cluster/family-a/store", json={"member": "Ann", "text": "Secret picnic by the lake."})

    # family-b must not see family-a's memory.
    assert client.get("/v1/cluster/family-b/memories").json() == []
    answer = client.post("/v1/cluster/family-b/run", json={"question": "picnic"}).json()
    assert answer["memories"] == []


# --- validation -------------------------------------------------------------


@pytest.mark.parametrize(
    "payload",
    [
        {"member": "", "text": "a valid memory"},  # empty member
        {"member": "Al", "text": "no"},  # text too short (< 3)
        {"member": "Al"},  # missing text
    ],
)
def test_store_validation_returns_422_envelope(client, payload):
    response = client.post("/v1/cluster/fam/store", json=payload)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "validation_error"


@pytest.mark.parametrize("limit", [0, 51])
def test_run_limit_out_of_range_is_422(client, limit):
    response = client.post("/v1/cluster/fam/run", json={"question": "who was there?", "limit": limit})
    assert response.status_code == 422


# --- single-memory fetch ----------------------------------------------------


def test_get_memory_roundtrip_and_404(client):
    created = client.post("/v1/cluster/fam/store", json={"member": "Al", "text": "a stored memory"}).json()

    found = client.get(f"/v1/cluster/fam/memories/{created['id']}")
    assert found.status_code == 200
    assert found.json()["id"] == created["id"]

    missing = client.get("/v1/cluster/fam/memories/does-not-exist")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "not_found"


# --- persistence ------------------------------------------------------------


def test_persistence_round_trip(tmp_path):
    path = tmp_path / "persist.json"
    writer = TestClient(create_app(store=JsonMemoryStore(path), synthesizers=[KeywordSynthesizer()]))
    writer.post("/v1/cluster/fam/store", json={"member": "Al", "text": "persisted memory"})

    # A fresh store instance reading the same file sees the memory.
    reader = TestClient(create_app(store=JsonMemoryStore(path), synthesizers=[KeywordSynthesizer()]))
    items = reader.get("/v1/cluster/fam/memories").json()
    assert len(items) == 1
    assert items[0]["text"] == "persisted memory"


# --- LLM synthesis path (stubbed) -------------------------------------------


def test_llm_synthesis_path_sets_used_ai(store):
    class StubLLM:
        used_ai = True

        def synthesize(self, question, memories):
            return "A coherent synthesized answer."

    client = TestClient(create_app(store=store, synthesizers=[StubLLM(), KeywordSynthesizer()]))
    client.post("/v1/cluster/fam/store", json={"member": "Al", "text": "wedding in June"})
    body = client.post("/v1/cluster/fam/run", json={"question": "when was the wedding?"}).json()
    assert body["used_ai"] is True
    assert body["answer"] == "A coherent synthesized answer."


def test_llm_defers_and_keyword_takes_over(store):
    class NullLLM:
        used_ai = True

        def synthesize(self, question, memories):
            return None

    client = TestClient(create_app(store=store, synthesizers=[NullLLM(), KeywordSynthesizer()]))
    client.post("/v1/cluster/fam/store", json={"member": "Al", "text": "wedding in June"})
    body = client.post("/v1/cluster/fam/run", json={"question": "wedding"}).json()
    assert body["used_ai"] is False
    assert "Al remembers" in body["answer"]
