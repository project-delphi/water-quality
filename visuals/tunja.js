import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ---------- constants -------------------------------------------------------
const IRCA = "IRCA (utility-supplied, INS open data)";
const BANDS = [
  { max: 5,   name: "No risk", color: "#2ec4b6" },
  { max: 14,  name: "Low",     color: "#a7d86e" },
  { max: 35,  name: "Medium",  color: "#f4c542" },
  { max: 80,  name: "High",    color: "#ef7b45" },
  { max: 100, name: "Unfit",   color: "#d62839" },
];
const NODATA = { name: "No reported IRCA", color: "#3a4658" };
const bandOf = (v) => (v == null ? null : BANDS.find((b) => v <= b.max) || BANDS[4]);
const colorOf = (v) => new THREE.Color((bandOf(v) || NODATA).color);
const $ = (s) => document.querySelector(s);
const fmt = (v, d = 1) => (v == null ? "n/a" : Number(v).toLocaleString("en", { maximumFractionDigits: d }));

const state = { yi: 13, zone: "urban", playing: false, selected: null, hover: null };

const data = await (await fetch("visuals/boyaca.json")).json();
const years = data.years;
const munis = data.munis;
const tunja = munis.find((m) => m.id === data.tunja);

// ---------- projection ------------------------------------------------------
const LON0 = -73.3, LAT0 = 5.9, K = 10, COS = Math.cos((LAT0 * Math.PI) / 180);
const proj = ([lon, lat]) => [(lon - LON0) * COS * K, (lat - LAT0) * K];
const heightOf = (m) => 0.12 + Math.max(0, m.alt ?? 0) / 3000 * 1.3;

// ---------- renderer / scene ------------------------------------------------
const hero = $("#hero");
const canvas = $("#stage");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
const scene = new THREE.Scene();
scene.fog = new THREE.Fog(0x06121c, 38, 80);
const camera = new THREE.PerspectiveCamera(42, 1, 0.1, 200);
const controls = new OrbitControls(camera, canvas);
controls.enableDamping = true;
controls.maxPolarAngle = Math.PI * 0.49;
controls.minDistance = 6;
controls.maxDistance = 48;
controls.autoRotate = true;
controls.autoRotateSpeed = 0.35;
controls.addEventListener("start", () => (controls.autoRotate = false));

scene.add(new THREE.HemisphereLight(0xbfe6ff, 0x08202e, 1.0));
const sun = new THREE.DirectionalLight(0xffffff, 1.6);
sun.position.set(-12, 22, 14);
scene.add(sun);

const grid = new THREE.GridHelper(80, 80, 0x16384d, 0x0d2535);
grid.position.y = -0.02;
grid.material.transparent = true;
grid.material.opacity = 0.5;
scene.add(grid);

// ---------- municipality meshes --------------------------------------------
const root = new THREE.Group();
scene.add(root);
const meshes = [];
let bbox = new THREE.Box3();

