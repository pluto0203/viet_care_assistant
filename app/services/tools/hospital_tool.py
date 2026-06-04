# app/services/tools/hospital_tool.py
import math
import httpx
from app.core.logging import get_logger

logger = get_logger(__name__)

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
OVERPASS_URL = "https://overpass-api.de/api/interpreter"
USER_AGENT = "VietCareAssistant/2.0 (healthcare-chatbot)"

HOSPITAL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "find_nearby_hospitals",
        "description": (
            "Tìm bệnh viện và phòng khám gần một địa điểm. "
            "Dùng khi user hỏi tìm cơ sở y tế, bệnh viện, phòng khám gần."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "Tên địa điểm, ví dụ: 'quận 1 HCM', 'Hoàn Kiếm Hà Nội'",
                },
                "radius_km": {
                    "type": "integer",
                    "description": "Bán kính tìm kiếm tính bằng km (mặc định 2)",
                    "default": 2,
                },
                "limit": {
                    "type": "integer",
                    "description": "Số kết quả tối đa (mặc định 5)",
                    "default": 5,
                },
            },
            "required": ["location"],
        },
    },
}


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in km between two coordinates."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _geocode(location: str) -> tuple[float, float] | None:
    """Convert location name to lat/lng via Nominatim. Returns None if not found."""
    try:
        response = httpx.get(
            NOMINATIM_URL,
            params={"q": location, "format": "json", "limit": 1},
            headers={"User-Agent": USER_AGENT},
            timeout=10,
        )
        response.raise_for_status()
        results = response.json()
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except Exception as e:
        logger.warning("nominatim_error", location=location, error=str(e))
        return None


def _query_overpass(lat: float, lon: float, radius_m: int) -> list[dict]:
    """Query Overpass API for hospitals/clinics within radius."""
    query = f"""
[out:json][timeout:15];
(
  node["amenity"="hospital"](around:{radius_m},{lat},{lon});
  node["amenity"="clinic"](around:{radius_m},{lat},{lon});
  way["amenity"="hospital"](around:{radius_m},{lat},{lon});
  way["amenity"="clinic"](around:{radius_m},{lat},{lon});
);
out center;
"""
    try:
        response = httpx.post(OVERPASS_URL, data=query, timeout=20)
        response.raise_for_status()
        return response.json().get("elements", [])
    except Exception as e:
        logger.warning("overpass_error", error=str(e))
        return []


def find_nearby_hospitals(location: str, radius_km: int = 2, limit: int = 5) -> str:
    """Find nearby hospitals/clinics and return a formatted list."""
    coords = _geocode(location)
    if coords is None:
        return (
            f"Không tìm thấy địa điểm '{location}'. "
            "Vui lòng thử lại với tên rõ hơn, ví dụ: 'quận 1 thành phố Hồ Chí Minh'."
        )

    lat, lon = coords
    elements = _query_overpass(lat, lon, radius_km * 1000)

    if not elements:
        return (
            f"Không tìm thấy bệnh viện hoặc phòng khám nào "
            f"trong bán kính {radius_km}km quanh '{location}'."
        )

    results = []
    for el in elements:
        tags = el.get("tags", {})
        name = tags.get("name") or tags.get("name:vi") or "Không rõ tên"

        if el["type"] == "node":
            el_lat, el_lon = el["lat"], el["lon"]
        elif el["type"] == "way" and "center" in el:
            el_lat, el_lon = el["center"]["lat"], el["center"]["lon"]
        else:
            continue

        distance = _haversine(lat, lon, el_lat, el_lon)
        address = tags.get("addr:street", "")
        results.append({"name": name, "address": address, "distance_km": round(distance, 2)})

    results.sort(key=lambda x: x["distance_km"])
    results = results[:limit]

    lines = [f"Bệnh viện/phòng khám gần '{location}' (bán kính {radius_km}km):\n"]
    for i, r in enumerate(results, 1):
        addr = f" — {r['address']}" if r["address"] else ""
        lines.append(f"{i}. {r['name']}{addr} ({r['distance_km']} km)")

    return "\n".join(lines)
