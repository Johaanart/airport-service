from app.infrastructure.api_colombia_adapter import ApiColombiaAdapter, normalize_coordinates


def test_swapped_coordinates_are_corrected():
    # Respuesta real de API Colombia para El Edén (Armenia): campos invertidos
    data = {
        "id": 1,
        "name": "Aeropuerto Internacional El Edén",
        "iataCode": "AXM",
        "oaciCode": "SKAR",
        "city": {"id": 885, "name": "Armenia"},
        "latitude": -75.7659806671205,
        "longitude": 4.4532428642135,
    }

    airport = ApiColombiaAdapter._map_to_airport(data)

    assert airport.latitude == 4.4532428642135
    assert airport.longitude == -75.7659806671205
    assert airport.icao_code == "SKAR"
    assert airport.city == "Armenia"


def test_correct_coordinates_are_not_modified():
    assert normalize_coordinates(4.70, -74.14) == (4.70, -74.14)


def test_san_andres_swapped_is_corrected():
    assert normalize_coordinates(-81.7, 12.58) == (12.58, -81.7)


def test_missing_coordinates_stay_none():
    airport = ApiColombiaAdapter._map_to_airport({"id": 2, "name": "Sin coordenadas"})
    assert airport.latitude is None
    assert airport.longitude is None