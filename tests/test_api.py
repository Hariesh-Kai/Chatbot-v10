from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(app)


def test_health() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_home_ui() -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "Industrial RAG Copilot" in resp.text


def test_ingest_and_query(tmp_path) -> None:
    sample = tmp_path / "sample.txt"
    sample.write_text(
        "MAWP for separator V-2100 is 125 bar(g).\n\n"
        "Design temperature range is 4 to 68 C for FL-33.",
        encoding="utf-8",
    )

    ingest_resp = client.post(
        "/v1/documents/ingest",
        json={"document_id": "doc-1", "file_path": str(sample)},
    )
    assert ingest_resp.status_code == 200
    assert ingest_resp.json()["chunks_indexed"] >= 1

    query_resp = client.post(
        "/v1/query",
        json={"question": "What is the MAWP for V-2100?", "document_id": "doc-1"},
    )
    assert query_resp.status_code == 200
    body = query_resp.json()
    assert "125 bar" in body["answer"]
    assert body["citations"]
