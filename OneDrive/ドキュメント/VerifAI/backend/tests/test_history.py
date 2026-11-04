"""Tests for analysis history endpoints and database persistence."""

from fastapi.testclient import TestClient


def test_history_flow_crud(client: TestClient) -> None:
    """Test full cycle: perform analysis, list history, fetch by ID, and delete."""
    # Step 1: Create an analysis entry
    payload = {
        "text": (
            "Hiring Junior Python Developer. Position offers competitive salary and benefits. "
            "Please send your resume through official channels."
        )
    }
    create_res = client.post("/api/analyze/text", json=payload)
    assert create_res.status_code == 200
    analysis_id = create_res.json()["id"]

    # Step 2: List history
    list_res = client.get("/api/history?limit=10&offset=0")
    assert list_res.status_code == 200
    history_data = list_res.json()
    assert history_data["total"] >= 1
    assert any(item["id"] == analysis_id for item in history_data["items"])

    # Step 3: Fetch detail by ID
    detail_res = client.get(f"/api/history/{analysis_id}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert detail_data["id"] == analysis_id
    assert "submitted_text_preview" in detail_data
    assert "Hiring Junior Python Developer" in detail_data["submitted_text_preview"]

    # Step 4: Delete entry by ID
    del_res = client.delete(f"/api/history/{analysis_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "success"

    # Step 5: Verify entry is gone (404)
    get_again = client.get(f"/api/history/{analysis_id}")
    assert get_again.status_code == 404


def test_get_nonexistent_history_404(client: TestClient) -> None:
    """Ensure querying non-existent history record returns 404."""
    response = client.get("/api/history/99999999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_nonexistent_history_404(client: TestClient) -> None:
    """Ensure deleting non-existent history record returns 404."""
    response = client.delete("/api/history/99999999")
    assert response.status_code == 404


def test_history_pagination_offset(client: TestClient) -> None:
    """Verify offset and limit pagination slicing."""
    for i in range(3):
        client.post(
            "/api/analyze/text",
            json={"text": f"Software Engineer role number {i} with competitive compensation and benefits."},
        )

    res_page1 = client.get("/api/history?limit=2&offset=0")
    assert res_page1.status_code == 200
    data1 = res_page1.json()
    assert data1["total"] == 3
    assert len(data1["items"]) == 2

    res_page2 = client.get("/api/history?limit=2&offset=2")
    assert res_page2.status_code == 200
    data2 = res_page2.json()
    assert data2["total"] == 3
    assert len(data2["items"]) == 1

