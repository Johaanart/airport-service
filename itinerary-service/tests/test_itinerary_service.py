import respx
import httpx
from fastapi.testclient import TestClient

from app.main import app
from app.config import AIRPORT_SERVICE_URL

client = TestClient(app)


@respx.mock
def test_create_itinerary_validates_against_airport_service():
    # Confirma que Itinerary Service llama al AIRPORT SERVICE (no a API
    # Colombia) para validar los aeropuertos.
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/1").mock(
        return_value=httpx.Response(200, json={"id": "1", "name": "El Edén"})
    )
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/2").mock(
        return_value=httpx.Response(200, json={"id": "2", "name": "El Dorado"})
    )

    response = client.post(
        "/itineraries",
        json={
            "user_name": "johan",
            "departure_airport_id": "1",
            "arrival_airport_id": "2",
            "travel_date": "2026-10-01",
            "duration_minutes": 90,
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "CREATED"


@respx.mock
def test_create_itinerary_airport_not_found():
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/999").mock(return_value=httpx.Response(404))
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/2").mock(
        return_value=httpx.Response(200, json={"id": "2", "name": "El Dorado"})
    )

    response = client.post(
        "/itineraries",
        json={
            "user_name": "johan",
            "departure_airport_id": "999",
            "arrival_airport_id": "2",
            "travel_date": "2026-10-01",
            "duration_minutes": 90,
        },
    )

    assert response.status_code == 404


@respx.mock
def test_create_itinerary_airport_service_unavailable():
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/1").mock(side_effect=httpx.ConnectError("down"))

    response = client.post(
        "/itineraries",
        json={
            "user_name": "johan",
            "departure_airport_id": "1",
            "arrival_airport_id": "2",
            "travel_date": "2026-10-01",
            "duration_minutes": 90,
        },
    )

    assert response.status_code == 503


@respx.mock
def test_update_and_delete_itinerary():
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/1").mock(
        return_value=httpx.Response(200, json={"id": "1"})
    )
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/2").mock(
        return_value=httpx.Response(200, json={"id": "2"})
    )
    respx.get(f"{AIRPORT_SERVICE_URL}/airports/3").mock(
        return_value=httpx.Response(200, json={"id": "3"})
    )

    created = client.post(
        "/itineraries",
        json={
            "user_name": "johan",
            "departure_airport_id": "1",
            "arrival_airport_id": "2",
            "travel_date": "2026-10-01",
            "duration_minutes": 90,
        },
    ).json()

    updated = client.put(
        f"/itineraries/{created['id']}",
        json={"arrival_airport_id": "3", "duration_minutes": 120},
    )
    assert updated.status_code == 200
    assert updated.json()["arrival_airport_id"] == "3"

    deleted = client.delete(f"/itineraries/{created['id']}")
    assert deleted.status_code == 204

    missing = client.get(f"/itineraries/{created['id']}")
    assert missing.status_code == 404
