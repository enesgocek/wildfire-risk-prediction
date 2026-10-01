# Proje Rehberi

Kapsam, veri kuralları ve mevcut durum tek belgede toplanmıştır.

- [Proje tanımı](#proje-tanımı--güncel-pilot-kapsamı)
- [Veri ve değerlendirme kuralları](#veri-ve-değerlendirme-protokolü)
- [Çalışma alanı](#çalışma-alanı-kararı)
- [Sıradaki işler](#ikinci-haftaya-geçiş)
- [Kurulum durumu](#ilk-hafta-durumu)
- [Servis erişimleri](#dış-servis-erişim-durumu)

Başlangıç prensibi: yalnızca kullanılan kod ve klasörler tutulur. Veri/model/arayüz
klasörleri ihtiyaç doğduğunda oluşturulur. Rapor ve deney çıktıları `outputs/`, coğrafi veriler `data/` altında tutulur.

Sadeleştirme sonrası kurulum, 18 test, lint/format ve yeni MLflow deneyi başarıyla
doğrulandı. Önceki deney kayıtları yeni konuma taşındı; taşımadan önce alınan veritabanı
yedeği `outputs/mlflow/before-layout-backup.db` altında saklanır. `src` içinde yalnızca
paket tanımı, yapılandırma doğrulaması ve veri ayrım kontrolü bulunur.
## Proje Tanımı — Güncel Pilot Kapsamı

30 Eylül 2026 tarihinde kullanıcı tarafından belirlenen kapsam: Antalya, Muğla, İzmir,
Mersin. Orijinal yol haritasındaki Hatay pilot önerisinin yerini Mersin alır.
Çalışma Ege ve Akdeniz bölgelerinin tamamını kapsadığı iddiasında bulunmaz.

| Konu | Başlangıç kararı |
|---|---|
| Çalışma alanı | Antalya, Muğla, İzmir, Mersin |
| Tahmin birimi | Uygun bitki örtüsü bulunan 5×5 km grid |
| Tahmin ufku | Sonraki 24 saat |
| Çıktı | 0–1 arasında yangın oluşma olasılığı |
| Pozitif etiket | Tahmin zamanından sonraki 24 saat içinde yeni olayın ilk aktif yangın tespiti |
| Eğitim dönemi | 2018–2023 |
| Doğrulama dönemi | 2024 |
| İzole final test | 2025 |
| Ana değerlendirme metriği | PR-AUC |
| Deney takibi | Yerel MLflow |

### Zaman sözleşmesi

Her satır `(grid_id, prediction_timestamp)` ile tanımlanır. Günlük tahmin saati
00:00 UTC'dir (Türkiye saatiyle 03:00). T hedef zamanı için pozitif etiket,
ilk aktif tespit zamanı `(T, T + 24 saat]` aralığında bulunan yeni olaydır.
T anında zaten tespit edilmiş bir yangının sonraki hotspot'ları yeni olay değildir.

Uydu ilk tespit zamanı gerçek ignition zamanı değildir. Başlangıç hedefi bu gözlenebilir
ve belirsizlik içeren proxy'dir; raporlarda kesin yangın başlangıç tahmini iddia edilmez.
Algılanmamış yangınlar ve geç tespitler nedeniyle negatif etiket belirsizliği kaydedilir.

### Bilimsel ilerleme

FIRMS olay kataloğu → günlük grid etiketleri → geçmişe uygun özellikler → temporal ve
spatial validation → FWI/RF/XGBoost baseline → hata analizi → gerekirse EO embedding
ve fusion → kalibrasyon → tek final değerlendirme → batch inference → API ve harita.

Öncelikli çekirdek: FIRMS + meteoroloji + vegetation + terrain, kalibre edilmiş tabular
model, FastAPI ve risk haritası. Uydu foundation modelinin faydası ayrıca kanıtlanmalıdır.

### Dış ülke verisi

Türkiye pilotunda olay sayısı, mevsimsel/il bazlı dağılım ve veri eksiklikleri eğitim ve
validation üzerinde ölçülmeden dış veri gereksinimi varsayılmaz. Yetersizliğe göre İtalya,
Yunanistan, İspanya veya Portekiz gibi bölgeler için uyumlu etiket/özellikler incelenebilir.
Ülke ve yıllar sürüm manifestine yazılır; Türkiye 2025 final testi adaptasyona girmez.
İlk hafta veri yeterliliği veya model performansı hakkında sonuç üretilmez.


## Veri ve Değerlendirme Protokolü

### Zaman ve anti-leakage

- Tahmin T=00:00 UTC; hedef yeni olayın ilk tespiti için `(T, T+24 saat]`.
- Dinamik özellik gözlemi ve erişilebilirlik zamanı T'den önce olmalıdır.
  `observation_timestamp`, `available_at`, `source_version` saklanır. Yalnızca gözlem
  zamanına bakmak, gecikmeli yayımlanan veride yeterli değildir.
- Sentinel görüntüsü tahmin gününden önceki geçerli görüntü olmalı; aynı gün ve yangından
  sonraki görüntüler kullanılamaz. Cloud mask ve eksik görüntü stratejisi ayrıca kaydedilir.
- Günlük gerçekleşmiş meteorolojik toplamlar/maksimumlar gün başında bilinmez.
  Geçmiş birikimler T'den önce bitmelidir. Forecast kullanılırsa issue/availability zamanı
  T'den önce olmalı; gelecekteki valid time planlı tahmin bilgisidir, gerçekleşmiş ölçüm değildir.
- ERA5-Land reanalysis ile tarihsel deney, operasyonel gerçek zaman erişimi iddiası değildir.
  Yayın gecikmesi ve train-serving farkı raporlanır; operasyonel iddia için arşivlenmiş forecast
  veya açıkça belgelenmiş erişilebilirlik yaklaşımı gerekir.
- Statik arazi örtüsü ve yol/yerleşim verilerinin referans yılı kaydedilir. Daha sonraki
  bir arazi örtüsü haritasının geçmiş yangın izlerini kodlaması olasılığı incelenir.

### Olay ve etiketler

FIRMS VIIRS geçmiş standard/science-quality veri önceliklidir. Hotspot'lar olaylara
gruplanır, ilk tespit ayrı tutulur. EFFIS perimeter ve tarih alanları yardımcı doğrulamadır;
Start date gerçek ignition zamanı kabul edilmez. Olay birleştirme zaman/mesafe eşikleri
final test performansına göre ayarlanmaz. Coverage eksikse “tespit yok” güvenilir negatif
sayılmaz; veri yeterliliği ve negatif etiket belirsizliği raporlanır.

### Sabit ayrım

| Kullanım | Türkiye yılları | İzin |
|---|---|---|
| Eğitim | 2018–2023 | Fit ve training içi spatial CV |
| Validation | 2024 | Model/hiperparametre/kalibrasyon/eşik seçimi |
| Final test | 2025 | Model freeze sonrası tek final değerlendirme |

- Aynı `event_id` iki split'e giremez. Yıl sınırını aşan olaylar ve T+24h pencereleri
  ayrı sınır kontrolüne tabidir; dışlama/embargo kararı manifestte kaydedilir.
- İmputasyon, ölçekleme, feature selection ve öğrenilen dönüşümler yalnızca train'e fit edilir.
  CV'de her fold'un training kısmına yeniden fit edilir. Pretrained encoder'ın provenance'ı kaydedilir.
- Training içi spatial CV yakın gridleri bloklar halinde ayırır. Blok/buffer kuralları testten
  öğrenilmez. Training için kontrollü negatif örnekleme yapılabilir; validation/test gerçek
  dağılımı korumalıdır. Sampling oranı ve olasılık kalibrasyonuna etkisi raporlanır.
- 2025 final performansı deney seçiminde, dış ülke ekleme kararında veya hata analizine
  dayanarak model değiştirmede kullanılamaz. Final sonuç görüldükten sonraki değişiklik için
  yeni bağımsız değerlendirme dönemi gerekir; eski sonuçla yeni model başarısı iddia edilmez.

### Test izolasyonu

`data/processed/train`, `validation`, `final_test` ayrı tutulur. `split_directory` yardımcı
fonksiyonu final test erişimini varsayılan olarak reddeder. Bu kontrol OS güvenliği değildir;
doğrudan dosya okumayı engellemez. Gerçek pipeline bu yardımcıyı kullanmalıdır.

Veri geldikten sonra eğitim/arama işlerinin yalnızca train/validation manifestini okuması,
final testin ayrı konum veya erişim yetkisiyle tutulması ve final değerlendirme komutunun
model freeze kaydı istemesi planlanır. Bu hafta yalnızca yapılandırma ve erişim guard'ı hazırdır;
gerçek label/feature/event leakage denetimleri henüz uygulanmadı.

### Sürümleme ve kayıt

Her gerçek dataset manifesti: `dataset_version`, AOI/grid sürümü, kaynak/sensör sürümleri,
tarih aralığı, indirme tarihi, dosya SHA-256 özetleri, preprocessing config, kod commit'i,
etiket tanımı, sampling stratejisi, split özeti ve eksiklik raporu içerir.

Her deney: veri sürümü + config + seed + kod sürümü + ortam kilidi + metrikler + artifact'lar.
PR-AUC birincil; ROC-AUC, precision/recall, F1, Brier ve kalibrasyon ikincildir.
Accuracy ana başarı ölçütü değildir. Karşılaştırmalar aynı değerlendirme protokolünü kullanır.

Büyük raster/veri/model dosyaları Git'e girmez. Şimdilik yerel depolama; gerçek veri
toplamadan önce yedekleme ve dataset sürüm depolaması seçilir. Git'te küçük manifestler tutulur.

### Akdeniz dış veri deneyi

Ek ülkelerin etiket, sensör, grid ve özellik tanımları uyumlu olmalıdır. Önce Türkiye-only
baseline kurulmalı, sonra aynı Türkiye 2024 validation üzerinden dış veri katkısı ölçülmelidir.
Ek verinin kesim tarihleri ve split politikası önceden kayıt altına alınmalı; 2025 veya sonrasından
bilgi Türkiye 2025 final değerlendirmesine sızdırılmamalıdır. Dış veri, eksik Türkçe etiketleri
kendiliğinden düzeltmez; domain farkı ayrıca değerlendirilir.


## Çalışma Alanı Kararı

Pilot iller: **Antalya, Muğla, İzmir, Mersin**. Kapsam değişiklikleri yeni AOI/dataset
sürümü gerektirir; deneyler arasında sessizce il eklenmez veya çıkarılmaz.

30 Eylül 2026 tarihinde FAO GAUL 2025 il sınırlarından `TR_PILOT_V1` çalışma alanı
oluşturuldu. Kaynak: `FAO/GAUL/2025/level1`. Dört il haritada ve kaynak adlarıyla doğrulandı.
Birleşik AOI, aradaki il dışı boşlukları doldurmaz.

Grid sürümü `E6933_5K_V1`; üretim ve alan hesaplama sistemi EPSG:6933, başlangıç noktası
(0, 0), hücre boyutu projeksiyonda 5.000 × 5.000 metredir. Eşit alan projeksiyonunda
her tam hücre yaklaşık 25 km²'dir; yeryüzündeki kenar uzunlukları her yerde tam 5 km değildir.
GeoJSON geometrileri EPSG:4326 ile saklanır; alan hesabı için EPSG:6933'e dönüştürülür.

Earth Engine'deki CRS ayrıştırma sorununu aşmak için eşdeğer açık WKT kullanıldı.
Bellek sınırı nedeniyle aday grid, AOI'yi çevreleyen basit dikdörtgende üretildi;
ayrıntılı kesişim hesabı GeoPandas/Shapely ile yerelde tamamlandı.

| Kontrol | Sonuç |
|---|---|
| Aday hücre | 12.006 |
| AOI ile pozitif alan kesişimi bulunan hücre | 2.899 |
| Benzersiz nihai grid kimliği | 2.899 |
| Geçersiz veya boş nihai geometri | 0 |
| EPSG:6933 ile AOI alanı | 60.727,113920 km² |
| Kapsanan AOI alanı farkı | Yaklaşık 3,49 × 10⁻¹⁰ km² |

Tam hücre geometrisi korunur. `cell_area_km2`, `aoi_area_km2` ve `aoi_fraction`
alanları çalışma alanı içinde kalan bölümü tanımlar. Çok küçük sınır parçaları şimdilik
korunur; bu 2.899 hücrenin tamamı henüz model için uygun bitki örtüsü alanı sayılmaz.
Uydu özellikleri ve yangın etiketleri hazırlanırken hücrenin AOI dışı bölümü maskelenmelidir.
İl bazında eşleştirme kuralı henüz belirlenmedi.

### Dosyalar ve tekrar üretim

- `scripts/define_aoi.js`: Code Editor'da dört ili seçer, AOI'yi Drive'a aktarır.
- `scripts/build_grid.js`: bağımsız çalışır; AOI ve kimlikli aday grid ihracını tanımlar.
- `data/aoi/aoi.geojson`: birleşik pilot çalışma alanı.
- `data/interim/grid_5km_candidates.geojson`: Drive'dan indirilen aday grid; Git'e girmez.
- `scripts/check_aoi_grid.py`: yerel AOI ve aday grid kontrolü.
- `scripts/prepare_grid.py`: AOI ile kesişen hücreleri seçer ve alan oranlarını hesaplar.
- `data/aoi/grid_5km.geojson`: nihai coğrafi grid.
- `data/aoi/manifest.json`: kaynak, sürüm, sayısal kontroller ve dosya SHA-256 özetleri.
- `outputs/reports/grid_preparation.json`: yerel hazırlık raporu.

İki JavaScript dosyası Google Earth Engine Code Editor'da çalıştırılır. Tasks sekmesinden
AOI ve aday grid GeoJSON ihracı başlatılır; indirmeler yukarıdaki konumlara kaydedilir.
`build_grid.js` önizlemesi yalnızca ilk 200 aday hücreyi gösterir.

Proje kökünde PowerShell ile:

```powershell
.\.venv\Scripts\python.exe scripts/check_aoi_grid.py
.\.venv\Scripts\python.exe scripts/prepare_grid.py
```

Kaynak veya parametre değişirse yeni AOI/grid sürümü ve güncel manifest gerekir.

## Arazi Örtüsü İncelemesi — 1 Ekim 2026

Gridin genel görünümü ve Antalya kıyısındaki sınır hücreleri görsel olarak kontrol edildi.
Copernicus `COPERNICUS/Landcover/100m/Proba-V-C3/Global/2017` sınıflandırması
Earth Engine'den kaynak piksel hizası korunarak indirildi. Bu kaynak inceleme adayıdır;
model girdisi veya nihai uygunluk maskesi olarak kesinleştirilmedi. Referans yılı 2017
olması, ürünün 2017'de yayımlandığı anlamına gelmez; üretim/yayın ve yardımcı veri
provenance'ı modelde kullanımdan önce değerlendirilecek.

- Ham raster: `data/raw/landcover/landcover_copernicus_2017.tif`.
- Kaynak SHA-256: `ee8bd6c9f742dbbdfcdcbbb6ecc446499f05d676eaeb202c4345c11ea6006470`.
- CRS: EPSG:3857; piksel boyutu projeksiyonda 100 × 100 metre.
- Boyut: 9.959 × 4.750 piksel; tek int16 bant; nodata -9999.
- İndirilen dikdörtgende eksik piksel yok; 417 sınıflandırılamayan piksel var.
- Pilot alan içinde bilinmeyen sınıfa rastlanmadı.

Hesap yalnızca her hücrenin AOI içindeki bölümünde yapıldı. EPSG:3857 eşit alanlı
olmadığından WGS84 üzerinde piksel köşelerinden yaklaşık alan ağırlıkları üretildi.
`exactextract` kısmi piksel kesişimleri ve alan ağırlıklarıyla sınıf oranlarını hesapladı.
Oranlar 0–1 aralığında; çok küçük kayan nokta taşmaları tolerans içinde değerlendirilir.

İlk hesapta raster kaynak adlarının ayrılmaması alan sonucunu bozdu. Kaynaklar
`landcover` ve `pixel_area` olarak adlandırılarak sorun düzeltildi; yanlış tablo yeniden
üretildi. Betik artık toplam raster/AOI alan farkını CSV yazılmadan önce denetler.

| Kontrol | Sonuç |
|---|---|
| İşlenen hücre | 2.899 |
| Hesaplanan toplam alan | 60.727,113921 km² |
| AOI ile toplam alan farkı | Yaklaşık 1,67 m² |
| En büyük hücre bazında göreli alan farkı | Yaklaşık 8,45 × 10⁻⁶ |
| Seçili örtü oranı medyanı | %94,79 |
| Oranı sıfır olan hücre | 15 |
| Oranı %20 altında olan hücre | 174 |
| AOI bölümü 1 km²'den küçük hücre | 108 |

`natural_vegetation_fraction`, kaynakta orman, çalı ve otsu bitki olarak sınıflandırılmış
alanların toplamını ifade eder. Canlı yeşillik, yalnızca ağaç örtüsü veya kesin doğal alan
ölçümü değildir; kaynak bazı odunsu tarım alanlarını orman/çalı sınıfına dahil edebilir.
Histogram hücre sayısıyla oluşturulur, toplam arazi alanı dağılımı değildir.
Mersin merkezindeki yerleşim sınıfı kullanıcı tarafından yerel gözlemle karşılaştırıldı;
belirgin uyumsuzluk görülmedi. Bu, bütün kaynak için doğruluk ölçümü yerine geçmez.

Bütün hücreler korunuyor. Örtü ve alan eşikleri, yangın kayıtları geldikten sonra eğitim
dönemi üzerinden değerlendirilecek; 2025 final test bu karara dahil edilmeyecek.

### İşlem sırası ve yerel çıktılar

1. `scripts/preview_grid.py`: grid haritası.
2. `scripts/inspect_landcover.js`: Earth Engine inceleme ve GeoTIFF ihracı.
3. `scripts/check_landcover.py`: kaynak raster kontrolü.
4. `scripts/prepare_grid_aoi_parts.py`: hesaplama için AOI içi hücre geometrileri.
5. `scripts/prepare_landcover_weights.py`: piksel alan ağırlıkları.
6. `scripts/calculate_landcover_fractions.py`: hücre bazında örtü tablosu.
7. `scripts/preview_landcover_fractions.py`: harita ve histogram.

Ara çıktılar `data/interim/`, kontrol raporları `outputs/reports/`, görseller
`outputs/figures/` altında. Ham raster, ara dosyalar ve yerel çıktılar Git'e girmez;
betikler ve bağımlılık kilidi Git'te tutulur. Raster yeniden indirilecekse mevcut kaynak
kimliği, tarih ve piksel hizasıyla karşılaştırılır; kaynak değişimi sessizce yapılmaz.

### FIRMS indirme isteği

1 Ekim 2026 tarihinde Türkiye, buffer 0 km, VIIRS S-NPP Collection 2,
2018-01-01–2024-12-31, CSV için istek gönderildi. İstek numarası **815579**.
Alındı e-postası geldi; indirme bağlantısı bekleniyor. Veri henüz indirilip kontrol edilmedi.
Geldiğinde kaynak/sürüm, standard-processing durumu, alan şeması ve zaman kapsamı
kontrol edilecek; ham dosya korunacak ve dört il filtresi yerelde uygulanacak.
2025 final test bu indirme isteğine dahil edilmedi.

Kaynaklar:

- [Copernicus CGLS-LC100 Collection 3](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global)
- [Exactextract işlemleri](https://isciences.github.io/exactextract/operations.html)
- [FIRMS arşiv indirmesi](https://firms.modaps.eosdis.nasa.gov/download/)

## İkinci Haftaya Geçiş

1. FIRMS 815579 numaralı isteğin indirme bağlantısı geldiğinde ham dosyayı kaydet ve kontrol et.
2. Arazi örtüsü adayının modelde kullanımını ve uygunluk kriterini eğitim verisiyle değerlendir.
   Sonraki yıllara ait yangın izlerini geçmiş özelliklere taşımamaya dikkat et.
3. FIRMS 2018–2024 veri bulunabilirliğini il/yıl/sensör bazında incele. NRT yerine
   mümkün olduğunca standard/science-quality geçmiş veri kullan. 2025 final verisinin
   bulunabilirliği kontrol edilebilir; model geliştirmede performans veya içerik keşfi yapılmaz.
4. EFFIS geçmiş perimeter erişimini doğrula; gerekiyorsa veri isteği başlat.
5. Coverage/missingness raporu çıkar. Ham veri formatını ve provenance manifestini sabitle.
6. Tekrarlı hotspot temizliği ve olay gruplama kurallarını train dönemi üzerinde geliştir.
   Yıl sınırını aşan olayları ayrı denetle.
7. `fire_event_catalog.parquet` üret; event_id, first_detection_time, lat/lon,
   ülke/il, sensör, confidence ve mümkünse EFFIS/alan alanlarını sakla.
8. Train/validation olay ve grid dağılımı yeterlilik raporu çıkar. Dış ülke verisi gerekip
   gerekmediğini bu raporla değerlendir. Türkiye 2025'i kararı vermek için kullanma.

Coğrafi altyapı hazırdır. Gerçek yangın verisi ve leakage denetimi tamamlanmadan
model eğitimine başlanmaz.

## İlk Hafta Durumu

30 Eylül 2026 — Python altyapısı, GitHub deposu, Earth Engine erişimi ve pilot grid hazır.

- Sade klasör yapısı, merkezi YAML yapılandırması ve bağımlılık kilidi oluşturuldu.
- Yapılandırma doğrulama ve final test erişim kontrolü hazırlandı.
- Yerel MLflow altyapı deneyi doğrulandı; bu deney gerçek model başarısı ölçmez.
- İlk kurulumda 18 test, Ruff ve temiz ortam kontrolü başarılı oldu.
- GeoPandas/Shapely eklendi; AOI ve grid geometrileri, kimlikler ve kapsama kontrol edildi.
- GitHub deposu: https://github.com/enesgocek/wildfire-risk-prediction
- Günlük çalışma özeti: `Diary/30-09-2026.md`.

Kurulum Windows ve Python 3.12 üzerinde doğrulandı. Farklı işletim sistemi veya bağımsız
bir bilgisayar üzerinde clone testi henüz yapılmadı. Yerel raporlar `outputs/reports/`
altında; MLflow kayıtları `outputs/mlflow/` altında tutulur ve Git'e gönderilmez.

## Dış Servis Erişim Durumu

1 Ekim 2026 itibarıyla:

| Servis | Durum | Sıradaki işlem |
|---|---|---|
| GitHub | main dalı ve origin bağlantısı hazır; ilk dosyalar yüklendi | Sonraki değişiklikleri commit/push ile kaydet |
| MLflow | Smoke deneyi, sağlık ve arayüz kontrolü doğrulandı | Modelleme aşamasında deneyleri kaydet |
| Earth Engine | Python API erişimi doğrulandı; Code Editor ihracı çalıştı | Veri kaynaklarını aşamalı incele |
| GEE non-commercial | Cloud konsolunda kayıt görüldü; geçerlilik 8 Şubat 2028'e kadar | Gerektiğinde konsoldaki durumu tekrar kontrol et |
| NASA FIRMS | 815579 numaralı Türkiye 2018–2024 isteği alındı; indirme bekleniyor | Gelen CSV dosyasını ve kapsamını kontrol et |
| EFFIS | Erişim/istek henüz başlatılmadı | Geçmiş perimeter erişimini incele |

`scripts/check_gee_access.py` sonucu `api_verified: true` olarak kaydedildi.
Non-commercial kayıt durumunu Python betiği doğrulamaz; bu bilgi Cloud konsolundan
ayrıca kontrol edildi. Yerel `outputs/reports/gee_access.json` raporundaki
`must_be_confirmed_in_google_console` alanı bu ayrımı belirtir.

Resmî kaynaklar:

- [Earth Engine erişimi](https://developers.google.com/earth-engine/guides/access)
- [Earth Engine kimlik doğrulama](https://developers.google.com/earth-engine/guides/auth)
- [FAO GAUL 2025 il sınırları](https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2025_level1)
- [MLflow tracking server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/)
