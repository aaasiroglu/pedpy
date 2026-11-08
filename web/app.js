/* pedx web demo – reads window.PEDX_DATA (built by examples/build_demo_caferaga.py).
   Every map layer comes from the registered feature catalogue (data contract, K-029). */
(function () {
  const D = window.PEDX_DATA, S = D.summary, T = S.total;
  const CAT = Object.fromEntries(S.catalog.features.map(f => [f.name, f]));
  const FAM = S.catalog.families;
  const fmt = (v, d = 0) => (v === null || v === undefined || Number.isNaN(v)) ? "—" :
    Number(v).toLocaleString("tr-TR", { maximumFractionDigits: d, minimumFractionDigits: d });
  const digits = v => (v === null || v === undefined) ? 0 : (Math.abs(v) >= 100 ? 0 : Math.abs(v) >= 1 ? 2 : 3);

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
  L.control.layers(null, { "OSM binaları": buildings }, { collapsed: true }).addTo(map);

  const RDBU = ["#b2182b", "#d6604d", "#f4a582", "#fddbc7", "#f7f7f7", "#d1e5f0", "#92c5de", "#4393c3", "#2166ac"];
  const SEQ = ["#fde725", "#b5de2b", "#6ece58", "#35b779", "#1f9e89", "#26828e", "#31688e", "#3e4989", "#482878"];
  const SPECIAL = {
    energy_balance: { scale: RDBU, breaks: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3] },
    energy_balance_low: { scale: RDBU, breaks: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3] },
    energy_balance_high: { scale: RDBU, breaks: [0.25, 0.5, 0.75, 0.95, 1.05, 1.5, 2, 3] },
    energy_roof_share_needed: { scale: RDBU.slice().reverse(), breaks: [0.05, 0.1, 0.15, 0.2, 0.26, 0.35, 0.5, 0.75] },
    xai_logbal_built: { scale: RDBU, breaks: [-1.5, -1, -0.5, -0.1, 0.1, 0.5, 1, 1.5] },
    xai_logbal_population: { scale: RDBU, breaks: [-1.5, -1, -0.5, -0.1, 0.1, 0.5, 1, 1.5] },
  };
  const feats = D.cells.features;
  const present = Object.keys(feats[0].properties).filter(k => CAT[k] && CAT[k].status === "active");

  // metric selector grouped by family
  const sel = document.getElementById("metric");
  Object.entries(FAM).forEach(([fam, label]) => {
    const names = present.filter(n => CAT[n].family === fam);
    if (!names.length) return;
    const g = document.createElement("optgroup"); g.label = label;
    names.forEach(n => { const o = document.createElement("option"); o.value = n; o.textContent = CAT[n].label_tr; g.appendChild(o); });
    sel.appendChild(g);
  });
  sel.value = "energy_balance";

  function breaksFor(key) {
    if (SPECIAL[key]) return SPECIAL[key].breaks;
    const v = feats.map(f => f.properties[key]).filter(x => x !== null && x !== undefined).sort((a, b) => a - b);
    if (!v.length) return [0];
    return [1, 2, 3, 4, 5, 6, 7, 8].map(i => v[Math.floor(i * (v.length - 1) / 9)]);
  }
  const colorFor = (v, br, sc) => { if (v === null || v === undefined) return "#bdbdbd"; let i = 0; while (i < br.length && v >= br[i]) i++; return sc[i]; };
  let cellLayer, legend;
  function draw(key) {
    const sc = SPECIAL[key] ? SPECIAL[key].scale : SEQ, br = breaksFor(key), spec = CAT[key];
    if (cellLayer) map.removeLayer(cellLayer);
    cellLayer = L.geoJSON(D.cells, {
      style: f => ({ color: "#333", weight: 0.6, fillOpacity: 0.72, fillColor: colorFor(f.properties[key], br, sc) }),
      onEachFeature: (f, layer) => {
        layer.bindTooltip(`${spec.label_tr}: ${fmt(f.properties[key], digits(f.properties[key]))} ${spec.unit}`, { sticky: true });
        layer.on("click", () => showCell(f.properties));
      },
    }).addTo(map);
    if (legend) map.removeControl(legend);
    legend = L.control({ position: "bottomleft" });
    legend.onAdd = () => {
      const div = L.DomUtil.create("div", "legend");
      div.innerHTML = `<b>${spec.label_tr}</b> <span class="note">(${spec.unit})</span>
        <div class="bar" style="background:linear-gradient(90deg,${sc.join(",")})"></div>
        <div class="ticks"><span>${fmt(br[0], digits(br[0]))}</span><span>${fmt(br[Math.floor(br.length / 2)], digits(br[Math.floor(br.length / 2)]))}</span><span>${fmt(br[br.length - 1], digits(br[br.length - 1]))}</span></div>
        <div class="note">${SPECIAL[key] ? "sabit eşikler" : "eşit sayılı dilimler (kantil)"} · gri: tanımsız</div>`;
      return div;
    };
    legend.addTo(map);
    document.getElementById("metricnote").textContent = `Kaynak: ${spec.source} · Lisans: ${spec.license}${spec.note ? " · " + spec.note : ""}`;
  }
  sel.addEventListener("change", e => draw(e.target.value));
  draw("energy_balance");

  function showCell(p) {
    let h = `<p class="note">H3 hücresi <b>${p.cell}</b></p>`;
    Object.entries(FAM).forEach(([fam, label]) => {
      const names = present.filter(n => CAT[n].family === fam);
      if (!names.length) return;
      h += `<h3>${label}</h3><table>` + names.map(n => `<tr><th>${CAT[n].label_tr}</th><td class="num">${fmt(p[n], digits(p[n]))} <span class="note">${CAT[n].unit}</span></td></tr>`).join("") + "</table>";
    });
    document.getElementById("cellinfo").innerHTML = h;
  }

  // ------------------------------------------------------------ summary
  const cards = [
    ["Bina (OSM)", fmt(T.n_buildings)], ["H3 hücresi", fmt(T.n_cells)], ["POI (OSM)", fmt(T.n_pois)],
    ["Nüfus (GHS-POP 2020)", fmt(T.population_ghs_2020)], ["Konut talebi (GWh/yıl)", fmt(T.demand_res_kwh / 1e6, 2)],
    ["PV potansiyeli (GWh/yıl)", fmt(T.pv_kwh / 1e6, 2)],
    ["Yıllık denge", `${fmt(T.balance, 2)} <span class="note">(${fmt(T.balance_low, 2)}–${fmt(T.balance_high, 2)})</span>`],
    ["Kayıtlı özellik / hücre", fmt(present.length)],
  ];
  document.getElementById("cards").innerHTML = cards.map(c => `<div class="card"><div class="v">${c[1]}</div><div class="k">${c[0]}</div></div>`).join("");
  const I = S.provenance.inputs;
  document.getElementById("balnote").textContent =
    `Kişi başı konut elektriği ${fmt(I.residential_kwh_per_capita_2023)} kWh/yıl (UNSD 2023 ÷ BM nüfusu). ` +
    `PV verimi ${fmt(I.pv_yield_kwh_per_kwp_2023)} kWh/kWp (PVGIS 2023, eğim ${I.pvgis_mounting.fixed.slope.value}°). ` +
    `Denge yalnızca konut elektriğini kapsar.`;

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
    document.getElementById("chart").innerHTML = s + `<text x="${pad}" y="12">maks. ${fmt(max)} kWh/kWp</text></svg>`;
  })();

  // ------------------------------------------------------------ associations (exploratory)
  document.getElementById("assoc").innerHTML =
    `<h2>Yıllık dengeyle keşifsel ilişkiler</h2>
     <p class="note"><b>Nedensel değildir.</b> Spearman ρ; n hücre. Hedefi tanım gereği tekrar eden bileşenler (${S.definitional_excluded.join(", ")}) listeden çıkarıldı.
     Bu tablo hipotez üretmek içindir; doğrulama gruplu mekânsal çapraz doğrulamayla yapılacak (docs/13 §6).</p>
     <table><tr><th>Özellik</th><th>Aile</th><th class="num">ρ</th><th class="num">n</th></tr>` +
    S.associations.map(a => `<tr><td>${(CAT[a.feature] || {}).label_tr || a.feature}</td><td>${FAM[(CAT[a.feature] || {}).family] || ""}</td><td class="num">${fmt(a.rho, 2)}</td><td class="num">${a.n}</td></tr>`).join("") +
    "</table><h3>Kesin XAI ayrıştırması</h3><p class='note'>ln(denge) = ln(taban alanı) − ln(nüfus) + sabit olduğundan, her hücrenin mahalle ortalamasından sapması tam olarak <i>yapı katkısı</i> ile <i>nüfus katkısının</i> toplamıdır. İki katman da harita listesinde 'Enerji' grubunda.</p>";

  // ------------------------------------------------------------ catalogue
  const rows = S.catalog.features.slice().sort((a, b) => (a.status > b.status) - (a.status < b.status) || a.family.localeCompare(b.family));
  document.getElementById("catalog").innerHTML = `<h2>Özellik kataloğu (veri sözleşmesi)</h2>
    <p class="note">${rows.filter(r => r.status === "active").length} etkin, ${rows.filter(r => r.status === "planned").length} planlanan özellik. Kataloğa kayıtlı olmayan hiçbir sütun dışa aktarılamaz.</p>
    <table><tr><th>Özellik</th><th>Kaynak</th><th>Lisans</th><th>Durum</th></tr>` +
    rows.map(r => `<tr><td>${r.label_tr}<div class="note">${FAM[r.family]} · ${r.unit}</div></td><td class="note">${r.source}</td><td class="note">${r.license}</td><td><span class="badge ${r.status === "active" ? "g1" : "gap"}">${r.status === "active" ? "etkin" : "planlı"}</span></td></tr>`).join("") + "</table>";

  // ------------------------------------------------------------ sources, validation, gaps
  const SOURCES = [
    ["Mahalle sınırı, binalar, POI", "OpenStreetMap (Overpass API)", "ODbL 1.0", "g1"],
    ["Nüfus", "JRC GHS-POP R2023A, E2020, 3″ (Schiavina vd., 2023)", "CC BY 4.0", "g1"],
    ["Konut elektriği (ulusal, 2023)", "UN Statistics Division Energy Statistics Database (UNdata)", "UNdata koşulları (atıfla serbest)", "g1"],
    ["Ülke nüfusu ve kişi başı talep", "UN WPP ve Ember, Our World in Data energy-data", "CC BY 4.0", "g1"],
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
    "</table><p class='note'>Ayrıntılı kaynak kütüğü: docs/11_veri_kaynaklari.md · Mimari: docs/13_sistem_mimarisi.md</p>";
  document.getElementById("validation").innerHTML = "<h2>Küresel açık veri (G1) ile İstanbul verisi (G2)</h2><table><tr><th>Gösterge</th><th class='num'>G1</th><th class='num'>G2</th><th class='num'>Fark</th></tr>" +
    S.validation.map(v => `<tr><td>${v.item}<div class="note">${v.unit}<br>G1: ${v.g1_source}<br>G2: ${v.g2_source}${v.note ? "<br>" + v.note : ""}</div></td><td class="num">${fmt(v.global_open_G1)}</td><td class="num">${fmt(v.local_G2)}</td><td class="num">${fmt(v.rel_diff * 100, 1)}%</td></tr>`).join("") +
    "</table><p class='note'>Sıradaki doğrulamalar: EPİAŞ konut (mesken) saatlik profili, İBB bina envanteri (kat, yaş), Demirel vd. (2025) 3B çatı ışınımı.</p>";
  document.getElementById("gaps").innerHTML = "<h2>Bilinen eksikler</h2><ul>" + S.provenance.gaps.map(g => `<li>${g}</li>`).join("") +
    `<li>OSM'de binaların yalnızca %${fmt(T.share_levels_known * 100)}'inde kat bilgisi var; yapım yılı neredeyse hiç yok (%${fmt(T.share_start_year_known * 100, 1)}).</li></ul>`;
})();
