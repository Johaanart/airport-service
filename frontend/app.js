// El frontend solo conoce los microservicios propios (nunca API Colombia).
const AIRPORT_API = "http://localhost:8001";
const ITINERARY_API = "http://localhost:8002";

// API Colombia identifica aeropuertos con IDs numéricos. Se consultan en este rango
// y se ignoran los que no existan o no tengan coordenadas.
const MAX_AIRPORT_ID = 60;

// Estimación simple de duración: distancia / velocidad de crucero + tiempo fijo.
const EARTH_RADIUS_KM = 6371;
const CRUISE_SPEED_KMH = 750;
const FIXED_OVERHEAD_MIN = 30;
const MIN_ESTIMATE_MIN = 30;

const COLORS = {
  base: "#2563eb",
  departure: "#16a34a",
  arrival: "#dc2626",
  route: "#f59e0b",
};

const airports = new Map(); // id -> { id, name, city, iata, lat, lon }
const selection = { departure: "", arrival: "" };
let toastTimer = null;

function $(id) {
  return document.getElementById(id);
}

function setText(el, text) {
  el.textContent = text;
}

/* ---------------- Utilidades ---------------- */

function toRadians(degrees) {
  return (degrees * Math.PI) / 180;
}

function distanceKm(a, b) {
  const dLat = toRadians(b.lat - a.lat);
  const dLon = toRadians(b.lon - a.lon);
  const h =
    Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(a.lat)) * Math.cos(toRadians(b.lat)) * Math.sin(dLon / 2) ** 2;
  return 2 * EARTH_RADIUS_KM * Math.asin(Math.sqrt(h));
}

function estimateMinutes(km) {
  const minutes = Math.round((km / CRUISE_SPEED_KMH) * 60 + FIXED_OVERHEAD_MIN);
  return Math.max(MIN_ESTIMATE_MIN, minutes);
}

function formatMinutes(total) {
  const hours = Math.floor(total / 60);
  const minutes = total % 60;
  if (hours === 0) return `${minutes} min`;
  if (minutes === 0) return `${hours} h`;
  return `${hours} h ${minutes} min`;
}

function todayIso() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}

function airportLabel(id) {
  const airport = airports.get(id);
  return airport ? airport.city || airport.name : `ID ${id}`;
}

function errorDetail(body) {
  if (!body) return "Error desconocido";
  if (typeof body.detail === "string") return body.detail;
  return JSON.stringify(body.detail || body);
}

function showMessage(text, ok) {
  const box = $("msg");
  box.className = ok ? "toast toast-ok" : "toast toast-err";
  setText(box, text);
  box.hidden = false;

  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    box.hidden = true;
  }, 7000);
}

/* ---------------- Estado de los servicios ---------------- */

async function isOnline(baseUrl) {
  try {
    const res = await fetch(`${baseUrl}/health`);
    return res.ok;
  } catch {
    return false;
  }
}

async function updateServiceChip(chipId, label, baseUrl) {
  const online = await isOnline(baseUrl);
  const state = online ? "en línea" : "sin conexión";
  const chip = $(chipId);
  chip.className = online ? "chip chip-ok" : "chip chip-bad";
  setText(chip, `${label}: ${state}`);
}

/* ---------------- Aeropuertos y mapa ---------------- */

async function loadAirports() {
  const ids = Array.from({ length: MAX_AIRPORT_ID }, (_, i) => String(i + 1));
  const results = await Promise.allSettled(
    ids.map(async (id) => {
      const res = await fetch(`${AIRPORT_API}/airports/${id}`);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return res.json();
    })
  );

  results.forEach((result) => {
    if (result.status !== "fulfilled") return;
    const a = result.value;
    if (typeof a.latitude !== "number" || typeof a.longitude !== "number") return;
    airports.set(a.id, {
      id: a.id,
      name: a.name,
      city: a.city || "",
      iata: a.iata_code || "s/c",
      lat: a.latitude,
      lon: a.longitude,
    });
  });

  setText($("stat-airports"), String(airports.size));
}

function highlightTrace(airport, color, label) {
  return {
    type: "scattergeo",
    mode: "markers+text",
    lat: [airport.lat],
    lon: [airport.lon],
    text: [label],
    textposition: "top center",
    textfont: { size: 12, color },
    marker: { size: 15, color, line: { width: 2, color: "#ffffff" } },
    hoverinfo: "skip",
    showlegend: false,
  };
}

