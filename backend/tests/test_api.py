async def test_health(client):
    resp = await client.get("/health")
    assert resp.json() == {"status": "ok"}


async def test_profile_defaults_then_update(client):
    resp = await client.get("/profile")
    assert resp.status_code == 200
    assert resp.json()["calorie_goal"] == 2200

    body = resp.json() | {"calorie_goal": 1800, "weekly_budget": "60.00"}
    resp = await client.put("/profile", json=body)
    assert resp.json()["calorie_goal"] == 1800


async def test_exclusions_round_trip(client):
    resp = await client.post("/profile/exclusions", json={"name": "peanut", "reason": "allergy"})
    assert resp.status_code == 201
    names = [e["name"] for e in (await client.get("/profile/exclusions")).json()]
    assert names == ["peanut"]


async def test_create_plan_enqueues_job(client, queue):
    resp = await client.post("/plans")
    assert resp.status_code == 202
    plan_id = resp.json()["id"]
    queue.enqueue_job.assert_awaited_once_with("generate_plan", plan_id)
    plan = (await client.get(f"/plans/{plan_id}")).json()
    assert plan["status"] == "queued"
