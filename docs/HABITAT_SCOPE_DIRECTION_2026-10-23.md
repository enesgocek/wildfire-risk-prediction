# Orman ve çalılık kapsam kararı ve nokta çevresi tanısı

23 Ekim 2026. Araştırmacı ana bitki örtüsü kapsamını **orman ve çalılık**
olarak seçti. Tarım/yerleşim eşleşmeleri ayrı incelemede korunacak; karar
2017 haritasına dayanan otomatik etiket veya kalıcı dışlama yetkisi vermiyor.
Karar, gözlem yeterliliği veya bağımsız olay doğrulaması değildir.

Yeni kayıt `configs/habitat_scope_direction_v1.json`: araştırma yönü bellidir;
orman/çalılık için asgari alan oranı veya nokta çevresi yarıçapı seçilmemiştir.
Önceki su kapsamı, ilk hücre, özellik, bulut paketleri ve etiket protokolleri
değiştirilmedi. Özellikle karışık hücrelerin tamamı korunuyor.

## Tamamlanan sınırlı inceleme

[Önceki 21 adayın](CANDIDATE_COVER_CONTEXT_2026-10-23.md) aynı 25 farklı
ilk tespit noktası, korunmuş 2017 örtü rasterinde incelendi. 25 noktanın
dördünün merkezi haritada orman/çalı, 21'inin merkezi başka sınıftadır.
Buradaki **21 nokta**, önceki **21 aday hücre-gün** paydasıyla aynı birim değildir.

Tek merkez pikselinin sınıfına dayanarak dışlama yapmanın etkisini görmek
için 100/250/500 metre çevreler **keşif amaçlı** karşılaştırıldı. Bu mesafeler
literatürden kabul edilmiş hata sınırları veya tespit pikselinin gerçek
ayak izi değildir; örnekleri tutma/silme kuralı seçmek için kullanılmadı.

| Keşif mesafesi | Merkezi orman/çalı olmayan nokta paydası | Çevresinde harita orman/çalı piksel merkezi bulunan |
|---|---:|---:|
| 100 m | 21 | 1 |
| 250 m | 21 | 8 |
| 500 m | 21 | 9 |

Bu sonuçlar dokuz yeni orman yangını veya dokuz yanlış merkez sınıfı değildir.
500 metre çevrede orman bulunması yangının orada başladığını göstermez;
bulunmaması da sonraki yılda orman bulunmadığını veya yangın olmadığını kanıtlamaz.
Çevre büyüyünce daha çok noktada orman bulunması, büyük çevrenin daha doğru
olduğu anlamına gelmez. Sonuca göre yarıçap seçilmedi.

## Yöntem ve sayısal sınır

EPSG:4326 boylam/enlem noktaları mevcut EPSG:3857 rasterine açık xy sırasıyla
dönüştürüldü. 30–45 derece enlem çalışma zarfında geniş bir arama kutusu
içindeki harita piksel merkezleri okundu; gerçek çevre üyeliği WGS84
elipsoidi üzerindeki nokta–piksel-merkezi mesafesiyle hesaplandı. Web Mercator
metresi doğrudan yer mesafesi sayılmadı. Mevcut 25 noktada arama penceresi
raster kenarında kesilmedi ve bütün çevrelerde en az bir sınıflı merkez bulundu.

Payda **sınıfı bilinen harita piksel merkezi sayısıdır**, tam kesişim alanı
veya VIIRS piksel alanı değildir. Pikselin çevreye kısmen girmesi alan ağırlığıyla
hesaplanmadı. Sınıfsız/maskeli yerler ayrı sayılır; payda sıfır olursa örtü
oranı eksik kalır, sıfır yapılmaz. Rasterin 2017 sınıfı güncel örtü veya
doğal orman doğruluğu değildir; önceki harita/konum/odunsu tarım sınırlamaları sürer.

## Doğrulamalar ve çıktı

Dokuz yeni vaka dahil **44 ilgili test** geçti; bütün depo testi değildir.
Komşu çalılık görünürken merkez tarım sınıfının korunması, geodesic mesafe,
artan çevrede iç içe sayımlar fakat azalıp artabilen oranlar, bilinmeyen
payda, geçersiz yarıçap/CRS/çalışma zarfı sınandı. İlk geliştirme denemesinde
matris çarpımı için görülen uyarı yeni kodda açık dönüşüm hesabıyla giderildi;
son testte Future/Deprecation/PendingDeprecation uyarıları hata sayıldı.
Üç yeni Python dosyasında lint/format geçti. Önceki dondurulmuş kod değişmedi.

Sonuç `outputs/reports/dataset/cover_neighborhood_v1/20261022T212508Z_648490a3/`.
Dizin UTC, çalışma tarihi Türkiye takvimidir. Readback SHA-256
`e73cd495e5d4b575693b0ca0a9490f7f5de64774495960d98757c19d661504f4`.
Dokuz doğrudan girdi başta/sonda aynı; iki CSV'nin tam içerik geri okuması
ve manifestle üç çıktı hash'i kontrol edildi. `point_neighborhoods.csv`
75 nokta×mesafe satırı, `center_group_summary.csv` ayrı sınıf özetidir.

## Sonraki yöntem işi

Orman/çalılık yönü kabul edildi; şimdi bu yönün uygulanabilir bir habitat
protokolüne dönüştürülmesi gerekiyor. Gerçek piksel desteği, komşu örtü
karışımı, tarihsel harita değişimi ve bulunabilen olay kanıtı birlikte
değerlendirilmeli. Merkez tarım/yerleşim diye kayıt silmek veya çevrede
tek orman pikseli var diye 1 atamak uygun kabul edilmedi.

Yalnız bu amaçlı pilotta hesaplanan oranlar bütün adayların hata oranı veya
nihai kapsam büyüklüğü değildir. Yeni etiket/dışlama protokolü gerekçeli
seçeneklerle ayrıca sunulacak. Bağımsız olay referansı ve yeterli gözlem
açıkları bu kapsam kararıyla kapanmadı. Gözlem unknown, etiket izinleri false;
2024/2025, bulut işi, eğitim ve nihai birleştirme açılmadı.