function routeTrace(from, to) {
  return {
    type: "scattergeo",
    mode: "lines",
    lat: [from.lat, to.lat],
    lon: [from.lon, to.lon],
    line: { width: 3, color: COLORS.route },
    hoverinfo: "skip",
    showlegend: false,
  };
}

function buildTraces() {
  const list = Array.from(airports.values());
  const traces = [
    {
      type: "scattergeo",
      mode: "markers",
      lat: list.map((a) => a.lat),
      lon: list.map((a) => a.lon),
      customdata: list.map((a) => a.id),
      text: list.map((a) => `${a.name} (${a.iata})<br>${a.city}`),
      hoverinfo: "text",
      marker: { size: 9, color: COLORS.base, line: { width: 1, color: "#ffffff" } },
      showlegend: false,
    },
  ];

  const dep = airports.get(selection.departure);
  const arr = airports.get(selection.arrival);

  if (dep && arr && dep.id !== arr.id) traces.push(routeTrace(dep, arr));
  if (dep) traces.push(highlightTrace(dep, COLORS.departure, "Salida"));
  if (arr) traces.push(highlightTrace(arr, COLORS.arrival, "Llegada"));
  return traces;
}

function mapLayout() {
  return {
    margin: { t: 0, b: 0, l: 0, r: 0 },
    paper_bgcolor: "rgba(0,0,0,0)",
    uirevision: "keep-view",
    geo: {
      scope: "south america",
      fitbounds: "locations",
      showcountries: true,
      countrycolor: "#cbd5e1",
      showland: true,
      landcolor: "#f8fafc",
      showocean: true,
      oceancolor: "#e0f2fe",
      showcoastlines: true,
      coastlinecolor: "#94a3b8",
      bgcolor: "rgba(0,0,0,0)",
    },
  };
}

const MAP_CONFIG = { responsive: true, displaylogo: false };

function onMapClick(event) {
  const id = event.points?.[0]?.customdata;
  if (!id) return;

  const startingNewRoute = !selection.departure || selection.arrival;
  if (startingNewRoute) {
    selection.departure = id;
    selection.arrival = "";
  } else if (id !== selection.departure) {
    selection.arrival = id;
  }

  syncSelects();
  refreshView();
}

async function initMap() {
  const status = $("map-status");

  if (airports.size === 0) {
    setText(status, "No se pudieron cargar aeropuertos. Verifica que airport-service esté activo en el puerto 8001.");
    return;
  }

  const mapEl = $("map");
  await Plotly.newPlot(mapEl, buildTraces(), mapLayout(), MAP_CONFIG);
  mapEl.on("plotly_click", onMapClick);
  setText(status, `${airports.size} aeropuertos cargados desde Airport Service.`);
}

function redrawMap() {
  if (airports.size === 0) return;
  void Plotly.react($("map"), buildTraces(), mapLayout(), MAP_CONFIG);
}

/* ---------------- Formulario ---------------- */

function fillSelects() {
  ["departure", "arrival"].forEach((selectId) => {
    const select = $(selectId);
    select.replaceChildren();

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "Selecciona un aeropuerto";
    select.appendChild(placeholder);

    airports.forEach((a) => {
      const option = document.createElement("option");
      option.value = a.id;
      option.textContent = `${a.name} - ${a.city} (${a.iata})`;
      select.appendChild(option);
    });
  });
}

function syncSelects() {
  $("departure").value = selection.departure;
  $("arrival").value = selection.arrival;
}

function updateRouteSummary() {
  const box = $("route-summary");
  const dep = airports.get(selection.departure);
  const arr = airports.get(selection.arrival);

  if (!dep || !arr || dep.id === arr.id) {
    box.hidden = true;
    return;
  }

  const km = Math.round(distanceKm(dep, arr));
  const minutes = estimateMinutes(km);
  setText($("route-title"), `${airportLabel(dep.id)} → ${airportLabel(arr.id)}`);
  setText($("route-meta"), `${km} km en línea recta · duración estimada ${formatMinutes(minutes)}`);
  box.dataset.minutes = String(minutes);
  box.hidden = false;
}

function refreshView() {
  redrawMap();
  updateRouteSummary();
}

function onSelectChange() {
  selection.departure = $("departure").value;
  selection.arrival = $("arrival").value;
  refreshView();
}

function useEstimate() {
  const minutes = $("route-summary").dataset.minutes;
  if (minutes) $("duration").value = minutes;
}

