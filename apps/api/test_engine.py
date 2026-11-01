"""Engine self-check. Run: `python test_engine.py` from apps/api.
Exercises the non-trivial logic end to end: tool dispatch, genuine planner
routing, the approval pause/resume, and the failed+retry path. No framework."""
import asyncio
import os
import tempfile

from app import db

# isolate: use a throwaway DB so the demo db stays pristine
db.DB_PATH = os.path.join(tempfile.gettempdir(), "orchestrix_test.db")
if os.path.exists(db.DB_PATH):
    os.remove(db.DB_PATH)
db._conn = None

from app import store                                  # noqa: E402
from app.agents.runtime import runtime                 # noqa: E402
from app.models import AgentCreate                      # noqa: E402
from app.tools.registry import REGISTRY, ToolError      # noqa: E402


def main():
    db.init_and_seed()

    # 1. tools run against real seeded data
    r = REGISTRY["search_customers"].handler({"query": "acme"})
    assert r["count"] >= 1 and any(c["id"] == "CUST-1001" for c in r["results"]), r
    assert REGISTRY["get_order"].handler({"order_id": "ORD-5003"})["status"] == "delayed"
    try:
        REGISTRY["get_order"].handler({"order_id": "ORD-9999"})
        assert False, "expected ToolError"
    except ToolError:
        pass

    # 2. read-only task routes to generate_report and completes
    a = store.create_agent(AgentCreate(name="T Analyst", instructions="report",
                                       tools=["generate_report", "search_customers"]))
    ex = store.create_execution(a, "Give me an orders summary report")
    asyncio.run(runtime.start(ex.id))
    ex = store.get_execution(ex.id)
    assert ex.status == "completed", ex.status
    assert any(s.tool == "generate_report" and s.status == "success" for s in ex.steps)

    # 3. sensitive tool pauses for approval, then resumes to completion
    a2 = store.create_agent(AgentCreate(name="T Support", instructions="resolve",
                                        tools=["search_customers", "create_ticket", "send_notification"]))
    ex2 = store.create_execution(a2, "Find customer Acme Robotics, open an urgent ticket and notify them")
    asyncio.run(runtime.start(ex2.id))
    ex2 = store.get_execution(ex2.id)
    assert ex2.status == "pending_approval", ex2.status
    assert any(s.tool == "create_ticket" and s.status == "success" for s in ex2.steps)
    asyncio.run(runtime.resume(ex2.id, approved=True))
    ex2 = store.get_execution(ex2.id)
    assert ex2.status == "completed", ex2.status
    assert any(s.tool == "send_notification" and s.status == "success" for s in ex2.steps)

    # 4. reject keeps run alive but declines the action
    ex2b = store.create_execution(a2, "Find Bluefin Logistics and notify them of the renewal")
    asyncio.run(runtime.start(ex2b.id))
    asyncio.run(runtime.resume(ex2b.id, approved=False))
    ex2b = store.get_execution(ex2b.id)
    assert ex2b.status == "completed", ex2b.status
    assert any(s.tool == "send_notification" and s.status == "rejected" for s in ex2b.steps)

    # 5. bad input -> retries -> failed state (then re-driveable)
    a3 = store.create_agent(AgentCreate(name="T Order", instructions="orders", tools=["get_order"]))
    ex3 = store.create_execution(a3, "Check order ORD-9999 please")
    asyncio.run(runtime.start(ex3.id))
    ex3 = store.get_execution(ex3.id)
    assert ex3.status == "failed", ex3.status
    failed = [s for s in ex3.steps if s.status == "failed" and s.tool == "get_order"]
    assert failed and failed[0].attempts == 2, failed

    print("OK engine self-check passed (tools, planner, approval, reject, retry/fail)")


if __name__ == "__main__":
    main()
