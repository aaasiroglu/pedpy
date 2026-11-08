/* pedx web demo – reads window.PEDX_DATA produced by examples/build_demo_caferaga.py */
(function () {
  const D = window.PEDX_DATA;
  const S = D.summary;
  const fmt = (v, d = 0) => (v === null || v === undefined || Number.isNaN(v)) ? "—" :
    Number(v).toLocaleString("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: d });

  // ------------------------------------------------------------ tabs
  document.querySelectorAll("nav.tabs button").forEach(b => b.addEventListener("click", () => {
    document.querySelectorAll("nav.tabs button").forEach(x => x.setAttribute("aria-selected", x === b));
    document.querySelectorAll("section.tab").forEach(s => s.classList.toggle("active", s.id === b.dataset.tab));
  }));

  // ------------------------------------------------------------ map
  const map = L.map("map", { preferCanvas: true });
  L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> katkıcıları · nüfus: JRC GHS-POP (CC BY 4.0) · PV: EU JRC PVGIS',
  }).addTo(map);
  const boundary = L.geoJSON(D.boundary, { style: { color: "#111", weight: 2, fill: false, dashArray: "6 4" } }).addTo(map);
  map.fitBounds(boundary.getBounds(), { padding: [12, 12] });
  const buildings = L.geoJSON(D.buildings, { style: { color: "#555", weight: 0.4, fillOpacity: 0.05 } });

  // colour scales (colour-blind safe: RdBu diverging, viridis-like sequential)
  const RDBU = ["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"];
  const SEQ = ["#fde725", "#b5de2b", "#6ece58", "#35b779", "#1f9e89", "#26828e", "#31688e", "#3e4989", "#482878"];
  const METRICS = {
    balance: { label: "PV / konut talebi", scale: RDBU, breaks: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3], d: 2 },
    roof_share_needed: { label: "gereken çatı payı", scale: RDBU.slice().reverse(), breaks: [0.05, 0.1, 0.15, 0.2, 0.26, 0.35, 0.5, 0.75], d: 2 },
    population: { label: "kişi", scale: SEQ, quantile: true, d: 0 },
    pv_kwh: { label: "kWh/yıl", scale: SEQ, quantile: true, d: 0 },
    demand_res_kwh: { label: "kWh/yıl", scale: SEQ, quantile: true, d: 0 },
  };
  const feats = D.cells.features;
  function breaksFor(key) {
    const m = METRICS[key];
    if (!m.quantile) return m.breaks;
    const v = feats.map(f => f.properties[key]).filter(x => x !== null).sort((a, b) => a - b);
    return [1, 2, 3, 4, 5, 6, 7, 8].map(i => v[Math.floor(i * (v.length - 1) / 9)]);
  }
  function colorFor(v, br, scale) {
    if (v === null || v === undefined) return "#bdbdbd";
    let i = 0; while (i < br.length && v >= br[i]) i++; return scale[i];
  }
  let cellLayer, legend;
  function draw(key) {
    const m = METRICS[key], br = breaksFor(key);
    if (cellLayer) map.removeLayer(cellLayer);
    cellLayer = L.geoJSON(D.cells, {
      style: f => ({ color: "#333", weight: 0.6, fillOpacity: 0.72, fillColor: colorFor(f.properties[key], br, m.scale) }),
      onEachFeature: (f, layer) => layer.on("click", () => showCell(f.properties)),
    }).addTo(map);
    if (legend) map.removeControl(legend);
    legend = L.control({ position: "bottomleft" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div", "legend");
      div.innerHTML = `<b>${document.querySelector('#metric option[value="' + key + '"]').textContent}</b>
        <div class="bar" style="background:linear-gradient(90deg,${m.scale.join(",")})"></div>
        <div class="ticks"><span>${fmt(br[0], m.d)}</span><span>${fmt(br[Math.floor(br.length / 2)], m.d)}</span><span>${fmt(br[br.length - 1], m.d)}</span></div>
        <div class="note">gri: tanımsız (nüfus yok)</div>`;
      return div;
    };
    legend.addTo(map);
  }
  L.control.layers(null, { "OSM binaları": buildings }, { collapsed: true }).addTo(map);
  document.getElementById("metric").addEventListener("change", e => draw(e.target.value));
  draw("balance");

  function showCell(p) {
    const rows = [
      ["H3 hücresi", p.cell], ["Bina sayısı", fmt(p.n_buildings)], ["Taban alanı (m²)", fmt(p.footprint_m2)],
      ["Nüfus (GHS-POP 2020)", fmt(p.population, 1)], ["Nüfus yoğunluğu (kişi/ha)", fmt(p.pop_density_per_ha, 1)],
      ["Konut talebi (kWh/yıl)", fmt(p.demand_res_kwh)], ["PV kurulu güç (kWp)", fmt(p.pv_kwp, 1)],
      ["PV üretimi (kWh/yıl)", fmt(p.pv_kwh)], ["Denge (ana senaryo)", fmt(p.balance, 2)],
      ["Denge aralığı (alt–üst)", `${fmt(p.balance_low, 2)} – ${fmt(p.balance_high, 2)}`],
      ["Denge = 1 için gereken çatı payı", fmt(p.roof_share_needed, 2)],
      ["Kat bilgisi olan bina oranı (OSM)", fmt(p.levels_known, 2)],
    ];
    document.getElementById("cellinfo").innerHTML = "<table>" + rows.map(r => `<tr><th>${r[0]}</th><td class="num">${r[1]}</td></tr>`).join("") + "</table>";
  }

  // ------------------------------------------------------------ summary cards
  const T = S.total;
  const cards = [
    ["Bina (OSM)", fmt(T.n_buildings)], ["H3 hücresi", fmt(T.n_cells)],
    ["Nüfus (GHS-POP 2020)", fmt(T.population_ghs_2020)], ["Konut talebi (GWh/yıl)", fmt(T.demand_res_kwh / 1e6, 2)],
    ["PV potansiyeli (GWh/yıl)", fmt(T.pv_kwh / 1e6, 2)], ["Yıllık denge", `${fmt(T.balance, 2)} <span class="note">(${fmt(T.balance_low, 2)}–${fmt(T.balance_high, 2)})</span>`],
  ];
  document.getElementById("cards").innerHTML = cards.map(c => `<div class="card"><div class="v">${c[1]}</div><div class="k">${c[0]}</div></div>`).join("");
  document.getElementById("balnote").textContent =
    `Kişi başı konut elektriği ${fmt(S.provenance.inputs.residential_kwh_per_capita_2023, 0)} kWh/yıl (UNSD 2023 ÷ BM nüfusu). ` +
    `PV verimi ${fmt(S.provenance.inputs.pv_yield_kwh_per_kwp_2023, 0)} kWh/kWp (PVGIS 2023, eğim ${S.provenance.inputs.pvgis_mounting.fixed.slope.value}°). ` +
    `Denge yalnızca konut elektriğini kapsar; hizmet sektörü ve ısıtma dahil değil.`;

  // ------------------------------------------------------------ monthly PV chart (inline SVG)
  (function chart() {
    const m = S.monthly_pv_kwh_per_kwp, vals = Array.from({ length: 12 }, (_, i) => m[i + 1] || 0);
    const W = 380, H = 140, pad = 24, max = Math.max(...vals), bw = (W - pad * 2) / 12;
    const months = ["O", "Ş", "M", "N", "M", "H", "T", "A", "E", "E", "K", "A"];
    let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Aylık PV verimi">`;
    vals.forEach((v, i) => {
      const h = (H - pad * 1.6) * v / max, x = pad + i * bw + 2, y = H - pad - h;
      s += `<rect x="${x}" y="${y}" width="${bw - 4}" height="${h}" fill="#f2a900"><title>${fmt(v, 1)} kWh/kWp</title></rect>`;
      s += `<text x="${x + (bw - 4) / 2}" y="${H - pad + 12}" text-anchor="middle">${months[i]}</text>`;
    });
    s += `<text x="${pad}" y="12">maks. ${fmt(max, 0)} kWh/kWp</text></svg>`;
    document.getElementById("chart").innerHTML = s;
  })();

  // ------------------------------------------------------------ sources, validation, gaps
  const SOURCES = [
    ["Mahalle sınırı ve binalar", "OpenStreetMap (Overpass API)", "ODbL 1.0", "g1"],
    ["Nüfus", "JRC GHS-POP R2023A, E2020, 3″ (Schiavina vd., 2023)", "CC BY 4.0", "g1"],
    ["Konut elektriği tüketimi (ulusal, 2023)", "UN Statistics Division Energy Statistics Database (UNdata)", "UNdata kullanım koşulları (atıfla serbest)", "g1"],
    ["Ülke nüfusu ve kişi başı talep", "UN WPP ve Ember, Our World in Data energy-data üzerinden", "CC BY 4.0", "g1"],
    ["PV üretimi (saatlik, 2023)", "EU JRC PVGIS 5.3 (SARAH-3 / ERA5)", "AB yeniden kullanım politikası", "g1"],
    ["Çatı kullanım katsayısı", "Gagnon vd. (2016), NREL/TP-6A20-65298", "kamu raporu", "g1"],
    ["Modül verimi aralığı", "Fraunhofer ISE, Photovoltaics Report", "kamu raporu", "g1"],
    ["İstanbul kişi başı net tüketim", "TEDAŞ 2023 Sektör Raporu, Tablo 7", "yalnızca doğrulama", "g2"],
    ["Caferağa nüfusu (2020)", "Kadıköy Belediyesi / TÜİK ADNKS", "yalnızca doğrulama", "g2"],
  ];
  document.getElementById("sources").innerHTML = "<h2>Veri kaynakları</h2><table><tr><th>Katman</th><th>Kaynak</th><th>Lisans / rol</th></tr>" +
    SOURCES.map(s => `<tr><td>${s[0]}</td><td>${s[1]}</td><td><span class="badge ${s[3]}">${s[3].toUpperCase()}</span> ${s[2]}</td></tr>`).join("") +
    "</table><h3>Parametreler</h3><table>" +
    Object.entries(S.provenance.params).map(([k, p]) => `<tr><th>${k}</th><td class="num">${p.value} (${p.low}–${p.high})</td><td class="note">${p.source}</td></tr>`).join("") +
    "</table><p class='note'>Ayrıntılı kaynak kütüğü: repo içinde docs/11_veri_kaynaklari.md.</p>";
  document.getElementById("validation").innerHTML = "<h2>Küresel açık veri (G1) ile İstanbul verisi (G2)</h2><table><tr><th>Gösterge</th><th class='num'>G1</th><th class='num'>G2</th><th class='num'>Fark</th></tr>" +
    S.validation.map(v => `<tr><td>${v.item}<div class="note">${v.unit}<br>G1: ${v.g1_source}<br>G2: ${v.g2_source}${v.note ? "<br>" + v.note : ""}</div></td><td class="num">${fmt(v.global_open_G1)}</td><td class="num">${fmt(v.local_G2)}</td><td class="num">${fmt(v.rel_diff * 100, 1)}%</td></tr>`).join("") +
    "</table><p class='note'>Sıradaki doğrulamalar: EPİAŞ konut (mesken) saatlik profili, İBB bina envanteri (kat, yaş), Demirel vd. (2025) 3B çatı ışınımı.</p>";
  document.getElementById("gaps").innerHTML = "<h2>Bilinen eksikler (dürüstlük notu)</h2><ul>" +
    S.provenance.gaps.map(g => `<li>${g}</li>`).join("") +
    `<li>OSM'de binaların yalnızca %${fmt(T.share_levels_known * 100, 0)}'inde kat bilgisi var; yapım yılı neredeyse hiç yok (%${fmt(T.share_start_year_known * 100, 1)}).</li></ul>`;
})();
