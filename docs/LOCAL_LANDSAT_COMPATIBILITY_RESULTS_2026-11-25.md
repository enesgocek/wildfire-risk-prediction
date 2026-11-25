# Yerel Landsat uyumluluk provası — 25 Kasım 2026

## Sonuç ve araştırmaya katkısı

Araştırmacının somut tek hücrelik A önerisinden sonraki “devam edelim”
talimatıyla sınırlı prova yürütüldü. Açık bir A harfi yanıtı uydurulmadı;
yürütme kararı ayrı `configs/local_landsat_compatibility_pilot_execution_v1.json`
dosyasında bağlandı. Önceki öneri ve eski bilimsel üreticiler değiştirilmedi.

**Herkese açık Landsat arşivinden gerekli görüntü parçalarını okuyup yerel
NDVI/NDMI özeti hesaplamak mümkün oldu.** GCP işi, ücretli işlem/abonelik,
hesap oluşturma veya yeni kullanıcı girişi kullanılmadı. Bu, eksik 2024
bitki örtüsü girdisi için somut bir yerel yol gösterir; tüm 2024 girdisinin
hazır olduğu veya eski yöntemle eşdeğerliğin kabul edildiği anlamına gelmez.

Bir hücrede yedi sahne ve dört pencere özeti tamamlandı. İlk bağlantı
denemesi dahil 738,802465 saniye, önceki denemeler dahil 13.028.791 bayt
HTTP yanıt gövdesi ve 204 HTTP denemesi kaydedildi. Özgün 900 saniye,
134.217.728 gövde baytı, 512 istek ve 20 tekil sahne sınırları aşılmadı.
Bayt sayacı ağ başlıkları/TLS dahil fiziksel toplam trafik ölçümü değildir.

## Kapsam ve hesap

Hücre `E6933_5K_V1_C517_R913`; 1 Temmuz 2022 ve 1 Temmuz 2024 UTC.
Her biri için yalnız `[T−30 gün,T)` ve `[T−60 gün,T)` kullanıldı.
Landsat 8 / Collection 2 Level-2 / Tier 1; red, NIR, SWIR1 ve iki kalite
bandı okundu. Eski ölçek/offset, [0,1] yansıma aralığı, QA dışlama maskesi
191, QA_RADSAT=0 ve iki indeksin pozitif paydası korundu. Sahne bulut
yüzdesine göre yeni eleme yapılmadı. Kalite sonrası tümü eksik sahneler
listede kaldı; negatif veya sıfır bitki örtüsü diye yazılmadı.

Yerel hesapta her sahnenin maskelenmiş indeksleri en yakın komşuyla
aday EPSG:6933/30 m gride taşındı; piksel medyanı sonrası tam düzlemsel
piksel/AOI kesişim alanıyla özetlendi. Global sıfır başlangıcı bir grid
varsayımıdır. Eski Earth Engine üreticisi CRS ve ölçek belirtiyor;
eski affine başlangıcının ve sınır rasterlemesinin aynı olduğu kanıtlanmadı.

## Ölçülen sayısal karşılık

İndeksler birimsizdir; fark yerel eksi eski özet olarak verilir. İki 2022
satırı aynı hücre/tarih için önceki yerel CSV karşılığıdır. 2024 satırları
yalnız tanısal hesap; eski eş karşılık veya model puanı değildir.

| Yıl / pencere | Sahne | Yerel NDVI | Eski NDVI | NDVI farkı | Yerel NDMI | Eski NDMI | NDMI farkı |
|---|---:|---:|---:|---:|---:|---:|---:|
| 2022 / 30 gün | 2 | 0,279612237 | 0,279732277 | −0,000120040 | 0,095849133 | 0,095772362 | +0,000076771 |
| 2022 / 60 gün | 4 | 0,265941237 | 0,266094260 | −0,000153023 | 0,088025123 | 0,088040175 | −0,000015053 |
| 2024 / 30 gün | 2 | 0,315285773 | — | — | 0,093204324 | — | — |
| 2024 / 60 gün | 3 | 0,315285773 | — | — | 0,093204324 | — | — |

2022 destek alanı yerel/eski: 30 günde 10.536.036,437 / 10.540.461,176 m²;
60 günde 11.354.293,840 / 11.357.682,353 m². Yerel AOI toplam alanı
12.426.392,220 m²; piksel kesişim ağırlıkları bu alanı 1e−5 m² içinde
tamamlıyor. Bu alan kontrolü eski gridin aynı olduğunu kanıtlamaz.