function polyArea(ring) {
  let a = 0;
  for (let i = 0, n = ring.length; i < n; i++) {
    const [x1, y1] = ring[i], [x2, y2] = ring[(i + 1) % n];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
}
function inRing(x, y, ring) {
  let c = false;
  for (let i = 0, j = ring.length - 1; i < ring.length; j = i++) {
    const [xi, yi] = ring[i], [xj, yj] = ring[j];
    if (yi > y !== yj > y && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi) c = !c;
  }
  return c;
}

for (const m of munis) {
  const h = heightOf(m);
  const geoms = [];
  let area = 0, big = null;
  const rings = [];
  for (const poly of m.poly) {
    const pr = poly.map((r) => r.map(proj));
    rings.push(pr);
    const a = polyArea(pr[0]);
    area += a;
    if (!big || a > big.a) big = { a, ring: pr[0] };
    const shape = new THREE.Shape(pr[0].map(([x, y]) => new THREE.Vector2(x, y)));
    for (const hole of pr.slice(1)) shape.holes.push(new THREE.Path(hole.map(([x, y]) => new THREE.Vector2(x, y))));
    geoms.push(new THREE.ExtrudeGeometry(shape, { depth: h, bevelEnabled: false, curveSegments: 1 }));
  }
  const merged = geoms.length === 1 ? geoms[0] : mergeGeoms(geoms);
  merged.rotateX(-Math.PI / 2);
  const mat = new THREE.MeshStandardMaterial({ color: 0x3a4658, roughness: 0.65, metalness: 0.1, emissive: 0x000000 });
  const mesh = new THREE.Mesh(merged, mat);
  mesh.userData = { m, h, area, rings, cur: new THREE.Color(0x3a4658), tgt: new THREE.Color(0x3a4658) };
  root.add(mesh);
  meshes.push(mesh);
  // outline on top face
  for (const pr of rings) {
    const pts = pr[0].map(([x, y]) => new THREE.Vector3(x, h + 0.005, -y));
    root.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(pts), new THREE.LineBasicMaterial({ color: 0x06121c, transparent: true, opacity: 0.8 })));
  }
  // centroid of largest polygon's bbox
  let x0 = 1e9, x1 = -1e9, y0 = 1e9, y1 = -1e9;
  for (const [x, y] of big.ring) { x0 = Math.min(x0, x); x1 = Math.max(x1, x); y0 = Math.min(y0, y); y1 = Math.max(y1, y); }
  mesh.userData.c = new THREE.Vector3((x0 + x1) / 2, h, -(y0 + y1) / 2);
  mesh.userData.bounds = [x0, x1, y0, y1];
  // pool of rain sample points inside the polygon
  const pool = [];
  for (let t = 0; t < 4000 && pool.length < 48; t++) {
    const x = x0 + Math.random() * (x1 - x0), y = y0 + Math.random() * (y1 - y0);
    if (rings.some((pr) => inRing(x, y, pr[0]) && !pr.slice(1).some((hl) => inRing(x, y, hl)))) pool.push([x, -y]);
  }
  mesh.userData.pool = pool.length ? pool : [[mesh.userData.c.x, mesh.userData.c.z]];
  bbox.expandByObject(mesh);
}
function mergeGeoms(gs) {
  const merged = new THREE.BufferGeometry();
  let pos = [], nor = [];
  for (const g of gs) {
    const ng = g.index ? g.toNonIndexed() : g;
    pos.push(...ng.attributes.position.array);
    nor.push(...ng.attributes.normal.array);
  }
  merged.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  merged.setAttribute("normal", new THREE.Float32BufferAttribute(nor, 3));
  return merged;
}
const tunjaMesh = meshes.find((x) => x.userData.m.id === data.tunja);
const bboxCenter = bbox.getCenter(new THREE.Vector3());

// ---------- Tunja beacon ----------------------------------------------------
const beaconMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.35, blending: THREE.AdditiveBlending, depthWrite: false });
const beacon = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 6, 12, 1, true), beaconMat);
beacon.position.copy(tunjaMesh.userData.c).add(new THREE.Vector3(0, 3, 0));
scene.add(beacon);
const ringMat = new THREE.MeshBasicMaterial({ color: 0xffffff, transparent: true, opacity: 0.8, blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide });
const pulse = new THREE.Mesh(new THREE.RingGeometry(0.9, 1, 48), ringMat);
pulse.rotation.x = -Math.PI / 2;
pulse.position.copy(tunjaMesh.userData.c).add(new THREE.Vector3(0, 0.03, 0));
scene.add(pulse);

