from fastapi import APIRouter
from pydantic import BaseModel
from typing import List
import math

router = APIRouter()

# -------------------------------
# Models
# -------------------------------
class Stop(BaseModel):
    id: str
    lat: float
    lon: float

class OptimizeRequest(BaseModel):
    depot: Stop
    stops: List[Stop]

# -------------------------------
# Haversine distance
# -------------------------------
def haversine(a, b):
    R = 6371.0
    lat1, lon1 = math.radians(a[0]), math.radians(a[1])
    lat2, lon2 = math.radians(b[0]), math.radians(b[1])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    sa = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    return R * 2 * math.asin(min(1, math.sqrt(sa)))

# -------------------------------
# Route Optimization
# -------------------------------
@router.post("/route")
def optimize_route(req: OptimizeRequest):
    depot = (req.depot.lat, req.depot.lon)
    remaining = [(s.id, s.lat, s.lon) for s in req.stops]
    route_list = []
    route_coords = [{"id": "Depot", "lat": depot[0], "lon": depot[1]}]  # include depot at start
    current = depot
    total_km = 0.0

    while remaining:
        # find nearest stop
        nearest = min(remaining, key=lambda x: haversine(current, (x[1], x[2])))
        dist = haversine(current, (nearest[1], nearest[2]))
        total_km += dist
        route_list.append({
            "id": nearest[0],
            "lat": nearest[1],
            "lon": nearest[2],
            "dist_from_prev_km": dist
        })
        route_coords.append({
            "id": nearest[0],
            "lat": nearest[1],
            "lon": nearest[2]
        })
        current = (nearest[1], nearest[2])
        remaining = [r for r in remaining if r[0] != nearest[0]]

    # return to depot
    back_dist = haversine(current, depot)
    total_km += back_dist
    route_coords.append({"id": "Depot", "lat": depot[0], "lon": depot[1]})

    # Prepare route order (including depot at start and end)
    route_order = ["Depot"] + [stop["id"] for stop in route_list] + ["Depot"]

    # Return in format frontend expects
    return {
        "distance": total_km,       # total distance in km
        "route": route_order,       # route order for Streamlit
        "route_coords": route_coords  # coordinates for PyDeck map
    }