2024'te 16 Mayıs ve 17 Haziran sahnelerinde aday gridde kalite sonrası
kullanılabilir piksel yok. 1 Haziran sahnesinde 12.056 geçerli aday grid
pikseli, AOI ile kesişen 11.838 piksel var. Bu nedenle iki pencere aynı
geçerli sahneye dayanıyor; değerler birbirinden kopyalanmadı. Aday grid
piksel sayısı ile AOI içi destek alanı farklı birimlerdir.

2022'de dört kaynak çekim kimliği eski 64 hücrelik batch sahne birleşiminde
bulundu. En büyük saat farkı 0,000431 saniye; eski milisaniye hassasiyetiyle
uyumlu. Bu kontrol batch'in yalnız bu hücredeki kesin sahne kümesini veya
iki sağlayıcının işlenmiş piksel içeriğini birebir doğrulamaz.

## Ayrı denetim ve çevrimdışı fark incelemesi

Ayrı denetleyici girdi/çıktı hash'lerini, kapanmış log kimliğini, önceki
denemelerden taşınan bayt/istek hesabını, sahne/pencere zamanını, ortak
indeks maskelerini ve aralıklarını kontrol etti. Dört özet kayıtlı piksel
dizilerinden skaler alan ağırlıklı toplamlarla yeniden hesaplandı; indeks
farkı 1e−12 altında. Bu ayrı hesap, ham kalite bayrağının bağımsız saha
doğrulaması veya tüm COG dosyalarının yeniden indirilmesi değildir.

