// ============================================================
// Metrolínea Live — app.js
// Lógica del mapa, polling al backend y UI (sin frameworks).
// ============================================================

const BACKEND_URL = ""; // mismo origen: FastAPI sirve este frontend, no hace falta dominio fijo
const INTERVALO_REFRESCO_MS = 3000;          // cada cuánto le pregunta al backend

let mapa;
const marcadores = {};   // bus_id -> L.circleMarker
let estacionesCache = [];

const COLORES = {
  vacio: "#00C2A8",
  medio: "#F5A623",
  lleno: "#E8485A",
};

function colorPorOcupacion(ocupacion) {
  return COLORES[ocupacion] || COLORES.medio;
}

function etiquetaOcupacion(ocupacion) {
  return { vacio: "Vacío", medio: "Medio", lleno: "Lleno" }[ocupacion] || ocupacion;
}

// ---------------------------------------------------------------- íconos
// Ícono de estación: un pin con el número de parada (orden real de la ruta).
function iconoEstacion(numero) {
  const html = `
    <div class="station-pin">
      <svg width="26" height="34" viewBox="0 0 26 34" xmlns="http://www.w3.org/2000/svg">
        <path d="M13 0C5.8 0 0 5.7 0 12.8 0 22 13 34 13 34s13-12 13-21.2C26 5.7 20.2 0 13 0z"
              fill="#161B22" stroke="#00C2A8" stroke-width="2"/>
        <circle cx="13" cy="13" r="7.5" fill="#00C2A8"/>
      </svg>
      <span class="station-pin__num">${numero}</span>
    </div>`;
  return L.divIcon({
    html,
    className: "station-icon",
    iconSize: [26, 34],
    iconAnchor: [13, 32],
    popupAnchor: [0, -28],
  });
}

// Ícono de bus: un círculo con un glifo de bus, coloreado por ocupación y
// rotado según el rumbo (bearing) hacia el siguiente punto de su ruta.
function iconoBus(color, bearing) {
  const html = `
    <div class="bus-pin" style="background:${color}">
      <svg width="16" height="16" viewBox="0 0 24 24" style="transform: rotate(${bearing}deg)">
        <path fill="#06120F" d="M12 2L4 14h6v8l8-12h-6z"/>
      </svg>
    </div>`;
  return L.divIcon({
    html,
    className: "bus-icon",
    iconSize: [26, 26],
    iconAnchor: [13, 13],
    popupAnchor: [0, -14],
  });
}

// Rumbo (en grados) desde un punto [lat,lng] hacia otro, para orientar el ícono.
function calcularRumbo([lat1, lng1], [lat2, lng2]) {
  const rad = Math.PI / 180;
  const dLng = (lng2 - lng1) * rad;
  const y = Math.sin(dLng) * Math.cos(lat2 * rad);
  const x =
    Math.cos(lat1 * rad) * Math.sin(lat2 * rad) -
    Math.sin(lat1 * rad) * Math.cos(lat2 * rad) * Math.cos(dLng);
  return (Math.atan2(y, x) * 180) / Math.PI;
}

// ---------------------------------------------------------------- reloj
function iniciarReloj() {
  const el = document.getElementById("clock");
  const tick = () => { el.textContent = new Date().toLocaleTimeString("es-CO"); };
  tick();
  setInterval(tick, 1000);
}

// ---------------------------------------------------------------- estado conexión
function marcarEstado(estado, texto) {
  const dot = document.getElementById("statusDot");
  const txt = document.getElementById("statusText");
  dot.classList.remove("is-live", "is-error");
  if (estado === "live") dot.classList.add("is-live");
  if (estado === "error") dot.classList.add("is-error");
  txt.textContent = texto;
}

// ---------------------------------------------------------------- mapa base
function iniciarMapa() {
  mapa = L.map("mapa", { zoomControl: true, attributionControl: true })
    .setView([7.08, -73.09], 12.3);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors",
    maxZoom: 19,
  }).addTo(mapa);

  cargarEstacionesYRuta();
  actualizarBuses();
  setInterval(actualizarBuses, INTERVALO_REFRESCO_MS);

  document.getElementById("toggleTiempos").addEventListener("click", toggleTiempos);
  document.getElementById("etaClose").addEventListener("click", cerrarEta);
}

function toggleTiempos() {
  const panel = document.getElementById("panelTiempos");
  const btn = document.getElementById("toggleTiempos");
  const colapsado = panel.classList.toggle("is-collapsed");
  btn.textContent = colapsado ? "+" : "–";
  btn.setAttribute("aria-expanded", String(!colapsado));
}

// ---------------------------------------------------------------- estaciones + ruta
async function cargarEstacionesYRuta() {
  try {
    const resp = await fetch(`${BACKEND_URL}/rutas`);
    const rutas = await resp.json();
    const estaciones = rutas["troncal"]; // [{nombre, lat, lng}, ...]
    estacionesCache = estaciones;

    const puntosLinea = estaciones.map((e) => [e.lat, e.lng]);

    // Línea base + línea "viva" encima (efecto de corredor activo)
    L.polyline(puntosLinea, { color: "#2A323F", weight: 6, opacity: 1 }).addTo(mapa);
    L.polyline(puntosLinea, { color: "#00C2A8", weight: 2.5, opacity: 0.85, dashArray: "1 10" }).addTo(mapa);

    estaciones.forEach((est, idx) => {
      L.marker([est.lat, est.lng], { icon: iconoEstacion(idx + 1) })
        .addTo(mapa)
        .bindPopup(`<div class="popup-title">${idx + 1}. ${est.nombre}</div>`);
    });

    cargarTablaTiempos();
  } catch (err) {
    console.error(err);
  }
}

