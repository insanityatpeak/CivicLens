"""HTTP-level tests of the FastAPI app using the labeled demonstration fallback (pipeline LOGIC, not model quality)."""
import pytest
from conftest import jpeg_bytes
from fastapi.testclient import TestClient

from civiclens.providers.mock import MockProvider
from civiclens.web import server


@pytest.fixture()
def client(monkeypatch):
    monkeypatch.setenv("CIVICLENS_PROVIDER", "mock")
    server._runs.clear()
    return TestClient(server.app)


def analyze(client, demo="pothole"):
    r = client.post("/api/analyze", files={"file": ("p.jpg", jpeg_bytes(), "image/jpeg")}, data={"demo": demo})
    assert r.status_code == 200, r.text
    return r.json()


def test_index_and_static_served(client):
    assert "CivicLens" in client.get("/").text
    assert client.get("/static/app.js").status_code == 200


def test_status_lists_existing_samples_only(client):
    st = client.get("/api/status").json()
    assert st["configured"] is True
    for s in st["samples"]:
        assert client.get(s["url"]).status_code == 200


def test_sample_endpoint_whitelists_files(client):
    assert client.get("/samples/..%2F..%2F.env").status_code == 404
    assert client.get("/samples/user_garbage_dumping_faces.png").status_code == 404


def test_unconfigured_server_reports_it_and_refuses_real_analysis(monkeypatch):
    monkeypatch.setenv("CIVICLENS_PROVIDER", "groq,openrouter")
    monkeypatch.setenv("GROQ_API_KEY", "")
    monkeypatch.setenv("OPENROUTER_API_KEY", "")
    c = TestClient(server.app)
    assert c.get("/api/status").json()["configured"] is False
    r = c.post("/api/analyze", files={"file": ("p.jpg", jpeg_bytes(), "image/jpeg")})
    assert r.status_code == 503 and r.json()["error"]["kind"] == "config"


def test_pothole_flow_english_and_hindi(client):
    a = analyze(client)
    assert a["is_fallback"] is True
    for lang, needle in (("en", "COMPLAINT DRAFT"), ("hi", "शिकायत")):
        r = client.post("/api/complaint", json={"analysis": a["analysis"], "language": lang, "demo": "pothole",
                                                "location_text": "Near the old bus stand", "ongoing": True})
        assert r.status_code == 200, r.text
        d = r.json()
        assert needle in d["text"] and d["passed"] and d["is_fallback"]
        kinds = {s["kind"] for s in d["sources"]}
        assert {"seen", "user"} <= kinds


def test_no_issue_and_unclear_scenarios(client):
    assert analyze(client, "no_issue")["analysis"]["is_civic_issue"] is False
    u = analyze(client, "unclear")["analysis"]
    assert u["clarifying_question"]
    r = client.post("/api/complaint", json={"analysis": u, "demo": "unclear"})
    assert r.status_code == 422 and r.json()["error"]["kind"] == "needs_clarification"
    r = client.post("/api/complaint", json={"analysis": u, "demo": "unclear", "clarification_answer": "water"})
    assert r.status_code == 200


def test_user_can_remove_observations_and_must_keep_evidence(client):
    a = analyze(client)["analysis"]
    seen = [o["id"] for o in a["observations"] if o["type"] == "observed"]
    r = client.post("/api/complaint", json={"analysis": a, "demo": "pothole", "observation_ids": seen[:1]})
    assert r.status_code == 200
    assert not any("gravel" in s["statement"].lower() for s in r.json()["sources"])
    r = client.post("/api/complaint", json={"analysis": a, "demo": "pothole", "observation_ids": []})
    assert r.status_code == 422 and r.json()["error"]["kind"] == "no_evidence"


def test_user_category_correction_is_applied(client):
    a = analyze(client)["analysis"]
    r = client.post("/api/complaint", json={"analysis": a, "demo": "pothole", "category": "garbage_overflow"})
    assert "garbage overflow" in r.json()["text"]


def test_bad_inputs_get_clear_errors(client):
    r = client.post("/api/analyze", data={"demo": "pothole"})
    assert r.status_code == 400
    r = client.post("/api/analyze", files={"file": ("x.txt", b"not an image", "text/plain")}, data={"demo": "pothole"})
    assert r.status_code == 422 and "could not be read" in r.json()["error"]["message"]
    assert client.post("/api/analyze", data={"demo": "bogus", "sample": "pothole"}).status_code == 400
    assert client.post("/api/complaint", json={"analysis": {"nope": 1}}).status_code == 422


def test_provider_errors_are_citizen_readable():
    kind, msg = server.friendly("provider", "Gemini request failed: ClientError: 429 RESOURCE_EXHAUSTED {...}")
    assert kind == "quota" and "429" not in msg and "RESOURCE" not in msg
    assert "ClientError" not in server.friendly("provider", "ClientError: boom")[1]


class _RealishProvider(MockProvider):
    is_fallback = False


def test_real_provider_sessions_are_capped(monkeypatch):
    monkeypatch.setattr(server, "_provider", lambda demo: _RealishProvider("pothole"))
    monkeypatch.setattr(server, "MAX_RUNS_PER_SESSION", 2)
    server._runs.clear()
    c = TestClient(server.app)
    c.get("/api/status")  # sets session cookie
    codes = [c.post("/api/analyze", files={"file": ("p.jpg", jpeg_bytes(), "image/jpeg")}).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


def test_fallback_sessions_are_not_capped(client, monkeypatch):
    monkeypatch.setattr(server, "MAX_RUNS_PER_SESSION", 1)
    for _ in range(3):
        analyze(client)
