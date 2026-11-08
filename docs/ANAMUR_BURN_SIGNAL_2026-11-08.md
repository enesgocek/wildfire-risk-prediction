# Anamur Belensazak olay sonrası değişim incelemesi — 8 Kasım 2026

Önceki örtü incelemesinin ardından, 11 Temmuz 2023 yerel tarihli
Anamur vakasında Sentinel-2 ile olay sonrası spektral değişim
arandı. Arama alanı ilk VIIRS merkezinin 700 m çevresiyle
sınırlandı. OGM'nin olay kaydı yaklaşık başlangıç saati ve
5,15 hektar zarar gören alan bildiriyor. İnceleme bu vakayla
sınırlı ve yangın tespitinden bağımsız bir örnekleme sayılmaz.
[Önceki örtü incelemesi](ANAMUR_PREEVENT_COVER_2026-11-08.md) ·
[Mersin OBM olay kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx).

## Karşılaştırma

Sentinel-2 L2A'nın 20 m B8A ve B12 bantları aynı yerel piksel
ızgarasında okundu. Beş ürünün özgün XML metadata değerleriyle
sayısal değerler yansımaya çevrildi. Tüm ürünlerde nicemleme
10.000, iki bant için ofset −1.000. Yalnız SCL 4 ve 5 olan,
geçerli ve pozitif bant toplamına sahip kara pikselleri kullanıldı.
NBR, iki bandın farkının toplamına bölünmesiyle hesaplandı.
Önceki NBR'den sonraki NBR çıkarılarak dNBR bulundu.
[Sentinel-2 işleme açıklaması](https://sentiwiki.copernicus.eu/web/s2-processing) ·
[EUMETSAT Sentinel-2 NBR yöntemi](https://fire.trainhub.eumetsat.int/docs/figure2345_Sentinel-2.html).

Üç çift aynı göreli yörünge içinde karşılaştırıldı. R021'de
7 → 12 ve 7 → 17 Temmuz, R064'te 5 → 15 Temmuz. Üç çiftte
de kullanılabilir ortak alan 700 m çevrede 3.620/3.844 piksel
(%94,2). Doğal renk görüntüsünde 12 Temmuz'da görülen koyu
yama, üç dNBR karşılaştırmasında da aynı yerde belirgin.
[Doğal renk ve dNBR karşılaştırması](../outputs/reports/dataset/anamur_burn_signal_v1/20261108T032607Z_71a08960/change_review.png).

| Üç çiftte ortak dNBR alt sınırı | En büyük bitişik değişim | İlk VIIRS merkezine en kısa mesafe | Yamanın CORINE 243 payı |
| --- | ---: | ---: | ---: |
| 0,10 | 6,40 ha | 163 m | %99,5 |
| 0,15 | 5,68 ha | 163 m | %99,5 |
| 0,20 | 4,96 ha | 172 m | %100,0 |

Eşikler duyarlılık denemesidir. Piksel kenarlarından bağlantılı
alan, ortak geçerli piksellerde ölçüldü. CORINE payı için her
yamanın 20 m piksel sınırı eş alanlı harita sistemine çevrildi
ve yerel CORINE 2018 hücreleriyle kesiştirildi. Kod 243 tarım ve
doğal örtüyü birlikte içeriyor. OGM'nin 5,15 hektarlık toplamı
denenen alan aralığına düşüyor. Bu yakınlık, resmî hasar
sınırının veya tarım ve orman paylarının geometrik doğrulaması
için yeterli değil.
[CORINE sınıf tanımları](https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/html/index.html) ·
[Mersin OBM olay kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx).

Üç eşiğin hepsinde Belensazak mevki noktası ve 23.23 UTC'deki
iki NOAA-20 merkezinden biri yamanın içinde. İlk S-NPP merkezi
kenardan 163–172 m uzakta. Ölçülen mesafe tespit merkezine
ait. VIIRS pikselinin alanını ve fiziksel tutuşma noktasını
belirlemiyor. Spektral değişim, olayın etkilediği alanı
araştırmak için güçlü bir aday sağlıyor. Başlangıç konumu,
ilk örtü ve olay kayıt kapsamı açık. Olay sonrası veriler
bu incelemede kullanıldı ve tahmin girdisine alınmadı. Hedef
boş, günlük gözlem `unknown` ve etiket izinleri kapalı.

Üretici `python scripts/quality/review_anamur_burn_signal.py`.
Beş yerel kesit özeti, kalibrasyon, piksel sayıları ve bitişik
alanlar ikinci bir hesapla doğrulandı. 39 ilgili test geçti.
Yerel dizin `outputs/reports/dataset/anamur_burn_signal_v1/20261108T032607Z_71a08960`.
`readback.json` SHA-256 `9ea89af5489310a5baa5f089605f87746a469ec54331a191f3b64f7ba59043e9`.
`cover_overlap.json` SHA-256 `6ec5ffe267aabf3b815693803a6653f07da46fe7814f73587541893ed12cd803`.
