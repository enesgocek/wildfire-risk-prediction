# Urla–Karaburun ve Aydıncık–Pembecik ilk tespitlerinde örtü — 8 Kasım 2026

Bu inceleme, [iki olayın açık kaynak karşılaştırmasını](PUBLIC_EVENT_CONTEXT_2026-11-08.md) tamamlar. Sorusu, ilk uydu noktalarının çevresinde hangi örtü bağlamının görüldüğü ve son yangın sınırıyla süzmenin hangi noktaları kaybettireceğidir.

## Yöntem

- Dokuz gruplama ayarında, eşleşen adayların en erken UTC zamanındaki tüm katalog noktalarının birleşimi alındı. Son yangın sınırı yalnız karşılaştırma için kullanıldı. Her merkezin CORINE 2018 sınıfı 100 m rasterdan okundu. Ürün 2017–2018 referans dönemini temsil eder. [Copernicus CORINE 2018](https://land.copernicus.eu/en/products/corine-land-cover/clc2018).
- Beş ilk hücrenin her birinde, o hücredeki ilk noktaların yerel UTM ortalamasına en yakın gerçek katalog noktası seçildi. Eşitlikte katalog kimliği kullanıldı. Merkezin 250 m çevresi görsel inceleme alanıdır. Bu yarıçap uydu ayak izini veya yangın sınırını temsil etmez.
- Olay gününün 00.00 UTC kesiminden önceki 30 günde, inceleme alanını kapsayan Sentinel-2 L2A sahneleri arandı. Önce sahne bulut oranı %20 veya altında olanlar, ardından kesime yakınlık ve katalog kimliği sıralandı. İki farklı gün seçildi. Sahne bulut oranı sıralama ölçütüdür. Yerel görüntü kalitesi 20 m sahne sınıflandırma katmanından (SCL) ayrıca ölçüldü. [Sentinel-2 L2A kataloğu](https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a).

## Bulgular

| Vaka | İlk merkez ve hücre | Merkezde CORINE 2018 | Son sınırın dışında kalan |
|---|---:|---|---:|
| Urla–Karaburun, 14 Ağustos 2021 | 12 / 1 | 9 sklerofil örtü (323), 2 orman–çalılık geçişi (324), 1 deniz (523) | 1 merkez |
| Aydıncık–Pembecik, 15 Temmuz 2021 | 34 / 4 | 19 iğne yapraklı orman (312), 5 orman–çalılık geçişi (324), 3 sklerofil örtü (323), 6 doğal örtüyle karışık tarım (243), 1 karma tarım deseni (242) | 3 merkez, bunlardan biri ayrı bir ilk hücrenin tek merkezi |

Beş temsili merkez için 10 pencerenin tamamı okundu. Aydıncık görüntüleri 7 ve 12 Temmuz, Urla görüntüleri 5 ve 10 Ağustos 2021 tarihlidir. Altı pencerede seçili yerel SCL kalite işaretlerinden en az biri görüldü. Bulut veya sirüs iki pencerenin inceleme çevresine girdi.

- **Aydıncık, C641_R864.** Temsili merkezin eski harita sınıfı doğal örtüyle karışık tarım. İki RGB kesitinde de merkezin çevresi açık zemin ve bitki örtüsü karışımı görünümünde. SCL, her iki tarihte aynı 489 piksel merkezinin yaklaşık %32'sini bitki örtüsü olarak sınıflandırdı. Komşu iki temsili noktada bu oran tarihe göre yaklaşık %82–87 aralığındaydı.
- **Aydıncık, C640_R864.** Son sınır dışında kalan tek noktalı hücre. Temsili merkez eski haritada karma tarım deseninde. İki kesitte de yeşil alanlar, yollar ve parlak açık yüzeyler birlikte görünüyor. Nokta ortak aday kaydında tutuldu.
- **Urla, C511_R910.** Temsili merkez eski haritada sklerofil örtüde. İki tarihte SCL bitki örtüsü oranı yaklaşık %50 ve %75. Bu değişimin nedeni bu kesitlerle belirlenemiyor. Eski haritada denize düşen ayrı bir ilk merkez var. Sentinel-2 pencere seçimi, bu deniz merkezini kapsamıyor. Sahil kenarındaki bu aykırılık için VIIRS piksel ayak izi ve kıyı geometrisi ayrıca gerekli.

SCL bitki örtüsü oranı, ağaç/çalılık türünü veya orman oranını ölçmez. Eski harita, ilk tespit merkezi ve olay öncesi görüntü farklı mekânsal ve zamansal ölçümler sağlar. İki vaka için kesin başlangıç konumu ve olay bazında pozitif doğrulama açık kalır. Son sınır dışında kalan veya örtüsü karışık noktalar adaydan çıkarılmadı. Günlük gözlem durumu `unknown`, pozitif ve negatif etiket izinleri `false` olarak kayıtlı.

## Yerel doğrulama

Çalıştırma `20261107T233443Z_6e504fcb` (UTC, yerel tarih 8 Kasım). İlk 46 CORINE pikseli ayrıca satır ve sütun üzerinden yeniden okundu. 17 girdi özeti, 20 TIFF dosya özeti, iki görüntü tarihi kuralı, 10 SCL paydası ve inceleme görselinin özeti doğrulandı. Görüntü işleme ile ilgili 37 test geçti.

Yerel çıktı klasörü `outputs/reports/dataset/public_event_cover_v1/20261107T233443Z_6e504fcb`. İnceleme görseli `cover_review.png`, ölçüm ve kaynak kayıtları `readback.json` dosyasındadır. Okuma kaydının SHA-256 özeti `aa0ad0e753d04be890837c7f5e46f7d2ac03ba1ecf9c6e183016946f30bfe38e`.
