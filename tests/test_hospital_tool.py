# tests/test_hospital_tool.py
from unittest.mock import patch, MagicMock
from app.services.tools.hospital_tool import find_nearby_hospitals, HOSPITAL_TOOL_SCHEMA


def test_schema_name():
    assert HOSPITAL_TOOL_SCHEMA["function"]["name"] == "find_nearby_hospitals"


def test_schema_location_is_required():
    required = HOSPITAL_TOOL_SCHEMA["function"]["parameters"]["required"]
    assert "location" in required


def _mock_geocode_response(lat="10.7769", lon="106.7009"):
    resp = MagicMock()
    resp.json.return_value = [{"lat": lat, "lon": lon}]
    resp.raise_for_status = MagicMock()
    return resp


def _mock_overpass_response(elements):
    resp = MagicMock()
    resp.json.return_value = {"elements": elements}
    resp.raise_for_status = MagicMock()
    return resp


def test_find_hospitals_returns_hospital_name():
    elements = [
        {
            "type": "node",
            "lat": 10.77,
            "lon": 106.70,
            "tags": {"name": "BV Chợ Rẫy", "amenity": "hospital"},
        }
    ]
    with patch("httpx.get", return_value=_mock_geocode_response()), \
         patch("httpx.post", return_value=_mock_overpass_response(elements)):
        result = find_nearby_hospitals(location="quận 1 HCM")

    assert "BV Chợ Rẫy" in result


def test_find_hospitals_location_not_found():
    resp = MagicMock()
    resp.json.return_value = []
    resp.raise_for_status = MagicMock()

    with patch("httpx.get", return_value=resp):
        result = find_nearby_hospitals(location="xyz unknown abc")

    assert isinstance(result, str)
    assert len(result) > 0


def test_find_hospitals_no_results():
    with patch("httpx.get", return_value=_mock_geocode_response()), \
         patch("httpx.post", return_value=_mock_overpass_response([])):
        result = find_nearby_hospitals(location="quận 1 HCM")

    assert isinstance(result, str)
    assert len(result) > 0


def test_find_hospitals_respects_limit():
    elements = [
        {
            "type": "node",
            "lat": 10.77 + i * 0.001,
            "lon": 106.70,
            "tags": {"name": f"BV {i}", "amenity": "hospital"},
        }
        for i in range(10)
    ]
    with patch("httpx.get", return_value=_mock_geocode_response()), \
         patch("httpx.post", return_value=_mock_overpass_response(elements)):
        result = find_nearby_hospitals(location="quận 1 HCM", limit=3)

    count = result.count("BV ")
    assert count <= 3


def test_find_hospitals_way_element_uses_center():
    elements = [
        {
            "type": "way",
            "center": {"lat": 10.77, "lon": 106.70},
            "tags": {"name": "BV Lớn", "amenity": "hospital"},
        }
    ]
    with patch("httpx.get", return_value=_mock_geocode_response()), \
         patch("httpx.post", return_value=_mock_overpass_response(elements)):
        result = find_nearby_hospitals(location="quận 1 HCM")

    assert "BV Lớn" in result
