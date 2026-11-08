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
  const VIEWS = ["sunum", "mimari", "tez", "mvp", "kriter", "veri", "kaynakca"];
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

  // ---------- presentation: architecture diagram (SVG; colours from theme tokens)
  (function arch() {
    const L = [
      ["L6 Sunum ve servis", "Web uygulaması · tıkla → hesapla API (FastAPI) · Docker", "web/ · pedx.api"],
      ["L5 Karar (YA/EM)", "ÇKKDS: CRITIC · Entropi · BWM · MARCOS · mutlak endeks · kararlılık · Pareto", "pedx.mcdm · index"],
      ["L4 Yapay zekâ ve XAI", "Gerçek PED'lerden öğrenme · kesin katkılar · Shapley · tersine analiz", "validation · xai · inverse"],
      ["L3 Fizik motorları", "Yıllık ve saatlik enerji dengesi · Demand.ninja · paylaşım oyunu", "pedx.energy · demand · graph"],
      ["L2 H3 özellik deposu", "Kayıtlı ~140 özellik · veri sözleşmesi · kent ızgarası · hücre imzası", "pedx.features · citygrid"],
      ["L1 Veri gölü", "Katalog · COG pencere okuma · GeoParquet satır grubu · raster → H3", "pedx.datalake"],
      ["L0 Küresel açık kaynaklar", "OSM · Overture · GHSL · HRSL · WorldCover · Sentinel-2 · Landsat · DEM · PVGIS", "yalnızca açık lisans"],
    ];
    const W = 760, h = 46, g = 8, H = L.length * (h + g) + 50;
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="pedx sistem mimarisi katmanları" style="max-width:${W}px;display:block">`;
    L.forEach((l, i) => {
      const y = i * (h + g);
      svg += `<rect x="0" y="${y}" width="${W - 215}" height="${h}" rx="4" fill="var(--sheet)" stroke="var(--rule)"/>
        <rect x="0" y="${y}" width="5" height="${h}" fill="${i < 2 ? "var(--sun)" : "var(--geo)"}"/>
        <text x="14" y="${y + 19}" font-size="13.5" font-weight="600" fill="var(--ink)">${l[0]}</text>
        <text x="14" y="${y + 36}" font-size="11.5" fill="var(--muted)">${l[1]}</text>
        <text x="${W - 205}" y="${y + 28}" font-size="10.5" fill="var(--muted)" font-family="monospace">${l[2]}</text>`;
    });
    const yb = L.length * (h + g) + 4;
    svg += `<rect x="0" y="${yb}" width="${W - 215}" height="40" rx="4" fill="none" stroke="var(--sun)" stroke-dasharray="5 4"/>
      <text x="14" y="${yb + 25}" font-size="12" fill="var(--ink)"><tspan font-weight="600">Doğrulama (salt okunur):</tspan> Faz 1 gerçek PED'ler · Faz 2 İBB, TÜİK, EPİAŞ</text></svg>`;
    $("arch").innerHTML = svg;
  })();

  // ---------- presentation: data table from the data-lake catalogue
  (function presData() {
    const lake = S.datalake || [], cnt = {};
    lake.forEach(d => cnt[d.status] = (cnt[d.status] || 0) + 1);
    $("pres-lakekpi").innerHTML = [["Veri seti", lake.length], ["Sistemde", cnt.ingested || 0, "sun"], ["Bağlayıcı hazır", cnt.connector || 0],
      ["Planlı", cnt.planned || 0], ["Reddedildi (lisans)", cnt.rejected || 0]].map(k => `<div class="kpi ${k[2] || ""}"><div class="v">${k[1]}</div><div class="k">${k[0]}</div></div>`).join("");
    const TH = { insan: "İnsan", bina: "Bina", sokak: "Sokak ve ulaşım", kent: "Kentsel işlev", enerji: "Enerji", cevre: "Çevre", iklim: "İklim",
      goruntu: "Uydu görüntüsü", kirilganlik: "Kırılganlık", ekonomi: "Ekonomi", sosyal: "Sosyal", ped: "PED referansı" };
    const B = { ingested: "<span class='badge ok'>sistemde</span>", connector: "<span class='badge geo'>bağlayıcı</span>", planned: "<span class='badge'>planlı</span>", rejected: "<span class='badge warn'>reddedildi</span>" };
    const rows = lake.filter(d => d.status === "ingested").sort((a, b) => (a.theme > b.theme ? 1 : -1));
    $("pres-data").innerHTML = "<table><tr><th>Tema</th><th>Veri</th><th>Çözünürlük</th><th>Lisans</th><th>Kullanım</th><th>Durum</th></tr>" +
      rows.map(d => `<tr><td>${TH[d.theme] || d.theme}</td><td>${d.provider}</td><td class="note">${d.resolution}</td><td class="note">${d.license}</td><td class="note">${d.pedx_use}</td><td>${B[d.status]}</td></tr>`).join("") +
      "</table><p class='note'>Planlı, bağlayıcısı hazır ve reddedilen veri setleri: Mimari → Veri gölü kataloğu.</p>";
  })();

  // ---------- criteria & SHAP view (K-050): source-by-source pages
  (function criteria() {
    const FA = P.features_analysis;
    if (!FA || !$("kr-schemes")) return;
    $("kr-schemes").innerHTML = "<table><tr><th>Ağırlıklandırma şeması</th><th class='num'>AUC (kent dışarıda)</th><th class='num'>Medyan üstü saha</th></tr>" +
      FA.schemes.map(r => `<tr><td>${r.scheme}${r.scheme.startsWith("Kanıt, temiz") ? " <span class='badge ok'>PED puanı</span>" : ""}</td><td class="num">${nf(r.auc_loco, 3)}</td><td class="num">${r.sites_above_half}/${FA.n_sites}</td></tr>`).join("") + "</table>";
    const fam = FA.family_summary.slice().sort((a, b) => b.shap_tree_share - a.shap_tree_share);
    $("kr-fam").innerHTML = `<div class="bars">` + fam.map(f => `<div class="row" style="grid-template-columns:260px 1fr 60px"><span>${f.family}</span><div class="track"><div class="fill" style="left:0;width:${100 * f.shap_tree_share / fam[0].shap_tree_share}%;background:var(--geo)"></div></div><span class="mono">%${nf(100 * f.shap_tree_share, 0)}</span></div>`).join("") +
      `</div><p class="note">Ağaç SHAP önem payı (ortalama |SHAP| toplamı). Yanında: anlamlı kriter sayısı (q &lt; 0,10): ${fam.map(f => `${f.family.split(" (")[0]} ${f.n_q10}/${f.n}`).join(" · ")}.</p>`;
    const byFam = {};
    FA.features.forEach(f => (byFam[f.family] = byFam[f.family] || []).push(f));
    const wkey = "w_Kanıt, temiz";
    const mx = Math.max(...FA.features.map(f => Math.max(Math.abs(f.ci05), Math.abs(f.ci95))));
    $("kr-pages").innerHTML = Object.entries(byFam).map(([fname, fs], k) => `<div class="sheet"><h2><span class="no">${k + 1}</span>${fname}</h2>
      <div class="tbl"><table><tr><th>Özellik</th><th style="min-width:180px">Etki d (%90 aralık)</th><th class="num">q</th><th class="num">SHAP (ağaç)</th><th class="num">Ağırlık</th><th>Not</th></tr>` +
      fs.sort((a, b) => a.q_bh - b.q_bh).map(f => {
        const L = 50 + 50 * f.ci05 / mx, R = 50 + 50 * f.ci95 / mx, C = 50 + 50 * f.effect_d / mx;
        const note = f.suspect_consequence ? "<span class='badge warn'>sonuç şüpheli</span>" : (FA.clean_features.includes(f.feature) ? "" : "<span class='badge'>tekrar</span>");
        return `<tr><td>${f.label} <span class="note mono">${f.feature}</span></td>
          <td><svg viewBox="0 0 200 16" width="180" height="16" role="img" aria-label="etki"><line x1="100" y1="0" x2="100" y2="16" stroke="var(--muted)" stroke-dasharray="2 2"/>
            <line x1="${2 * L}" y1="8" x2="${2 * R}" y2="8" stroke="${f.q_bh < 0.1 ? (f.effect_d > 0 ? "var(--ok)" : "var(--bad)") : "var(--muted)"}" stroke-width="3"/>
            <circle cx="${2 * C}" cy="8" r="4" fill="${f.q_bh < 0.1 ? (f.effect_d > 0 ? "var(--ok)" : "var(--bad)") : "var(--muted)"}"/></svg> <span class="mono">${f.effect_d >= 0 ? "+" : ""}${nf(f.effect_d, 2)}</span></td>
          <td class="num">${nf(f.q_bh, 3)}</td><td class="num">${nf(f.shap_tree_mean_abs, 2)}</td><td class="num">${f[wkey] > 0 ? nf(f[wkey], 3) : "—"}</td><td>${note}</td></tr>`;
      }).join("") + "</table></div><p class='note'>Yeşil: gerçek PED'lerde anlamlı biçimde yüksek; kırmızı: anlamlı biçimde düşük; gri: anlamlı değil (q ≥ 0,10). Ağırlık: PED puanındaki kriter ağırlığı.</p></div>").join("");
    const F = FA.corr.features, R = FA.corr.rho, n = F.length, cs = 11, off = 150;
    let svg = `<svg viewBox="0 0 ${off + n * cs} ${off + n * cs}" width="${off + n * cs}" role="img" aria-label="Özellik korelasyon matrisi">`;
    const lab = f => (FA.features.find(x => x.feature === f) || {}).label || f;
    F.forEach((f, i) => { svg += `<text x="${off - 4}" y="${off + i * cs + 8}" font-size="8" text-anchor="end" fill="var(--ink)">${lab(f)}</text>
      <text transform="translate(${off + i * cs + 8},${off - 4}) rotate(-60)" font-size="8" fill="var(--ink)">${lab(f)}</text>`; });
    R.forEach((row, i) => row.forEach((v, j) => { const a = Math.min(1, Math.abs(v));
      svg += `<rect x="${off + j * cs}" y="${off + i * cs}" width="${cs - 1}" height="${cs - 1}" fill="${v >= 0 ? "#b2182b" : "#2166ac"}" fill-opacity="${a}"><title>${lab(F[i])} × ${lab(F[j])}: ${nf(v, 2)}</title></rect>`; }));
    $("kr-corr").innerHTML = svg + "</svg>";
  })();

  // ---------- presentation: data-scaling curve (value of information)
  (function scaling() {
    const el = $("pres-scaling"), C = ((P.ped_validation || {}).scaling || {}).curve;
    if (!el) return;
    if (!C) { el.innerHTML = "<p class='note'>Henüz hesaplanmadı: python scripts/data_scaling.py</p>"; return; }
    const W = 760, H = 250, x0 = 60, x1 = W - 60, y0 = 20, y1 = 200, n = C.length;
    const SHORT = ["Fizik", "+ Yapı", "+ Demografi", "+ Uydu", "+ Arazi", "+ Kentsel işlev", "+ Altyapı"];
    const X = i => x0 + (x1 - x0) * (n === 1 ? 0.5 : i / (n - 1)), Y = v => y1 - (y1 - y0) * (v - 0.5) / 0.5;
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Veri ölçekleme eğrisi" style="max-width:${W}px;display:block">`;
    [0.5, 0.6, 0.7, 0.8, 0.9, 1.0].forEach(v => svg += `<line x1="${x0}" x2="${x1}" y1="${Y(v)}" y2="${Y(v)}" stroke="var(--rule)" ${v === 0.5 ? 'stroke-dasharray="4 3" stroke="var(--muted)"' : ""}/><text x="${x0 - 6}" y="${Y(v) + 4}" font-size="11" text-anchor="end" fill="var(--muted)">${nf(v, 1)}</text>`);
    svg += `<path d="${C.map((c, i) => `${i ? "L" : "M"}${X(i)},${Y(c.ci95)}`).join("")}${C.slice().reverse().map((c, j) => `L${X(n - 1 - j)},${Y(c.ci05)}`).join("")}Z" fill="var(--geo)" opacity="0.15"/>`;
    svg += `<path d="${C.map((c, i) => `${i ? "L" : "M"}${X(i)},${Y(c.auc)}`).join("")}" fill="none" stroke="var(--geo)" stroke-width="2.5"/>`;
    C.forEach((c, i) => {
      svg += `<circle cx="${X(i)}" cy="${Y(c.auc)}" r="4" fill="var(--geo)"><title>${c.step}: AUC ${nf(c.auc, 2)} (%90: ${nf(c.ci05, 2)}–${nf(c.ci95, 2)}), ${c.n_features} özellik</title></circle>
        <text x="${X(i)}" y="${Y(c.auc) - 9}" font-size="11" text-anchor="middle" fill="var(--ink)">${nf(c.auc, 2)}</text>
        <text x="${X(i)}" y="${y1 + 18}" font-size="11" text-anchor="middle" fill="var(--ink)">${SHORT[i] || c.step}</text>
        <text x="${X(i)}" y="${y1 + 33}" font-size="10" text-anchor="middle" fill="var(--muted)">${c.n_features} özellik</text>`;
    });
    el.innerHTML = svg + "</svg>";
  })();

  // ---------- presentation: real-PED validation chart
  (function pedChart() {
    const V = P.ped_validation || {}, el = $("pres-pedchart");
    if (!V.rows) { el.innerHTML = "<p class='note'>Doğrulama henüz çalıştırılmadı.</p>"; return; }
    const R = V.rows.slice().sort((a, b) => (b.percentile_multi ?? -1) - (a.percentile_multi ?? -1)), s = V.summary;
    const W = 760, rh = 20, x0 = 190, bw = W - x0 - 60, H = R.length * rh + 46;
    let svg = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Gerçek PED sahalarının yüzdelikleri" style="max-width:${W}px;display:block">`;
    svg += `<line x1="${x0 + bw / 2}" y1="0" x2="${x0 + bw / 2}" y2="${R.length * rh}" stroke="var(--muted)" stroke-dasharray="4 3"/>`;
    R.forEach((r, i) => {
      const y = i * rh;
      svg += `<text x="${x0 - 8}" y="${y + 14}" font-size="11.5" text-anchor="end" fill="var(--ink)">${r.site} · ${r.city}</text>`;
      if (r.percentile_multi != null) svg += `<rect x="${x0}" y="${y + 3}" width="${bw * r.percentile_multi}" height="8" fill="var(--geo)"><title>Tüm katmanlar: ${nf(r.percentile_multi, 2)}</title></rect>`;
      if (r.percentile != null) svg += `<rect x="${x0}" y="${y + 11}" width="${bw * r.percentile}" height="6" fill="var(--sun)"><title>Yalnız denge: ${nf(r.percentile, 2)}</title></rect>`;
    });
    const yl = R.length * rh + 18;
    svg += `<text x="${x0}" y="${yl}" font-size="11" fill="var(--muted)">0</text><text x="${x0 + bw / 2 - 8}" y="${yl}" font-size="11" fill="var(--muted)">0,5</text><text x="${x0 + bw - 6}" y="${yl}" font-size="11" fill="var(--muted)">1</text>
      <rect x="${x0}" y="${yl + 10}" width="12" height="8" fill="var(--geo)"/><text x="${x0 + 16}" y="${yl + 18}" font-size="11" fill="var(--ink)">Tüm katmanlar (AUC ${nf(s.auc_multi_loco, 2)})</text>
      <rect x="${x0 + 230}" y="${yl + 10}" width="12" height="8" fill="var(--sun)"/><text x="${x0 + 246}" y="${yl + 18}" font-size="11" fill="var(--ink)">Yalnız enerji dengesi (AUC ${nf(s.auc_pooled, 2)})</text></svg>`;
    el.innerHTML = svg;
  })();
  (function pedVal() {
    const V = P.ped_validation || {}, el = $("pedval");
    if (!el) return;
    if (!V.rows) { el.innerHTML = "<p class='note'>Henüz çalıştırılmadı: python scripts/validate_ped_sites.py</p>"; return; }
    const s = V.summary, dev = { brownfield: "kahverengi alan", new: "yeni yapım", existing: "mevcut stok" };
    const caf = s.caferaga_in_istanbul || {};
    el.innerHTML = `<div class="kpis"><div class="kpi sun"><div class="v">${nf(s.auc_pooled, 2)}</div><div class="k">AUC · yalnız enerji dengesi (${s.sites_above_median}/${s.n_sites} saha medyan üstü, p = ${nf(s.sign_test_p_one_sided, 3)})</div></div>
      <div class="kpi"><div class="v">${nf(s.auc_multi_loco, 2)}</div><div class="k">AUC · tüm katmanlar, bir kent dışarıda (${s.sites_above_median_multi}/${s.n_sites}, p = ${nf(s.sign_test_p_multi, 3)})</div></div>
      <div class="kpi"><div class="v">${nf(caf.percentile_multi, 2)}</div><div class="k">Caferağa'nın İstanbul içindeki yüzdeliği (tüm katmanlar; denge ile ${nf(caf.percentile_balance, 2)})</div></div></div>` +
      "<table><tr><th>Saha</th><th>Program</th><th>Tip</th><th class='num'>Saha dengesi</th><th class='num'>Kontrol medyanı (n)</th><th class='num'>Yüzdelik: denge</th><th class='num'>Yüzdelik: tüm katmanlar</th></tr>" +
      V.rows.map(r => `<tr><td>${r.site} <span class="note">${r.city} · OSM ${r.osm}</span></td><td class="note">${r.programme}</td><td>${dev[r.development] || r.development}</td>
        <td class="num">${nf(r.case_balance, 2)}</td><td class="num">${nf(r.controls_median_balance, 2)} (${r.controls_n})</td><td class="num">${nf(r.percentile, 2)}</td><td class="num">${nf(r.percentile_multi, 2)}</td></tr>`).join("") + "</table>" +
      `<h3>Gerçek PED'leri ayıran katmanlar (kent içi z-puanı, lojistik katsayı)</h3><table><tr><th>Özellik</th><th class='num'>Katsayı</th></tr>` +
      (s.coefficients_full_fit || []).map(c => `<tr><td class="mono">${c.feature}</td><td class="num">${nf(c.coef, 2)}</td></tr>`).join("") + "</table>" +
      `<p class="note">Pozitif katsayı: gerçek PED sahaları o özellikte kendi kentlerinin sıradan yerleşik alanlarından yüksek. İlişki, nedensellik değil. 16 vaka küçük bir örneklem.</p>`;
  })();

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
  const st = { ingested: ["ok", "sistemde"], connector: ["geo", "bağlayıcı hazır"], planned: ["warn", "planlı"], rejected: ["bad", "reddedildi (lisans)"] };
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
    initAtlas(bnd);
    initScales();
  }

  // ---------- multi-scale view, energy-sharing flows and drawable project site (K-052)
  function initScales() {
    const SC = P.scales;
    if (!SC || typeof h3 === "undefined") { $("scale").disabled = true; $("scalenote").textContent = "Çok ölçekli veri ya da H3 kütüphanesi yok."; return; }
    const inp = S.provenance.inputs, prm = S.provenance.params;
    const d = inp.residential_kwh_per_capita_2023, Y = inp.pv_yield_kwh_per_kwp_2023, u = prm.roof_utilization.value, eta = prm.module_efficiency.value;
    const BB = [0.5, 0.75, 0.9, 1, 1.1, 1.5, 2, 3];
    const colB = v => v === null || v === undefined || !isFinite(v) ? "#bdbdbd" : col(v, BB, RDBU);
    let flowLayer = null, siteLayer = null, tmpLine = null, verts = [];
    const legendB = title => { if (legend) map.removeControl(legend); legend = L.control({ position: "bottomleft" });
      legend.onAdd = () => { const el = L.DomUtil.create("div", "legend");
        el.innerHTML = `<b>${title}</b><div class="bar" style="background:linear-gradient(90deg,${RDBU.join(",")})"></div><div class="ticks"><span>&lt;0,5</span><span>1</span><span>3+</span></div><div class="note">kırmızı: açık · mavi: fazla (PV/talep)</div>`; return el; };
      legend.addTo(map); };
    function drawScale(v) {
      if (v === "r10") { draw(sel.value); $("scalenote").textContent = ""; return; }
      if (cellLayer) map.removeLayer(cellLayer);
      let gj, styleFn, tip, note;
      if (v === "block") {
        gj = SC.blocks; styleFn = f => ({ color: "#333", weight: 0.4, fillOpacity: 0.75, fillColor: colB(f.properties.balance) });
        tip = p => `Yapı adası ${p.block_id} · denge ${nf(p.balance, 2)} · ${nf(p.pop, 0)} kişi · ${nf(p.area_m2 / 1e4, 2)} ha`; note = "Sokak ağından poligonlaştırılmış yapı adaları (Fleischmann vd. 2020).";
      } else if (v === "bld") {
        const vals = Object.values(SC.building).map(x => x[0]).sort((a, b) => a - b), br = [1, 2, 3, 4, 5, 6, 7, 8].map(i => vals[Math.floor(i * (vals.length - 1) / 9)]);
        gj = P.buildings; styleFn = f => { const r = SC.building[f.properties.id]; return { color: "#222", weight: 0.3, fillOpacity: 0.85, fillColor: r ? col(r[0], br, SEQ) : "#bdbdbd" }; };
        tip = p => { const r = SC.building[p.id]; return r ? `Bina ${p.id} · çatı FV ${nf(r[0] / 1000, 1)} MWh/yıl` : p.id; };
        note = "Bina dengesi, nüfus taban alanına orantılı dağıtıldığı için hücre dengesine eşittir; bu yüzden binada yalnız arz (FV potansiyeli) gösterilir.";
      } else {
        const rows = SC[v];
        gj = { type: "FeatureCollection", features: rows.map(r => ({ type: "Feature", properties: { cell: r[0], balance: r[1], pop: r[2], pv: r[3] }, geometry: { type: "Polygon", coordinates: [h3.cellToBoundary(r[0], true)] } })) };
        styleFn = f => ({ color: "#333", weight: 0.3, fillOpacity: 0.75, fillColor: colB(f.properties.balance) });
        tip = p => `${p.cell} · denge ${nf(p.balance, 2)} · ${nf(p.pop, 0)} kişi`; note = v === "r11" ? "H3 r11 (~0,2 ha): 1–3 bina." : "H3 r9 (~10 ha): birkaç yapı adası.";
      }
      cellLayer = L.geoJSON(gj, { style: styleFn, onEachFeature: (f, l) => l.bindTooltip(tip(f.properties), { sticky: true }) }).addTo(map);
      if (v !== "bld") legendB("Yıllık konut elektriği dengesi"); else if (legend) map.removeControl(legend);
      const m = (SC.maup || []).find(x => x.scale.startsWith(v === "block" ? "Yapı" : "H3 " + v));
      $("scalenote").innerHTML = note + (m ? ` <b>Dengedeki nüfus payı: %${nf(100 * m.share_pop_in_B_ge_1, 0)}</b> · birim sayısı ${m.n_units} · toplam denge ${nf(m.total_balance, 3)} (her ölçekte aynı).` : "");
    }
    $("scale").addEventListener("change", e => drawScale(e.target.value));

    // energy sharing among neighbouring r10 cells (k = 1): greedy, surplus → deficit
    $("flowbtn").addEventListener("click", () => {
      if (flowLayer) { map.removeLayer(flowLayer); flowLayer = null; $("flowbtn").textContent = "Enerji akışını göster"; return; }
      const cells = {}; P.cells.features.forEach(f => { const p = f.properties; cells[p.cell] = { s: (p.energy_pv_kwh || 0) - (p.energy_demand_res_kwh || 0) }; });
      const flows = []; let deficit = 0, covered = 0;
      Object.entries(cells).filter(([, c]) => c.s < 0).sort((a, b) => a[1].s - b[1].s).forEach(([id, c]) => {
        let need = -c.s; deficit += need;
        h3.gridDisk(id, 1).filter(n => n !== id && cells[n] && cells[n].s > 0).sort((a, b) => cells[b].s - cells[a].s).forEach(n => {
          if (need <= 0) return; const q = Math.min(need, cells[n].s); cells[n].s -= q; need -= q; covered += q; flows.push([n, id, q]); });
      });
      const mx = Math.max(...flows.map(f => f[2]), 1);
      flowLayer = L.layerGroup(flows.map(([a, b, q]) => L.polyline([h3.cellToLatLng(a), h3.cellToLatLng(b)], { renderer: L.svg(), className: "flow", color: css("--sun"), weight: 1 + 6 * Math.sqrt(q / mx), opacity: 0.9 })
        .bindTooltip(`${nf(q / 1000, 0)} MWh/yıl paylaşım`))).addTo(map);
      $("flowbtn").textContent = "Akışı gizle";
      $("scalenote").innerHTML = `Komşu altıgenler arası yıllık paylaşım (k = 1, açgözlü dağıtım): ${flows.length} akış, ${nf(covered / 1e6, 2)} GWh. Açığı olan hücrelerin açığının <b>%${nf(100 * covered / Math.max(deficit, 1), 0)}</b>'i komşu fazlasıyla karşılanıyor.`;
    });

    // drawable project site: exact sum over buildings whose centroid falls inside
    const cen = {}; P.buildings.features.forEach(f => { const r = f.geometry.coordinates[0]; let x = 0, y = 0; r.forEach(p => { x += p[0]; y += p[1]; }); cen[f.properties.id] = [y / r.length, x / r.length]; });
    const inside = (pt, poly) => { let c = false; for (let i = 0, j = poly.length - 1; i < poly.length; j = i++) {
      const [yi, xi] = poly[i], [yj, xj] = poly[j]; if (((yi > pt[0]) !== (yj > pt[0])) && (pt[1] < (xj - xi) * (pt[0] - yi) / (yj - yi) + xi)) c = !c; } return c; };
    $("drawbtn").addEventListener("click", () => { window.__pedxDrawing = true; verts = []; if (siteLayer) map.removeLayer(siteLayer); $("drawend").hidden = false;
      $("siteout").innerHTML = "<p class='note'>Haritaya tıklayarak köşeleri ekleyin, sonra “Çizimi bitir”.</p>"; });
    map.on("click", ev => { if (!window.__pedxDrawing) return; verts.push([ev.latlng.lat, ev.latlng.lng]);
      if (tmpLine) map.removeLayer(tmpLine); tmpLine = L.polyline(verts, { color: css("--sun"), weight: 2, dashArray: "4 3" }).addTo(map); });
    $("drawend").addEventListener("click", () => {
      window.__pedxDrawing = false; $("drawend").hidden = true; if (tmpLine) { map.removeLayer(tmpLine); tmpLine = null; }
      if (verts.length < 3) { $("siteout").innerHTML = "<p class='note'>En az üç köşe gerekir.</p>"; return; }
      siteLayer = L.polygon(verts, { color: css("--sun"), weight: 3, fillOpacity: 0.08 }).addTo(map);
      let n = 0, pv = 0, pop = 0;
      Object.entries(cen).forEach(([id, c]) => { if (inside(c, verts) && SC.building[id]) { n++; pv += SC.building[id][0]; pop += SC.building[id][1]; } });
      const dem = pop * d, B = dem > 0 ? pv / dem : null, A = pv / (u * eta * Y);
      const lat0 = verts[0][0] * Math.PI / 180, R = 6371008.8;
      let ar = 0; verts.forEach((p, i) => { const q = verts[(i + 1) % verts.length]; ar += (p[1] * q[0] - q[1] * p[0]); });
      const area = Math.abs(ar) / 2 * (Math.PI / 180) ** 2 * R * R * Math.cos(lat0);
      const uNeed = A > 0 ? dem / (A * eta * Y) : null, cut = Math.max(0, 1 - A * prm.roof_utilization.high * eta * Y / Math.max(dem, 1e-9));
      $("siteout").innerHTML = `<div class="verdict ${B >= 1 ? "ok" : "warn"}"><b>Çizilen saha: denge ${nf(B, 2)}</b> ${B >= 1 ? "≥ 1, yerinde dengede" : "< 1"}</div>
        <table class="kv"><tr><td>Alan</td><td>${nf(area / 1e4, 2)} ha</td></tr><tr><td>Bina · taban alanı</td><td>${n} · ${nf(A / 1e4, 2)} ha</td></tr>
        <tr><td>Nüfus (dasimetrik)</td><td>${nf(pop, 0)} kişi</td></tr><tr><td>Konut talebi · çatı FV</td><td>${nf(dem / 1e6, 2)} · ${nf(pv / 1e6, 2)} GWh/yıl</td></tr>
        <tr><td>Gereken çatı kullanımı</td><td>%${nf(100 * uNeed, 0)} ${uNeed <= prm.roof_utilization.high ? "(sınır içinde)" : "(sınırı aşıyor)"}</td></tr>
        <tr><td>%${nf(100 * prm.roof_utilization.high, 0)} çatıyla gereken talep azaltımı</td><td>%${nf(100 * cut, 0)}</td></tr></table>
        <p class="note">Toplam binalardan kesin hesaplandı: denge = Σ çatı FV / Σ (nüfus × ${nf(d, 0)} kWh). Sahanın içi ağırlık merkezine göre.</p>`;
    });
  }

  // ---------- global atlas: total PED score (K-049) — learned from real PEDs, exact contributions, closed-form inverse
  let atlasLayer = null, atlasLegend = null, siteMarker = null;
  function initAtlas(bnd) {
    const AT = P.atlas;
    if (!AT || typeof h3 === "undefined") {
      $("atlasnote").textContent = AT ? "H3 kütüphanesi yüklenemedi; atlas için internet bağlantısı gerekir." : "Atlas verisi yok (python scripts/build_atlas.py).";
      $("mode").value = "caf"; setMode("caf", bnd); return;
    }
    const M = AT.model, B = M.coef, ib = M.features.indexOf("log_energy_balance");
    const sig = x => 100 / (1 + Math.exp(-x));
    const logitOf = z => M.intercept + z.reduce((a, v, i) => a + v * B[i], 0);
    AT.cities.forEach((c, i) => { const o = document.createElement("option"); o.value = i;
      o.textContent = `${c.city} · ${c.site}${c.is_ped ? "" : " (aday, PED değil)"}`; $("city").appendChild(o); });
    $("city").value = String(AT.cities.length - 1);
    const SC = ["#f7fbff", "#deebf7", "#c6dbef", "#9ecae1", "#6baed6", "#4292c6", "#2171b5", "#08519c", "#08306b"];
    const BR = [5, 10, 20, 30, 40, 50, 65, 80];
    const colOf = v => { let i = 0; while (i < BR.length && v >= BR[i]) i++; return SC[i]; };
    const tiles = L.tileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap katkıcıları" });

    function drawCity() {
      const c = AT.cities[+$("city").value];
      c.logits = c.logits || c.cells.map(r => logitOf(r[4]));
      const sorted = c.logits.slice().sort((a, b) => a - b);
      c.pctOf = l => { let lo = 0, hi = sorted.length; while (lo < hi) { const m = (lo + hi) >> 1; sorted[m] < l ? lo = m + 1 : hi = m; } return lo / sorted.length; };
      if (atlasLayer) map.removeLayer(atlasLayer);
      const feats = c.cells.map((r, i) => ({ type: "Feature", properties: { i },
        geometry: { type: "Polygon", coordinates: [h3.cellToBoundary(r[0], true)] } }));
      atlasLayer = L.geoJSON({ type: "FeatureCollection", features: feats }, {
        style: f => { const isSite = c.cells[f.properties.i][0] === c.site_r9;
          return { color: isSite ? css("--sun") : "#334", weight: isSite ? 3 : 0.3, fillOpacity: 0.72, fillColor: colOf(sig(c.logits[f.properties.i])) }; },
        onEachFeature: (f, layer) => {
          layer.bindTooltip(`PED skoru ${nf(sig(c.logits[f.properties.i]), 0)}`, { sticky: true });
          layer.on("click", ev => { L.DomEvent.stopPropagation(ev); showCell(c, f.properties.i); });
        } }).addTo(map);
      if (siteMarker) map.removeLayer(siteMarker);
      siteMarker = L.circleMarker([c.lat, c.lon], { radius: 7, color: css("--sun"), weight: 3, fillOpacity: 0 })
        .bindTooltip(`${c.site}${c.is_ped ? " · gerçek PED sahası" : " · aday"}`, { permanent: false }).addTo(map);
      map.fitBounds(atlasLayer.getBounds(), { padding: [8, 8] });
      $("atlasnote").innerHTML = `${c.country || "—"} · konut elektriği ${nf(c.kwh_per_capita, 0)} kWh/kişi · FV ${nf(c.pv_yield, 0)} kWh/kWp · ${nf(c.cells.length)} aday saha. ` +
        `${c.is_ped ? "Gerçek PED sahası" : "Aday saha"} (turuncu halka) tam noktasında: skor <b>${nf(c.site_score, 0)}</b>, kent içi yüzdelik <b>${nf(100 * c.pctOf(logitOf(c.site_z)), 0)}</b>. Altıgenler kendi merkezlerindeki ~28 ha'lık sahayı puanlar.`;
      if (atlasLegend) map.removeControl(atlasLegend);
      atlasLegend = L.control({ position: "bottomleft" });
      atlasLegend.onAdd = () => { const d = L.DomUtil.create("div", "legend");
        d.innerHTML = `<b>Toplam PED skoru</b> <span class="note">0–100</span><div class="bar" style="background:linear-gradient(90deg,${SC.join(",")})"></div>
          <div class="ticks"><span>0</span><span>40</span><span>80+</span></div><div class="note">Gerçek PED'lerden öğrenildi · kent dışarıda AUC ${nf(M.auc_loco, 2)}</div>`; return d; };
      atlasLegend.addTo(map);
      const si = c.cells.findIndex(r => r[0] === c.site_r9);
      if (si >= 0) showCell(c, si);
    }

    function inverse(c, r, target) {
      const p = S.provenance.params, u0 = p.roof_utilization.value, umax = p.roof_utilization.high, e0 = p.module_efficiency.value, emax = p.module_efficiency.high;
      const L0 = logitOf(r[4]), sdb = c.stats.log_energy_balance.sd, bb = B[ib];
      if (sig(L0) >= target) return { ok: true, txt: "Saha zaten hedefin üstünde." };
      const t = Math.min(Math.max(target, 0.01), 99.99) / 100, need = Math.exp((Math.log(t / (1 - t)) - L0) * sdb / bb);
      const fu = Math.min(need, umax / u0), fe = Math.min(need / fu, emax / e0), fd = Math.min(need / (fu * fe), 1 / (1 - 0.5)), got = fu * fe * fd;
      const z2 = r[4].slice(); z2[ib] += Math.log(got) / sdb;
      return { ok: got >= need * (1 - 1e-9), u: u0 * fu, eta: e0 * fe, cut: 1 - 1 / fd, Bneed: r[1] * need, Bafter: r[1] * got, after: sig(logitOf(z2)) };
    }

    function siteReport(c, r) {
      const REP = AT.report || [], v = r[5];
      if (!REP.length || !v) return "";
      c.repSorted = c.repSorted || REP.map((_, j) => c.cells.map(x => x[5] && x[5][j]).filter(x => x !== null && x !== undefined && isFinite(x)).sort((a, b) => a - b));
      const pct = (j, x) => { const a = c.repSorted[j]; if (x === null || x === undefined || !a.length) return null; let lo = 0, hi = a.length;
        while (lo < hi) { const m = (lo + hi) >> 1; a[m] < x ? lo = m + 1 : hi = m; } let up = lo; while (up < a.length && a[up] === x) up++; return (lo + up) / 2 / a.length; };
      const P = REP.map((m, j) => ({ m, x: v[j], p: pct(j, v[j]) }));
      const ranked = P.filter(o => o.p !== null && o.m.key !== "nonosm_share");
      const top = ranked.slice().sort((a, b) => b.p - a.p).slice(0, 4), low = ranked.slice().sort((a, b) => a.p - b.p).slice(0, 4);
      const sections = [...new Set(REP.map(m => m.section))];
      const bar = o => o.p === null ? "<span class='note'>veri yok</span>" :
        `<div class="track" title="kent içi yüzdelik ${nf(100 * o.p, 0)}"><div class="fill" style="left:0;width:${100 * o.p}%;background:var(--geo)"></div><div class="mid"></div></div>`;
      return `<h3 style="margin-top:14px">Kapsamlı saha raporu (PED + kentsel dönüşüm)</h3>
        <p class="note">Her gösterge bu ~28 ha'lık sahada ölçüldü; çubuk, kent içindeki yüzdeliği gösterir (orta çizgi = kent medyanı).</p>
        <div class="grid2" style="gap:8px"><div class="cell"><b>Kentinde öne çıkan</b><br>${top.map(o => `${o.m.label} <span class="mono">%${nf(100 * o.p, 0)}</span>`).join("<br>")}</div>
        <div class="cell"><b>Kentinde geride kalan</b><br>${low.map(o => `${o.m.label} <span class="mono">%${nf(100 * o.p, 0)}</span>`).join("<br>")}</div></div>` +
        sections.map(sec => `<h4 style="margin:12px 0 4px;font-family:var(--display)">${sec}</h4><div class="bars">` +
          P.filter(o => o.m.section === sec).map(o => `<div class="row" style="grid-template-columns:170px 1fr 86px"><span title="${o.m.ref || ""}">${o.m.label}</span>${bar(o)}<span class="mono" style="font-size:11.5px">${o.x === null || o.x === undefined ? "—" : nf(o.x, Math.abs(o.x) < 10 ? 2 : 0)} ${o.m.unit}</span></div>`).join("") + "</div>").join("") +
        `<p class="note">Kaynaklar: Overture (yerler, arazi kullanımı, altyapı), Meta HRSL, ESA WorldCover, Sentinel-2, Landsat, Copernicus DEM, Wikidata (CC0), Wikimedia Commons. Çevrim içi yorumlar (Google vb.) kullanım koşulları ve KVKK nedeniyle kullanılmaz.</p>`;
    }

    function showCell(c, i) {
      const r = c.cells[i], z = r[4], L0 = logitOf(z), sc = sig(L0);
      const con = M.features.map((f, k) => [f, z[k] * B[k]]).sort((a, b) => Math.abs(b[1]) - Math.abs(a[1])).slice(0, 8);
      const mx = Math.max(...con.map(x => Math.abs(x[1])), 1e-9);
      const p = S.provenance.params, thr = c.kwh_per_capita / (p.roof_utilization.value * p.module_efficiency.value * c.pv_yield);
      const isSite = r[0] === c.site_r9;
      const tg = +($("tgt") ? $("tgt").value : 70);
      const inv = inverse(c, r, tg);
      $("atlasout").innerHTML = `<div class="verdict ${sc >= 50 ? "ok" : sc >= 20 ? "warn" : "bad"}"><b>PED skoru ${nf(sc, 0)}/100</b> · kent içi yüzdelik ${nf(100 * c.pctOf(L0), 0)}
        ${isSite ? `<br><span class="note">Bu, ${c.is_ped ? "gerçek PED sahası" : "aday saha"}: ${c.site}</span>` : ""}</div>
        <table class="kv"><tr><td>Yıllık konut elektriği dengesi</td><td>${nf(r[1], 2)} ${r[1] >= 1 ? "≥ 1 (yerinde dengede)" : "< 1"}</td></tr>
        <tr><td>Kişi başı çatı tabanı / eşik</td><td>${nf(r[3] / Math.max(r[2], 1), 1)} / ${nf(thr, 1)} m²</td></tr>
        <tr><td>Nüfus (HRSL) · taban alanı</td><td>${nf(r[2], 0)} kişi · ${nf(r[3] / 1e4, 1)} ha</td></tr></table>
        <h3 style="margin-top:10px">Skoru oluşturanlar (kesin logit katkıları)</h3><div class="bars">` +
        con.map(([f, v]) => `<div class="row"><span title="${f}">${M.labels_tr[f] || f}</span><div class="track"><div class="mid"></div><div class="fill" style="background:${v >= 0 ? "var(--ok)" : "var(--bad)"};left:${v >= 0 ? 50 : 50 - 50 * Math.abs(v) / mx}%;width:${50 * Math.abs(v) / mx}%"></div></div><span class="mono">${v >= 0 ? "+" : ""}${nf(v, 2)}</span></div>`).join("") +
        `</div><p class="note">Katkı = katsayı × kent içi z-puanı; toplamları + sabit = logit; skor = 100·σ(logit). Yaklaşık değil, kesin.</p>
        <h3 style="margin-top:10px">Tersine analiz: hedef skora ne gerekir?</h3>
        <label for="tgt">Hedef skor: <b id="tgtv">${tg}</b></label><input id="tgt" type="range" min="10" max="95" step="5" value="${tg}" style="width:100%">
        ${inv.txt ? `<p>${inv.txt}</p>` : `<table class="kv"><tr><td>Çatı kullanımı</td><td>%${nf(100 * p.roof_utilization.value, 0)} → <b>%${nf(100 * inv.u, 0)}</b></td></tr>
          <tr><td>Modül verimi</td><td>%${nf(100 * p.module_efficiency.value, 0)} → <b>%${nf(100 * inv.eta, 1)}</b></td></tr>
          <tr><td>Talep azaltımı (yenileme)</td><td><b>%${nf(100 * inv.cut, 0)}</b></td></tr>
          <tr><td>Denge</td><td>${nf(r[1], 2)} → ${nf(inv.Bafter, 2)} (gereken ${nf(inv.Bneed, 2)})</td></tr>
          <tr><td>Ulaşılan skor</td><td><b>${nf(inv.after, 0)}</b> ${inv.ok ? "✓" : "— enerji kaldıraçları yetmiyor"}</td></tr></table>
          ${inv.ok ? "" : "<p class='note'>Skoru taşıyan öteki özellikler (yapı örtüsü, yeşil, su, işlev) kentsel dönüşüm ölçeğinde değişiklik gerektirir.</p>"}`}
        <p class="note">Sıra: önce çatı kullanımı (en fazla %${nf(100 * p.roof_utilization.high, 0)}), sonra modül verimi (en fazla %${nf(100 * p.module_efficiency.high, 0)}), sonra talep azaltımı (en fazla %50). Kapalı biçim; arama yok.</p>`;
      $("atlasout").insertAdjacentHTML("beforeend", siteReport(c, r));
      $("tgt").addEventListener("input", e => { $("tgtv").textContent = e.target.value; });
      $("tgt").addEventListener("change", () => showCell(c, i));
    }

    $("city").addEventListener("change", drawCity);
    $("mode").addEventListener("change", e => setMode(e.target.value, bnd));
    function setModeAtlas(on) {
      if (on) { if (cellLayer) map.removeLayer(cellLayer); if (legend) map.removeControl(legend); tiles.addTo(map); drawCity(); }
      else { if (atlasLayer) map.removeLayer(atlasLayer); if (atlasLegend) map.removeControl(atlasLegend); if (siteMarker) map.removeLayer(siteMarker); map.removeLayer(tiles); }
    }
    window.__pedxAtlasMode = setModeAtlas;
    setMode($("mode").value, bnd);
  }
  function setMode(m, bnd) {
    $("atlaspanel").hidden = m !== "atlas"; $("cafpanel").hidden = m !== "caf";
    if (window.__pedxAtlasMode) window.__pedxAtlasMode(m === "atlas");
    if (m === "caf") { draw(sel.value); map.fitBounds(bnd.getBounds(), { padding: [10, 10] }); }
  }

  // ---------- on-demand assessment anywhere (K-040): needs `make api`; otherwise disabled, never faked
  const API = "http://127.0.0.1:8766";
  let liveLayer = null;
  function initLive() {
    fetch(API + "/health").then(r => r.json()).then(h => {
      $("livestatus").textContent = `API hazır (pedx ${h.version}). Caferağa dışında haritada herhangi bir yere tıklayın; dünya üzerinde gezinmek için uzaklaştırın.`;
      map.on("click", ev => { if (!window.__pedxDrawing) live(ev.latlng.lat, ev.latlng.lng); });
    }).catch(() => {
      $("livestatus").innerHTML = "Yerel API çalışmıyor. Açmak için terminalde <code>make api</code>; bu sayfa yalnız önceden hesaplanmış Caferağa'yı gösterir.";
    });
  }
  function live(lat, lon) {
    const k = $("livek").value;
    $("liveout").innerHTML = `<p class="note">${lat.toFixed(4)}, ${lon.toFixed(4)} için açık veriler çekiliyor (Overture, HRSL, GHS-POP, PVGIS, UNSD, OSM)…</p>`;
    fetch(`${API}/score?lat=${lat}&lon=${lon}`).then(r => r.json()).then(r => {
      const e = r.explain || {}, inv = r.inverse || {};
      const box = document.createElement("div");
      box.className = "verdict " + (e.score >= 50 ? "ok" : e.score >= 20 ? "warn" : "bad");
      box.innerHTML = `<b>Toplam PED skoru ${nf(e.score, 0)}/100</b> (gerçek PED'lerden öğrenildi, AUC ${nf((r.model || {}).auc_loco, 2)})<br>` +
        (inv.feasible === false ? `<span class="note">Hedef 70 için enerji kaldıraçları yetmiyor (en fazla ${nf(inv.score_after, 0)}).</span>` :
         inv.levers && inv.levers.roof_utilization ? `<span class="note">Hedef 70: çatı %${nf(100 * inv.levers.roof_utilization.to, 0)}, verim %${nf(100 * inv.levers.module_efficiency.to, 1)}, talep −%${nf(100 * inv.levers.demand_cut_share.to, 0)}</span>` : "");
      $("liveout").prepend(box);
    }).catch(() => {});
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
