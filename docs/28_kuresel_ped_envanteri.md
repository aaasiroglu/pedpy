# 28 — Küresel PED envanteri: tanım, kaynaklar, ilk sonuç (K-068)

Amaç: dünyada, sınırı çizilmiş bir bölgede enerji üretip bunu bölgeye ve çevresine veren bütün proje
sahalarını — kendine PED desin ya da demesin — konum ve sınırlarıyla tek bir açık veri tabanında toplamak.

## 1. Envantere ne girer

Bir saha şu dört koşulu kaynakla belgeliyorsa girer:

1. **Sınırlı bölge:** tek bina değil, birden çok yapıdan oluşan tanımlı bir alan.
2. **Yerel yenilenebilir üretim:** üretim bölgenin içinde ya da ona bağlı.
3. **Denge hedefi:** yıllık net sıfır ya da pozitif enerji hedefi, ya da çevreye enerji verme.
4. **Belgelenmiş kaynak:** proje belgesi, veri tabanı kaydı ya da hakemli yayın.

Üç sınıf tutulur ve karıştırılmaz:

| Sınıf | Tanım | Örnek kaynak |
|---|---|---|
| A | Kendine PED diyen | PED Booklet "PED projects", PED veritabanı, Horizon PED projeleri |
| B | PED'e doğru / PED ile ilgili | PED Booklet "Towards PED", PED veritabanı "PED relevant" |
| C | PED demeyen benzerler | Net sıfır enerji mahalleleri, artı enerji yerleşimleri, sıfır enerji toplulukları (Avrupa dışı dahil) |

Her kayıt için tutulan alanlar: ad, kent, ülke, proje, sınıf, durum, yapı türü (yeni / mevcut / karma),
büyüklük, arazi kullanımı, finansman, kaynak, konum, sınır geometrisi, sınırın kaynağı ve güven düzeyi.

## 2. Kaynaklar ve durum

| # | Kaynak | Kapsam | Durum |
|---|---|---|---|
| 1 | PED Booklet, Şubat 2020 (Gollner vd., JPI Urban Europe) | 61 proje, Avrupa | **Alındı** (`data/inventory/ped_booklet_2020.csv`) |
| 2 | PED veritabanı (PED-EU-NET, Annex 83, JPI UE; pedeu.net/map) | PED, PED ile ilgili, PED laboratuvarı | Site bu ortamdan bağlantıyı kesiyor; dışa aktarımın elle indirilmesi gerekiyor |
| 3 | IEA EBC Annex 83 raporları (STA–STD) | Vaka çalışmaları | Erişim açık; sırada |
| 4 | Horizon 2020 / Horizon Europe öncü projeleri | ATELIER, SPARCS, MAKING-CITY, POCITYF, +CityxChange, RESPONSE, syn.ikia ve diğerleri | Sırada; mevcut 16 saha buradan |
| 5 | Norveç ZEN pilotları | 9 pilot bölge | Bir kısmı 1'de; sırada |
| 6 | Avrupa dışı benzerler (C sınıfı) | ABD, Japonya, Çin, Avustralya, Körfez | Kaynak taraması yapılacak |

## 3. İlk sonuç: PED Booklet (61 proje)

- **Sınıf:** 29 PED, 32 "PED'e doğru".
- **Durum:** PED'lerin 2'si işletmede, 19'u uygulamada, 8'i planlamada (Şubat 2020 itibarıyla).
- **Ülke:** 19 ülke; en çok Norveç, İtalya, Finlandiya, İsveç, Hollanda. Türkiye'den Kadıköy (MAKING-CITY).
- **Yapı türü kaynaktan geliyor:** yeni yapı, mevcut mahalle ya da karma. Bu, K-064'te elle yaptığım
  etiketlemenin yerini alır.
- **Finansman ve arazi kullanımı** alanları da kaynakta var; ekonomi sorusunun (AS4) ilk verisi.

### Konum ve sınır (`data/inventory/ped_sites_global.csv`, `.geojson`)

Saha adı yalnız booklet metninde geçiyorsa kabul edildi, sonra OpenStreetMap'te arandı (63 kayıt; iki
projede birden çok saha var).

| Düzey | Kayıt | Anlamı |
|---|---|---|
| Adı taşıyan OSM alanı | 13 | Aday sınır var |
| Yalnız nokta | 21 | Yer belli, sınır yok |
| Yalnız kent | 25 | Booklet saha adı vermiyor ya da OSM'de yok |
| Bulunamadı | 4 | Ada, ülke programı, yazım farkı |

**Asıl bulgu: OSM'deki adlı alan, proje sınırı değildir.**

| Saha | OSM alanı | Booklet'teki proje alanı |
|---|---|---|
| Kaukovainio (Oulu) | 490 ha | 4 ha |
| Pietralata (Roma) | 587 ha | 7 ha |
| Brunnshög (Lund) | 387 ha | 225 ha |
| Buiksloterham (Amsterdam) | 43 ha | iki yapı adası, 28.500 m² kat alanı |
| Hunziker Areal (Zürih) | 3,8 ha | 4,1 ha |

13 aday sınırdan yalnız biri (Hunziker Areal) proje alanıyla örtüşüyor. PED çoğu zaman adını taşıdığı
mahallenin küçük bir parçası. Bu, danışmanın "sınır tanımlamak zor" tespitinin sayısal karşılığı ve
AS1'in gerekçesi: sınır, mahalle adından değil proje belgesinden ve yapı adalarından çıkarılmalı.

## 4. Sıradaki adımlar

1. Kaynak 3–5'i aynı şemaya ekle; yinelenenleri birleştir (hedef: 100+ kayıt, A ve B sınıfı).
2. PED veritabanı dışa aktarımını al (elle indirme ya da proje ekibinden).
3. Her saha için proje belgesindeki sınır haritasını bul; yapı adası kümesi olarak sayısallaştır.
   Önce booklet'te alanı ha olarak verilen sahalar (alan, sayısallaştırmanın denetimi olur).
4. C sınıfı için kaynak taraması ve aynı dört koşulla eleme.

## 5. Yeniden üretim

```bash
pdftotext -layout PED-Booklet-Update-Feb-2020_2.pdf booklet.txt
```

```bash
python scripts/build_ped_inventory.py booklet.txt
```

```bash
python scripts/geocode_ped_inventory.py booklet.txt
```

Booklet: https://jpi-urbaneurope.eu/wp-content/uploads/2020/06/PED-Booklet-Update-Feb-2020_2.pdf