// ---------- rain ------------------------------------------------------------
const N = 9000;
const rainPos = new Float32Array(N * 3), rainCol = new Float32Array(N * 3);
const rainOwner = new Int16Array(N), rainSpeed = new Float32Array(N);
const rainGeo = new THREE.BufferGeometry();
rainGeo.setAttribute("position", new THREE.BufferAttribute(rainPos, 3));
rainGeo.setAttribute("color", new THREE.BufferAttribute(rainCol, 3));
const dot = document.createElement("canvas");
dot.width = dot.height = 32;
{ const g = dot.getContext("2d"), gr = g.createRadialGradient(16, 16, 0, 16, 16, 16);
  gr.addColorStop(0, "#fff"); gr.addColorStop(0.4, "#fffa"); gr.addColorStop(1, "#fff0");
  g.fillStyle = gr; g.fillRect(0, 0, 32, 32); }
const rain = new THREE.Points(rainGeo, new THREE.PointsMaterial({
  size: 0.13, map: new THREE.CanvasTexture(dot), vertexColors: true, transparent: true,
  blending: THREE.AdditiveBlending, depthWrite: false, sizeAttenuation: true }));
rain.frustumCulled = false;
scene.add(rain);
const TOP = 7;

function assignRain() {
  // owner of each drop is chosen with weight = annual rainfall x polygon area
  const w = meshes.map((x) => (x.userData.m.rain[state.yi] ?? 0) * x.userData.area);
  const cum = []; let s = 0;
  for (const v of w) cum.push((s += v));
  for (let i = 0; i < N; i++) {
    const r = Math.random() * s;
    let lo = 0, hi = cum.length - 1;
    while (lo < hi) { const mid = (lo + hi) >> 1; if (cum[mid] < r) lo = mid + 1; else hi = mid; }
    rainOwner[i] = lo;
    respawn(i, true);
  }
}
function respawn(i, scatter) {
  const u = meshes[rainOwner[i]].userData;
  const p = u.pool[(Math.random() * u.pool.length) | 0];
  rainPos[i * 3] = p[0] + (Math.random() - 0.5) * 0.15;
  rainPos[i * 3 + 2] = p[1] + (Math.random() - 0.5) * 0.15;
  rainPos[i * 3 + 1] = scatter ? u.h + Math.random() * (TOP - u.h) : TOP + Math.random() * 1.5;
  rainSpeed[i] = 1.6 + Math.random() * 1.8;
}

// ---------- state -> visuals -----------------------------------------------
const ircaNow = (m) => m.irca[state.zone][state.yi];
function applyState() {
  for (const x of meshes) x.userData.tgt.copy(colorOf(ircaNow(x.userData.m)));
  $("#yearlabel").textContent = years[state.yi];
  $("#year").value = state.yi;
  document.querySelectorAll("[data-zone]").forEach((b) => b.classList.toggle("on", b.dataset.zone === state.zone));
  assignRain();
  renderPanel();
  drawBands();
}

