"""Tests for Home Overview, Teachers, Skills, Locations, and ETag caching."""
import pytest
from src.category.controllers import seed_categories
from src.category.models import CategoryModel
from src.profile.models import TeacherProfileModel
from src.roles.models import RoleModel, UserRoleModel
from src.skills.models import SkillListingModel
from src.users.models import UserModel
from src.utils.auth import hash_password


def test_etag_caching(client, db):
    """Verify ETag header generation and 304 Not Modified response."""
    seed_categories(db)

    # 1. First GET request - should receive 200 OK and ETag header
    res1 = client.get("/api/v1/categories")
    assert res1.status_code == 200
    etag = res1.headers.get("etag")
    assert etag is not None
    assert "cache-control" in res1.headers
    assert len(res1.json()["data"]) > 0

    # 2. Conditional GET with matching If-None-Match - should return 304 Not Modified
    res2 = client.get("/api/v1/categories", headers={"If-None-Match": etag})
    assert res2.status_code == 304
    assert res2.text == ""

    # 3. Conditional GET with mismatched If-None-Match - should return 200 OK
    res3 = client.get("/api/v1/categories", headers={"If-None-Match": 'W/"different-hash"'})
    assert res3.status_code == 200
    assert res3.json()["status"] == 200


def test_home_overview_endpoint(client, db):
    """Test GET /api/v1/home/overview aggregation."""
    seed_categories(db)

    res = client.get("/api/v1/home/overview")
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == 200
    data = body["data"]

    # Verify all aggregated sections exist
    assert "categories" in data
    assert "popular_skills" in data
    assert "locations" in data
    assert "featured_teachers" in data
    assert "stats" in data

    assert len(data["categories"]) >= 8
    assert len(data["popular_skills"]) > 0
    assert len(data["locations"]) > 0
    assert len(data["featured_teachers"]) > 0

    # Verify ETag on overview
    etag = res.headers.get("etag")
    assert etag is not None
    res_cached = client.get("/api/v1/home/overview", headers={"If-None-Match": etag})
    assert res_cached.status_code == 304


def test_skills_popular_and_suggestions(client, db):
    """Test GET /api/v1/skills/popular and /api/v1/skills/suggestions."""
    seed_categories(db)

    # Popular skills
    res_pop = client.get("/api/v1/skills/popular?limit=5")
    assert res_pop.status_code == 200
    pop_data = res_pop.json()["data"]
    assert len(pop_data) <= 5
    assert all("name" in item and "category" in item for item in pop_data)

    # Suggestions without query
    res_sug1 = client.get("/api/v1/skills/suggestions?limit=6")
    assert res_sug1.status_code == 200
    sug_data1 = res_sug1.json()["data"]
    assert len(sug_data1) <= 6

    # Suggestions with query
    res_sug2 = client.get("/api/v1/skills/suggestions?query=guitar")
    assert res_sug2.status_code == 200
    sug_data2 = res_sug2.json()["data"]
    assert any("guitar" in item["name"].lower() for item in sug_data2)


def test_locations_suggestions(client, db):
    """Test GET /api/v1/locations/suggestions."""
    res = client.get("/api/v1/locations/suggestions?q=delhi")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) > 0
    assert any("delhi" in item["city"].lower() for item in data)


def test_teachers_featured_and_listing(client, db):
    """Test GET /api/v1/teachers and /api/v1/teachers/featured."""
    # Featured teachers
    res_feat = client.get("/api/v1/teachers/featured?limit=4")
    assert res_feat.status_code == 200
    feat_data = res_feat.json()["data"]
    assert len(feat_data) <= 4
    for teacher in feat_data:
        assert "name" in teacher
        assert "specialty" in teacher
        assert "hourly_rate" in teacher

    # Teacher listing
    res_list = client.get("/api/v1/teachers?page=1&page_size=5")
    assert res_list.status_code == 200
    list_data = res_list.json()["data"]
    assert "teachers" in list_data
    assert "total" in list_data
    assert len(list_data["teachers"]) <= 5

    # Teacher detail
    teacher_id = feat_data[0]["user_id"]
    res_detail = client.get(f"/api/v1/teachers/{teacher_id}")
    assert res_detail.status_code == 200
    detail_data = res_detail.json()["data"]
    assert detail_data["user_id"] == teacher_id

