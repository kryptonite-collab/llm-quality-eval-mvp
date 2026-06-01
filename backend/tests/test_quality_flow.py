import json

from fastapi.testclient import TestClient

from app.main import app
from app.services.eval_runner import run_eval_dataset
from app.services import badcase as badcase_service_module


client = TestClient(app)


def test_quality_flow_from_eval_to_badcase_api(monkeypatch, tmp_path):
    dataset_path = tmp_path / "flow_sample.jsonl"
    report_path = tmp_path / "latest_report.json"

    dataset_path.write_text(
        '{"id":"q001","question":"test rag mode","expected_keywords":["test rag mode"],"expected_source":"mock_policy.md","category":"rag_fact"}\n'
        '{"id":"q002","question":"test badcase flow","expected_keywords":["impossible_keyword"],"expected_source":"mock_policy.md","category":"badcase"}\n',
        encoding="utf-8",
    )

    report = run_eval_dataset(
        dataset_path=dataset_path,
        report_path=report_path,
        use_rag=True,
        top_k=3,
    )

    assert report["total"] == 2
    assert report["passed"] == 1
    assert report["failed"] == 1
    assert report["badcase_count"] == 1
    assert report_path.exists()

    monkeypatch.setattr(
        badcase_service_module,
        "DEFAULT_REPORT_PATH",
        report_path,
    )

    list_response = client.get("/api/v1/badcases")
    assert list_response.status_code == 200

    list_data = list_response.json()
    assert list_data["total"] == 1
    assert list_data["items"][0]["id"] == "q002"
    assert list_data["items"][0]["question_id"] == "q002"
    assert list_data["items"][0]["missing_keywords"] == ["impossible_keyword"]

    detail_response = client.get("/api/v1/badcases/q002")
    assert detail_response.status_code == 200

    detail_data = detail_response.json()
    assert detail_data["id"] == "q002"
    assert detail_data["expected_source"] == "mock_policy.md"
    assert detail_data["retrieved_sources"] == ["mock_policy.md"]

    replay_response = client.post("/api/v1/badcases/q002/replay")
    assert replay_response.status_code == 200

    replay_data = replay_response.json()
    assert replay_data["id"] == "q002"
    assert replay_data["answer"] == "Mock answer for question: test badcase flow"
    assert replay_data["model"] == "mock-llm-local"

    saved_report = json.loads(report_path.read_text(encoding="utf-8"))
    assert saved_report["badcases"][0]["question_id"] == "q002"
