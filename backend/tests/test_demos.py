"""Run with:  pytest -q   (from the backend folder)"""
from uuid import uuid4

from fastapi.testclient import TestClient

from main import app

client = TestClient(app, headers={"X-Session-ID": str(uuid4())})


def get(demo_id):
    r = client.get(f"/api/demo/{demo_id}")
    assert r.status_code == 200
    return r.json()


def test_health():
    assert client.get("/api/health").json()["status"] == "ok"


def test_health_without_api_prefix():
    assert client.get("/health").json()["status"] == "ok"


def test_api_docs_remain_available_locally():
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_demo1_genuine_is_trusted():
    o = get("demo1")["overall"]
    assert o["decision"] == "TRUSTED"
    assert o["trust_score"] >= 90 and o["confidence"] >= 0.75


def test_demo2_manipulated_is_high_risk():
    case = get("demo2")
    assert case["overall"]["decision"] in ("HIGH RISK", "VERY HIGH RISK")
    assert case["manipulation"]["risk"] >= 0.6


def test_demo3_conflict_is_inconclusive_even_if_score_is_high():
    o = get("demo3")["overall"]
    assert o["decision"] == "INCONCLUSIVE"
    assert o["forced_inconclusive"] is True        # raw band was higher than INCONCLUSIVE
    assert o["confidence"] <= 0.60


def test_demo3_has_contradiction_panel_and_insufficient_claim():
    case = get("demo3")
    assert case["contradictions"], "expected a conflicting evidence panel"
    c2 = next(c for c in case["claims"] if c["id"] == "c2")
    assert c2["insufficient"] and c2["status"] == "INCONCLUSIVE"


def test_opinions_are_not_verified():
    c3 = next(c for c in get("demo1")["claims"] if c["id"] == "c3")
    assert c3["status"] == "NOT VERIFIED" and c3["evidence"] == []


def test_case_is_stored_and_retrievable():
    cid = get("demo1")["case_id"]
    assert client.get(f"/api/case/{cid}").json()["case_id"] == cid


def test_case_history_is_scoped_to_the_browser_session():
    session_a, session_b = str(uuid4()), str(uuid4())
    case = client.get("/api/demo/demo1", headers={"X-Session-ID": session_a}).json()

    history_a = client.get("/api/cases", headers={"X-Session-ID": session_a})
    history_b = client.get("/api/cases", headers={"X-Session-ID": session_b})
    other_session_case = client.get(
        f"/api/case/{case['case_id']}", headers={"X-Session-ID": session_b}
    )

    assert case["case_id"] in {item["case_id"] for item in history_a.json()}
    assert case["case_id"] not in {item["case_id"] for item in history_b.json()}
    assert other_session_case.status_code == 404


def test_case_history_requires_a_session_id():
    response = client.get("/api/cases", headers={"X-Session-ID": ""})
    assert response.status_code == 422


def test_no_evidence_is_inconclusive():
    body = {"claims": [{"claim": "Something unverifiable happened.", "importance": "high", "type": "factual"}]}
    o = client.post("/api/calculate-trust", json=body).json()["overall"]
    assert o["decision"] == "INCONCLUSIVE" and o["confidence"] < 0.25


def test_live_without_keys_fails_gracefully(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("TAVILY_API_KEY", raising=False)
    r = client.post("/api/analyze/text", data={"text": "The bridge opened to traffic on 4 May 2021."})
    assert r.status_code == 503 and r.json()["demo_available"] is True