// ---------- panel -----------------------------------------------------------
function spark(m) {
  const W = 268, H = 56, pad = 3;
  const xs = (i) => pad + (i / (years.length - 1)) * (W - 2 * pad), ys = (v) => H - pad - (v / 100) * (H - 2 * pad);
  const line = (arr, col) => {
    let d = "", pen = false;
    arr.forEach((v, i) => { if (v == null) { pen = false; return; } d += `${pen ? "L" : "M"}${xs(i).toFixed(1)},${ys(v).toFixed(1)}`; pen = true; });
    return `<path d="${d}" fill="none" stroke="${col}" stroke-width="1.8" ${col === "#9db4c6" ? 'stroke-dasharray="3 3"' : ""}/>`;
  };
  const other = state.zone === "urban" ? "rural" : "urban";
  return `<svg width="${W}" height="${H}" role="img" aria-label="IRCA over time">
    ${line(m.irca[other], "#9db4c6")}${line(m.irca[state.zone], "#7fd6ff")}
    <line x1="${xs(state.yi)}" x2="${xs(state.yi)}" y1="0" y2="${H}" stroke="#fff6"/></svg>`;
}
function renderPanel() {
  const m = (state.selected || tunja);
  const v = m.irca[state.zone][state.yi], b = bandOf(v);
  const cover = m.capital ? m.wc_total[state.yi] : m.wc[state.zone][state.yi];
  const coverLbl = m.capital ? "Aqueduct coverage (whole municipality)" : `Aqueduct coverage (${state.zone})`;
  const ipm = state.zone === "urban" ? m.ipm_urban : m.ipm_rural;
  $("#panel").innerHTML = `
    <h3>${m.name}${m.capital ? " ★" : ""}</h3>
    <div class="sub">${m.capital ? "Department capital · " : ""}${state.zone} zone · ${years[state.yi]}</div>
    <div><span class="big" style="color:${(b || NODATA).color}">${v == null ? "n/a" : fmt(v)}</span>
      <span class="band" style="background:${(b || NODATA).color}">${(b || NODATA).name}</span></div>
    <div class="sub" style="margin:4px 0 2px">${IRCA}</div>
    ${spark(m)}
    <div class="sub">solid: ${state.zone} · dashed: ${state.zone === "urban" ? "rural" : "urban"} · 0–100</div>
    <dl>
      <dt>Head-town altitude (SRTM)</dt><dd>${fmt(m.alt, 0)} m</dd>
      <dt>Rainfall (CHIRPS)</dt><dd>${fmt(m.rain[state.yi], 0)} mm</dd>
      <dt>Zone population</dt><dd>${fmt(m.pop[state.zone][state.yi], 0)}</dd>
      <dt>${coverLbl}</dt><dd>${fmt(cover)}%</dd>
      <dt>Poverty, IPM (census 2018)</dt><dd>${fmt(ipm)}%</dd>
      <dt>Infant mortality /1,000</dt><dd>${fmt(m.imr[state.yi])}</dd>
    </dl>
    <div class="fine">Descriptive only: these values do not show that water quality causes any of the others. Infant mortality changes method in 2017 and is volatile for small municipalities.</div>`;
}

// ---------- legend / bands bar ---------------------------------------------
$("#legend").innerHTML = `<div class="t">${IRCA}</div>` +
  [...BANDS.map((b, i) => `<span><i style="background:${b.color}"></i>${b.name} ${i ? BANDS[i - 1].max + "–" : "0–"}${b.max}</span>`),
   `<span><i style="background:${NODATA.color}"></i>${NODATA.name}</span>`].join("");
$("#bandbar").innerHTML = BANDS.map((b, i) =>
  `<div style="background:${b.color};flex:${[5, 9, 21, 45, 20][i]}"><b>${b.name}</b>${i ? BANDS[i - 1].max + 0.1 + "–" : "0–"}${b.max}</div>`).join("");

