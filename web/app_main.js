/* pedx app: presentation + thesis outline + MVP (project-candidate feasibility) + data/method + references.
   All numbers come from window.PEDX (built by web/build_app.py from global open data). */
(function () {
  "use strict";
  const P = window.PEDX, S = P.summary, T = S.total, CAT = {}, FAM = S.catalog.families;
  S.catalog.features.forEach(f => { CAT[f.name] = f; });
  const nf = (v, d = 0) => (v === null || v === undefined || !isFinite(v)) ? "—" :
    Number(v).toLocaleString("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: d });
  const dg = v => (v === null || v === undefined) ? 0 : (Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 1 ? 2 : 3);
  const $ = id => document.getElementById(id);
  const css = n => getComputedStyle(document.documentElement).getPropertyValue(n).trim();

  // ------------------------------------------------------------------ routing
  const VIEWS = ["sunum", "mimari", "tez", "mvp", "veri", "kaynakca"];
  let mapReady = false;
  function route() {
    const h = (location.hash || "#sunum").slice(1);
    const v = VIEWS.includes(h) ? h : "sunum";
    VIEWS.forEach(n => { $("v-" + n).hidden = n !== v; });
    document.querySelectorAll("nav.views a").forEach(a => a.setAttribute("aria-current", a.getAttribute("href") === "#" + v ? "page" : "false"));
    if (v === "mvp") { if (!mapReady) initMap(); else map.invalidateSize(); }
  }
  window.addEventListener("hashchange", route);

  // ------------------------------------------------------------------ presentation
  const I = S.provenance.inputs;
  $("pres-kpis").innerHTML = [
    ["Bina (OSM)", nf(T.n_buildings)], ["H3 r10 hücresi", nf(T.n_cells)], ["Nüfus (GHS-POP 2020)", nf(T.population_ghs_2020)],
    ["Konut talebi, GWh/yıl", nf(T.demand_res_kwh / 1e6, 2)], ["Çatı PV, GWh/yıl", nf(T.pv_kwh / 1e6, 2), "sun"],
    ["Yıllık denge (aralık)", `${nf(T.balance, 2)} <span class="note">${nf(T.balance_low, 2)}–${nf(T.balance_high, 2)}</span>`, "sun"],
  ].map(k => `<div class="kpi ${k[2] || ""}"><div class="v">${k[1]}</div><div class="k">${k[0]}</div></div>`).join("");
  const valTable = () => "<table><tr><th>Gösterge</th><th class='num'>G1 açık veri</th><th class='num'>G2 yerel</th><th class='num'>Fark</th></tr>" +
    S.validation.map(v => `<tr><td>${v.item} <span class="note">(${v.unit})</span><div class="note">G1: ${v.g1_source}<br>G2: ${v.g2_source}</div></td><td class="num">${nf(v.global_open_G1)}</td><td class="num">${nf(v.local_G2)}</td><td class="num">${nf(v.rel_diff * 100, 1)}%</td></tr>`).join("") + "</table>";
  $("pres-val").innerHTML = valTable();

  // ------------------------------------------------------------------ data & method view
  $("src").innerHTML = "<table><tr><th>Katman</th><th>Kaynak</th><th>Lisans</th><th>Rol</th></tr>" + P.sources.map(s =>
    `<tr><td>${s[0]}</td><td>${s[1]}</td><td>${s[2]}</td><td><span class="badge ${s[3] === "G1" ? "geo" : "ok"}">${s[3]}</span></td></tr>`).join("") + "</table>";
  $("params").innerHTML = "<table><tr><th>Parametre</th><th class='num'>Değer (alt–üst)</th><th>Kaynak</th></tr>" +
    Object.entries(S.provenance.params).map(([k, p]) => `<tr><td class="mono">${k}</td><td class="num">${p.value} (${p.low}–${p.high})</td><td class="note">${p.source}</td></tr>`).join("") +
    `<tr><td class="mono">res_kwh_per_capita</td><td class="num">${nf(I.residential_kwh_per_capita_2023, 1)}</td><td class="note">UNSD 2023 hane elektriği ÷ BM nüfusu (Türkiye)</td></tr>` +
    `<tr><td class="mono">pv_yield_kwh_per_kwp</td><td class="num">${nf(I.pv_yield_kwh_per_kwp_2023, 1)}</td><td class="note">PVGIS 5.3, 2023, eğim ${I.pvgis_mounting.fixed.slope.value}°, azimut ${I.pvgis_mounting.fixed.azimuth.value}°, kayıp %14</td></tr></table>`;
  $("val").innerHTML = valTable();
  $("assoc").innerHTML = "<table><tr><th>Özellik</th><th>Aile</th><th class='num'>Spearman ρ</th><th class='num'>n</th></tr>" +
    S.associations.map(a => `<tr><td>${(CAT[a.feature] || {}).label_tr || a.feature}</td><td>${FAM[(CAT[a.feature] || {}).family] || ""}</td><td class="num">${nf(a.rho, 2)}</td><td class="num">${a.n}</td></tr>`).join("") + "</table>";
  const rows = S.catalog.features.slice().sort((a, b) => (a.status > b.status) - (a.status < b.status) || a.family.localeCompare(b.family));
  $("catalog").innerHTML = `<p class="note">${rows.filter(r => r.status === "active").length} etkin, ${rows.filter(r => r.status === "planned").length} planlanan özellik.</p><table><tr><th>Özellik</th><th>Aile</th><th>Kaynak · lisans</th><th>Durum</th></tr>` +
    rows.map(r => `<tr><td>${r.label_tr} <span class="note">${r.unit}</span></td><td>${FAM[r.family] || r.family}</td><td class="note">${r.source} · ${r.license}</td><td><span class="badge ${r.status === "active" ? "ok" : "warn"}">${r.status === "active" ? "etkin" : "planlı"}</span></td></tr>`).join("") + "</table>";
  $("gaps").innerHTML = S.provenance.gaps.map(g => `<li>${g}</li>`).join("") +
    `<li>OSM'de binaların yalnızca %${nf(T.share_levels_known * 100)}'inde kat bilgisi var.</li>`;
  $("refs").innerHTML = P.refs.map(r => `<li>${r}</li>`).join("");
  if (S.embedding) $("emb").innerHTML = `<p class="note">${S.embedding.n_features} özellik kullanıldı.</p><table><tr><th>Bileşen</th><th class="num">Açıklanan varyans</th><th>En yüksek yükler</th></tr>` +
    S.embedding.components.map(c => `<tr><td class="mono">${c.component}</td><td class="num">%${nf(c.explained_variance * 100, 1)}</td><td class="note">${c.top_loadings.slice(0, 4).map(t => `${(CAT[t.feature] || {}).label_tr || t.feature} (${t.loading > 0 ? "+" : ""}${nf(t.loading, 2)})`).join(" · ")}</td></tr>`).join("") + "</table>";
  // architecture view
  $("nfeat").textContent = `${Object.keys(P.cells.features[0].properties).filter(k => CAT[k] && CAT[k].status === "active").length} özellik/hücre`;
  const st = { ingested: ["ok", "sistemde"], connector: ["geo", "bağlayıcı hazır"], planned: ["warn", "planlı"] };
  $("lake").innerHTML = `<p class="note">${S.datalake.length} veri seti · ${S.datalake.filter(d => d.status === "ingested").length} sistemde</p><table><tr><th>Veri seti</th><th>Tema</th><th>Tür · çözünürlük</th><th>Lisans</th><th>Kullanım</th><th>Durum</th></tr>` +
    S.datalake.map(d => `<tr><td>${d.provider}</td><td>${d.theme}</td><td class="note">${d.kind} · ${d.resolution}</td><td class="note">${d.license}</td><td class="note">${d.pedx_use}</td><td><span class="badge ${st[d.status][0]}">${st[d.status][1]}</span></td></tr>`).join("") + "</table>";
  (function dnChart() {
    const D = S.demand_status, H = D.monthly_heating_index, C = D.monthly_cooling_index;
    const vals = Array.from({ length: 12 }, (_, i) => [H[i + 1] || 0, C[i + 1] || 0]);
    const W = 640, Ht = 170, pad = 30, max = Math.max(...vals.flat()), bw = (W - pad * 2) / 12;
    const mo = ["Oca", "Şub", "Mar", "Nis", "May", "Haz", "Tem", "Ağu", "Eyl", "Eki", "Kas", "Ara"];
    let s = `<svg viewBox="0 0 ${W} ${Ht}" width="100%" role="img" aria-label="Aylık ısıtma ve soğutma indeksi">`;
    vals.forEach((v, i) => {
      const x = pad + i * bw, hh = (Ht - pad * 1.7) * v[0] / max, hc = (Ht - pad * 1.7) * v[1] / max;
      s += `<rect x="${x + 3}" y="${Ht - pad - hh}" width="${bw / 2 - 4}" height="${hh}" fill="var(--bad)"><title>${mo[i]} ısıtma ${nf(v[0], 0)}</title></rect>`;
      s += `<rect x="${x + bw / 2}" y="${Ht - pad - hc}" width="${bw / 2 - 4}" height="${hc}" fill="var(--geo)"><title>${mo[i]} soğutma ${nf(v[1], 0)}</title></rect>`;
      s += `<text x="${x + bw / 2}" y="${Ht - pad + 14}" text-anchor="middle" fill="var(--muted)" font-size="11">${mo[i]}</text>`;
    });
    $("dnchart").innerHTML = s + "</svg>";
  })();

  // ------------------------------------------------------------------ MVP
  let map, cellLayer, legend;
  const cand = new Set();
  const feats = P.cells.features;
  const byCell = {}; feats.forEach(f => { byCell[f.properties.cell] = f.properties; });
  const present = Object.keys(feats[0].properties).filter(k => CAT[k] && CAT[k].status === "active");
  const RDBU = ["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"];
  const SEQ = ["#fde725", "#b5de2b", "#6ece58", "#35b779", "#1f9e89", "#26828e", "#31688e", "#3e4989", "#482878"];
  const FIX = {
    energy_balance: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3], energy_balance_low: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3],
    energy_balance_high: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3], energy_roof_share_needed: [0.05, 0.1, 0.15, 0.2, 0.26, 0.35, 0.5, 0.75],
    xai_logbal_built: [-1.5, -1, -0.5, -0.1, 0.1, 0.5, 1, 1.5], xai_logbal_population: [-1.5, -1, -0.5, -0.1, 0.1, 0.5, 1, 1.5],
  };
  const scaleOf = k => k === "energy_roof_share_needed" ? RDBU.slice().reverse() : (FIX[k] ? RDBU : SEQ);
  function breaks(k) {
    if (FIX[k]) return FIX[k];
    const v = feats.map(f => f.properties[k]).filter(x => x !== null && x !== undefined).sort((a, b) => a - b);
    return v.length ? [1, 2, 3, 4, 5, 6, 7, 8].map(i => v[Math.floor(i * (v.length - 1) / 9)]) : [0];
  }
  const col = (v, br, sc) => { if (v === null || v === undefined) return "#bdbdbd"; let i = 0; while (i < br.length && v >= br[i]) i++; return sc[i]; };

  const sel = $("metric");
  Object.entries(FAM).forEach(([fam, label]) => {
    const names = present.filter(n => CAT[n].family === fam);
    if (!names.length) return;
    const g = document.createElement("optgroup"); g.label = label;
    names.forEach(n => { const o = document.createElement("option"); o.value = n; o.textContent = CAT[n].label_tr; g.appendChild(o); });
    sel.appendChild(g);
  });
  sel.value = "energy_balance";

  function initMap() {
    mapReady = true;
    map = L.map("map", { preferCanvas: true, zoomSnap: 0.25 });
    const base = L.layerGroup().addTo(map);
    L.geoJSON(P.streets, { style: { color: css("--street"), weight: 1, opacity: 0.9 }, interactive: false }).addTo(base);
    const bld = L.geoJSON(P.buildings, { style: { color: css("--bldg"), weight: 0.4, fillColor: css("--bldg"), fillOpacity: 0.18 }, interactive: false }).addTo(base);
    const bnd = L.geoJSON(P.boundary, { style: { color: css("--ink"), weight: 2, fill: false, dashArray: "6 4" }, interactive: false }).addTo(map);
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap katkıcıları" });
    L.control.layers(null, { "OSM sokakları ve binaları (vektör)": base, "OSM karoları (yerel çalıştırmada)": tiles }, { collapsed: true }).addTo(map);
    map.attributionControl.addAttribution("Veri © OpenStreetMap katkıcıları (ODbL) · JRC GHS-POP (CC BY 4.0) · EU JRC PVGIS");
    map.fitBounds(bnd.getBounds(), { padding: [10, 10] });
    draw(sel.value);
    sel.addEventListener("change", e => draw(e.target.value));
    renderCand();
    initLive();
  }

  // ---------- on-demand assessment anywhere (K-040): needs `make api`; otherwise disabled, never faked
  const API = "http://127.0.0.1:8766";
  let liveLayer = null;
  function initLive() {
    fetch(API + "/health").then(r => r.json()).then(h => {
      $("livestatus").textContent = `API hazır (pedx ${h.version}). Caferağa dışında haritada herhangi bir yere tıklayın; dünya üzerinde gezinmek için uzaklaştırın.`;
      map.on("click", ev => live(ev.latlng.lat, ev.latlng.lng));
    }).catch(() => {
      $("livestatus").innerHTML = "Yerel API çalışmıyor. Açmak için terminalde <code>make api</code>; bu sayfa yalnız önceden hesaplanmış Caferağa'yı gösterir.";
    });
  }
  function live(lat, lon) {
    const k = $("livek").value;
    $("liveout").innerHTML = `<p class="note">${lat.toFixed(4)}, ${lon.toFixed(4)} için açık veriler çekiliyor (Overture, HRSL, GHS-POP, PVGIS, UNSD, OSM)…</p>`;
    fetch(`${API}/assess?lat=${lat}&lon=${lon}&k=${k}`).then(r => r.json()).then(r => {
      const s = r.summary, e = s.explanation || {};
      if (liveLayer) map.removeLayer(liveLayer);
      const sc = scaleOf("energy_balance"), br = breaks("energy_balance");
      liveLayer = L.geoJSON(r.geojson, { style: f => ({ color: "#222", weight: 0.6, fillOpacity: 0.6, fillColor: col(f.properties.energy_balance, br, sc) }),
        onEachFeature: (f, l) => l.bindTooltip(`Denge: ${nf(f.properties.energy_balance, 2)} · nüfus ${nf(f.properties.population, 0)}`, { sticky: true }) }).addTo(map);
      const inp = s.inputs || {}, fails = Object.entries(r.failures || {});
      $("liveout").innerHTML = `<p><b>${{ped_candidate: "PED adayı", conditional_roof: "Koşullu (çatı)", conditional_demand: "Koşullu (talep azaltımı)", not_on_site: "Yerinde olmaz", insufficient_data: "Veri yetersiz", no_population: "Nüfus yok"}[e.verdict] || e.verdict}</b></p>
        <p>${e.text_tr || ""}</p>
        <table class="kv"><tr><td>Yıllık denge (aralık)</td><td>${nf(e.balance, 2)} (${nf((s.balance_range || [])[0], 2)}–${nf((s.balance_range || [])[1], 2)})</td></tr>
        <tr><td>Nüfus · kaynak</td><td>${nf(s.population, 0)} · ${(r.provenance.population || {}).source || "-"}</td></tr>
        <tr><td>60+ / 0–5 / 15–24</td><td>${nf(s.vul_elderly60, 0)} / ${nf(s.vul_children0_5, 0)} / ${nf(s.vul_youth15_24, 0)}</td></tr>
        <tr><td>Mekân (Overture)</td><td>${nf(s.places, 0)}</td></tr>
        <tr><td>Kişi başı konut elektriği</td><td>${nf((inp.kwh_per_capita || {}).kwh_per_capita, 0)} kWh (${(inp.kwh_per_capita || {}).basis || "-"}, ${(inp.country || {}).name || "-"})</td></tr>
        <tr><td>FV verimi</td><td>${nf((inp.pv_yield || {}).kwh_per_kwp, 0)} kWh/kWp</td></tr>
        <tr><td>Süre</td><td>${nf((r.timing_s || {}).total, 1)} s</td></tr></table>
        ${fails.length ? `<p class="note">Alınamayan kaynaklar (sentetik değerle doldurulmadı): ${fails.map(x => x[0]).join(", ")}</p>` : ""}`;
    }).catch(err => { $("liveout").innerHTML = `<p class="note">Hata: ${err}</p>`; });
  }

  function draw(k) {
    const sc = scaleOf(k), br = breaks(k), sp = CAT[k];
    if (cellLayer) map.removeLayer(cellLayer);
    cellLayer = L.geoJSON(P.cells, {
      style: f => ({ color: cand.has(f.properties.cell) ? css("--ink") : "#444", weight: cand.has(f.properties.cell) ? 3 : 0.5,
        fillOpacity: 0.62, fillColor: col(f.properties[k], br, sc) }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`${sp.label_tr}: ${nf(f.properties[k], dg(f.properties[k]))} ${sp.unit}`, { sticky: true });
        layer.on("click", ev => { L.DomEvent.stopPropagation(ev); const c = f.properties.cell; cand.has(c) ? cand.delete(c) : cand.add(c); restyle(); renderCand(); });
      },
    }).addTo(map);
    if (legend) map.removeControl(legend);
    legend = L.control({ position: "bottomleft" });
    legend.onAdd = () => {
      const d = L.DomUtil.create("div", "legend"), m = Math.floor(br.length / 2);
      d.innerHTML = `<b>${sp.label_tr}</b> <span class="note">${sp.unit}</span><div class="bar" style="background:linear-gradient(90deg,${sc.join(",")})"></div>
        <div class="ticks"><span>${nf(br[0], dg(br[0]))}</span><span>${nf(br[m], dg(br[m]))}</span><span>${nf(br[br.length - 1], dg(br[br.length - 1]))}</span></div>
        <div class="note">${FIX[k] ? "sabit eşikler" : "kantil dilimleri"} · gri: tanımsız · kalın çerçeve: proje adayı</div>`;
      return d;
    };
    legend.addTo(map);
    $("metricnote").textContent = `Kaynak: ${sp.source} · Lisans: ${sp.license}${sp.note ? " · " + sp.note : ""}`;
  }
  function restyle() { draw(sel.value); }

  // ---------- candidate aggregation (exact sums of per-cell real data)
  const A = P.agg;
  function sums(cells) {
    const s = { pop: 0, dem: 0, pv: 0, pvl: 0, pvh: 0, fp: 0, ha: 0, n: 0 };
    cells.forEach(c => { const a = A[c]; if (!a) return; s.n++; ["pop", "dem", "pv", "pvl", "pvh", "fp", "ha"].forEach(k => s[k] += a[k]); });
    s.bal = s.dem > 0 ? s.pv / s.dem : NaN; s.ball = s.dem > 0 ? s.pvl / s.dem : NaN; s.balh = s.dem > 0 ? s.pvh / s.dem : NaN;
    return s;
  }
  const meanOf = (cells, k) => { const v = [...cells].map(c => byCell[c] && byCell[c][k]).filter(x => x !== null && x !== undefined && isFinite(x)); return v.length ? v.reduce((a, b) => a + b, 0) / v.length : NaN; };
  const frontier = cells => { const f = new Set(); cells.forEach(c => (P.adj[c] || []).forEach(n => { if (!cells.has(n) && A[n]) f.add(n); })); return f; };

  // Growth rule: seed = highest-balance cell among cells with at least median population;
  // while the candidate is a PED (balance ≥ 1) add the neighbour that serves the most people and keeps balance ≥ 1;
  // while it is not, add the neighbour that raises the balance most. (Annual rule; hourly complementarity comes with hourly demand.)
  const popMedian = (() => { const v = Object.values(A).map(a => a.pop).filter(x => x > 0).sort((a, b) => a - b); return v.length ? v[Math.floor(v.length / 2)] : 0; })();
  $("grow").addEventListener("click", () => {
    if (!cand.size) {
      let best = null; Object.keys(A).forEach(c => { const a = A[c]; if (a.dem > 0 && a.pop >= popMedian && (!best || a.pv / a.dem > A[best].pv / A[best].dem)) best = c; });
      if (best) cand.add(best);
    }
    const max = +$("maxcells").value;
    while (cand.size < max) {
      const fr = frontier(cand); if (!fr.size) break;
      const cur = sums(cand); let pick = null, score = -Infinity;
      fr.forEach(n => {
        const t = new Set(cand); t.add(n); const s2 = sums(t);
        if (cur.bal >= 1) { if (s2.bal >= 1 && A[n].pop > score) { score = A[n].pop; pick = n; } }
        else { const b = isFinite(s2.bal) ? s2.bal : -1; if (b > score) { score = b; pick = n; } }
      });
      if (!pick) break;
      cand.add(pick);
    }
    restyle(); renderCand();
  });
  $("clear").addEventListener("click", () => { cand.clear(); restyle(); renderCand(); });
  $("copy").addEventListener("click", async () => {
    const keys = ["energy_balance", "energy_balance_low", "energy_balance_high", "demo_population", "energy_demand_res_kwh", "energy_pv_kwh", "built_footprint_m2", "poi_daytime_share", "mob_walk800_daily_completeness", "morph_shared_wall_ratio"];
    const csv = ["cell," + keys.join(",")].concat([...cand].map(c => c + "," + keys.map(k => byCell[c][k] ?? "").join(","))).join("\n");
    const btn = $("copy");
    try { await navigator.clipboard.writeText(csv); btn.textContent = "Kopyalandı"; }
    catch (e) { const ta = document.createElement("textarea"); ta.value = csv; ta.rows = 6; ta.style.width = "100%"; $("cand").prepend(ta); ta.select(); btn.textContent = "Metni seçip kopyalayın"; }
    setTimeout(() => { btn.textContent = "Adayı kopyala (CSV)"; }, 2500);
  });

  function renderCand() {
    const el = $("cand");
    if (!cand.size) {
      el.innerHTML = `<div class="verdict"><b>Henüz aday yok.</b> Bir altıgene tıklayın ya da <b>Otomatik büyüt</b> düğmesine basın. Büyütme, nüfusu ortanca üstü hücreler arasında dengesi en yüksek olandan başlar; denge 1'in üstünde kaldıkça en çok kişiye hizmet eden komşuyu ekler.</div>`;
      $("copy").disabled = true; return;
    }
    $("copy").disabled = false;
    const s = sums(cand), D = P.district;
    const yieldK = I.pv_yield_kwh_per_kwp_2023, eta = S.provenance.params.module_efficiency.value, uH = S.provenance.params.roof_utilization.high;
    // verdict (technology axis)
    let cls = "bad", txt = "Fiziksel olarak yetersiz: yıllık denge 1'in altında (alt ve ana senaryo).";
    if (s.bal >= 1) { cls = "ok"; txt = "Fiziksel olarak yapılabilir: ana senaryoda yıllık konut elektriği dengesi ≥ 1."; }
    else if (s.balh >= 1) { cls = "warn"; txt = "Koşullu: yalnızca üst senaryoda (çatı payı 0,50, verim 0,25) denge ≥ 1."; }
    // what-if (physical inverse)
    const needKwp = s.dem / yieldK, needRoof = needKwp / eta, availRoof = s.fp * uH, share = s.fp > 0 ? needRoof / s.fp : NaN;
    let whatif;
    if (s.dem <= 0) whatif = "Hücrelerde nüfus yok; konut talebi tanımsız.";
    else if (needRoof <= availRoof) whatif = `Denge = 1 için taban alanının <b>%${nf(share * 100)}</b>'ine PV yeterli (${nf(needKwp)} kWp). Bu oran üst sınır olan %${nf(uH * 100)}'in içinde.`;
    else whatif = `Çatı tek başına yetmiyor: gereken çatı payı %${nf(share * 100)}, üst sınır %${nf(uH * 100)}. Açık ${nf(s.dem - availRoof * eta * yieldK)} kWh/yıl. Komşu hücre eklemek veya talebi azaltmak gerekiyor.`;
    // best neighbour
    let bestN = null, bestB = -Infinity; frontier(cand).forEach(n => { const t = new Set(cand); t.add(n); const b = sums(t).bal; if (isFinite(b) && b > bestB) { bestB = b; bestN = n; } });
    // XAI exact decomposition vs district
    const xb = Math.log((s.fp / s.n) / (D.fp / D.n)), xp = -Math.log((s.pop / s.n) / (D.pop / D.n));
    const bar = (lab, v) => { const w = Math.min(Math.abs(v) / 1.5, 1) * 50; const left = v >= 0 ? 50 : 50 - w;
      return `<div class="row"><span>${lab}</span><span class="track"><span class="mid"></span><span class="fill" style="left:${left}%;width:${w}%;background:${v >= 0 ? "var(--geo)" : "var(--bad)"}"></span></span><span class="num mono">${v >= 0 ? "+" : ""}${nf(v, 2)}</span></div>`; };
    const ctx = [["Gündüz işlevli POI payı", meanOf(cand, "poi_daytime_share"), 2], ["10 dk yürüme: günlük ihtiyaç tamlığı", meanOf(cand, "mob_walk800_daily_completeness"), 2],
      ["Ortak duvar oranı", meanOf(cand, "morph_shared_wall_ratio"), 2], ["Nüfus yoğunluğu (kişi/ha)", s.pop / s.ha, 0],
      ["Yaz yüzey sıcaklığı LST (°C)", meanOf(cand, "env_lst_mean_c"), 1], ["NDVI (bitki örtüsü)", meanOf(cand, "env_ndvi_mean"), 2],
      ["Ortalama eğim (°)", meanOf(cand, "env_slope_deg"), 1], ["Sokak dolambaçlılığı", meanOf(cand, "mob_circuity"), 2]];
    const C = [
      ["Teknoloji", cls === "ok" ? "ok" : cls === "warn" ? "warn" : "bad", `denge ${nf(s.bal, 2)} (${nf(s.ball, 2)}–${nf(s.balh, 2)})`],
      ["Bağlam", "geo", "aşağıdaki göstergeler"],
      ["Piyasa", "warn", "ROI: kaynaklı tarife ve maliyet bekleniyor"],
      ["Sosyal", "warn", "sosyal katman planlı (GDELT, WVS)"],
      ["Yönetişim", "warn", "şehir iklim taahhütleri (CoM/SECAP) araştırılıyor"],
      ["Teşvik", "warn", "destek mekanizmaları araştırılıyor"],
      ["Süreç", "", "açık veriyle ölçülemez (nitel)"],
    ];
    el.innerHTML = `
      <div class="verdict ${cls}"><b>${s.n} hücrelik aday.</b> ${txt}</div>
      <div class="kpis">
        <div class="kpi"><div class="v">${nf(s.pop)}</div><div class="k">nüfus</div></div>
        <div class="kpi"><div class="v">${nf(s.dem / 1e3)}</div><div class="k">konut talebi, MWh/yıl</div></div>
        <div class="kpi sun"><div class="v">${nf(s.pv / 1e3)}</div><div class="k">çatı PV, MWh/yıl</div></div>
        <div class="kpi sun"><div class="v">${nf(s.bal, 2)}</div><div class="k">yıllık denge (${nf(s.ball, 2)}–${nf(s.balh, 2)})</div></div>
      </div>
      <div><h3>Ne yapılırsa olur? (fiziksel tersine analiz)</h3><p class="note" style="margin:4px 0">${whatif}</p>
        ${bestN ? `<p class="note" style="margin:4px 0">En çok katkı verecek komşu: <span class="mono">${bestN}</span> → denge ${nf(bestB, 2)}</p>` : ""}</div>
      <div><h3>Neden? (kesin ayrıştırma, mahalle ortalamasına göre)</h3>
        <div class="bars">${bar("Yapı (taban alanı)", xb)}${bar("Nüfus", xp)}${bar("Toplam Δln(denge)", xb + xp)}</div>
        <p class="note" style="margin:4px 0">ln(denge) = ln(taban alanı) − ln(nüfus) + sabit; iki katkının toplamı tam olarak farka eşittir.</p></div>
      <div><h3>Elverişlilik alanları (Krangsås vd., 2021)</h3>
        <div class="crit">${C.map(c => `<span class="k">${c[0]}</span><span class="note">${c[2]}</span><span>${c[1] ? `<span class="badge ${c[1]}">${c[1] === "ok" ? "uygun" : c[1] === "bad" ? "yetersiz" : c[1] === "geo" ? "bilgi" : "veri bekleniyor"}</span>` : `<span class="badge">nitel</span>`}</span>`).join("")}</div></div>
      <div><h3>Bağlam göstergeleri (aday ortalaması)</h3><table>${ctx.map(r => `<tr><td>${r[0]}</td><td class="num">${nf(r[1], r[2])}</td></tr>`).join("")}</table></div>
      <p class="note">Bu sürümde denge yalnızca yıllık konut elektriğini kapsar. Saatlik tamamlayıcılık ve Shapley katkıları saatlik talep kaynağı seçilince eklenecek.</p>`;
  }

  route();
})();
