"""
End-to-end test script for multi-tenant hospital SaaS platform.
Covers Phase 1 (DB migration), Phase 2 (backend infra), Phase 3 (frontend routing/context), Phase 4 (URL mapping).
Run with: pytest tests/test_multi_tenant_e2e.py
"""

import requests
import pytest

BASE_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:3000"

# Demo slugs for test
HOSPITAL_SLUGS = ["demo1", "demo2"]

# Cache tokens for each hospital admin and superadmin
TOKENS = {}

def get_token(username, password="Admin@123"):
    if username in TOKENS:
        return TOKENS[username]
    resp = requests.post(f"{BASE_URL}/admin/login", json={"username": username, "password": password})
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    token = resp.json()["access_token"]
    TOKENS[username] = token
    return token

def get_admin_token_for_slug(slug):
    return get_token(f"admin_{slug}")

def get_superadmin_token():
    # Try default superadmin credentials
    return get_token("superadmin", "Admin@123")

@pytest.mark.parametrize("slug", HOSPITAL_SLUGS)
def test_url_mapping_service(slug):
    """Test backend URL mapping service for slug→hospital_id resolution."""
    resp = requests.get(f"{BASE_URL}/admin/hospitals/by-slug/{slug}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["slug"] == slug
    assert "id" in data

@pytest.mark.parametrize("slug", HOSPITAL_SLUGS)
def test_tenant_middleware_and_isolation(slug):
    """Test backend tenant middleware and data isolation."""
    # Get hospital_id from slug
    resp = requests.get(f"{BASE_URL}/admin/hospitals/by-slug/{slug}")
    hospital_id = resp.json()["id"]
    # Get doctors for hospital (authenticated as hospital admin)
    token = get_admin_token_for_slug(slug)
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/admin/doctors", params={"slug": slug}, headers=headers)
    assert resp.status_code == 200, f"Doctors fetch failed for {slug}: {resp.text}"
    doctors = resp.json()
    for doc in doctors:
        assert doc.get("hospital_id", hospital_id) == hospital_id

@pytest.mark.parametrize("slug", HOSPITAL_SLUGS)
def test_frontend_routing_and_context(slug):
    """Test frontend routing, context loading, and deep linking."""
    resp = requests.get(f"{FRONTEND_URL}/h/{slug}")
    assert resp.status_code == 200
    assert f"/h/{slug}" in resp.url
    # Check hospital context loads
    # (Assume hospital name appears in page HTML)
    assert slug in resp.text

@pytest.mark.parametrize("slug", HOSPITAL_SLUGS)
def test_admin_panel_data_isolation(slug):
    """Test admin panel only shows current hospital's data."""
    token = get_admin_token_for_slug(slug)
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/admin/hospitals", params={"slug": slug}, headers=headers)
    assert resp.status_code == 200, f"Hospitals fetch failed for {slug}: {resp.text}"
    hospitals = resp.json()
    for hosp in hospitals:
        assert hosp["slug"] == slug

# Additional tests for error handling, invalid slugs, and superadmin bypass

def test_invalid_slug_redirect():
    resp = requests.get(f"{FRONTEND_URL}/h/invalidslug", allow_redirects=True)
    assert resp.status_code == 200
    # Should redirect to /h/demo1 or show error
    assert "/h/demo1" in resp.url or "Hospital not found" in resp.text

def test_superadmin_access():
    token = get_superadmin_token()
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.get(f"{BASE_URL}/admin/hospitals", headers=headers)
    assert resp.status_code == 200, f"Superadmin hospitals fetch failed: {resp.text}"
    hospitals = resp.json()
    assert len(hospitals) >= 2  # Superadmin sees all hospitals