// ---------------------------------------------------------------- tabla de tiempos
async function cargarTablaTiempos() {
  const cont = document.getElementById("tiemposBody");
  const meta = document.getElementById("tiemposMeta");
  try {
    const resp = await fetch(`${BACKEND_URL}/rutas/troncal/tiempos`);
    const data = await resp.json();

    meta.innerHTML =
      `vel. asumida <strong>${data.velocidad_asumida_kmh} km/h</strong> · ` +
      `${data.hora_pico_aplicada ? "hora pico" : "hora normal"} · ` +
      `total <strong>${data.tiempo_total_min} min</strong>`;

    cont.innerHTML = data.tramos.map((t) => `
      <div class="tramo-row">
        <div class="tramo-row__route">${t.origen}<span class="tramo-row__arrow">→</span>${t.destino}</div>
        <div class="tramo-row__stats">
          <span>${t.distancia_km} km</span>
          <span><b>${t.tiempo_estimado_min} min</b></span>
          <span>acum. ${t.tiempo_acumulado_min} min</span>
        </div>
      </div>
    `).join("");
  } catch (err) {
    cont.innerHTML = `<p class="panel__hint">No se pudo cargar la tabla de tiempos.</p>`;
    console.error(err);
  }
}

// ---------------------------------------------------------------- buses en vivo
async function actualizarBuses() {
  try {
    const resp = await fetch(`${BACKEND_URL}/buses/live`);
    const buses = await resp.json();

    marcarEstado("live", `en vivo · ${buses.length} bus${buses.length === 1 ? "" : "es"}`);
    renderListaFlota(buses);

    buses.forEach((bus) => {
      const posicion = [bus.lat, bus.lng];
      const color = colorPorOcupacion(bus.ocupacion);

      // Rumbo hacia la siguiente estación de su ruta, para rotar el ícono.
      const siguiente = estacionesCache[bus.siguiente_parada_index];
      const bearing = siguiente
        ? calcularRumbo(posicion, [siguiente.lat, siguiente.lng])
        : 0;

      if (marcadores[bus.bus_id]) {
        marcadores[bus.bus_id].setLatLng(posicion);
        marcadores[bus.bus_id].setIcon(iconoBus(color, bearing));
      } else {
        const marcador = L.marker(posicion, { icon: iconoBus(color, bearing) }).addTo(mapa);
        marcador.bindPopup(construirPopup(bus));
        marcador.on("popupopen", () => marcador.setPopupContent(construirPopup(bus)));
        marcadores[bus.bus_id] = marcador;
      }
    });
  } catch (err) {
    marcarEstado("error", "sin conexión al backend");
    console.error(err);
  }
}

function construirPopup(bus) {
  const div = document.createElement("div");
  div.innerHTML = `
    <div class="popup-title">${bus.bus_id}</div>
    <div class="popup-speed">${bus.velocidad_kmh} km/h · ${etiquetaOcupacion(bus.ocupacion)}</div>
    <button class="popup-btn">Ver ETA</button>
  `;
  div.querySelector(".popup-btn").addEventListener("click", () => {
    consultarEta(bus.bus_id, bus.siguiente_parada_index);
  });
  return div;
}

// ---------------------------------------------------------------- lista de flota
function renderListaFlota(buses) {
  const cont = document.getElementById("listaBuses");
  cont.innerHTML = buses.map((bus) => `
    <div class="bus-item" data-bus="${bus.bus_id}" data-stop="${bus.siguiente_parada_index}">
      <span class="bus-item__dot" style="background:${colorPorOcupacion(bus.ocupacion)}"></span>
      <span class="bus-item__id">${bus.bus_id}</span>
      <span class="bus-item__speed">${bus.velocidad_kmh} km/h</span>
    </div>
  `).join("");

  cont.querySelectorAll(".bus-item").forEach((item) => {
    item.addEventListener("click", () => {
      const busId = item.dataset.bus;
      const stop = Number(item.dataset.stop);
      consultarEta(busId, stop);
      const marcador = marcadores[busId];
      if (marcador) mapa.panTo(marcador.getLatLng());
    });
  });
}

// ---------------------------------------------------------------- ficha ETA
async function consultarEta(busId, stopIndex) {
  try {
    const resp = await fetch(`${BACKEND_URL}/buses/${busId}/eta/${stopIndex}`);
    const data = await resp.json();

    document.getElementById("etaBus").textContent = data.bus_id;
    document.getElementById("etaDest").textContent = `llega a ${data.parada_destino}`;
    document.getElementById("etaMin").textContent = data.eta_minutos;
    document.getElementById("etaKm").textContent = data.distancia_km;
    document.getElementById("etaHora").textContent = data.hora_consulta;
    document.getElementById("etaCard").hidden = false;
  } catch (err) {
    console.error(err);
  }
}

function cerrarEta() {
  document.getElementById("etaCard").hidden = true;
}

// ---------------------------------------------------------------- arranque
iniciarReloj();
iniciarMapa();
