# Bitki örtüsü ve arazi özellikleri

Kayıt tarihi: 9 Ekim 2026. Uydu yangın gözlem kuyruğu devam ederken bağımsız
özellik hazırlığı yapıldı. Çalışma, geriye dönük aday özellikler ve bir bitki
örtüsü örneğidir; nihai model tablosu veya günlük bitki örtüsü serisi değildir.

## Veri ve yöntem

Mevcut 2017 Copernicus sınıflandırmasından hazırlanmış 2.899 hücrelik örtü
tablosu korundu. Orman, çalı, otsu bitki, tarım, yerleşim ve su sınıfı oranları
bu kaynağın sınıf alanı paylarıdır; piksel içindeki gerçek ağaç örtüsü yüzdesi
ile eş anlamlı değildir. Referans yılı 2017 olan ürünün Collection 3 sürümü
2020 kaynak kaydı taşıyor. Eski referans yılı, o tarihte yayımlanmış veri
olduğunu kanıtlamaz; geçmiş erişilebilirlik ve yardımcı veri zamanları açık
konudur. Aynı 2017 haritasının sonraki yıllarda eskimesi ayrıca sınırlamadır.
[Copernicus kaynak tanımı](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global).

Arazi kaynağı `USGS/SRTMGL1_003`, nominal 1 yay-saniyesi/yaklaşık 30 m
yükseklik verisidir. DEM boşlukları yardımcı kaynaklarla doldurulmuş olabilir.
`ee.Terrain.products`, bütün kaynak üzerinde çalıştırıldı; türev hesabından
önce hücre sınırında kırpma yapılmadı. Yükseklik, yükseklik standart sapması ve
eğim için piksel alanı integralleri hücrenin AOI içinde kalan bölümünde
özetlendi. Kaynak CRS ve piksel dönüşümü korundu.
[SRTM](https://developers.google.com/earth-engine/datasets/catalog/USGS_SRTMGL1_003)
· [Arazi türevleri](https://developers.google.com/earth-engine/apidocs/ee-terrain-products).

Bakı, derece ortalaması olarak kullanılmadı. Sıfırdan büyük eğimi bulunan
pikseller için `cos(bakı)` kuzey ve `sin(bakı)` doğu bileşenlerinin alan
ağırlıklı ortalaması alındı. Düz arazinin bakısı eksik bırakıldı. Hücrelerde
yönler birbirini dengeleyebileceğinden bu iki bileşenin birlikte yorumu gerekir.

Earth Engine sınır pikseli kesişim ağırlıklarını yaklaşık ve nicemlenmiş
hesaplar. Alan payı ham değer olarak tutuldu; bire zorlanmadı. GEE sınır/alan
modeli ile yerel EPSG:6933 alanının farkı, tek başına DEM veri boşluğunun
kanıtı sayılmadı. `%99–101` yakınlık bayrağı yalnız tanısal proje kontrolüdür;
model uygunluk eşiği değildir.
[Bölgesel hesaplama ve ağırlıklar](https://developers.google.com/earth-engine/guides/reducers_reduce_region).

## Statik sonuçlar

| Kontrol | Sonuç |
|---|---:|
| Hücre sayısı | 2.899 |
| Kalıcı ham arazi grubu | 91 |
| Arazi desteği olmayan hücre | 0 |
| Alan yakınlık kontrolünde işaretlenen hücre | 17 |
| İşaretli hücrelerin toplam AOI alanı | Yaklaşık 1,010 km² |
| Bakı desteği olmayan tamamen düz hücre | 3 |
| Hücre ortalama yükseklik aralığı | −2,02–3.127,92 m |
| Hücre ortalama eğim aralığı | 0–34,97° |

İşaretli 17 hücrenin AOI bölümleri küçük sınır parçalarıdır; ham alan oranı
yaklaşık 0,7654–1,0586 aralığına ulaşıyor. Kıyı/kenar desteği ayrıca
incelenmelidir. Bu hücreler otomatik silinmedi; örtüye dayalı habitat seçimi
ve yangın etiketi oluşturulmadı.

Ana çıktı `data/interim/landscape/v1/grid_static.csv`, kaynak ve çıktı özetleri
`data/interim/landscape/v1/manifest.json` içindedir. Önceki örtü tablosunun
sütun ve değerleri korundu. Ek özellikler `elevation_mean_m`,
`elevation_std_m`, `slope_mean_deg`, `northness_mean`, `eastness_mean`;
destek alanı ve tanısal bayraklar ayrı tutulur.

## Geçmiş görüntülerden bitki örtüsü örneği

Landsat 8 Collection 2 Level 2 kaynağıyla 1 Ağustos 2018 00:00 UTC hedefi
için, önceki 60 günde çekilmiş görüntüler incelendi. Sıralı hücre kimlikleri
üzerinden eşit aralıklarla 32 hücre seçildi; yangın etiketi veya final test
verisi seçimde kullanılmadı. Örnek, dört ildeki bütün hücreleri temsil eden
bir istatistiksel örneklem iddiası taşımaz.

Kırmızı, yakın kızılötesi ve kısa dalga kızılötesi bantlar kaynak ölçeği
`0,0000275` ve ofseti `−0,2` ile yansıtıma dönüştürüldü. Dolgu, genişletilmiş
bulut, cirrus, bulut, gölge, kar ve su pikselleri; doygunluk/örtülme işaretleri
ve fiziksel yansıtım sınırları kontrol edildi. NDVI ve NDMI aynı geçerli
piksel desteğiyle üretildi. İndekslerin 60 günlük piksel medyanları,
hücrelerde alan ağırlıklı özetlendi; bu ölçüler tek güne ait canlı gözlem değildir.
[Landsat kaynak ve kalite bantları](https://developers.google.com/earth-engine/datasets/catalog/LANDSAT_LC08_C02_T1_L2).

| Kontrol | Sonuç |
|---|---:|
| Örnek hücre | 32 |
| Kaynak sahne | 52 |
| En geç kaynak çekim zamanı | 30 Temmuz 2018 08:33:54 UTC |
| Desteksiz bitki örtüsü hücresi | 0 |
| Hücre NDVI özeti aralığı | 0,3049–0,7718 |
| Hücre NDMI özeti aralığı | −0,0346–0,3749 |

Kaynak kimlikleri ve çekim zamanları ham JSON'da tutuldu. Tahmin anından
sonraki görüntü bulunmadı; 2025 erişimden önce reddedilir. Görüntülerin geçmiş
yayımlanma/erişilebilirlik zamanı bilinmiyor. `available_at` boş, kullanım
`retrospective_candidate_only` olarak kalıyor. Operasyonel tahmin için bu
erişim açığı çözülmelidir. 60 günlük pencere başlangıç denemesidir;
hızlı değişimleri yumuşatabilir ve dönem karşılaştırması gerektirir.

Çıktı `data/interim/vegetation/pilot_v1/2018-08-01_32cells.csv`;
ham kayıt `data/raw/vegetation/landsat_pilot_v1/2018-08-01_32cells.json`.
Hücre desteği bazı örneklerde kısmi; eksik alan komşudan veya sıfırla doldurulmadı.

## Kontrol ve sonraki aşama

Statik tablo ve bitki örtüsü örneği kaynak/çıktı hash'leriyle kontrol edildi.
Ham Earth Engine integrallerinden ortalamalar ve varyanslar yerelde yeniden
hesaplanıp geri okunan CSV değerleriyle karşılaştırıldı. Önceki örtü tablosu
değerlerinin korunduğu doğrulandı. Bu kontrol bağımsız bir DEM ile doğruluk
karşılaştırması veya bulut maskesinin saha doğrulaması değildir.

Yeni arazi/indeks kuralları, zaman sözleşmesi ve mevcut hava politikası için
42 ilgili test geçti; Ruff denetimi başarılı. VM ve donmuş bulut paketlerine
müdahale edilmedi. Yeni dosyalar mevcut kod/veri ayrımına yerleştirildi.

Sıradaki işler:

1. Küçük kıyı/sınır hücrelerini destek alanı ve haritayla incelemek.
2. Bitki örtüsü penceresini farklı eğitim mevsimlerinde sınamak; gerçek
   çalışma süresi ve geçerli alanı ölçerek bütün dönem için indirme yolunu seçmek.
3. Günlük/as-of özellik seçimini, görüntü eskiliğini ve destek alanını
   kaydederek zaman serisini üretmek; bütün yıllara henüz uygulama yapılmadı.
4. Örtü sınıfları için habitat politikasını yalnız eğitim dönemi üzerinden
   gerekçelendirmek; bilinmeyen gözlemler negatif etikete dönüştürülmeyecek.

Yerel raporlar: `outputs/reports/landscape/static_preparation.json`,
`local_readback.json`, `vegetation_pilot_2018-08-01_32cells.json`.
