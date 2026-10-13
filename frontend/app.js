// El frontend solo conoce los microservicios propios (nunca API Colombia).
const AIRPORT_API = "http://localhost:8001";
const ITINERARY_API = "http://localhost:8002";

// API Colombia identifica aeropuertos con IDs numéricos. Se consultan en este rango
// y se ignoran los que no existan o no tengan coordenadas.
const MAX_AIRPORT_ID = 60;

const airports = new Map(); // id -> { id, name, city, iata, lat, lon }

function setText(el, text) {
  el.textContent = text;
}

// Algunos registros de API Colombia traen latitud y longitud invertidas
// (ej. latitud -75.7, longitud 4.4). Colombia está en lat -5..14 y lon -82..-66.
function normalizeCoords(lat, lon) {
  const looksSwapped = lat < -20 && lon > -20 && lon < 20;
  return looksSwapped ? { lat: lon, lon: lat } : { lat, lon };
}

async function loadAirports() {
  const ids = Array.from({ length: MAX_AIRPORT_ID }, (_, i) => String(i + 1));
  const results = await Promise.allSettled(
    ids.map(async (id) => {
      const res = await fetch(`${AIRPORT_API}/airports/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
  );

  results.forEach((r) => {
    if (r.status !== "fulfilled") return;
    const a = r.value;
    if (typeof a.latitude !== "number" || typeof a.longitude !== "number") return;
    const { lat, lon } = normalizeCoords(a.latitude, a.longitude);
    airports.set(a.id, {
      id: a.id,
      name: a.name,
      city: a.city || "",
      iata: a.iata_code || "s/c",
      lat,
      lon,
    });
  });
}

function drawMap() {
  const list = Array.from(airports.values());
  const status = document.getElementById("map-status");

  if (list.length === 0) {
    setText(status, "No se pudieron cargar aeropuertos. Verifica que airport-service esté activo en el puerto 8001.");
    return;
  }

  const trace = {
    type: "scattergeo",
    mode: "markers",
    lat: list.map((a) => a.lat),
    lon: list.map((a) => a.lon),
    text: list.map((a) => `${a.name} (${a.iata})<br>${a.city}`),
    hoverinfo: "text",
    marker: { size: 9, color: "#1b6ef3" },
  };

  const layout = {
    margin: { t: 0, b: 0, l: 0, r: 0 },
    geo: {
      scope: "south america",
      fitbounds: "locations",
      showcountries: true,
      showland: true,
      landcolor: "#eef1f5",
    },
  };

  Plotly.newPlot("map", [trace], layout, { responsive: true });
  setText(status, `${list.length} aeropuertos cargados desde Airport Service.`);
}

function fillSelects() {
  ["departure", "arrival"].forEach((selectId) => {
    const select = document.getElementById(selectId);
    select.replaceChildren();
    airports.forEach((a) => {
      const option = document.createElement("option");
      option.value = a.id;
      option.textContent = `${a.name} - ${a.city} (${a.iata})`;
      select.appendChild(option);
    });
  });
}

function airportLabel(id) {
  const a = airports.get(id);
  return a ? a.name : `ID ${id}`;
}

function errorDetail(body) {
  if (!body) return "Error desconocido";
  if (typeof body.detail === "string") return body.detail;
  return JSON.stringify(body.detail || body);
}

function showMessage(text, ok) {
  const msg = document.getElementById("msg");
  msg.className = ok ? "ok" : "err";
  setText(msg, text);
}

async function loadItineraries() {
  const tbody = document.getElementById("itineraries");
  tbody.replaceChildren();
  try {
    const res = await fetch(`${ITINERARY_API}/itineraries`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const items = await res.json();

    items.forEach((it) => {
      const tr = document.createElement("tr");
      [
        it.user_name,
        airportLabel(it.departure_airport_id),
        airportLabel(it.arrival_airport_id),
        it.travel_date,
        String(it.duration_minutes),
        it.status,
      ].forEach((value) => {
        const td = document.createElement("td");
        setText(td, value);
        tr.appendChild(td);
      });

      const actions = document.createElement("td");
      const del = document.createElement("button");
      del.className = "danger";
      setText(del, "Eliminar");
      del.addEventListener("click", () => deleteItinerary(it.id));
      actions.appendChild(del);
      tr.appendChild(actions);

      tbody.appendChild(tr);
    });
  } catch (err) {
    showMessage("No se pudo cargar la lista de itinerarios (¿itinerary-service activo en 8002?).", false);
  }
}

async function deleteItinerary(id) {
  const res = await fetch(`${ITINERARY_API}/itineraries/${id}`, { method: "DELETE" });
  if (res.status === 204) {
    showMessage("Itinerario eliminado.", true);
    loadItineraries();
  } else {
    showMessage("No se pudo eliminar el itinerario.", false);
  }
}

document.getElementById("itinerary-form").addEventListener("submit", async (event) => {
  event.preventDefault();

  const payload = {
    user_name: document.getElementById("user_name").value.trim(),
    departure_airport_id: document.getElementById("departure").value,
    arrival_airport_id: document.getElementById("arrival").value,
    travel_date: document.getElementById("travel_date").value,
    duration_minutes: Number(document.getElementById("duration").value),
  };

  try {
    const res = await fetch(`${ITINERARY_API}/itineraries`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const body = await res.json().catch(() => null);

    if (res.status === 201) {
      showMessage("Itinerario creado. La notificación se procesa de forma asíncrona.", true);
      event.target.reset();
      loadItineraries();
    } else {
      showMessage(`No se pudo crear el itinerario: ${errorDetail(body)}`, false);
    }
  } catch (err) {
    showMessage("No se pudo contactar itinerary-service.", false);
  }
});

(async function init() {
  await loadAirports();
  drawMap();
  fillSelects();
  loadItineraries();
})();
