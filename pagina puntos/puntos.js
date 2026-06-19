/* ============================================================
   Metrolínea Reportes — app.js (versión standalone, 3 archivos)
   Router por hash + estado persistido en localStorage
   ============================================================ */

// ---------- Tema claro/oscuro ----------

const THEME_KEY = "metrolinea-theme";

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  document.querySelectorAll("[data-theme-toggle]").forEach(btn => {
    btn.textContent = theme === "dark" ? "☀️" : "🌙";
  });
}

function getPreferredTheme() {
  return localStorage.getItem(THEME_KEY) ||
    (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
}

function toggleTheme() {
  const current = document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
  const next = current === "dark" ? "light" : "dark";
  localStorage.setItem(THEME_KEY, next);
  applyTheme(next);
}

document.addEventListener("click", e => {
  if (e.target.closest("[data-theme-toggle]")) toggleTheme();
});

applyTheme(getPreferredTheme());

// ---------- "Base de datos" en localStorage ----------

const DB_KEY = "metrolinea_db";
const SESSION_KEY = "metrolinea_session";

const PUNTOS_POR_REPORTE = { "daño": 10, "incidente": 20, "emergencia": 50 };

const CANJES = [
  { id: 1, nombre: "Descuento 10% en pasaje", puntos: 100 },
  { id: 2, nombre: "Descuento 50% en pasaje", puntos: 200 },
  { id: 3, nombre: "Pasaje gratis",            puntos: 300 },
  { id: 4, nombre: "Acceso VIP sala de espera", puntos: 500 },
];

function cargarDB() {
  const raw = localStorage.getItem(DB_KEY);
  if (raw) return JSON.parse(raw);
  const fresh = {
    usuarios: {
      "1097105023": { cedula: "1097105023", puntos: 0, canjes: [], fecha_registro: new Date().toISOString() },
      "1116775734": { cedula: "1116775734", puntos: 0, canjes: [], fecha_registro: new Date().toISOString() }
    },
    reportes: []
  };
  guardarDB(fresh);
  return fresh;
}

function guardarDB(db) { localStorage.setItem(DB_KEY, JSON.stringify(db)); }

function getSesion() { return localStorage.getItem(SESSION_KEY); }
function setSesion(cedula) { localStorage.setItem(SESSION_KEY, cedula); }
function limpiarSesion() { localStorage.removeItem(SESSION_KEY); }

// ---------- Router ----------

const viewRoot = document.getElementById("view-root");
const topbarAuth = document.getElementById("topbar");
const topbarGuest = document.getElementById("topbar-guest");

const RUTAS_PUBLICAS = ["/", "/geolocalizacion"];

function navegar(ruta) { window.location.hash = "#" + ruta; }

function rutaActual() {
  const h = window.location.hash.replace(/^#/, "");
  return h || "/";
}

function render() {
  const ruta = rutaActual();
  const cedula = getSesion();

  if (!RUTAS_PUBLICAS.includes(ruta) && !cedula) {
    navegar("/");
    return;
  }

  topbarAuth.hidden = !cedula;
  topbarGuest.hidden = !!cedula;

  document.querySelectorAll(".topbar nav a[data-route]").forEach(a => {
    a.classList.toggle("active", a.dataset.route === ruta);
  });

  switch (ruta) {
    case "/": return cedula ? navegar("/reportar") : vistaLogin();
    case "/reportar": return vistaReportar();
    case "/mis_puntos": return vistaMisPuntos();
    case "/ranking": return vistaRanking();
    case "/geolocalizacion": return vistaGeolocalizacion();
    case "/admin": return vistaAdmin();
    default: return navegar("/");
  }
}

window.addEventListener("hashchange", render);
window.addEventListener("DOMContentLoaded", () => {
  applyTheme(getPreferredTheme());
  render();
});

document.getElementById("logoutBtn").addEventListener("click", () => limpiarSesion());

// ---------- Vista: Login ----------

function vistaLogin() {
  viewRoot.innerHTML = `
    <div class="login-wrap">
      <div class="login-card">
        <div class="logo">🚇</div>
        <h1>Metrolínea Reportes</h1>
        <p>Ingresa tu número de cédula para continuar</p>
        <div id="loginError"></div>
        <form id="loginForm">
          <input type="text" name="cedula" placeholder="Ej: 1098765432" maxlength="12" pattern="[0-9]+" required autofocus>
          <button type="submit" class="btn btn-primary">Ingresar →</button>
        </form>
      </div>
    </div>
  `;

  document.getElementById("loginForm").addEventListener("submit", e => {
    e.preventDefault();
    const cedula = e.target.cedula.value.trim();
    if (!/^\d+$/.test(cedula)) {
      document.getElementById("loginError").innerHTML = `<div class="error-msg">Ingresa solo números.</div>`;
      return;
    }
    const db = cargarDB();
    if (!db.usuarios[cedula]) {
      db.usuarios[cedula] = { cedula, puntos: 0, canjes: [], fecha_registro: new Date().toISOString() };
      guardarDB(db);
    }
    setSesion(cedula);
    navegar("/reportar");
  });
}

// ---------- Vista: Reportar ----------

function vistaReportar() {
  viewRoot.innerHTML = `
    <div class="container container--narrow">
      <h2 style="margin-bottom:4px;">Nuevo reporte</h2>
      <p style="color:var(--text-muted);font-size:13.5px;margin-bottom:22px;">
        Cuéntanos qué viste. Cada reporte válido suma puntos canjeables.
      </p>
      <form id="reporteForm" class="card" style="padding:22px;">
        <label for="tipo">Tipo de reporte</label>
        <select name="tipo" id="tipo" required>
          <option value="" disabled selected>Selecciona una opción</option>
          <option value="daño">Daño en bus o estación (+10 pts)</option>
          <option value="incidente">Incidente / objeto perdido (+20 pts)</option>
          <option value="emergencia">Emergencia (+50 pts)</option>
        </select>
        <label for="ubicacion">Ubicación</label>
        <input type="text" name="ubicacion" id="ubicacion" placeholder="Ej: Estación Provenza" required>
        <label for="descripcion">Descripción</label>
        <textarea name="descripcion" id="descripcion" placeholder="Describe lo que observaste..." required></textarea>
        <label for="foto">Foto (opcional)</label>
        <input type="file" name="foto" id="foto" accept="image/*">
        <button type="submit" class="btn btn-primary" style="margin-top:22px;">Enviar reporte</button>
      </form>
    </div>
  `;

  document.getElementById("reporteForm").addEventListener("submit", e => {
    e.preventDefault();
    const f = e.target;
    const tipo = f.tipo.value, ubicacion = f.ubicacion.value, descripcion = f.descripcion.value;
    const fotoFile = f.foto.files[0];

    const guardar = (fotoData) => {
      const db = cargarDB();
      const cedula = getSesion();
      const puntos = PUNTOS_POR_REPORTE[tipo] || 10;
      db.reportes.push({
        id: Math.random().toString(36).slice(2, 10),
        cedula, tipo, descripcion, ubicacion, foto: fotoData || null,
        puntos, fecha: new Date().toLocaleString("es-CO"), estado: "pendiente"
      });
      db.usuarios[cedula].puntos += puntos;
      guardarDB(db);
      navegar("/mis_puntos?nuevo=" + puntos);
    };

    if (fotoFile) {
      const reader = new FileReader();
      reader.onload = () => guardar(reader.result);
      reader.readAsDataURL(fotoFile);
    } else {
      guardar(null);
    }
  });
}

// ---------- Vista: Mis puntos ----------

function vistaMisPuntos() {
  const db = cargarDB();
  const cedula = getSesion();
  const usuario = db.usuarios[cedula];
  const misReportes = db.reportes.filter(r => r.cedula === cedula).reverse();

  const params = new URLSearchParams(rutaActual().split("?")[1] || "");
  const nuevo = params.get("nuevo");

  viewRoot.innerHTML = `
    <div class="container">
      ${nuevo ? `<div class="alerta">🎉 ¡Reporte enviado! Ganaste +${nuevo} puntos</div>` : ""}
      <div id="canjeMsg"></div>

      <div class="puntos-card">
        <div class="puntos-num">${usuario.puntos}</div>
        <div class="puntos-label">puntos acumulados</div>
      </div>

      <h3 class="section-title">🎁 Canjear puntos</h3>
      <div class="canje-grid">
        ${CANJES.map(c => `
          <div class="canje">
            <div class="canje-info">
              <div class="nombre">${c.nombre}</div>
              <div class="pts">${c.puntos} puntos requeridos</div>
            </div>
            <button class="btn-canje ${usuario.puntos < c.puntos ? "disabled" : ""}" data-canje="${c.id}">Canjear</button>
          </div>
        `).join("")}
      </div>

      <h3 class="section-title">📋 Mis reportes</h3>
      ${misReportes.length ? misReportes.map(r => `
        <div class="reporte">
          <div>
            <div class="tipo">${r.tipo}</div>
            <div class="fecha">${r.fecha} — ${r.ubicacion}</div>
          </div>
          <span class="pts-badge">+${r.puntos}pts</span>
        </div>
      `).join("") : `<p style="color:var(--text-muted);text-align:center;padding:20px 0;">Aún no has enviado reportes.</p>`}

      <button class="btn btn-primary" id="nuevoReporteBtn" style="margin-top:8px;">+ Nuevo reporte</button>
    </div>
  `;

  document.getElementById("nuevoReporteBtn").addEventListener("click", () => navegar("/reportar"));

  document.querySelectorAll("[data-canje]").forEach(btn => {
    btn.addEventListener("click", () => {
      const canje = CANJES.find(c => c.id === Number(btn.dataset.canje));
      const db2 = cargarDB();
      const u = db2.usuarios[cedula];
      if (u.puntos < canje.puntos) {
        document.getElementById("canjeMsg").innerHTML = `<div class="alerta alerta-error">❌ No tienes suficientes puntos para este canje.</div>`;
        return;
      }
      u.puntos -= canje.puntos;
      u.canjes.push({ canje: canje.nombre, fecha: new Date().toLocaleString("es-CO") });
      guardarDB(db2);
      navegar("/mis_puntos");
      render();
    });
  });
}

// ---------- Vista: Ranking ----------

function vistaRanking() {
  const db = cargarDB();
  const cedula = getSesion();
  const top = Object.values(db.usuarios).sort((a, b) => b.puntos - a.puntos).slice(0, 10);

  viewRoot.innerHTML = `
    <div class="container">
      <h2 style="margin-bottom:4px;">🏆 Ranking de colaboradores</h2>
      <p style="color:var(--text-muted);font-size:13.5px;margin-bottom:22px;">
        Los usuarios que más reportan ayudan a mejorar el sistema para todos.
      </p>
      <div class="table-wrap">
        <table>
          <thead><tr><th>#</th><th>Cédula</th><th>Puntos</th></tr></thead>
          <tbody>
            ${top.length ? top.map((u, i) => `
              <tr class="${u.cedula === cedula ? "me" : ""}">
                <td data-label="#"><span class="rank-cell ${i === 0 ? "top1" : ""}">${i + 1}</span></td>
                <td data-label="Cédula">${u.cedula.slice(0,3)}•••${u.cedula.slice(-3)} ${u.cedula === cedula ? "<strong>(tú)</strong>" : ""}</td>
                <td data-label="Puntos"><strong>${u.puntos}</strong></td>
              </tr>
            `).join("") : `<tr><td colspan="3" style="text-align:center;color:var(--text-muted);">Aún no hay datos suficientes.</td></tr>`}
          </tbody>
        </table>
      </div>
      <button class="btn btn-secondary" id="volverBtn" style="margin-top:20px;">← Volver a mis puntos</button>
    </div>
  `;

  document.getElementById("volverBtn").addEventListener("click", () => navegar("/mis_puntos"));
}

// ---------- Vista: Admin ----------

function vistaAdmin() {
  const db = cargarDB();
  const reportes = [...db.reportes].reverse();

  viewRoot.innerHTML = `
    <div class="container" style="max-width:920px;">
      <h2 style="margin-bottom:20px;">🔐 Panel Admin — Reportes</h2>
      <div class="stats">
        <div class="stat"><div class="num">${db.reportes.length}</div><div class="lbl">Total reportes</div></div>
        <div class="stat"><div class="num">${Object.keys(db.usuarios).length}</div><div class="lbl">Usuarios registrados</div></div>
        <div class="stat"><div class="num">${db.reportes.filter(r => r.tipo === "emergencia").length}</div><div class="lbl">Emergencias</div></div>
      </div>
      <h3 class="section-title">📋 Todos los reportes</h3>
      <div class="table-wrap">
        <table>
          <thead><tr><th>ID</th><th>Cédula</th><th>Tipo</th><th>Ubicación</th><th>Descripción</th><th>Fecha</th><th>Foto</th></tr></thead>
          <tbody>
            ${reportes.length ? reportes.map(r => `
              <tr>
                <td data-label="ID">#${r.id}</td>
                <td data-label="Cédula">${r.cedula}</td>
                <td data-label="Tipo"><span class="badge ${r.tipo}">${r.tipo}</span></td>
                <td data-label="Ubicación">${r.ubicacion}</td>
                <td data-label="Descripción">${r.descripcion.slice(0,60)}${r.descripcion.length > 60 ? "..." : ""}</td>
                <td data-label="Fecha">${r.fecha}</td>
                <td data-label="Foto">${r.foto ? `<img class="thumb" src="${r.foto}">` : "—"}</td>
              </tr>
            `).join("") : `<tr><td colspan="7" style="text-align:center;color:var(--text-muted);">No hay reportes todavía.</td></tr>`}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

// ---------- Vista: Geolocalización ----------

let mapaInstancia = null;

function vistaGeolocalizacion() {
  viewRoot.innerHTML = `
    <div class="container" style="max-width:920px;">
      <h2 style="margin-bottom:4px;">📍 Mapa en vivo</h2>
      <p style="color:var(--text-muted);font-size:13.5px;margin-bottom:18px;">
        Ubicación simulada de buses sobre la red Metrolínea. Permite el acceso a tu ubicación para verte en el mapa.
      </p>
      <div class="map-shell">
        <div id="map"></div>
        <div class="map-legend">
          <span><i class="dot bus"></i> Bus disponible</span>
          <span><i class="dot medio"></i> Ocupación media</span>
          <span><i class="dot lleno"></i> Bus lleno</span>
          <span><i class="dot user"></i> Tu ubicación</span>
        </div>
      </div>
    </div>
  `;

  // Destruir mapa anterior si existía (al navegar de ida y vuelta)
  if (mapaInstancia) { mapaInstancia.remove(); mapaInstancia = null; }

  const CENTER = [7.1193, -73.1227]; // Bucaramanga
  const map = L.map("map").setView(CENTER, 13);
  mapaInstancia = map;

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  const colorIcon = color => L.divIcon({
    className: "",
    html: `<div style="width:16px;height:16px;border-radius:50%;background:${color};border:2px solid white;box-shadow:0 1px 4px rgba(0,0,0,.4)"></div>`,
    iconSize: [16, 16], iconAnchor: [8, 8]
  });

  const colores = { disponible: "#3E5150", medio: "#9C7A2E", lleno: "#9C4A3F" };

  const rutas = [
    { id: "B12", estado: "disponible", puntos: [[7.1193,-73.1227],[7.1230,-73.1180],[7.1265,-73.1130]] },
    { id: "B07", estado: "medio",      puntos: [[7.1100,-73.1290],[7.1140,-73.1250],[7.1180,-73.1210]] },
    { id: "B21", estado: "lleno",      puntos: [[7.1300,-73.1300],[7.1260,-73.1260],[7.1220,-73.1230]] }
  ];

  const marcadores = rutas.map(r => {
    const m = L.marker(r.puntos[0], { icon: colorIcon(colores[r.estado]) })
      .addTo(map).bindPopup(`<strong>Bus ${r.id}</strong><br>Ocupación: ${r.estado}`);
    return { marker: m, puntos: r.puntos, step: 0 };
  });

  const intervalo = setInterval(() => {
    if (!document.getElementById("map")) { clearInterval(intervalo); return; }
    marcadores.forEach(m => {
      m.step = (m.step + 1) % m.puntos.length;
      m.marker.setLatLng(m.puntos[m.step]);
    });
  }, 3000);

  if (navigator.geolocation) {
    navigator.geolocation.getCurrentPosition(pos => {
      const { latitude, longitude } = pos.coords;
      L.marker([latitude, longitude], { icon: colorIcon("#466067") }).addTo(map).bindPopup("Tú estás aquí");
    }, () => {});
  }
}