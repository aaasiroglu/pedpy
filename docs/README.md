# pedpy: Tez Planlama ve Araştırma Notları

Bu klasör, `pedpy` kütüphanesi ve ona bağlı yüksek lisans tezinin **planlama, literatür, karar ve ilerleme notlarını** tutar. Kural: *önce yaz, sonra kodla.* Koda geçilen her adımın gerekçesi, literatür bağlantısı ve kabul ölçütü burada önceden kayda geçer.

| Dosya | İçerik | Ne zaman güncellenir? |
| --- | --- | --- |
| **[PROJE_DOSYASI.md](PROJE_DOSYASI.md)** | **Hande Hoca için ana belge:** amaç, sistem mimarisi, kullanılan veriler, işlem adımları, sonuçlar, proje yönetimi | Her sürümde |
| **[00_TEZ_PUSULASI.md](00_TEZ_PUSULASI.md)** | **Tek sayfa, tek doğruluk kaynağı:** tez cümlesi, 3 soru, 3 katkı, 3 yayın, kapsam, durum, kritik yol | Her karar sonrası |
| *(arşiv)* [01_proje_degerlendirmesi.md](arsiv/01_proje_degerlendirmesi.md) | Mevcut önerinin (README, mimari, global ölçekleme notları) eleştirel değerlendirmesi; bilimsel riskler ve düzeltmeler | Kapsam değiştiğinde |
| [02_literatur_haritasi.md](02_literatur_haritasi.md) | Tema bazlı literatür haritası; künyesi doğrulanmış kaynaklar; boşluk analizi | Her yeni kaynakta |
| *(arşiv)* [03_arastirma_tasarimi.md](arsiv/03_arastirma_tasarimi.md) | Araştırma soruları, hipotezler, katkılar; XAI + Graf + NLP + ÇKKDS entegrasyonu; deney tasarımı | Danışman görüşmesinden sonra |
| *(arşiv)* [04_yol_haritasi.md](arsiv/04_yol_haritasi.md) | Adım adım iş paketleri, çıktılar, kabul ölçütleri, tez bölümleriyle eşleşme | Her faz sonunda |
| [05_karar_gunlugu.md](05_karar_gunlugu.md) | Teknik ve metodolojik kararlar (ADR biçiminde) | Her kararda |
| [06_acik_sorular.md](06_acik_sorular.md) | Sizin ve danışmanınızın yanıtlaması gereken sorular | Yanıt geldikçe |
| [08_tersine_analiz.md](08_tersine_analiz.md) | Tersine (reçeteleyici) analiz: hedefler, paylaşılan kodun incelemesi, uygulanan matematik, doğrulama | Tersine modül değiştikçe |
| *(arşiv)* [09_v0_sunum.md](arsiv/09_v0_sunum.md) | **Hande Hoca'ya v0 sunumu**: yapılanlar, ilk sonuçlar, dürüst bulgular, istenen kararlar | Her sürümde |
| [10_sprint_plani.md](10_sprint_plani.md) | 2 haftalık sprintler (Kasım 2026 – Haziran 2027), yayın planı, görüşme notları | Her sprint sonunda |
| [13_sistem_mimarisi.md](13_sistem_mimarisi.md) | **Sistem mimarisi**: gereksinimler, L0–L6 katmanları, veri sözleşmesi, karar motoru, sosyal katman, ROI | Mimari değiştikçe |
| [15_proje_elverislilik.md](15_proje_elverislilik.md) | **Mekânsal uygunluktan proje elverişliliğine:** literatür (megaproje, XAI ile inşaat riski, kentsel dönüşüm, PED başarı faktörleri), çerçeve, karar ve doğrulama | — |
| [14_acik_kaynak_atlasi.md](14_acik_kaynak_atlasi.md) | **Açık kaynak atlası**: insan, bina, sokak, kent, enerji, çevre, görüntü, ekonomi, sosyal ve PED etiketleri; lisans, durum, öncelik | Her yeni kaynakta |
| [LOCAL_SETUP.md](LOCAL_SETUP.md) | Yerelde kurulum ve çalıştırma | — |
| [11_veri_kaynaklari.md](11_veri_kaynaklari.md) | **Veri kaynağı kütüğü**: her katmanın kaynağı, lisansı, rolü (G1 veya G2) ve gerekçesi; araştırma günlüğü; eksikler | Her yeni veri katmanında |
| [12_onceki_calismalar.md](12_onceki_calismalar.md) | Tasarım projesi (2024) ve YL önerisinin (2025) değerlendirmesi; teze bağlanması | — |
| [07_kirilganlik_analizi.md](07_kirilganlik_analizi.md) | Kırmızı takım incelemesi: kırılgan, anlamsız ve değersiz bileşenler; tut, düzelt, bırak kararları; "kült araç" konumlandırması | Her büyük tasarım değişikliğinde |
| [references.bib](references.bib) | Doğrulanmış BibTeX kayıtları (Zotero'ya aktarılabilir) | Her yeni kaynakta |

## Doğrulama işaretleri

Literatür notlarında her kaynak için şu işaretler kullanılır:

- ✅ **Doğrulandı**: başlık, yazar, dergi, cilt ve DOI en az iki bağımsız katalogda eşleşti.
- ⚠️ **Kısmi**: kaynak var, ama künyenin bir kısmı (DOI, sayfa, yazar adı) teyit edilmedi.
- ❓ **Doğrulanmadı**: kaynak önerildi ama henüz bulunamadı; **tezde kullanılmadan önce** teyit edilmeli.

> Not: Yapay zekâ asistanlarından gelen metinlerdeki kaynaklar (önceki sohbetlerden aktarılan README dahil) **otomatik olarak doğru kabul edilmez.** Her kaynak burada tek tek işaretlenir.
