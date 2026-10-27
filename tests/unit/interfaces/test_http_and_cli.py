import asyncio
import json
import os
from pathlib import Path

import httpx
import pytest

from streaming_assistant.infrastructure.scripted_stream import Pace, ScriptedStreamingModel
from streaming_assistant.infrastructure.settings import Settings
from streaming_assistant.interfaces import cli
from streaming_assistant.interfaces.http import create_app, encode
from streaming_assistant.interfaces.wiring import build_components, database_exists

ROOT = Path(__file__).resolve().parents[3]
CUSTOMER = {"Authorization": "Bearer demo-customer-token"}
REVIEWER = {"Authorization": "Bearer demo-reviewer-token"}
SHIPPING = "A question about shipping times: standard delivery takes three to five business days after dispatch?"
LATE_REFUND = "Can I get a refund on an order from seventy five days ago?"
FAST = Pace(0, 0, 0, 0, jitter=0)


def settings(**env):
    return Settings.from_environ({"PROJECT_ROOT": str(ROOT), "DATABASE": ":memory:", "TTFT_STANDARD_MS": "0", **env})


def client_for(components):
    app = create_app(
        components.assistant, components.desk, components.catalog, components.authenticator, components.audit
    )
    return httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test")


def parse(body):
    out, name = [], ""
    for line in body.splitlines():
        if line.startswith("event: "):
            name = line.removeprefix("event: ")
        elif line.startswith("data: "):
            out.append((name, json.loads(line.removeprefix("data: "))))
    return out


def components():
    model = ScriptedStreamingModel(FAST, hallucinate_every=0)
    return build_components(settings(), model=model, fresh=True)


def test_ask_streams_typed_events_with_a_run_id_header():
    async def go():
        async with client_for(components()) as client:
            return await client.post("/ask", json={"question": SHIPPING}, headers=CUSTOMER)

    response = asyncio.run(go())
    names = [name for name, _ in parse(response.text)]
    assert response.status_code == 200 and response.headers["content-type"].startswith("text/event-stream")
    assert response.headers["x-run-id"].startswith("run-") and response.headers["cache-control"] == "no-store"
    assert names[0] == "token" and "citation" in names and names[-1] == "done"
    assert (
        encode(
            __import__("streaming_assistant.application.assistant", fromlist=["Event"]).Event("token", {"text": "a"})
        )
        == 'event: token\ndata: {"text": "a"}\n\n'
    )


def test_a_missing_or_wrong_token_is_a_401_and_a_bad_body_is_a_422():
    async def go():
        async with client_for(components()) as client:
            return (
                (await client.post("/ask", json={"question": SHIPPING})).status_code,
                (
                    await client.post("/ask", json={"question": SHIPPING}, headers={"Authorization": "Bearer nope"})
                ).status_code,
                (await client.post("/ask", json={"question": "x"}, headers=CUSTOMER)).status_code,
                (await client.get("/runs/run-1/status")).status_code,
            )

    assert asyncio.run(go()) == (401, 401, 422, 401)


def test_the_whole_pause_review_resume_path_over_http_with_role_checks():
    async def go():
        async with client_for(components()) as client:
            asked = await client.post("/ask", json={"question": LATE_REFUND}, headers=CUSTOMER)
            run_id = asked.headers["x-run-id"]
            customer_sees_queue = await client.get("/reviews", headers=CUSTOMER)
            waiting = (await client.get("/reviews", headers=REVIEWER)).json()
            early = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)
            status_before = (await client.get(f"/runs/{run_id}/status", headers=CUSTOMER)).json()["status"]
            ref = waiting[0]["retrieved"][0]
            bad = await client.post(
                f"/reviews/{run_id}/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "ok"}
            )
            missing = await client.post(
                "/reviews/run-x/answer", headers=REVIEWER, json={"reviewer_id": "ana", "answer": "ok", "no_page": True}
            )
            good = await client.post(
                f"/reviews/{run_id}/answer",
                headers=REVIEWER,
                json={"reviewer_id": "ana", "answer": "Store credit approved.", "cited": [ref]},
            )
            resumed = await client.get(f"/runs/{run_id}/resume", headers=CUSTOMER)
            audit = (await client.get("/audit/verify", headers=REVIEWER)).json()
            forbidden = await client.get("/audit/verify", headers=CUSTOMER)
            unknown_status = await client.get("/runs/run-x/status", headers=CUSTOMER)
            return (
                asked,
                customer_sees_queue,
                waiting,
                early,
                status_before,
                bad,
                missing,
                good,
                resumed,
                audit,
                forbidden,
                unknown_status,
            )

    asked, queue, waiting, early, before, bad, missing, good, resumed, audit, forbidden, unknown = asyncio.run(go())
    assert [n for n, _ in parse(asked.text)] == ["paused", "done"] and queue.status_code == 403
    assert waiting[0]["reason"] == "policy_exception" and early.status_code == 409 and before == "waiting"
    assert bad.status_code == 422 and missing.status_code == 404 and good.json()["status"] == "answered"
    text = "".join(data["text"] for name, data in parse(resumed.text) if name == "token")
    assert "Store credit approved." in text and audit["first_broken_index"] is None and audit["entries"] >= 6
    assert forbidden.status_code == 403 and unknown.status_code == 404


