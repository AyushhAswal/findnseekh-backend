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


def test_teachers_sorting_and_price_filters(client, db):
    """Test teacher sorting (price, experience, rating) and budget filtering."""
    # 1. Test Price: Low to High (both kebab-case and snake_case)
    res_asc = client.get("/api/v1/teachers?sort=price-asc")
    assert res_asc.status_code == 200
    teachers_asc = res_asc.json()["data"]["teachers"]
    assert len(teachers_asc) >= 2
    for i in range(len(teachers_asc) - 1):
        assert float(teachers_asc[i]["hourly_rate"]) <= float(teachers_asc[i + 1]["hourly_rate"])

    res_asc2 = client.get("/api/v1/teachers?sort=price_asc")
    assert res_asc2.status_code == 200
    teachers_asc2 = res_asc2.json()["data"]["teachers"]
    assert float(teachers_asc2[0]["hourly_rate"]) <= float(teachers_asc2[-1]["hourly_rate"])

    # 2. Test Price: High to Low
    res_desc = client.get("/api/v1/teachers?sort=price-desc")
    assert res_desc.status_code == 200
    teachers_desc = res_desc.json()["data"]["teachers"]
    assert float(teachers_desc[0]["hourly_rate"]) >= float(teachers_desc[-1]["hourly_rate"])

    # 3. Test Experience sorting
    res_exp = client.get("/api/v1/teachers?sort=experience")
    assert res_exp.status_code == 200
    teachers_exp = res_exp.json()["data"]["teachers"]
    assert teachers_exp[0]["experience_years"] >= teachers_exp[-1]["experience_years"]

    # 4. Test Price filtering (min_price and max_price)
    res_price_filter = client.get("/api/v1/teachers?min_price=600&max_price=800")
    assert res_price_filter.status_code == 200
    filtered_teachers = res_price_filter.json()["data"]["teachers"]
    assert len(filtered_teachers) > 0
    for t in filtered_teachers:
        rate = float(t["hourly_rate"])
        assert 600 <= rate <= 800

    # 5. Test Rating filtering
    res_rating = client.get("/api/v1/teachers?min_rating=4.8")
    assert res_rating.status_code == 200
    rating_teachers = res_rating.json()["data"]["teachers"]
    for t in rating_teachers:
        assert float(t["rating"]) >= 4.8