async function submitItinerary(event) {
  event.preventDefault();

  if (selection.departure === selection.arrival) {
    showMessage("El aeropuerto de salida y el de llegada deben ser distintos.", false);
    return;
  }

  const payload = {
    user_name: $("user_name").value.trim(),
    departure_airport_id: selection.departure,
    arrival_airport_id: selection.arrival,
    travel_date: $("travel_date").value,
    duration_minutes: Number($("duration").value),
  };

  const button = $("submit-btn");
  button.disabled = true;
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
      selection.departure = "";
      selection.arrival = "";
      refreshView();
      await loadItineraries();
    } else {
      showMessage(`No se pudo crear el itinerario: ${errorDetail(body)}`, false);
    }
  } catch {
    showMessage("No se pudo contactar itinerary-service.", false);
  } finally {
    button.disabled = false;
  }
}

/* ---------------- Itinerarios ---------------- */

function textCell(value) {
  const td = document.createElement("td");
  setText(td, value);
  return td;
}

function badgeCell(status) {
  const td = document.createElement("td");
  const badge = document.createElement("span");
  badge.className = "badge";
  setText(badge, status);
  td.appendChild(badge);
  return td;
}

function actionButton(label, className, onClick) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = `btn btn-small ${className}`;
  setText(button, label);
  button.addEventListener("click", onClick);
  return button;
}

function showOnMap(itinerary) {
  selection.departure = itinerary.departure_airport_id;
  selection.arrival = itinerary.arrival_airport_id;
  syncSelects();
  refreshView();
  $("map").scrollIntoView({ behavior: "smooth", block: "center" });
}

function actionsCell(itinerary) {
  const td = document.createElement("td");
  const wrapper = document.createElement("div");
  wrapper.className = "actions";
  wrapper.appendChild(actionButton("Ver en mapa", "btn-ghost", () => showOnMap(itinerary)));
  wrapper.appendChild(
    actionButton("Eliminar", "btn-danger", () => {
      void deleteItinerary(itinerary.id);
    })
  );
  td.appendChild(wrapper);
  return td;
}

function itineraryRow(itinerary) {
  const tr = document.createElement("tr");
  const route = `${airportLabel(itinerary.departure_airport_id)} → ${airportLabel(itinerary.arrival_airport_id)}`;

  tr.appendChild(textCell(itinerary.user_name));
  tr.appendChild(textCell(route));
  tr.appendChild(textCell(itinerary.travel_date));
  tr.appendChild(textCell(formatMinutes(itinerary.duration_minutes)));
  tr.appendChild(badgeCell(itinerary.status));
  tr.appendChild(actionsCell(itinerary));
  return tr;
}

function emptyRow(text) {
  const tr = document.createElement("tr");
  const td = document.createElement("td");
  td.colSpan = 6;
  td.className = "empty";
  setText(td, text);
  tr.appendChild(td);
  return tr;
}

async function loadItineraries() {
  const tbody = $("itineraries");
  tbody.replaceChildren();

  try {
    const res = await fetch(`${ITINERARY_API}/itineraries`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const items = await res.json();

    setText($("stat-itineraries"), String(items.length));
    if (items.length === 0) {
      tbody.appendChild(emptyRow("Aún no hay itinerarios. Crea el primero desde el formulario."));
      return;
    }
    items.forEach((item) => tbody.appendChild(itineraryRow(item)));
  } catch {
    setText($("stat-itineraries"), "-");
    tbody.appendChild(emptyRow("No se pudo cargar la lista (¿itinerary-service activo en el puerto 8002?)."));
  }
}

async function deleteItinerary(id) {
  const res = await fetch(`${ITINERARY_API}/itineraries/${id}`, { method: "DELETE" });
  if (res.status === 204) {
    showMessage("Itinerario eliminado.", true);
    await loadItineraries();
  } else {
    showMessage("No se pudo eliminar el itinerario.", false);
  }
}

/* ---------------- Arranque ---------------- */

$("departure").addEventListener("change", onSelectChange);
$("arrival").addEventListener("change", onSelectChange);
$("use-estimate").addEventListener("click", useEstimate);
$("itinerary-form").addEventListener("submit", (event) => {
  void submitItinerary(event);
});

async function init() {
  $("travel_date").min = todayIso();

  await Promise.all([
    loadAirports(),
    updateServiceChip("chip-airport", "Airport Service", AIRPORT_API),
    updateServiceChip("chip-itinerary", "Itinerary Service", ITINERARY_API),
  ]);

  fillSelects();
  await initMap();
  await loadItineraries();
}

init().catch((err) => {
  setText($("map-status"), `Error al iniciar la aplicación: ${err.message}`);
});
