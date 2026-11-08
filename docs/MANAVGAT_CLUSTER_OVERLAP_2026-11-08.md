# Manavgat başlangıçları ve ortak uydu kümeleri — 8 Kasım 2026

Manavgat 2021'e ait yedi başlangıç zamanı ve yaklaşık harita konumu
korundu. Bu incelemede, bildirilen farklı başlangıçlar için bulunan
uydu tespitlerinin aynı kümeye düşüp düşmediği sınandı. Kaynakta ilk
müdahale saatleri ayrı tutuldu. [Birincil yayın](https://doi.org/10.3390/ijgi14020065) · [Önceki yerel denetim](MANAVGAT_REPORTED_STARTS_2026-11-08.md).

## Sonuç

Sabit 2021 kataloğunda, her vaka için aynı UTC hedef gününde ve
bildirilen başlangıçta veya sonrasında kalan tespitler 1, 2 ve 3 km
yarıçaplarda seçildi. Önceki 21 satır sayımı tekrar elde edildi.
Her tespit mevcut dokuz mesafe/zaman gruplamasına bağlandı. Bir
vaka çiftinde en az bir ortak küme varsa çift o ayarda bir kez sayıldı.
Kümenin en erken kayıtlı zamanı, bildirilen başlangıçla ayrıca kıyaslandı.

| Yaklaşık merkez çevresi | Tespit bulunan vaka | Dokuz ayar arasında ortak kümesi olan vaka çifti sayısı |
| --- | ---: | ---: |
| 1 km | 4 / 7 | 2–6 |
| 2 km | 6 / 7 | 6–15 |
| 3 km | 6 / 7 | 6–15 |

**Vaka 3 ve 4.** OGM kökenli saatler 28 Temmuz 20.45 ve 22.30 UTC,
aralarında 105 dakika var. 1 km çevrede sırasıyla yedi ve iki uydu
tespiti bulundu. İki vaka için bulunan tespit satırları birbirinden
farklıydı. Buna rağmen dokuz ayarın tamamında her iki
vakanın tespitleri aynı tek kümeye girdi. Bu çakışma 2 ve 3 km
denemelerinde de sürdü. Dokuz ayarın dördünde ortak kümede iki
başlangıçtan daha erken uydu kaydı yoktu. Dolayısıyla daha erken
kayıtları elemek bu iki başlangıcı her ayarda ayırmaya yetmedi.

2 km'de 2.000 m bağlantı mesafesi kullanan üç ayarın her birinde,
tespit bulunan altı vakanın tamamı aynı tek kümeye düştü. Bu ölçüm
yalnız Manavgat 2021'deki yedi kayıt, yaklaşık konumlar ve dokuz
keşif ayarıyla sınırlıdır. Fiziksel olay kimlikleri ve başlangıç
konumları doğrulanmayı bekliyor.

## Açık geometri kaynakları

Açık ArcGIS servisindeki 30, 31 ve 32 numaralı katmanların şemaları
okundu. Üçü de poligon katmanı. 30 ve 31'de yıllık sayı ve alan
alanları, 32'de ad, işletme şefliği ve alan alanları var. Bu katmanlarda
başlangıç saati ve özgün nokta alanı bulunmadı. [ArcGIS servis dizini](https://services-eu1.arcgis.com/YmubkUgykRVQRzwG/arcgis/rest/services/YananOrmanAlanlari_WFL1/FeatureServer).

Antalya İRAP'ında 2020 başlangıç noktaları haritada gösteriliyor.
2023 tarihli kule görünürlüğü çalışması, 2008–2021 için ORBİS'ten
alınan 2.504 konumu tarif ediyor. Bu iki yayında Manavgat'ın yedi
kayıt saatiyle eşlenebilen özgün nokta tablosu bulunmadı.
Kule çalışmasında 2.504 vakanın 535'inin orman dışında başlayıp ormana
yayıldığı belirtiliyor. Bu ayrım, başlangıç örtüsünü yanan alan
örtüsünden ayrı denetlememizle uyumlu. [Antalya İRAP, Şekil 2.17](https://antalya.afad.gov.tr/kurumlar/antalya.afad/Tasarim/IRAP/Antalya-IRAP_2022.pdf) · [Coşgun vd., 2023](https://doi.org/10.3390/fire6080305).

## Araştırma kararı ve doğrulama

Ortak kümesi olan kaynak kayıtları ayrı referanslar olarak kalır.
Kümeleri tek tek yangın kimliği olarak kullanmak için özgün başlangıç
geometrisi, kaynak olay kimliği ve olay gruplama kuralı gerekir.
Günlük gözlem durumu `unknown`, pozitif ve negatif etiket izinleri
`false`. Hiçbir gruplama ayarı nihai yöntem olarak seçilmedi.

Üretici `python scripts/quality/audit_manavgat_cluster_overlap.py`.
Yerel makbuz `outputs/reports/dataset/manavgat_cluster_overlap_v1/20261108T023504Z_5c2435a8/readback.json`.
SHA-256 `e1365de5c839a772d23fc388d63f851cbf0251bc6eec4e484586226e0c10e2a1`.
Vaka 3 ve 4'ün ayrı tespit anahtarları ve dokuz ataması ikinci yöntemle
doğrulandı. 43 ilgili test geçti.
