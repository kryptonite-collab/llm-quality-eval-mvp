import json

from fastapi.testclient import TestClient

from app.main import app
from app.services import badcase as badcase_service_module


client = TestClient(app)


def _write_report(report_path):
    report = {
        "total": 2,
        "passed": 1,
        "failed": 1,
        "pass_rate": 0.5,
        "avg_latency_ms": 0.0,
        "badcases": [
            {
                "id": "q002",
                "question_id": "q002",
                "question": "test missing keyword",
                "category": "badcase",
                "answer": "Mock answer for question: test missing keyword",
                "expected_keywords": ["impossible_keyword"],
                "reason": "missing keywords: impossible_keyword",
                "missing_keywords": ["impossible_keyword"],
                "expected_source": "mock_policy.md",
                "retrieved_sources": ["mock_policy.md"],
                "score": 0.0,
                "failed_metrics": ["answer_keyword_recall"],
                "badcase_type": "keyword_miss",
                "created_at": "2026-05-26T00:00:00+00:00",
            }
        ],
        "results": [],
    }

    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def test_list_badcases(monkeypatch, tmp_path):
    report_path = tmp_path / "latest_report.json"
    _write_report(report_path)

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )

    response = client.get("/api/v1/badcases")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == "q002"
    assert data["items"][0]["question"] == "test missing keyword"


def test_get_badcase(monkeypatch, tmp_path):
    report_path = tmp_path / "latest_report.json"
    _write_report(report_path)

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )

    response = client.get("/api/v1/badcases/q002")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "q002"
    assert data["reason"] == "missing keywords: impossible_keyword"
    assert data["missing_keywords"] == ["impossible_keyword"]
    assert data["failed_metrics"] == ["answer_keyword_recall"]
    assert data["badcase_type"] == "keyword_miss"
    assert data["replay_status"] == "not_replayed"


def test_get_badcase_not_found(monkeypatch, tmp_path):
    report_path = tmp_path / "latest_report.json"
    _write_report(report_path)

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )

    response = client.get("/api/v1/badcases/not-exist")

    assert response.status_code == 404


def test_replay_badcase(monkeypatch, tmp_path):
    report_path = tmp_path / "latest_report.json"
    _write_report(report_path)

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )

    response = client.post("/api/v1/badcases/q002/replay")

    assert response.status_code == 200

    data = response.json()
    assert data["id"] == "q002"
    assert data["question"] == "test missing keyword"
    assert data["answer"] == "Mock answer for question: test missing keyword"
    assert data["model"] == "mock-llm-local"
    assert data["replay_status"]["replayed"] is True
    assert data["replay_status"]["pass_after_replay"] is False
    assert data["replay_status"]["still_failed_metrics"] == ["answer_keyword_recall"]
    assert data["metrics"]["pass"] is False
    assert data["original_badcase"]["id"] == "q002"


def test_export_badcases(monkeypatch, tmp_path):
    report_path = tmp_path / "latest_report.json"
    export_path = tmp_path / "badcases.jsonl"
    _write_report(report_path)

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )
    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_EXPORT_PATH",
        export_path,
    )

    response = client.post("/api/v1/badcases/export")

    assert response.status_code == 200

    data = response.json()
    assert data["total"] == 1
    assert data["path"] == str(export_path)
    assert data["items"][0]["id"] == "q002"
    assert data["items"][0]["failed_metrics"] == ["answer_keyword_recall"]
    assert data["items"][0]["badcase_type"] == "keyword_miss"
    assert data["items"][0]["replay_status"] == "not_replayed"

    assert export_path.exists()

    exported = [
        json.loads(line)
        for line in export_path.read_text(encoding="utf-8").splitlines()
    ]

    assert len(exported) == data["total"]
    assert len(exported) == len(data["items"])

    exported_first = exported[0]
    response_first = data["items"][0]

    assert exported_first["id"] == response_first["id"]
    assert exported_first["question_id"] == response_first["question_id"]
    assert exported_first["question"] == response_first["question"]
    assert exported_first["answer"] == response_first["answer"]
    assert exported_first["expected_keywords"] == response_first["expected_keywords"]
    assert exported_first["missing_keywords"] == response_first["missing_keywords"]
    assert exported_first["expected_source"] == response_first["expected_source"]
    assert exported_first["retrieved_sources"] == response_first["retrieved_sources"]
    assert exported_first["score"] == response_first["score"]
    assert exported_first["failed_metrics"] == response_first["failed_metrics"]
    assert exported_first["badcase_type"] == response_first["badcase_type"]
    assert exported_first["reason"] == response_first["reason"]
    assert exported_first["replay_status"] == "not_replayed"
    assert exported_first["created_at"]