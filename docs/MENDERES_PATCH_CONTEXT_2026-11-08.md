# Menderes'te değişim alanı, örtü ve saha kaydı — 8 Kasım 2026

10 Temmuz 2023 vakasında, önceki Sentinel-2 denetimindeki iki çevrenin
en büyük değişim parçaları CORINE 2018, belediyenin mahalle sınırları
ve EFFIS yanık alanıyla karşılaştırıldı. Aynı 700 m çevreler ve üç dNBR
eşiği kullanıldı. CORINE sınıf payları, 100 m kaynak pikselleriyle
eşit alan projeksiyonunda gerçek alan kesişiminden hesaplandı.
[Önceki optik inceleme](MENDERES_BURN_SIGNAL_2026-11-08.md) ·
[CORINE sınıf sözlüğü](https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/html/index.html).

## Ölçülen örtü ve yanık alanı

| dNBR eşiği | Güneydeki değişim parçası | Güneyde iğne yapraklı orman (312) | Güneyde EFFIS kesişimi | Kuzeydeki değişim parçası | Kuzeyde EFFIS'e en kısa mesafe |
| --- | ---: | ---: | ---: | ---: | ---: |
| 0,10 | 39,88 ha | %96,3 | 38,85 ha | 10,88 ha | 5,06 km |
| 0,15 | 35,72 ha | %97,3 | 35,69 ha | 7,68 ha | 5,08 km |
| 0,20 | 29,60 ha | %97,5 | 29,58 ha | 3,20 ha | 5,08 km |

Kuzeydeki en büyük parçanın tamamı üç eşikte de CORINE 211
(sulanmayan ekilebilir arazi) içinde. Güneydeki kalan pay aynı
sınıfa ait. Kuzeyde 0,15 eşiğindeki parça iki VIIRS merkezinden
79 ve 91 m uzakta. Öncesi ve sonrası görüntülerde parsel desenleri
arasında belirgin koyulaşma var. CORINE 2018'in referans yılı ve
25 ha asgari haritalama birimi, 2023'te parça içindeki yerel
örtünün tamamını veya değişimin nedenini belirlemeye yetmiyor.
[Kuzey yakın planı](../outputs/reports/dataset/menderes_patch_context_v1/20261108T042450Z_308aaf99/north_patch_review.png) ·
[CORINE teknik özeti](https://land.copernicus.eu/en/products/corine-land-cover/?tab=technical_summary).

EFFIS sorgusunda bir poligon döndü. Kaynak kimliği **217014**,
kayıt alanı **416 ha**. Güneyde 12 tespit merkezinin dördü,
kuzeyde iki merkezin sıfırı poligon içinde veya sınırında.
Üç eşikteki altı parçadan yalnız güneydekiler poligonla
kesişiyor. EFFIS çizimi ile yerel dNBR hesabı ayrı ürünler.
EFFIS yöntemi Sentinel-2 ve VIIRS verilerinden yararlanabildiği
için bu uyum bağımsız saha doğrulaması olarak sayılmadı. Kuzeyde
kesişim olmaması küçük bir yangının yokluğunu göstermiyor.
Kaynağın tarih alanları özgün tutuşma saati olarak kullanılmadı.
[EFFIS yöntem ve kapsamı](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/rapid-damage-assessment).

## Yer adları ve müdahale kanıtı

10 Temmuz belediye meclisi tutanağında Menderes için Küner adı
geçiyor. İzmir Orman Bölge Müdürlüğü aynı tarih için Oğlananası
adını veriyor. Güncel belediye sınırında iki kuzey merkezi
Oğlananası Atatürk'te. 0,15 eşiğinde kuzey parçası bu mahallede,
güney parçasının %76,6'sı Altıntepe'de ve %23,4'ü Tekeli
Fevzi Çakmak'ta. Küner sınırı aynı eşikte güney parçasına
4,83 km ve kuzey parçasına 9,35 km uzaklıkta. Katmanın olay
tarihindeki sürümü doğrulanmadı. Bu adlar ve mesafeler özgün
başlangıç koordinatı sağlamıyor.
[Meclis tutanağı, 10 Temmuz 2023](https://www.izmir.bel.tr/YuklenenDosyalar/MeclisToplantiTutanak/23082023150057.pdf) ·
[İzmir Orman Bölge Müdürlüğü](https://www.ogm.gov.tr/izmirobm/haberler/sehidimiz-mustafa-gurpinar%E2%80%99i-torenle-ugurladik) ·
[Belediye mahalle katmanı](https://kentrehberi.izmir.bel.tr/arcgis/rest/services/Rehber/CbsRehberGeoSB/MapServer/126).

10 Temmuz 2023 belediye dosyasında Menderes için bir
orman/fidanlık, üç ot ve iki çöp müdahalesi var. Torbalı'da
bir orman/fidanlık ve bir ot müdahalesi var. Bu ilçe ve
gün toplamları kuzey parçasını belirli bir müdahaleye
bağlamıyor. Taranan açık saha kaynaklarında kuzey parçasına
konumuyla bağlanan ayrı bir kayıt bulunmadı.
[Belediye veri sözlüğü](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi/resource/f718e29e-0e3f-4b63-8019-e1920ca94330) ·
[Yayın kapsamı](IZMIR_DISPATCH_COVERAGE_2026-11-08.md).

Güneydeki yanık alanı adayına ek mekânsal destek kaydedildi.
Kuzey grubu tarımsal bağlamı ve belirsiz değişim nedeniyle
ayrı incelemede tutuluyor. İki grubun aynı fiziksel olaya
ait olup olmadığı, kuzeydeki değişimin nedeni ve gerçek
tutuşma konumu açık. İki grup için de hedef boş, günlük
gözlem durumu `unknown` ve etiket izinleri kapalı.

## Yeniden üretim ve kontrol

Üretici `python scripts/quality/audit_menderes_patch_context.py`.
Mahalle katmanı, 27,17–27,27° D ve 38,19–38,29° K zarfı
ile ayrı Küner poligonu (36884) için sorgulandı. EFFIS WFS
`ms:modis.ba.poly` sorgusunda 27,10–27,31° D ve 38,16–38,31° K
zarfı, 9–12 Temmuz 2023 tarih sınırları ve 100 kayıt tavanı
kullanıldı. Sunucunun bir kayıt bildiren sayımıyla poligon
yanıtı eşleşti. Kaynak dosyaları `sources/` altında saklandı.
[EFFIS WFS](https://maps.effis.emergency.copernicus.eu/effis) ·
[Önceki WFS biçim denetimi](PERIMETER_REFERENCE_REVIEW_2026-10-14.md).

Altı parça ayrı piksel bağlantı hesabıyla yeniden oluşturuldu.
CORINE payları kaynak sınıf poligonlarıyla, EFFIS geometrisi
eksen sırası açık belirtilen ikinci GML okumasıyla ve
müdahale sayımları ikinci Excel okuyucusuyla doğrulandı.
85 ilgili test geçti. Yerel çıktı
`outputs/reports/dataset/menderes_patch_context_v1/20261108T042450Z_308aaf99/readback.json`.
SHA-256 `ba4ec1b522a81e1077df9e1f3b8a5951370c6e01d67c1d8930ceddb8ece9c22d`.
