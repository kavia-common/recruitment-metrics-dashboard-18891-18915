def test_metrics_summary_and_notifications(client, seed_basic_data):
    # Summary should reflect seeded data
    rs = client.get("/metrics/summary")
    assert rs.status_code == 200
    summary = rs.get_json()
    assert summary["total_candidates"] >= 1
    assert "open_positions" in summary
    assert "upcoming_interviews" in summary

    rn = client.get("/metrics/notifications")
    assert rn.status_code == 200
    notifs = rn.get_json()
    assert isinstance(notifs, list)
    # Since we have at least 1 open position seeded, expect an info notification
    assert any(n["type"] in ("info", "success", "warning") for n in notifs)
