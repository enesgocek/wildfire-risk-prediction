# Anamur vakasında olay öncesi örtü incelemesi — 8 Kasım 2026

Belensazak vakasında ilk VIIRS tespiti, Belensazak mevki noktası ve
Aşağı Kükür yer referansı ayrı incelendi. Her birinde 250 m çevre
kullanıldı. İlk tespitten sonra aynı keşif kümesinde gelen dört
merkez de CORINE 2018 üzerinde ölçüldü. Çevreler birer inceleme
alanıdır. Uydu pikselinin kesin sınırı veya tutuşma konumu olarak
kullanılmadı. [Olay ve katalog karşılaştırması](JULY_2023_START_CONTEXT_2026-11-08.md).

## İki tarihli Sentinel-2 incelemesi

Tahmin kesimi 10 Temmuz 2023 00.00 UTC. Üç çevreyi birlikte
kapsayan 19 katalog adayı içinden 7 ve 5 Temmuz tarihli iki
Sentinel-2 L2A sahnesi seçildi. 10 m doğal renk ve 20 m SCL
kesitleri doğal çözünürlüklerinde okundu. SCL'deki genel bitki
örtüsü payı, çevre içindeki piksel merkezlerinin payıdır.
Bulut ve sirüs işareti altı çevre-tarih kesitinde sıfır.
5 Temmuz Aşağı Kükür kesitindeki 14 piksel koyu alan veya gölge
olarak işaretlendi. Bu 14 piksel çevrenin %2,9'unu oluşturuyor.
[Sentinel-2 L2A kataloğu](https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a).

| 250 m çevre | SCL genel bitki örtüsü, 7 / 5 Temmuz | CORINE 2018 alan payı | Görsel ön yorum |
| --- | ---: | --- | --- |
| İlk VIIRS tespiti | %68,2 / %72,9 (491 piksel) | %54,3 geçiş orman/çalılığı (324), %45,7 tarım-doğal örtü mozaiği (243) | Düzensiz yeşil örtü, açık şeritler ve parsel benzeri desenler iki tarihte de görülüyor. |
| Belensazak mevki noktası | %81,8 / %82,0 (488 piksel) | %75,8 tarım-doğal örtü mozaiği (243), %24,2 iğne yapraklı orman (312) | Yeşil yamalar, açıklıklar ve yol kenarında parlak yapı benzeri izler iç içe. |
| Aşağı Kükür yer referansı | %89,6 / %88,3 (489 piksel) | %59,1 geçiş orman/çalılığı (324), %40,9 iğne yapraklı orman (312) | Doğu kesiminde daha sürekli yeşil örtü, batıda açık ve yerleşim benzeri parçalar var. |

İki ölçümün tarihleri, çözünürlüğü ve sınıf tanımları farklı.
SCL yeşil bitki örtüsünü işaretler. CORINE 243 sınıfı tarım ve
doğal örtüyü aynı harita sınıfında tutar, bu çevrede ikisinin
ayrı yüzdelerini vermez. Dolayısıyla 243 payı tarım yüzdesi
olarak alınmadı. Görsel yorumlar asistanın ön değerlendirmesidir.
[CORINE sınıf tanımları](https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/html/index.html) ·
[Altı Sentinel-2 kesiti](../outputs/reports/dataset/anamur_preevent_cover_v1/20261108T032025Z_2e88ca22/cover_review.png).

## Tespit noktası seçiminin etkisi

Beş tespit merkezi aynı 5 km hücresinde. Her merkezin 250 m
çevresinde CORINE 312 ve 324 kodlarının toplam alan payı
**%3,7 ile %70,8** arasında değişiyor. Örneğin 23.23 UTC'deki
iki NOAA-20 tespitinden birinin çevresinde bu pay %64,6,
diğerinde %3,7. Bu fark, aynı uydu kümesinde dahi farklı
merkezlerin yerel örtü hakkında farklı sonuç verdiğini gösteriyor.
Küme içindeki örtü farkından yayılım rotası çıkarılmadı.

İlk tespit çevresinde karışık örtü değerlendirmesi iki tarihte
de desteklendi. Yayımlanan vaka kaydında etkilenen bahçe ve
orman ayrı belirtiliyor. İlk tutuşmanın hangi örtüde olduğu
ve özgün başlangıç konumu açık kaldı. Vaka öncelikli kaynak
incelemesinde duruyor. Hedef boş, günlük gözlem `unknown`,
pozitif ve negatif etiket izinleri kapalı.
[Mersin OBM olay kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx).

Üretici `python scripts/quality/review_anamur_preevent_cover.py`.
12 raster özeti, altı SCL sayımı ve yedi CORINE çevre payı
ayrı yöntemle kontrol edildi. 83 ilgili test geçti.
Yerel makbuz
`outputs/reports/dataset/anamur_preevent_cover_v1/20261108T032025Z_2e88ca22/readback.json`.
SHA-256 `ef0333fce0b9339f6559d7f4516f9f49b2f03b73c59f52a9da2b24b88b5f1c0e`.