// ---------- interaction -----------------------------------------------------
const ray = new THREE.Raycaster(), mouse = new THREE.Vector2();
let moved = false, down = null;
function pick(ev) {
  const r = canvas.getBoundingClientRect();
  mouse.set(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  ray.setFromCamera(mouse, camera);
  const hit = ray.intersectObjects(meshes, false)[0];
  return hit ? hit.object : null;
}
canvas.addEventListener("pointermove", (ev) => {
  const o = pick(ev);
  state.hover = o;
  const tip = $("#tooltip");
  if (o) {
    const r = hero.getBoundingClientRect();
    const v = ircaNow(o.userData.m);
    tip.style.left = ev.clientX - r.left + "px"; tip.style.top = ev.clientY - r.top + "px";
    tip.textContent = `${o.userData.m.name} · IRCA ${v == null ? "n/a" : fmt(v)}`;
    tip.style.opacity = 1;
  } else tip.style.opacity = 0;
});
canvas.addEventListener("pointerdown", (e) => (down = [e.clientX, e.clientY]));
canvas.addEventListener("pointerup", (e) => {
  if (down && Math.hypot(e.clientX - down[0], e.clientY - down[1]) < 5) {
    const o = pick(e);
    state.selected = o ? o.userData.m : null;
    renderPanel();
  }
  down = null;
});
$("#year").addEventListener("input", (e) => { state.yi = +e.target.value; applyState(); });
document.querySelectorAll("[data-zone]").forEach((b) => b.addEventListener("click", () => { state.zone = b.dataset.zone; applyState(); }));
let playTimer = null;
$("#play").addEventListener("click", () => {
  state.playing = !state.playing;
  $("#play").textContent = state.playing ? "❚❚" : "▶";
  clearInterval(playTimer);
  if (state.playing) {
    if (state.yi === years.length - 1) { state.yi = 0; applyState(); }
    playTimer = setInterval(() => {
      if (state.yi >= years.length - 1) { state.playing = false; $("#play").textContent = "▶"; clearInterval(playTimer); return; }
      state.yi++; applyState();
    }, 900);
  }
});

// ---------- loop ------------------------------------------------------------
function resize() {
  const w = hero.clientWidth, h = hero.clientHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h; camera.updateProjectionMatrix();
}
addEventListener("resize", resize);
resize();

const lookAt = new THREE.Vector3(tunjaMesh.userData.c.x * 0.4, 0.4, tunjaMesh.userData.c.z * 0.4);
controls.target.copy(lookAt);
const camStart = new THREE.Vector3(0, 40, 40), camEnd = new THREE.Vector3(-3, 15, 21);
camera.position.copy(camStart);
const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
if (reduced) { camera.position.copy(camEnd); controls.autoRotate = false; }
const clock = new THREE.Clock();
let t0 = 0, visible = true;
new IntersectionObserver(([e]) => (visible = e.isIntersecting)).observe(hero);
const label = $("#tunjalabel");
const tmp = new THREE.Vector3();

function frame() {
  requestAnimationFrame(frame);
  if (!visible) return;
  const dt = Math.min(clock.getDelta(), 0.05), t = (t0 += dt);
  // intro fly-in
  if (!reduced && t < 3.2 && !down) camera.position.lerpVectors(camStart, camEnd, 1 - Math.pow(1 - Math.min(t / 3.2, 1), 3));
  controls.update();
  // colour easing
  for (const x of meshes) {
    const u = x.userData;
    u.cur.lerp(u.tgt, 1 - Math.exp(-dt * 6));
    x.material.color.copy(u.cur);
    const hov = state.hover === x, sel = state.selected === u.m || (!state.selected && u.m === tunja);
    x.material.emissive.copy(u.cur).multiplyScalar(hov ? 0.55 : sel ? 0.3 : 0.06);
  }
  // rain
  for (let i = 0; i < N; i++) {
    const u = meshes[rainOwner[i]].userData;
    rainPos[i * 3 + 1] -= rainSpeed[i] * dt * (reduced ? 0 : 1);
    if (rainPos[i * 3 + 1] < u.h) respawn(i, false);
    const c = u.cur;
    rainCol[i * 3] = 0.45 + c.r * 0.55; rainCol[i * 3 + 1] = 0.55 + c.g * 0.45; rainCol[i * 3 + 2] = 0.7 + c.b * 0.3;
  }
  rainGeo.attributes.position.needsUpdate = true;
  rainGeo.attributes.color.needsUpdate = true;
  // beacon follows Tunja's current band
  const tc = tunjaMesh.userData.cur;
  beaconMat.color.copy(tc).lerp(new THREE.Color(0xffffff), 0.35);
  ringMat.color.copy(beaconMat.color);
  beaconMat.opacity = 0.28 + 0.12 * Math.sin(t * 2);
  const ph = (t % 2.4) / 2.4;
  pulse.scale.setScalar(0.3 + ph * 2.2);
  ringMat.opacity = 0.9 * (1 - ph);
  // label
  tmp.copy(tunjaMesh.userData.c).add(new THREE.Vector3(0, 1.2, 0)).project(camera);
  label.style.left = ((tmp.x + 1) / 2) * hero.clientWidth + "px";
  label.style.top = ((1 - tmp.y) / 2) * hero.clientHeight + "px";
  label.style.opacity = tmp.z < 1 ? 1 : 0;
  renderer.render(scene, camera);
}

// ---------- story charts (SVG) ---------------------------------------------
const W = 780, H = 300, M = { l: 44, r: 16, t: 14, b: 28 };
const X = (i) => M.l + (i / (years.length - 1)) * (W - M.l - M.r);
const Y = (v, max = 100) => M.t + (1 - v / max) * (H - M.t - M.b);
const axes = (max, unit = "") => {
  let s = "";
  for (let v = 0; v <= max; v += max / 5) s += `<line x1="${M.l}" x2="${W - M.r}" y1="${Y(v, max)}" y2="${Y(v, max)}" stroke="#0001"/><text x="${M.l - 6}" y="${Y(v, max) + 4}" text-anchor="end" font-size="11" fill="#5b6b79">${v}${unit}</text>`;
  years.forEach((y, i) => { if (i % 2 === 0 || i === years.length - 1) s += `<text x="${X(i)}" y="${H - 8}" text-anchor="middle" font-size="11" fill="#5b6b79">${y}</text>`; });
  return s;
};
const path = (arr, max, col, dash = "") => {
  let d = "", pen = false;
  arr.forEach((v, i) => { if (v == null) { pen = false; return; } d += `${pen ? "L" : "M"}${X(i)},${Y(v, max)}`; pen = true; });
  const dots = arr.map((v, i) => (v == null ? "" : `<circle cx="${X(i)}" cy="${Y(v, max)}" r="3" fill="${col}"/>`)).join("");
  return `<path d="${d}" fill="none" stroke="${col}" stroke-width="2.4" ${dash ? `stroke-dasharray="${dash}"` : ""}/>${dots}`;
};

function drawTunja() {
  const u = tunja.irca.urban, r = tunja.irca.rural;
  let bands = "", lo = 0;
  BANDS.slice(0, 4).forEach((b) => { bands += `<rect x="${M.l}" width="${W - M.l - M.r}" y="${Y(b.max)}" height="${Y(lo) - Y(b.max)}" fill="${b.color}" opacity=".16"/>`; lo = b.max; });
  const last = years.length - 1;
  $("#chartTunja").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Tunja urban and rural IRCA, 2010 to 2023">
    ${bands}${axes(100)}${path(r, 100, "#c2571a", "")}${path(u, 100, "#0b6e99", "")}
    <text x="${X(last) - 4}" y="${Y(r[last]) - 10}" text-anchor="end" font-size="12" font-weight="600" fill="#c2571a">Rural ${fmt(r[last])}</text>
    <text x="${X(last) - 4}" y="${Y(u[last]) - 10}" text-anchor="end" font-size="12" font-weight="600" fill="#0b6e99">Urban ${fmt(u[last])}</text></svg>`;
  const ratio = r[last] && u[last] ? r[last] / u[last] : null;
  $("#tunjaLead").innerHTML = `Tunja is Boyacá's capital, a city of about ${fmt(tunja.pop.urban[last] + tunja.pop.rural[last], 0)} people at roughly ${fmt(tunja.alt, 0)} m.
    Its urban IRCA (utility-supplied, INS open data) went from <b>${fmt(u[0])}</b> in ${years[0]} to <b>${fmt(u[last])}</b> in ${years[last]}.
    Its rural zone went from <b>${fmt(r[0])}</b> to <b>${fmt(r[last])}</b>${ratio ? `, still about ${fmt(ratio, 0)}× the urban figure in ${years[last]}` : ""}.
    Same municipality, same year, a very different score depending on who is drinking.`;
  $("#tunjaNote").innerHTML = `<b>Read with care.</b> Rural IRCA is missing far more often than urban IRCA, and which systems were sampled can change from year to year, so the rural line may partly reflect sampling. The gap is descriptive: it does not tell us why, and it does not show an effect of water quality on anything.`;
}

function drawBands() {
  const z = state.zone;
  const n = munis.length, bw = (W - M.l - M.r) / years.length * 0.72;
  let s = axes(100, "%");
  years.forEach((yr, i) => {
    const cnt = [0, 0, 0, 0, 0, 0];
    munis.forEach((m) => { const v = m.irca[z][i]; cnt[v == null ? 5 : BANDS.indexOf(bandOf(v))]++; });
    let acc = 0;
    [5, 0, 1, 2, 3, 4].forEach((k) => {
      const hgt = (cnt[k] / n) * 100, col = k === 5 ? NODATA.color : BANDS[k].color;
      s += `<rect x="${X(i) - bw / 2}" y="${Y(acc + hgt)}" width="${bw}" height="${Y(acc) - Y(acc + hgt)}" fill="${col}"><title>${yr} · ${k === 5 ? NODATA.name : BANDS[k].name}: ${cnt[k]} of ${n}</title></rect>`;
      acc += hgt;
    });
  });
  $("#chartBands").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Boyacá municipalities by IRCA band">${s}</svg>`;
  const li = years.length - 1;
  const c = (zz, i) => { const k = [0, 0, 0]; munis.forEach((m) => { const v = m.irca[zz][i]; k[v == null ? 2 : v <= 5 ? 0 : 1]++; }); return k; };
  const [uN, uH, uM] = c("urban", li), [rN, rH, rM] = c("rural", li);
  const rank = (zz) => { const t = tunja.irca[zz][li]; const all = munis.map((m) => m.irca[zz][li]).filter((v) => v != null); return t == null ? null : { below: all.filter((v) => v < t).length, n: all.length }; };
  const ru = rank("urban"), rr = rank("rural");
  const pctLine = `Among municipalities with a reported score, ${ru.below} of ${ru.n} had a lower urban IRCA than Tunja's, and ${rr.below} of ${rr.n} had a lower rural IRCA.`;
  $("#bandLead").innerHTML = `In ${years[li]}, ${uN} of Boyacá's ${n} municipalities reported an urban IRCA in the no-risk band (≤5), and ${uM} reported none. For the rural zone it was ${rN} in the no-risk band and <b>${rM} with no reported IRCA</b>. ${pctLine} Switch zone to see how much thinner the rural record is.`;
  $("#zoneseg2").querySelectorAll("[data-zone]").forEach((b) => b.classList.toggle("on", b.dataset.zone === z));
}

function drawCover() {
  const w = tunja.wc_total, s = tunja.sc_total;
  $("#chartCover").innerHTML = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Tunja aqueduct and sewerage coverage">
    ${axes(100, "%")}${path(s, 100, "#7a8794", "5 4")}${path(w, 100, "#0b6e99")}
    <text x="${X(0) + 6}" y="${Y(w[0]) - 12}" font-size="12" font-weight="600" fill="#0b6e99">Aqueduct</text>
    <text x="${X(0) + 6}" y="${Y(s[0]) + 18}" font-size="12" font-weight="600" fill="#5b6b79">Sewerage</text></svg>`;
  const i21 = years.indexOf(2021);
  $("#coverNote").innerHTML = `<b>Flag.</b> Tunja's reported coverage is erratic: ${fmt(w[years.indexOf(2020)])}% (aqueduct) in 2020, <b>${fmt(w[i21])}%</b> in ${years[i21]}, ${fmt(w[years.indexOf(2022)])}% in 2022. A real city does not lose and regain its network in two years, so this looks like a reporting artefact in the REC series. We show it as published and do not smooth or fill it. <b>TODO:</b> check the Superservicios REC submissions for Tunja 2021 before drawing any conclusion from coverage.`;
}

document.querySelectorAll("#zoneseg2 [data-zone]").forEach((b) => b.addEventListener("click", () => { state.zone = b.dataset.zone; applyState(); }));

drawTunja(); drawCover();
meshes.forEach((x) => x.userData.cur.copy(x.userData.tgt)); // first paint without easing from slate
applyState();
meshes.forEach((x) => x.userData.cur.set(0x3a4658)); // ease in from slate for the reveal
$("#loading").classList.add("gone");
frame();