def test_stop_returns_202_and_pages_open_with_their_anchors():
    async def go():
        async with client_for(components()) as client:
            stop = await client.post("/runs/run-1/stop", headers=CUSTOMER)
            page = await client.get("/pages/help-01")
            missing = await client.get("/pages/help-99")
            home = await client.get("/")
            review = await client.get("/review")
            health = await client.get("/healthz")
            return stop, page, missing, home, review, health

    stop, page, missing, home, review, health = asyncio.run(go())
    assert stop.status_code == 202 and "<section id=" in page.text and missing.status_code == 404
    assert "EventSource" in home.text or "fetch(" in home.text
    assert review.status_code == 200 and health.json() == {"status": "ok"}


def test_the_database_is_detected_by_file_and_never_for_memory(tmp_path):
    assert not database_exists(settings())
    assert not database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))
    (tmp_path / "x.sqlite").write_bytes(b"")
    assert database_exists(settings(DATABASE=str(tmp_path / "x.sqlite")))


@pytest.fixture
def env(monkeypatch, tmp_path):
    monkeypatch.setenv("PROJECT_ROOT", str(ROOT))
    monkeypatch.setenv("DATABASE", str(tmp_path / "assistant.sqlite"))
    monkeypatch.setenv("TTFT_STANDARD_MS", "0")
    monkeypatch.setenv("TTFT_FAST_MS", "0")
    monkeypatch.setenv("TOKEN_MS", "0")
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    return tmp_path


def test_the_commands_build_the_database_trace_a_request_and_verify_the_audit_chain(env, capsys):
    assert cli.main(["db"]) == 0 and (env / "assistant.sqlite").exists()
    assert cli.main(["trace"]) == 0
    out = capsys.readouterr().out
    assert "cold" in out and "warm" in out and "stage sum" in out
    assert cli.main(["tamper-demo"]) == 0
    tampered = capsys.readouterr().out
    assert (
        "chain intact: None" in tampered
        and "after tampering entry 1: 1" in tampered
        and "after deleting entry 1: 1" in tampered
    )
    assert cli.main(["verify-audit"]) == 0 and "first broken index: None" in capsys.readouterr().out
    assert cli.main(["replay", "run-demo"]) == 0 and "paused" in capsys.readouterr().out


def test_verify_audit_exits_one_when_the_chain_is_broken(env, capsys):
    import sqlite3

    cli.main(["db"])
    cli.main(["tamper-demo"])
    connection = sqlite3.connect(env / "assistant.sqlite")
    connection.execute("DROP TRIGGER audit_log_no_update")
    connection.execute("UPDATE audit_log SET content = 'edited' WHERE seq = 2")
    connection.commit()
    connection.close()
    capsys.readouterr()
    assert cli.main(["verify-audit"]) == 1 and "first broken index: 1" in capsys.readouterr().out


def test_evaluate_reports_the_pause_and_citation_counts(env, capsys):
    assert cli.main(["evaluate"]) == 0
    report = json.loads(capsys.readouterr().out)
    assert report["paused_of_should"] == report["should_pause"] == 20 and report["paused_of_others"] == 0
    assert report["citations_outside_retrieved"] == 0 and report["false_pause_rate"] == 0


def test_a_bad_environment_stops_with_exit_code_two(monkeypatch, capsys):
    monkeypatch.setenv("PORT", "eighty")
    assert cli.main(["db"]) == 2 and "PORT" in capsys.readouterr().err
    assert os.environ["PORT"] == "eighty"