Google belgeleri ağırlıklı bölge indirgemesinde yaklaşık piksel kapsamı
ve 8 bit/256 düzeyli kesişim ağırlığı açıklıyor. Yerel tam geometrik alan
bu işlemle kendiliğinden eşdeğer değildir.
[Bölge indirgeme](https://developers.google.com/earth-engine/guides/reducers_reduce_region),
[ağırlıklı hesap](https://developers.google.com/earth-engine/guides/reducers_weighting).

Mevcut dizilerle, yeni ağ erişimi olmadan tam alan/255 düzeyine en yakın/
255 düzeyine aşağı yuvarlama olmak üzere üç varsayım ve dört özet için
12 tanısal sonuç hesaplandı. Tam alan sonucuna göre en büyük indeks
değişimi 0,000004310087. İki basit yaklaşım 2022 farkını kapatmadı.
Bunlar Earth Engine rasterlemesinin yeniden üretimi değildir; en iyi
eşleşen yöntem seçilmedi, eşdeğerlik toleransı sonuca bakarak belirlenmedi.
Farkın kesin kaynağı; grid, rasterleme, yeniden örnekleme ve işleme
soy zinciri birlikte açıklığa kavuşmadan atfedilmiyor. Grafik asistan
tarafından görüntü olarak incelendi; insan örtü/yangın yorumu sayılmadı.

Güncel kodla 40 ilgili test geçti: beş yeni aktarım/QA testi ve mevcut
bitki örtüsü/nihai birleştirme kapısı testleri. Ayrı süreçte yerel aktarım
aracısının çalışması gerçek yedi sahnelik koşuda gözlendi; 40 birim testin
bu süreç davranışını bağımsız kapsadığı iddia edilmez. Yeni dosyalarda
Ruff kontrolü geçti. Eski bilimsel üreticilerin hash'leri değişmedi.

## Teknik kesinti ve korunmuş kayıtlar

İlk bağlantı denemesi gövde almadan bağlantı hatası verdi. Sonraki küçük
metadata yanıtında sorgu alanı taşıyan bağlantıları kaydetmeme koruması
durdu; ham yanıt/token diske yazılmadı. İlk raster koşusu, yerel HTTP
aracısı ile GDAL aynı süreçteyken Windows bağlantı kesilmeleri nedeniyle
asistan tarafından sonlandırıldı. Bu deneme başarı sayılmadı; kaynak kod
anlık görüntüsü, ağ sayacı ve kesinti makbuzu kendi klasöründe korundu.

Aracı ayrı sürece taşındı. Aynı özgün başlangıç saati ve taşınan 2.264.215
bayt/28 deneme ile devam edildi; bütçe sıfırlanmadı veya büyütülmedi.
Yedi sahne bu teknik devamda tamamlandı. GIL kaynaklı kesinti açıklaması
kanıtlanmış neden diye yazılmıyor. Erişim tokenları yalnız bellekte kaldı;
JSON/günlük kontrolünde imzalı sorgu içeriği görülmedi. Başarılı koşunun
ana hesap ve aktarım kodu hash ile sabittir; rapor için değiştirilmedi.
Yeni hash-bağlı yedi kod/yürütme dosyasının Git index kopyaları özgün
dosyalarla bayt olarak eşleştirildi. Bu dosyalarda otomatik satır sonu
dönüşümü kapatıldı; deneyde kullanılan dosya içerikleri değiştirilmedi.

## Makbuzlar ve yeniden izleme

Aşağıdaki klasörler `outputs/reports/dataset/` altındadır; her hash ilgili
`readback.json` dosyasınındır. Büyük veri/ikili dosyalar Git'e eklenmez.

| İş | Klasör | SHA-256 |
|---|---|---|
| Başarılı sınırlı koşu | `local_landsat_compatibility_v1/20261125T092425Z_afc36fb5` | `2ff8413250d1d56cb8ac87eb66cdd29663362c798f55e6cab60b34865e9242d5` |
| Ayrı çevrimdışı denetim | `local_landsat_compatibility_audit_v1/20261125T092809Z_3454247d` | `371d61701eee785a21d9d809fac3f5a173f060023bc230b83770fe9690cf3460` |
| Alan duyarlılığı/grafik | `local_landsat_diagnostic_review_v1/20261125T093305Z_71e6f651` | `17882ef8158adc50be5c9d2427f50770fd70a7490e9d736f9852df9ebc90f34d` |

Kaynak CSV SHA `4447b22f3cdf74baea9562e424e49094b6a5648c8c87d49c4f7c119f78649115`;
kaynak manifest SHA `7401a16570676e7c468a53a4fabfc079cdb3330735a7af24e96f1cab2e43daa3`.
Başarılı koşunun kapanmış log SHA
`ee73f06809330e25e6d6c67259eacf3b32ed5d61a4fa81e782c0b45bb9a06c61`.
Süresi bitmiş yürütme kaydı yeniden başlatılacak bir iş değildir.

## Sonraki somut yöntem kararı

Tek hücre sonucu üzerine bütün 2024 için üretim yapmak yeterince
gerekçeli değil. **Öneri A:** aynı yerel hesapla dört ilden birer hücrede
1 Temmuz 2022 / 30–60 gün karşılaştırması. Sekiz pencere karşılığı;
amaç coğrafi farkı ölçmek, eşdeğerlik veya özellik kabulü vermek değil.

Örnekler, AOI kesri ≥0,9 ve eski iki penceresi sonlu hücrelerde il
bazında sıralı kimliklerin üst ortanca kaydıdır. İl alanı hücrenin iç
temsil noktasından belirlenir; seçimin yangın doğruluğu/temsiliyeti
iddiası yok. Örtü veya yangın puanına göre en iyi örnek seçilmedi.

| İl | Hücre | Uygun örnekleme havuzu |
|---|---|---:|
| Antalya | C594/R879 | 749 |
| İzmir | C526/R902 | 388 |
| Mersin | C652/R878 | 585 |
| Muğla | C550/R879 | 429 |

Yeni edinimin toplam sınırı ilk ağ denemesinden itibaren 900 saniye,
268.435.456 yanıt gövdesi baytı (256 MiB), 2.048 HTTP denemesi ve
40 tekil sahne. Örnekleme/indirme önerisi hazır; henüz yürütülmedi.
Ücret/giriş gereksiniminde veya eksik/aşırı bütçeli listede durulur;
tamamlanmayan hücre geçerli özellik sayılmaz. 2023/2024/2025 yeni
bilimsel değerleri, model kurma/tahmin, yeni etiket ve final merge yok.

Hazırlık `landsat_spatial_compatibility_preparation_v1/20261125T093449Z_263452e2`;
buradaki `proposal.json` SHA
`7d191d1c49ae6c6b353fe2819cda40963591ee42f3107ea40269896b7dc363a7`.
Öneri `execute_authorized=false`; bu rapor yürütme onayı değildir.
İlk hazırlıkta boş eski değerleri sayıya çevirme kontrolü durdu; boşlar
dışarıda tutularak seçim tamamlandı, önceki başarısızlık sonuç sayılmadı.

**Alternatif B:** yeni raster edinimi açmadan bu tek hücrelik sonucu
saklamak ve mevcut araştırma teslimiyle sınırlı kalmak. Bu, eksik 2024
NDVI/NDMI girdisini çözmez; meteorolojiyle ayrı yardımcı sınama başka
model kapsamıdır. Yeni coğrafi edinim kararı araştırmacıya bırakılır.

İki yönde de mevcut S/U/model, `daily_observation_status=unknown`,
`negative_label_permitted=false` ve kapalı 2025 korunur. Yerel Landsat
yolunun çalışması olay kimliği, gözlem veya PU'dan gerçek yeni yangına
aktarımın doğrulanması değildir. Nihai etiketli veri birleştirme onayı yok.
