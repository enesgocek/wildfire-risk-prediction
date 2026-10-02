# Proje Rehberi

Kapsam, veri kuralları ve mevcut durum tek belgede toplanmıştır.

**3 Ekim güncel durum:** 2018 ve 2019 meteoroloji verileri denetlendi;
toplam 730 gün ve 2.116.270 hücre-gün. Sonraki oturumda 2020’den devam edilecek. Nihai olay/etiket/model henüz yok. Kısa özet
[STATUS.md](STATUS.md), denetim kapsamı [kalite incelemesinde](QUALITY_REVIEW_2026-10-02.md).
Bu belge tarihli ilerleme kayıtlarını da içerir; eski durum notları tamamlanmış
sonraki işlerin önüne geçmez.

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

- `scripts/earth_engine/define_aoi.js`: Code Editor'da dört ili seçer, AOI'yi Drive'a aktarır.
- `scripts/earth_engine/build_grid.js`: bağımsız çalışır; AOI ve kimlikli aday grid ihracını tanımlar.
- `data/aoi/aoi.geojson`: birleşik pilot çalışma alanı.
- `data/interim/grid_5km_candidates.geojson`: Drive'dan indirilen aday grid; Git'e girmez.
- `scripts/geography/check_aoi_grid.py`: yerel AOI ve aday grid kontrolü.
- `scripts/geography/prepare_grid.py`: AOI ile kesişen hücreleri seçer ve alan oranlarını hesaplar.
- `data/aoi/grid_5km.geojson`: nihai coğrafi grid.
- `data/aoi/manifest.json`: kaynak, sürüm, sayısal kontroller ve dosya SHA-256 özetleri.
- `outputs/reports/grid_preparation.json`: yerel hazırlık raporu.

İki JavaScript dosyası Google Earth Engine Code Editor'da çalıştırılır. Tasks sekmesinden
AOI ve aday grid GeoJSON ihracı başlatılır; indirmeler yukarıdaki konumlara kaydedilir.
`build_grid.js` önizlemesi yalnızca ilk 200 aday hücreyi gösterir.

Proje kökünde PowerShell ile:

```powershell
.\.venv\Scripts\python.exe scripts/geography/check_aoi_grid.py
.\.venv\Scripts\python.exe scripts/geography/prepare_grid.py
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

1. `scripts/geography/preview_grid.py`: grid haritası.
2. `scripts/earth_engine/inspect_landcover.js`: Earth Engine inceleme ve GeoTIFF ihracı.
3. `scripts/landcover/check_landcover.py`: kaynak raster kontrolü.
4. `scripts/geography/prepare_grid_aoi_parts.py`: hesaplama için AOI içi hücre geometrileri.
5. `scripts/landcover/prepare_landcover_weights.py`: piksel alan ağırlıkları.
6. `scripts/landcover/calculate_landcover_fractions.py`: hücre bazında örtü tablosu.
7. `scripts/landcover/preview_landcover_fractions.py`: harita ve histogram.

Ara çıktılar `data/interim/`, kontrol raporları `outputs/reports/`, görseller
`outputs/figures/` altında. Ham raster, ara dosyalar ve yerel çıktılar Git'e girmez;
betikler ve bağımlılık kilidi Git'te tutulur. Raster yeniden indirilecekse mevcut kaynak
kimliği, tarih ve piksel hizasıyla karşılaştırılır; kaynak değişimi sessizce yapılmaz.

### FIRMS arşivi ve gözlem kapsamı — 1 Ekim 2026

815579 numaralı Türkiye S-NPP arşivi indirildi ve kontrol edildi. 2018–2024 dönemindeki
277.291 ham kayıtta eksik alan, geçersiz koordinat/zaman, dönem dışı veya birebir tekrar
bulunmadı. Kaynak SHA-256:
`346d9e4e09d49d21166e98049635d64326c9330cd42b15b2f44c19456b54d5d2`.

Pilot AOI içinde 35.107 tespit 1.118 gride eşleştirildi. `type=0` ve güven `n/h`
seçimiyle 16.262 geçici aday oluşturuldu; bütün kayıtlar seçim gerekçeleriyle korunuyor.
14.833 aday eğitim, 1.429 aday doğrulama döneminde. Bunlar olay veya kesin etiket değil.
Kaynak işlem geçmişi ve type yeniden işleme durumu modellemeden önce doğrulanacak;
CSV `version=2` alanı üretim yazılım sürümünün tek başına kanıtı değildir.

Eğitim döneminde Türkiye genelinde 26 sıfır kayıt günü bulundu. 27 Temmuz–10 Ağustos
2022 arasındaki 15 günlük boşluk resmi S-NPP kesintisiyle örtüşüyor; kesinti 26 Temmuz'da
gün içinde başladığı için o gün de kısmi gözlem içeriyor. Diğer 11 gün henüz kesin kesinti
sayılmıyor. Günlük tespit sayısı tam gözlem kapsamını kanıtlamaz. Eksik gözlem günleri
“yangın yok” etiketi olarak kullanılmayacak; nihai coverage maskesi henüz üretilmedi.

NOAA-20 arşivi 815590 numaralı talepten indirildi: Türkiye, buffer 0 km,
2018-04-01–2024-12-31. 284.963 ham kaydın temel kontrolleri geçti; 37.196 pilot
kayıttan 16.993 geçici aday seçildi. Kaynak SHA-256:
`f3b0a716c335e89976fcc2620cc29dc871938411c6ad5b7f8737a4e55c6e46ec`.

S-NPP boşluğundaki 15 günde NOAA-20 Türkiye genelinde 1.108, pilotta 173 tespit,
seçim kuralıyla 23 aday sağladı. Bu, bütün hücrelerde tam kapsam olduğunu kanıtlamaz.
İki kaynak 33.255 benzersiz tespit kimliğiyle ortak inceleme tablosunda tutuluyor:
30.295 eğitim ve 2.960 doğrulama adayı; toplam 1.343 hücre. Tekrar silinmedi,
olay gruplaması yapılmadı. Sensör/talep/kaynak kayıt kimlikleri korunuyor.
2018'in ilk üç ayındaki tek sensör kapsamı ayrıca değerlendirilecek.

2019 ve 2021 eğitim örnekleri günlük ve 6 saatlik grafiklerde incelendi; MODIS
MCD64A1 yanmış alanları görsel karşılaştırma için açıldı. Henüz doğrudan hotspot/raster
örtüşme ölçümü veya olay doğrulaması yapılmadı. Yangın sonrası yanmış alan bilgisi
etiket incelemesine yardımcıdır; yangın öncesi model özelliği olarak kullanılmaz.
2025 final test verisi bu işlemlere dahil edilmedi.

İşlem sırası:

1. `scripts/firms/check_firms_archive.py`: ham CSV kontrolü.
2. `scripts/firms/prepare_firms_pilot.py`: AOI seçimi, UTC zamanı ve grid eşleştirme.
3. `scripts/firms/profile_firms_pilot.py`: tür/güven dağılımları ve eğitimde sabit kaynak yoğunluğu.
4. `scripts/firms/prepare_firms_candidates.py`: geçici adaylar ve seçim denetim tablosu.
5. `scripts/firms/preview_firms_candidates.py`: yalnızca eğitim dönemi haritası ve aylık grafiği.
6. `scripts/firms/check_firms_coverage.py`: eğitim döneminde günlük S-NPP Türkiye tespit sayıları.
7. `scripts/firms/combine_firms_candidates.py`: iki kaynağın izlenebilir ortak aday tablosu.
8. `scripts/firms/preview_firms_event_samples.py`: eğitim örneklerinde günlük/6 saatlik inceleme.
9. `scripts/earth_engine/inspect_burned_area_samples.js`: MODIS yanmış alan karşılaştırması.

Betikler konuya göre alt klasörlerde tutulur; güncel komutlar ve kaynak farkları
`scripts/README.md` dosyasında açıklanır. Python betikleri proje kökünü kendi dosya
konumlarından bulur. Veri dizinleri taşınmadı; betik klasörleri veri ayrımını değiştirmez.

Ham dosyalar `data/raw/firms/`, ara tablolar `data/interim/`, raporlar ve görseller
`outputs/` altında tutulur ve Git'e girmez. Ayrıntılı çalışma kaydı: `Diary/01-10-2026.md`.

Arazi örtüsü kaynakları: [Copernicus CGLS-LC100 Collection 3](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global),
[Exactextract işlemleri](https://isciences.github.io/exactextract/operations.html).

FIRMS kaynakları: [Arşiv indirmesi](https://firms.modaps.eosdis.nasa.gov/download/),
[NASA kesinti kayıtları](https://modaps.modaps.eosdis.nasa.gov/services/production/outages_suomi_npp.html),
[NOAA-20 arşiv kapsamı](https://firms2.modaps.eosdis.nasa.gov/content/academy/data_api/firms_api_use.html).

## İkinci Haftaya Geçiş

1. S-NPP/NOAA-20 adaylarının gözlem kapsamı ve işlem geçmişini kesinleştir; yanmış alan karşılaştırmasını ilerlet.
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
| NASA FIRMS | S-NPP ve NOAA-20 arşivleri kontrol edildi; ortak aday tablosu hazır | Gözlem kapsamı ve olay gruplama kurallarını doğrula |
| EFFIS | Erişim/istek henüz başlatılmadı | Geçmiş perimeter erişimini incele |

`scripts/environment/check_gee_access.py` sonucu `api_verified: true` olarak kaydedildi.
Non-commercial kayıt durumunu Python betiği doğrulamaz; bu bilgi Cloud konsolundan
ayrıca kontrol edildi. Yerel `outputs/reports/gee_access.json` raporundaki
`must_be_confirmed_in_google_console` alanı bu ayrımı belirtir.

Resmî kaynaklar:

- [Earth Engine erişimi](https://developers.google.com/earth-engine/guides/access)
- [Earth Engine kimlik doğrulama](https://developers.google.com/earth-engine/guides/auth)
- [FAO GAUL 2025 il sınırları](https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2025_level1)
- [MLflow tracking server](https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/)


## Tarihsel kaynak incelemesi — H01 (1 Ekim 2026)

Bu kayıt, kullanıcının Earth Engine Console çıktılarından alınmıştır. Ham görüntüler
ve makine tarafından dışa aktarılmış inceleme raporu henüz arşivlenmedi. H01,
SNPP_815579_3922, 23 Nisan 2018 00:30 UTC, 38.73095 N / 26.93221 E.
Sonraki ilk yakın type=2 kaydı 16 Mayıs 2019 00:06 UTC'dir; tesis kuruluş tarihi değildir.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki Sentinel-2 görüntüsü | 2018-02-27 09:06 UTC; 20180227T085921_20180227T090625_T35SMC |
| Sonraki Sentinel-2 görüntüsü | 2018-04-28 09:09 UTC; 20180428T085601_20180428T090404_T35SMC |
| Sonraki sabit kayıt dönemi görüntüsü | 2019-05-28 09:09 UTC; 20190528T085609_20190528T090917_T35SMC |
| 2017 nokta örtüsü | Sınıf 50 (kentsel/yapılaşmış), urban %100; ağaç/çalı/ot %0 |
| NDVI medyanı: önce / sonra | 0.10886075949367088 / 0.06386333771353482 |
| NBR medyanı: önce / sonra | 0.25608732157850544 / 0.01234773219020419 |
| MODIS Nisan 2018 | BurnDate ve Uncertainty: -9999; QA=3; FirstDay=76, LastDay=141 |
| MODIS Mayıs 2018 | BurnDate ve Uncertainty: -9999; QA=3; FirstDay=104, LastDay=170 |

Örtü kaydı noktanın düştüğü 100 m kaynak pikselidir; indeksler 100 m yarıçaplı
çevrede her indeks için ortak geçerli piksellerin medyanıdır. Bunlar aynı örnekleme
alanı değildir. 2017 sınıfı yer gerçeği olarak kabul edilmez. Görsellerdeki renk
farkı, farklı mevsimlerde seçilmiş görüntüler ve yaklaşık 55 günlük önceki görüntü
aralığı nedeniyle tek başına yangın kanıtı değildir. NDVI/NBR değişiminin nedeni doğrulanmadı.

-9999, inceleme betiğinin maskeli veriye atadığı değerdir; kaynak ürünün yanmamış
sınıfı değildir. Her iki ayda QA_land=1, QA_valid=1, QA_shortened_period=0,
QA_special_condition=0 olması, eksik BurnDate değerini kullanılabilir yapmaz.
Kaynak bant maskeleri betiğin sonraki sürümünde ayrıca gösterilir.

Karar: H01 için orman yangını doğrulanmadı; sabit kaynak olasılığı da kesinleştirilmedi.
İlk görsel orman/yanma yorumundan kesin etiket çıkarılmaz. Hiçbir tespit elenmedi.
Bu altı vaka hedefli örneklerdir; tüm verinin doğruluk oranını ölçmez. Eğitim dönemi
ile sınırlıdır; 2024 doğrulama ve 2025 final test kural seçimine dahil edilmez.

2017 referans yılı, ürünün 2017'de yayımlandığı anlamına gelmez. Collection 3'ün
2020 tarihli kaynak kaydı nedeniyle bu ürün burada tarihsel etiket incelemesinde
kullanılır; gerçek zamanda mevcut model özelliği sayılmadan önce erişilebilirlik
ve yayın tarihi ayrıca denetlenmelidir.
Kaynak: [Copernicus arazi örtüsü resmî veri kataloğu](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global).

Sıradaki inceleme H02'dir. Aynı betikte vaka seçimi, görüntü tarihleri, kalite
oranları, nokta örtüsü, indeksler ve MODIS bant maskeleri birlikte gösterilir.
Sonraki sabit kayıt dönemi, kaydın tam UTC zamanından başlayan 46 günlük penceredir.
Başvuru öncesi eksikler arasında tam kaynak sürümü ve indirme tarihi, yeniden
üretilebilir inceleme çıktıları, etiket karar günlüğü, bağımsız doğrulama, gözlem
kapsamı ve veri sızıntısı denetimi bulunur. TÜBİTAK programı seçilmedi; bu çalışmalar
bir programın koşullarını sağladığı iddiası değildir.


## Tarihsel kaynak incelemesi — H02 (1 Ekim 2026)

Kaynak: kullanıcının paylaştığı Console çıktısı ve sekiz Earth Engine ekran görüntüsü.
Henüz makine tarafından dışa aktarılmış görüntü/rapor arşivi değildir.
Aday SNPP_815579_32141, 2018-10-19 10:56 UTC, 38.78931 N / 26.91908 E.
Yakındaki ilk sonraki type=2 kaydı 2018-12-12 00:11 UTC; bu tarih tesisin kuruluşu
veya faaliyete geçiş tarihi olarak yorumlanmaz.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki görüntü | 2018-10-10 09:09 UTC; 20181010T090019_20181010T090126_T35SMD |
| Sonraki görüntü | 2018-11-04 09:09 UTC; 20181104T090131_20181104T090130_T35SMD |
| Önce: görüntü / uygun görüntü sayısı | 30 / 3; çekirdek açık alan oranı 1, bağlam 0.9954432579319354 |
| Sonra: görüntü / uygun görüntü sayısı | 18 / 3; çekirdek açık alan oranı 1, bağlam 0.9996857419263404 |
| Sonraki sabit kayıt dönemi | 18 görüntü; 100 m çevresi en az %90 açık görüntü 0; görüntü seçilmedi |
| 2017 nokta örtüsü | Sınıf 40 (tarım); tree/shrub/grass/urban örtü oranları %0 |
| NDVI medyanı: önce / sonra | 0.019686543927208346 / 0.041016031646887365 |
| NBR medyanı: önce / sonra | -0.04528891202498698 / -0.020373697718448262 |
| MODIS Ekim ve Kasım 2018 | BurnDate ve Uncertainty maskesi 0; her iki değer -9999; FirstDay/LastDay -9999; QA=0 |

Her iki MODIS ayında QA_land=0, QA_valid=0, QA_shortened_period=0,
QA_special_condition=0. Ürün bu pikseli kara/geçerli gözlem olarak işaretlemiyor.
Kıyıdaki karışık piksel veya ürünün kara/su maskesi olası açıklamalardır;
nedeni doğrulanmadı. MODIS bu noktada yanmış/yanmamış kararı için kullanılamaz.
Haritada turuncu piksel görülmemesi yangın yokluğu kanıtı değildir.

Görsel gözlem: 10 Ekim görüntüsünde, yani adaydan önce, noktanın yakınında tank
benzeri dairesel yapılar, yollar ve tesis düzeni görülüyor; 4 Kasım'da da mevcut.
Bu görseller, bu aday için sonradan yapılaşma varsayımını desteklemiyor. Ancak 2017
örtü sınıfı ile 2018 görüntüsünün uyumsuzluğu 2017'de de aynı tesisin mevcut
olduğunu kanıtlamaz; değişim ve sınıflandırma hatası olasılıkları ayrıştırılmadı.
2017 ürününde sınıf 40 tarımdır; diğer dört örtü oranının sıfır olması tarım
oranının sıfır olduğu anlamına gelmez; crops-coverfraction henüz örneklenmedi.

İndeks medyanları düşük; sonrasında her iki indeks de artıyor. Bu karşılaştırma
bitki yanmasını destekleyen belirgin bir düşüş göstermiyor. Medyanların farkı,
piksel bazında değişim medyanı değildir; kesin bir yanma eşiği uygulanmadı.
Önceki görüntü yaklaşık 9 gün, sonraki yaklaşık 16 gün uzakta; bu aralıkta kısa
olayların gözden kaçması mümkündür. Kıyı/su yakınındaki NBR değişimleri yangın
olarak yorumlanmaz. İnceleme çemberi VIIRS piksel ayak izi veya konum doğruluğu
sınırı değildir; tesisin hangi ekipmanının tespiti ürettiği belirlenmedi.

Geçici değerlendirme: adaydan önce mevcut tesis bağlamı nedeniyle sanayi kaynaklı
ısı olasılığı destekleniyor. Orman/bitki yangını doğrulanmadı; kesin kaynak
ataması veya otomatik eleme yapılmadı. Yakında tesis bulunması, tesiste ya da
çevresinde gerçek yangın olasılığını tek başına dışlamaz. H03 aynı yöntemle
incelenecek; bu hedefli örneklerden tüm veri için hata oranı çıkarılmayacak.
Kaynaklar: [Copernicus örtü sınıfları](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global),
[MODIS bant ve QA açıklamaları](https://developers.google.com/earth-engine/datasets/catalog/MODIS_061_MCD64A1).


## Tarihsel kaynak incelemesi — H03 (1 Ekim 2026)

Kaynak: kullanıcının Console çıktısı ve yedi ekran görüntüsü; bağımsız saha
kanıtı veya arşivlenmiş ham görüntü dışa aktarımı değildir.
Aday SNPP_815579_3073, 2018-04-06 00:49 UTC, 38.82114 N / 27.06561 E.
Yakındaki ilk sonraki type=2 kaydı 2019-06-19 23:59 UTC; tesis kuruluş tarihi değildir.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki görüntü | 2018-01-28 09:09 UTC; 20180128T090221_20180128T090925_T35SNC |
| Sonraki görüntü | 2018-04-28 09:09 UTC; 20180428T085601_20180428T090404_T35SMD |
| Sonraki sabit kayıt dönemi | 2019-06-22 09:09 UTC; 20190622T085601_20190622T085827_T35SNC |
| Kaynak / uygun görüntü sayıları | Önce 66 / 3; sonra 36 / 4; sonraki sabit dönem 36 / 27 |
| Seçilen görüntülerin açık alan oranları | Üçünde de çekirdek ve bağlam oranları 1 |
| 2017 nokta örtüsü | Sınıf 30; grass %49, shrub %9, tree %3, urban %35 |
| NDVI medyanı: önce / sonra | 0.33733493397358943 / 0.2139439433813095 |
| NBR medyanı: önce / sonra | 0.11261281596193534 / 0.05232649073004723 |
| MODIS Nisan 2018 | BurnDate/Uncertainty -9999, iki kaynak maskesi 0; QA=3; FirstDay=80, LastDay=141 |
| MODIS Mayıs 2018 | BurnDate/Uncertainty -9999, iki kaynak maskesi 0; QA=3; FirstDay=102, LastDay=170 |

Her iki MODIS ayında QA_land=1, QA_valid=1, QA_shortened_period=0,
QA_special_condition=0. Buna rağmen BurnDate ve Uncertainty kaynak maskeleri 0;
betikteki -9999 yanmamış sınıfı değildir. Bu gözlemle yangın yokluğu kararı verilmez.

Görsel gözlem: 28 Ocak 2018 tarihli Sentinel katmanında aday çevresinde açık renkli
uzun yapılar ve yollar zaten görülüyor. Nisan ve Haziran 2019 görüntülerinde de
benzer yerleşim düzeni mevcut. Yapıların işlevi ve ısı üreten ekipman doğrulanmadı.
Tarihli Sentinel katmanının dışındaki Google uydu altlığının çekim tarihi
belirlenmedi; 2018 arazi durumu kanıtı olarak kullanılmaz. Altlıktaki telif/yıl
bilgisi görüntünün çekim tarihini belirlemez.

2017 pikselinin sınıf 30 olması, tüm alanın orman olduğu anlamına gelmez; aynı
pikselde %35 yapılaşmış örtü ve %3 ağaç örtüsü tahmini var. Nokta pikseli ile
100 m çevrenin indeks medyanları farklı örnekleme alanlarıdır. Ot/çalı örtüsü
orman değildir; bununla birlikte otsu/çalılık yangını proje kapsamı açısından
ayrıca değerlendirilmelidir. Sınıf değerleri kesin yer gerçeği değildir.

Önceki görüntü adaydan yaklaşık 68 gün önce, sonraki yaklaşık 22 gün sonradır.
NDVI medyanı yaklaşık 0.1234, NBR medyanı yaklaşık 0.0603 azalıyor; bu medyan
farkları piksel bazında değişim medyanı veya yangın eşiği değildir. Ocak/Nisan
mevsimselliği, yüzey/bitki değişimi, gölge ve farklı Sentinel tile/projeksiyonları
etkisi dışlanmadı. Azalma tek başına yangın, ağaç kesimi veya inşaat nedeni
atamaya yeterli değildir; %100 açık alan kalite ölçütü bu nedenleri ayrıştırmaz.

Geçici değerlendirme: adaydan önce yapılaşmış ve bitkili karma çevre mevcut;
yangın ve ağaç kesimi doğrulanmadı. Sabit kaynak olasılığı incelenmeye devam ediyor;
yapı varlığı kesin kaynak ataması veya tüm yakın tespitlerin elenmesi anlamına gelmez.
Hiçbir tespit elenmedi. H01–H03, sonradan type=2 görülen konumların otomatik olarak
arazi dönüşümü veya yanlış yangın tespiti sayılmaması gerektiğini gösteren hedefli
incelemelerdir; tüm veri doğruluğu için temsil edici örneklem değildir.
Sıradaki H04, adaydan önce yakın type=2 kaydı bulunan kategoriye aittir.


## Tarihsel kaynak incelemesi — H04 (1 Ekim 2026)

Kaynak: kullanıcının Console çıktısı ve dokuz ekran görüntüsü; görüntüler henüz
ham raster olarak arşivlenmedi. Aday SNPP_815579_3395, 2018-04-13 00:18 UTC,
38.42831 N / 27.21594 E. Denetim tablosunda 100 m içinde son önceki type=2 kaydı
2018-03-12 00:18 UTC (adaydan 32 gün önce), ilk sonraki kayıt
2018-04-29 23:08 UTC. Bunlar kaynak sınıflandırma kayıtlarıdır; tesis kimliği
ve faaliyet başlangıcı kanıtı değildir.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki görüntü | 2018-01-28 09:09 UTC; 20180128T090221_20180128T090925_T35SNC |
| Sonraki görüntü | 2018-04-28 09:09 UTC; 20180428T085601_20180428T090404_T35SNC |
| Sonraki sabit kayıt dönemi | 2018-06-02 09:09 UTC; 20180602T085549_20180602T090540_T35SNC |
| Kaynak / uygun görüntü sayıları | Önce 17 / 1; sonra 9 / 1; sonraki sabit dönem 9 / 2 |
| Seçilen görüntülerin açık alan oranları | Üçünde de çekirdek ve bağlam oranları 1 |
| 2017 nokta örtüsü | Sınıf 50; urban %93, grass %6, shrub %0, tree %0 |
| NDVI medyanı: önce / sonra | 0.17358967499114103 / 0.14613095238095236 |
| NBR medyanı: önce / sonra | 0.09458720612356479 / 0.045950209293853454 |
| MODIS Nisan 2018 | BurnDate/Uncertainty -9999; iki kaynak maskesi 0; QA=3; FirstDay=91, LastDay=141 |
| MODIS Mayıs 2018 | BurnDate/Uncertainty -9999; iki kaynak maskesi 0; QA=3; FirstDay=104, LastDay=166 |

Her iki MODIS ayında QA_land=1, QA_valid=1, QA_shortened_period=0,
QA_special_condition=0; maskeli BurnDate ve Uncertainty nedeniyle yanmış/yanmamış
kararı verilemez. Haritadaki turuncu alan yokluğu yangın yokluğu olarak kaydedilmez.

Görsel gözlem: Ocak 2018 görüntüsünde aday çevresinde yollar ve yapılar zaten var;
Nisan ve Haziran görüntülerinde de benzer yapılaşmış düzen görülüyor. Tesisin
adı, işlevi ve ısı üreten ekipman belirlenmedi. Tarihi belirsiz Google uydu
altlığı, tarihli Sentinel görüntüsünün yerine geçmiş arazi kanıtı sayılmaz.
2017 nokta örtüsü bu yapılaşmış bağlamı destekliyor; tüm VIIRS ayak izinin örtüsü
veya kesin yer gerçeği olarak yorumlanmaz.

Önceki görüntü adaydan yaklaşık 75 gün önce, sonraki yaklaşık 15 gün sonra.
NDVI medyan farkı yaklaşık 0.0275, NBR medyan farkı yaklaşık 0.0486 azalmadır;
mevsim, gölge ve yüzey değişimleri ayrıştırılmadı. Piksel bazında değişim medyanı
veya kabul edilmiş yanma eşiği değildir. Bu karşılaştırmada belirgin bir bitki
yangını izi seçilmedi; kısa veya küçük yangın dışlanmadı.

Geçici değerlendirme: adaydan önce yapılaşmış çevre ve yakın type=2 kaydı birlikte
sabit/tekrarlayan ısı kaynağı olasılığını destekliyor. Adayın kesin kaynağı ve yangın
niteliği doğrulanmadı; şehir veya tesis içindeki gerçek yangın olasılığı da bu
kanıtlarla dışlanamaz. Hiçbir kayıt elenmedi. FIRMS type alanının kaynak üretim
sürümü sorunu çözülmeden bu kayıtlar kesin doğrulama etiketi olarak kullanılmaz.
Sıradaki H05 aynı prior_static kategorisindedir; nihai filtre henüz belirlenmedi.


## Tarihsel kaynak incelemesi — H05 (1 Ekim 2026)

Kaynak: kullanıcının Console çıktısı ve beş ekran görüntüsü.
Aday N20_815590_158, 2018-04-03 22:56 UTC, 36.26247 N / 33.73007 E.
Kategori prior_static. Önceki denetim tablosunda 100 m içinde son önceki type=2
kaydı 2018-03-19 23:28 UTC; ilk sonraki kayıt 2018-04-13 23:09 UTC.
Bu kayıtlar kaynak kimliği veya tesis kuruluş tarihi değildir.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki dönem | 16 kaynak görüntü; kalite koşulunu sağlayan 0; görüntü seçilmedi |
| Sonraki görüntü | 2018-04-04 08:35 UTC; 20180404T082559_20180404T083550_T36SWF |
| Sonraki dönem: kaynak / uygun sayı | 9 / 5; çekirdek açıklık 0.9233220373273985, bağlam 0.9576766611327935 |
| Sonraki sabit kayıt dönemi görüntüsü | 2018-04-14 08:30 UTC; 20180414T082559_20180414T083052_T36SWF |
| Sabit dönem: kaynak / uygun sayı | 10 / 6; çekirdek açıklık 0.9374336148904961, bağlam 0.9044768887346338 |
| 2017 nokta örtüsü | Sınıf 60 (çıplak/seyrek bitkili); grass %0, shrub %6, tree %0, urban %0 |
| NDVI/NBR önce-sonra | Önceki görüntü yok; hesaplanmadı, bu beklenen davranış |
| MODIS Nisan 2018 | BurnDate/Uncertainty -9999, kaynak maskeleri 0; QA=3; FirstDay=85, LastDay=138 |
| MODIS Mayıs 2018 | BurnDate/Uncertainty -9999, kaynak maskeleri 0; QA=3; FirstDay=103, LastDay=175 |

İki MODIS ayında QA_land=1, QA_valid=1, QA_shortened_period=0,
QA_special_condition=0; maskeli yanma tarihi nedeniyle yangın yokluğu kararı verilmez.
İlk sonraki Sentinel görüntüsü adaydan yaklaşık 9 saat 39 dakika sonradır
(Console dakika hassasiyetinde). Görüntülerde tesis benzeri yapılar mevcut;
kesin tesis/ekipman kimliği ve ısı kaynağı doğrulanmadı. Önceki uygun görüntü
olmadığından görüntü karşılaştırmasıyla önceki arazi durumu ya da yanma değişimi
belirlenemez. Maskeli deliklerden görünen Google uydu altlığı tarihli Sentinel
verisi değildir; bu delikler tarihsel yapı veya yanma kanıtı sayılmaz.

Geçici değerlendirme: önceki yakın type=2 kaydı ve adaydan kısa süre sonraki
teşhis amaçlı görüntüde tesis bağlamı, sabit ısı kaynağı olasılığını destekliyor;
yangın/sabit kaynak etiketi kesinleşmedi. Hiçbir kayıt elenmedi. Kullanıcının
sonradan paylaştığı 2017 örtü özellikleri kayda eklendi. Sınıf 60 ve urban %0,
2018 tarihli görüntüdeki tesis bağlamını geçersiz kılmaz; farklı yıl, çözünürlük,
örnekleme alanı ve sınıflandırma hatası olasılıkları ayrıştırılmadı. Bu piksel
2017 için ağaç örtüsü göstermiyor; tüm çevrenin ormansız olduğu veya yangın
olmadığı sonucu çıkarılmaz. Önceki uygun görüntü bulunmaması belirsizliği sürüyor.

Örnekleme kapsamı: H01–H03, 100 m içinde yalnızca adaydan sonra type=2 görülen;
H04–H06, adaydan önce type=2 bulunan hedefli inceleme örnekleridir. Seçim eğitim
verisi, aday yoğunluğu ve konumlar arası mesafe üzerinden yapılmıştır; rastgele
veya temsil edici doğruluk örneklemi değildir. Amaç yanlış eleme riskini ve
filtre tasarımının sınırlarını incelemektir. Bu altı örnekten tüm verinin hata
oranı veya bir eleme kuralının duyarlılığı/özgüllüğü hesaplanamaz. Sonraki filtre
kontrolü, sabit kaynağa yakın gerçek bitki yangınlarını ve sabit kayda uzak
örnekleri de kapsamalı; seçim yöntemi ve belirsiz kararlar ayrıca raporlanmalıdır.


## Tarihsel kaynak incelemesi — H06 ve altı vaka özeti (1 Ekim 2026)

Kaynak: kullanıcının Console çıktısı ve dokuz ekran görüntüsü.
Aday N20_815590_1070, 2018-04-21 00:18 UTC, 37.25166 N / 30.44355 E.
Denetim tablosunda 100 m içinde son önceki type=2 kaydı 2018-04-18 00:24 UTC,
ilk sonraki kayıt 2018-04-24 00:12 UTC. Bunlar tesis kuruluş tarihleri değildir.

| Gözlem | Değer / kapsam |
|---|---|
| Önceki görüntü | 2018-04-15 08:59 UTC; 20180415T084601_20180415T085037_T35SQB |
| Sonraki görüntü | 2018-04-22 08:49 UTC; 20180422T083601_20180422T084821_T36STG |
| Sonraki sabit kayıt dönemi | 2018-04-30 08:45 UTC; 20180430T084559_20180430T084557_T35SQB |
| Kaynak / uygun görüntü sayıları | Önce 73 / 25; sonra 34 / 12; sonraki sabit dönem 34 / 12 |
| Önce açık alan oranı | Çekirdek 1; bağlam 0.9996863607515535 |
| Sonra açık alan oranı | Çekirdek 1; bağlam 1 |
| Sonraki sabit dönem açık alan oranı | Çekirdek 0.9042166851608999; bağlam 0.9018321451940624 |
| 2017 nokta örtüsü | Sınıf 30; grass %52, shrub %19, tree %9, urban %0 |
| NDVI medyanı: önce / sonra | 0.10081708574843856 / 0.13803625851869583 |
| NBR medyanı: önce / sonra | -0.1374941342092914 / -0.10471203923225403 |
| MODIS Nisan 2018 | BurnDate/Uncertainty -9999; iki kaynak maskesi 0; QA=3; FirstDay=76, LastDay=141 |
| MODIS Mayıs 2018 | BurnDate/Uncertainty -9999; iki kaynak maskesi 0; QA=3; FirstDay=100, LastDay=166 |

İki MODIS ayında QA_land=1, QA_valid=1, QA_shortened_period=0,
QA_special_condition=0; maskeli yanma tarihi nedeniyle yangın yokluğu kararı verilmez.
Önceki görüntü yaklaşık 6 gün önce, sonraki yaklaşık 1 gün 8.5 saat sonra;
H01/H03/H04'e göre daha yakın tarihli bir karşılaştırmadır. Görüntülerde
adaydan önce tesis benzeri yapı düzeni mevcut. Kesin tesis/ekipman adı belirlenmedi.
2017 nokta örtüsünde urban %0 olması bu görsel gözlemi ortadan kaldırmaz;
karma piksel, tarih farkı ve sınıflandırma hatası olasılıkları ayrıştırılmadı.

NDVI medyanı yaklaşık 0.0372, NBR medyanı yaklaşık 0.0328 artıyor; bu çiftte
belirgin bitki yanmasını destekleyen azalma görülmedi. Yangın kesin dışlanmadı.
Önce ve sonra farklı Sentinel tile/UTM bölgeleri kullanılmış; ortak maske,
hizalama/yeniden örnekleme ve bakış/gölge etkileri nedeniyle küçük farklar
kesin fiziksel değişim sayılmamalı. İndekslerin işareti doğrudan olay türü değildir.
Maskeli deliklerden ve tarihli görüntü alanı dışından görünen Google altlığı,
tarihli Sentinel gözlemi olarak yorumlanmaz.

Geçici değerlendirme: önceki yakın type=2 kaydı ve adaydan önce mevcut tesis
bağlamı, sabit ısı kaynağı olasılığını destekliyor; kesin kaynak ve yangın
etiketi doğrulanmadı. Hiçbir kayıt elenmedi.

Altı hedefli vakanın ilk inceleme turu tamamlandı; olay doğrulaması ve filtre
kalibrasyonu tamamlanmadı. Ortak sonuçlar:

- Yakın type=2 kaydı otomatik eleme için yeterli değil; kayıt zamanı tesis tarihi değildir.
- Arazi örtü haritası, tarihli görüntü ve tespitin kaynak sınıfı birlikte ele alınmalı.
- Ağaç örtüsünün azlığı ot/çalı yangınını dışlamaz; tesis yakınında gerçek yangın olabilir.
- Tüm altı örnekte MODIS yanma tarihi maskeli geldi; bunlar negatif etiket yapılmaz.
  Bu örüntünün Earth Engine bant maskesi/ingestion davranışıyla ilişkisi ayrıca incelenmeli;
  mevcut çıktılardan tümünün yanmamış olduğu varsayılmaz.
- Hedefli örneklerden tüm veri için doğruluk veya yanlış eleme oranı çıkarılamaz.
- FIRMS arşivinin type alanını üreten işleme sürümü ve bilinen düzeltmelerin indirilen
  dosyalara uygulanıp uygulanmadığı, mevcut CSV version=2 değerinden çıkarılamaz.
  Bu kaynak denetimi kapanmadan type temelli nihai filtre dondurulmaz.

Sıradaki çalışma: FIRMS kaynak üretim sürümünü doğrulamak ve maskeli MODIS yanma
bandının anlamını kaynak düzeyinde kontrol etmek. Ardından eğitim döneminde
sabit kaynağa yakın gerçek bitki yangınlarını da kapsayan karşılaştırma örnekleri
ile aday filtrelerin etkisi ölçülecek. 2025 final test bu karar sürecine katılmayacak.


## Kaynak anlamı denetimi — 1 Ekim 2026

Resmî VIIRS C2 kılavuzu 1.2, bölüm 6.1 ve FIRMS duyurusu, aylık Vxx14IMGML
üretim sürümü 1/2'de bazı type=2 kaynakların type=0 yazılabildiğini; Mayıs 2025'te
hatanın düzeltilip aylık ürünlerin üretim sürümü 3'e yeniden işlendiğini bildiriyor.
FIRMS CSV Collection/Version alanı ile bu aylık üretim sürümü aynı kavram değildir.
815579 ve 815590 teslimlerinin düzeltilmiş type değerlerini içerdiği henüz teyit
edilmedi; CSV version=2 tek başına hata veya düzeltme kanıtı değildir.
Genel Readme metni NOAA-20 standart ürün durumu konusunda güncel teslimle uyumsuz
bilgi içeriyor; bu metin tek başına talebe özgü işlem geçmişi sayılmaz.

MODIS bağımsız salt okunur kontrolü: doğrudan Earth Engine varlığından, hiçbir
updateMask/selfMask uygulanmadan H06, Nisan 2018 noktası native projeksiyonda
örneklendi. BurnDate/Uncertainty maskeleri 0; QA/FirstDay/LastDay maskeleri 1.
QA=3, FirstDay=76, LastDay=141. Bu maske inceleme betiğinden kaynaklanmıyor.
NASA ham HDF kılavuzunda BurnDate 0=yanmamış, -1=eşlenmemiş, -2=su; belirsizlik
yanmamış ve eşlenmemiş piksellerde 0. Earth Engine maskesiyle ham HDF değerinin
birebir ilişkisi henüz doğrulanmadı. Bu nedenle maskeli bant 0 ile doldurulup
negatif etikete çevrilmez. Var olan yanmış piksel eşleşmeleri bu kontrolde değişmedi.
Yerel salt okunur kontrol raporu: outputs/reports/firms_modis_source_semantics_check.json.

Resmî kaynaklar:
- https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf
- https://firms2.modaps.eosdis.nasa.gov/api/data_availability/
- https://firms.modaps.eosdis.nasa.gov/download/Readme.txt
- https://lpdaac.usgs.gov/documents/1006/MCD64_User_Guide_V61.pdf
- https://developers.google.com/earth-engine/apidocs/ee-image-unmask

FIRMS destek sorusu taslağı (gönderilmedi):

Subject: Confirm corrected VIIRS fire Type field for archive requests 815579 and 815590

Hello FIRMS team,
We downloaded Turkey VIIRS Collection 2 archive CSVs for requests 815579
(S-NPP, 2018-01-01 through 2024-12-31) and 815590 (NOAA-20, 2018-04-01 through
2024-12-31). Both CSVs contain version=2 and a type field.
The VIIRS C2 375 m User Guide v1.2 section 6.1 describes the monthly production
versions 1/2 Type error corrected in May 2025 and reprocessed to version 3.
Do these two delivered FIRMS requests include the corrected Type classifications?
Does CSV version=2 denote Collection 2 rather than the monthly production version?
Please identify the underlying production/reprocessing version and whether any
2018–2024 months in either request still use the affected Type classifications.
Thank you.

Earth Engine veri desteği sorusu taslağı (gönderilmedi):

For MODIS/061/MCD64A1 image 2018_04_01, at longitude 30.44355 and latitude
37.25166 sampled in the native BurnDate projection, BurnDate and Uncertainty
have mask=0, while QA=3, FirstDay=76 and LastDay=141 are unmasked. No user
updateMask/selfMask was applied. How are native HDF BurnDate values 0 (unburned),
-1 (unmapped), and -2 (water) mapped to Earth Engine values and per-band masks?
Is this expected ingestion behavior or a data issue? We need to distinguish
valid unburned pixels from unavailable observations without filling masked data.

Açık işler: talebe özgü FIRMS üretim sürümü teyidi ve ham HDF/EE maske eşdeğerliği.
Her iki soru çözülene kadar otomatik kaynak elemesi ve negatif etiket üretimi yok.


### Ham MODIS erişim hazırlığı — 1 Ekim 2026

H06 Nisan 2018 noktası için NASA CMR granül sorgusu, aynı Collection 6.1 ve
h20v05 tile dosyasını döndürdü: MCD64A1.A2018091.h20v05.061.2021354033000
(CMR G2595802694-LPCLOUD). Oturumsuz doğrudan HEAD isteği HTTP 403 verdi;
kimliği doğrulanmış tarayıcı indirmesi henüz yapılmadı. Karşılaştırma tamamlanmadı.
Ham dosya hedefi data/raw/burned_area/source_checks/; klasör oluşturuldu.
Dosya indirildiğinde kimlik, SHA-256, native grid/piksel adresi, bütün beş bant
ve ham fill değerleri EE değer/maskeleriyle birlikte denetlenecek. Koleksiyon
aynı olsa da yeniden işleme tarihi farkı ayrıca raporlanmalı.

Mevcut Rasterio ortamında HDF4 sürücüsü yok (HDF5 farklı formattır). pyhdf için
Python 3.12 Windows amd64 hazır wheel bulundu; henüz kurulmadı. Bağımlılık
projenin pyproject/lock yöntemiyle ayrıca eklenmeli, gizli ortam değişikliği
ve HDF dosyasının GeoTIFF'e rastgele dönüştürülmesi yapılmamalı.
Erişim/uyumluluk raporu outputs/reports/modis_native_source_access_check.json.


### 2026-10-01 — Nisan 2018 native HDF ile maskeli MODIS değerlerinin doğrulanması

Kullanıcı Earthdata üzerinden `MCD64A1.A2018091.h20v05.061.2021354033000.hdf`
dosyasını indirdi ve `data/raw/burned_area/source_checks` klasörüne yerleştirdi.
Dosya HDF4 olarak açıldı. SHA-256: `792bfbfa260a5f5f3e2fe512dcf19712d5e010cd27a3432374aae1247afe74a9`.
`pyhdf` bağımlılığı kullanıcı tarafından uv ile eklendi.

Piksel satır/sütunu dosyanın StructMetadata sınırlarından ve kendi sinusoidal
küresel yarıçapından (6371007.181 m) hesaplandı; tam sayı alt sınırı kullanıldı.
H06 için sıfır tabanlı satır 659, sütun 1015 bulundu. Native değerler:
BurnDate=0, Uncertainty=0, QA=3, FirstDay=76, LastDay=141.
H06 merkezinin 3x3 komşuluğunda BurnDate=0 ve QA=3 bulundu.

Aynı dosya H01, H03, H04 ve H05 noktalarını da kapsıyor. Beş noktanın
Nisan 2018 kaynak pikselinde BurnDate=0, Uncertainty=0 ve QA=3 okundu.
Earth Engine `MODIS/061/MCD64A1/2018_04_01` üzerinden yeniden yapılan
okumada beş noktada BurnDate ve Uncertainty maskeli; QA/FirstDay/LastDay
native dosyayla birebir aynı. Ayrıntılı satır/sütun ve bant değerleri
`outputs/reports/modis_native_hdf_comparison.json` dosyasına kaydedildi.

Bu bulgu önceki maskeli EE çıktısından çıkarılan belirsizliği, yalnızca
kontrol edilen bu beş Nisan pikseli için giderir: native ürün bunları
**yanmamış** sınıfında kaydetmiştir. -9999 native BurnDate değildir;
betiğin maskeli değer yerine koyduğu işarettir. Bu noktalar için veri yok
sonucu artık kullanılmamalıdır. Ancak tüm maskeli EE piksellerini sıfırla
doldurmak için genel kural çıkarılmadı; bütün varlığın veya üretim granülünün
birebir eşliği kanıtlanmış değildir. H02'nin Ekim/Kasım ayları ve diğer
vakaların Mayıs ayları henüz native dosyadan kontrol edilmedi.

Ürünün yanmamış sınıfı, küçük/kısa süreli yangının kesinlikle olmadığını
kanıtlamaz ve otomatik eleme gerekçesi değildir. H05'in aday öncesi uygun
Sentinel-2 görüntüsü bulunmaması devam eden bir sınırlamadır. FIRMS
815579/815590 isteklerindeki Type alanının düzeltilmiş üretimden geldiği
henüz doğrulanmadı; kullanıcı NASA'ya e-posta gönderdiğini bildirdi ve
cevap bekleniyor. Hiçbir kayıt elenmedi; 2025 test verisine erişilmedi.


### 2 Ekim 2026 — Meteoroloji kaynağı için ilk bağımsız kontrol

Kullanıcı NASA FIRMS yanıtını beklerken bağımsız meteoroloji hazırlığına devam
edilmesini istedi. ERA5-Land saatlik Earth Engine kaynağı incelendi:
`ECMWF/ERA5_LAND/HOURLY`. Bu, geçmişi yeniden hesaplayan reanalysis ürünüdür;
verinin gözlem zamanı geçmişte olsa da aynı anda erişilebilir olduğu varsayılmaz.
Operasyonel hava tahmini doğrulaması veya gerçek zamanlı özellik tablosu oluşturulmadı.

Kaynak belgeler:
- https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY
- https://confluence.ecmwf.int/spaces/CKB/pages/140385202/ERA5-Land+data+documentation

Native Earth Engine grid EPSG:4326 ve 0,1 derece aralıklıdır; 5 km pilot gridden
daha kabadır. İnceleme için AOI oranı >=0,99 olan mevcut hücrelerden dört kontrol
konumuna en yakın hücre merkezleri seçildi. Bunlar nokta örnekleridir; il ortalaması
veya hücre alan ortalaması değildir. Kontrol konumları Antalya (30,7;37,1), Muğla
(28,36;37,21), İzmir (27,18;38,4), Mersin (34,5;36,9). Gerçek seçilen merkez ve
grid kimlikleri raporda kayıtlıdır. Bu örnekleme nihai mekânsal eşleme kararı değildir.

İncelenen iki pencere [2017-12-31,2018-01-02) ve [2018-07-01,2018-07-03).
96 farklı saat x 4 nokta = 384 kayıt. 2017 verisi eğitim etiketlerine dahil değildir;
2018 başındaki geçmiş pencerelerin hazırlık ihtiyacını kontrol etmek içindir.
2024/2025 gözlemleri sorgulanmadı.

Seçilen bantlar: temperature_2m, dewpoint_temperature_2m (K), 10 m rüzgârın
u/v bileşenleri (m/s), total_precipitation ve total_precipitation_hourly (m),
volumetric_soil_water_layer_1 (hacim oranı). Her bandın maskesi, native piksel
x/y kimliği, saat ve kaynak görüntü kimliğinin zaman bilgisi korundu. İlk kontrol
örneğinde yedi bant için 384/384 geçerli kayıt bulundu; bu, tüm pilot/yıl kapsamının
eksiksiz olduğunu kanıtlamaz. Sıcaklık aralığı 273,2456–309,9385 K (yaklaşık
0,10–36,79 C). Kaynak değerler dönüştürülmeden saklandı.

Yağışın birikimli bandı saatlik gibi toplanmamalıdır. ECMWF belgesine göre 00 UTC
birikimi önceki günün tamamını kapsar; yeni birikim 01 UTC'de yeni güne başlar.
Saatlik yağış 01 UTC için o andaki birikime, diğer saatlerde ardışık birikim
farkına eşit olmalıdır. 376 ardışık-saat karşılaştırmasında maksimum fark 0 m
bulundu; gece yarısı geçişleri dahil. 11 negatif saatlik değer var; minimum
-7,450580596923828e-09 m (yaklaşık -0,00000745 mm). Bunlar fiziksel negatif
yağış olarak yorumlanmaz; neden ve düzeltme politikası henüz genel veri üzerinde
belirlenmedi. Ham değerler korunur, sıfıra kesme otomatik uygulanmadı.

İlk sorgu her saat için sampleRegions yaptığı için EE eşzamanlı aggregation
limitine takıldı. Küçük örnek saatleri toBands ile istifleyip tek sampleRegions
kullanarak sorgu tamamlandı. Bu yöntem yalnızca küçük kaynak kontrolü için;
yıllık/bütün-pilot sorgusu aynı şekilde genişletilmez (bant/sorgu limitleri).
Earth Engine ihracı veya batch görevi başlatılmadı.

Yerel örnek: `data/raw/meteorology/source_checks/era5_land_hourly_small_sample.csv`.
SHA-256: `2531ad89050819577c63ec2e01607ec3df40bb9d2d575a6a20e10c175185f792`.
Rapor: `outputs/reports/era5_land_source_check.json`.
Bunlar kısa, salt kaynak kontrolüyle hazırlandı; ayrı kalıcı meteoroloji betiği
henüz oluşturulmadı. Bu kontrol henüz kalıcı bir betiğe dönüştürülmedi.

Sıradaki uygulama: bu sınırlı kontrolü yeniden üretilebilir betik hâline getirmek;
sonra küçük günlük geçmiş özellik örneği ve zamansal denetim. 00:00 UTC T anı
için gerçekleşmiş tahmin-günü sıcaklık/yağış bilgisi kullanılmayacak. Fiziksel
birikim aralığı ile kaynak zaman etiketi ayrı tutulacak. İlk inceleme taslağı
T'den kesin önceki saatlerle çalışır; yağışın saat sonu damgası nedeniyle
pencereler açıkça belgelenir. 3/7/14 günlük geçmiş pencereler hazırlanırken
2018 başlangıcından önce yeterli 2017 saatleri gerekir. available_at bilinmiyorsa
uydurulmaz; reanalysis araştırması, operasyonel kullanılabilirlik testiyle ayrılır.
Bağıl nem türetme formülü, yağış düzeltme eşiği ve tam pilot mekânsal eşleme
henüz seçilmedi. Model/etiket üretilmedi, FIRMS kayıtları elenmedi.


### 2 Ekim 2026 — NASA e-postasının geçici teslim sorunu

Kullanıcının paylaştığı Gmail bildirimi, support@earthdata.nasa.gov adresine
ilk mesajın henüz teslim edilmediğini gösteriyor: alıcı sunucuya bağlantı
zaman aşımına uğramış. Bildirim kalıcı başarısızlık değil; Gmail 46 saat daha
yeniden deneyeceğini belirtiyor. Önceki yanıt-bekleme durumu bu teslim
belirsizliğiyle birlikte okunmalıdır; NASA'nın mesajı aldığı doğrulanmadı.

Resmî Earthdata forumunda benzer bir teslim sorununda LAADS kullanıcı
hizmetleri earthdata-support@nasa.gov adresini önermiş ve kullanıcı teslimin
başarılı olduğunu bildirmiş (2024 kaydı, güncel teslim garantisi değildir):
https://forum.earthdata.nasa.gov/viewtopic.php?t=6100
Bu adres güncel Earthdata Login belgelerinde de bulunuyor; doğrudan FIRMS
teknik ekibi olduğu varsayılmayacak. Orijinal sorunun bu adrese, gerekirse FIRMS
archive/VIIRS ekibine yönlendirme talebiyle iletilmesi kullanıcıya önerildi.
Asistan e-posta göndermedi; kullanıcının yeniden gönderdiği henüz doğrulanmadı.
Meteoroloji kaynak hazırlığı bu teslim sorunundan bağımsız ilerleyebilir.


### 2 Ekim 2026 — Meteoroloji zaman ve mekân denetiminin devamı

384 kaydın SHA-256'sı tekrar doğrulandı. Grid/zaman anahtarları benzersiz;
her örnek konum/gün için 24 saat var. Çiy noktası sıcaklığı hava sıcaklığını
geçmiyor; dört konumda native kaynak piksel kimliği zamanla sabit. Negatif
saatlik yağışın minimumu -0,00000745058 mm, toplamı yaklaşık -0,00007023635 mm;
bu dar örnekten genel düzeltme eşiği çıkarılmadı.

Örnek CSV üzerinden dört nokta x iki tahmin anı (2018-01-01 00 UTC ve
2018-07-02 00 UTC) için sekiz satırlık geçmiş özellik kontrolü yapıldı.
Her satırda [T-24 saat,T) zaman etiketli 24 gözlem var; son kaynak saati
T-1 saat ve bütün kaynak etiketleri kesin olarak T'den önce. Ortalama/min/max
sıcaklık C, ortalama çiy noktası C, saatlik sqrt(u²+v²) üzerinden ortalama/maksimum
rüzgâr m/s, ham yağış toplamı mm ve ortalama üst toprak su hacim oranı çıkarıldı.
Toprak su oranı bağıl hava nemi değildir; bağıl nem türetilmedi.

Saatlik yağış son saati kapsadığı için bu etiket seçiminin fiziksel yağış
penceresi (T-25 saat,T-1 saat] olur. Bu, tam önceki UTC takvim günü toplamı
değildir; özellikle böyle adlandırılmadı. available_at boş bırakıldı. Bu sekiz
satır model hazır veri değil; geçmiş pencereler için denetim örneğidir.
Kaynak saat sırası, tamlık, birimler ve benzersiz anahtar kontrolleri geçti.
Ara CSV: data/interim/meteorology/source_checks/era5_land_daily_past_sample.csv.
Rapor: outputs/reports/era5_land_daily_past_sample_check.json.

Tam pilot gridin (data/aoi/grid_5km.geojson, 2.899 hücre) EPSG:6933 merkezleri
2018-01-01 00 UTC ERA5-Land native pikselleriyle eşlendi. Ara aday dikdörtgen
12.006 hücre içerir ve tam pilotla karıştırılmadı. 2.899 merkez için kayıt geldi;
849 farklı native piksel, aynı native pikselde en çok dört pilot merkezi var.
711 native pikselde seçilen altı bant geçerli, 138 native pikselde maskeli.
Maskeli bantlar 353 pilot merkezini etkiliyor: 321 AOI oranı <0,99, 32 >=0,99.
Bu, yalnızca bir saatin ve merkez yönteminin kontrolüdür; tüm gün/yıl kapsamı,
maskenin nedeni veya hücrenin tamamının veri dışı olduğu iddia edilmez.

pixelCoordinates bu kaynakta köşe tabanlı tamsayı değil, (sütun+0,5,satır+0,5)
piksel merkezi koordinatlarını döndürdü. Ters affine alt tamsayı +0,5 hesabı
bütün 2.899 kayıtta eşleşti. İlk tamsayı eşitlik varsayımı denetimde başarısız
oldu ve merkez koordinatı sözleşmesiyle düzeltildi; veri dosyası kaybı yok.
Ara eşleme: data/interim/meteorology/source_checks/era5_land_grid_centroid_diagnostic.csv.
Rapor: outputs/reports/era5_land_grid_centroid_check.json.

Hiçbir hücre elenmedi, maskeli sıcaklık/yağış sıfırla doldurulmadı, en yakın
kara pikseliyle gizli ikame yapılmadı. Nihai hava verisi eşleme kuralı seçilmeden
AOI içi alanla kesişim ve geçerli kaynak alanı ağırlıkları incelenmeli.
2018–2024 toplu indirmesi henüz başlatılmadı; 2025 kapalı. Kaynak kontrolünün
kalıcı bir betiğe dönüştürülmesi sıradaki uygulama adımıdır.


### 2 Ekim 2026 — Kalıcı meteoroloji veri hazırlama hattı

Kullanıcının yol haritasına dönüp meteoroloji işini ilerletme talimatıyla
scripts/meteorology/prepare_era5_land.py oluşturuldu. Antigravity'deki başka
bir ajana görev verme önerisi geri çekildi; bu sohbet üzerinden uygulama yapıldı.

Üç aşama: weights (yerel native kaynak/AOI kesişimleri), download (EE'den günlük
agregalı native GeoTIFF+manifest), prepare (yerel alan ağırlıklı günlük tablo).
Mevcut AOI içi geometri kaynak SHA'sı doğrulanır. 2.899 hücre için 6.213 pozitif
kaynak piksel kesişimi hesaplandı; toplam kesişim alanlarıyla AOI parça alanları
arasında en büyük bağıl fark 7,98e-13'ten küçük. Her raster 37x93 native piksel,
EPSG:4326 ve 0,1 derece gridinde. İnterpolasyon veya en yakın kara doldurması yok.

Geçerli kaynak saatleri [T-h,T), T=00 UTC. 336 saatlik kaynak listesinin
benzersiz zaman sayısı, ilk/son saati ve 24 saatlik pencere sayısı doğrulanır.
Native pikselde ilgili bandın bütün saatleri geçerli değilse o özellik maskeli
kalır. Her alan ortalaması yalnızca geçerli kaynak kesişimlerinden hesaplanır;
geçerli alan payı ayrı sütundur. Sıfır geçerli alan NaN, yağıştaki gerçek sıfır
ise geçerli sıfırdır. Hücre çıkarılmaz ve uygunluk oranı eşiği seçilmez.

13 çıktı: sıcaklık ortalama/min/max, çiy noktası ortalaması, saatlik u/v'den
rüzgâr hızı ortalama/max, üst toprak su oranı ortalaması, 24/72/168/336 saat
ham yağış toplamları, 24/336 saat negatif yağış-saatlerinin alan ortalamaları.
Maksimumlar piksel içi zamansal maksimumların alan ağırlıklı ortalamasıdır.
Yağış son-saati T-1 saat; fiziksel pencere (T-h-1 saat,T-1 saat]. Birikim bandı
saatlik gibi toplanmaz. Negatif yağış ham olarak tutulur; fiziksel düzeltme veya
model eksik değer politikası bu aşamada kesinleşmez. Bağıl nem formülü seçilmedi;
çiy noktası saklanır. Operasyonel forecast/erişilebilirlik iddiası yok.

2018-01-01 ve 2018-07-02 için native rasterlar indirildi ve toplam 5.798
hücre-gün satırı hazırlandı. Her gün sıcaklıkta 2.400 hücre tam alanla geçerli,
310 kısmi, 189 sıfır geçerli alan. İlk günün eski merkez yönteminde 353
maskeli hücresinden 164'ü geçerli alan kesişimiyle veri aldı. 189 hücre için
hücrenin tümü yangına uygunsuz veya bütün meteoroloji kaynakları eksik sonucu
çıkarılmaz; bu kaynağın bu yöntemle kapsamadığı alan olarak kalır.

İki gün x dört önceki kontrol noktası x sekiz özellik native rasterdan yeniden
okunup bağımsız saatlik CSV hesaplarıyla karşılaştırıldı. En büyük mutlak fark
8,91e-7; float32 toleransı içinde. Zaman/anahtar/saat tamlığı ve raster hizası
kontrolleri geçti. Testlere alan ağırlığı, kısmi/tam eksik veri, gerçek sıfır
yağış ve final-test tarih sınırı kontrolleri eklendi. 26 test, Ruff lint ve
28 Python dosyası biçim kontrolü geçti.

2018–2024 toplu indirmesi henüz yapılmadı. Betik açık start/end ile ay veya
aralık bazında çalışır; doğrulanmış mevcut rasterları atlayarak devam edebilir.
2025 tahmin tarihleri remote erişimden önce reddedilir. 2018 başındaki 14 günlük
geçmiş için 2017-12-18 saatlerinden yararlanılır; 2017 yangın etiketi değildir.
Tam dönem için kullanıcı terminalinde çalıştırılacak ilk ay komutları betik
rehberine eklendi. NASA ilk e-postasının teslimi doğrulanmadı; alternatif adrese
önerilen yeniden gönderimin yapıldığı henüz teyit edilmedi.


### 2 Ekim 2026 — Ocak 2018 meteoroloji toplu kontrolü

Kullanıcının download/prepare çalıştırması sonrası 2018-01-01 dahil,
2018-02-01 hariç 31 günün dosyaları yerelden denetlendi: 2.899 hücre/gün,
toplam 89.869 benzersiz hücre-gün. Her TIF ve CSV SHA-256 kaydı, kaynak/sürüm,
bant sırası metadatası, AOI ağırlık manifesti, raster boyutu/CRS/hizası,
günlük ve dönem raporu eşleşti. CSV'deki bütün 13 özellik kaynak raster ve
kesişim ağırlıklarından yeniden hesaplandı; en büyük mutlak CSV yuvarlama
farkı 2,85e-14'ten küçük. Bu kontrol mekânsal hazırlamayı doğrular; saatlik
kaynağın bağımsız doğrulaması önceki iki gün/dört nokta örneğiyle sınırlıdır.

Zaman sütunları ve geçmiş pencereler, benzersiz anahtarlar, NaN-geçerli alan
ilişkisi, sıcaklık min/ortalama/max sırası, çiy noktası, rüzgâr ve toprak suyu
aralık kontrolleri geçti. Her gün sıcaklıkta 2.400 hücre tam alan, 310 kısmi
alan, aynı 189 hücre sıfır geçerli kaynak alanıyla temsil ediliyor. 84.010
satırda 13 özelliğin tamamı dolu; 5.859 satırda eksik veri var. Kısmi alanla
üretilen dolu satırlar, tüm hücre alanının gözlendiği anlamına gelmez.

24 saatlik ham yağış toplamında 35 hücre-gün negatif; minimum yaklaşık
-0,0000119209 mm. 72/168/336 saat toplamlarında negatif yok. Ham değerler
korundu; model için düzeltme ve eksik/kısmi alan politikası henüz seçilmedi.
Hücre elemesi veya eksik veriyi sıfırla doldurma yapılmadı.

Denetim raporu: outputs/reports/meteorology/audit_2018-01.json.
Ocak veri hazırlaması kontrolü geçti; eğitim tablosu henüz nihai değil.
Sıradaki indirme aralığı 2018-02-01 dahil, 2019-01-01 hariçtir; sonrasında
2018 yılı birlikte denetlenecek. 2019–2023 eğitim dönemi ve 2024 doğrulama
dönemi sonraki aşamalardır; 2025 kapalıdır. available_at bilinmiyor ve boş;
bu özellikler geriye dönük yeniden analiz araştırması içindir.


### 2 Ekim 2026 — 2018 meteoroloji yılı tamamlandı

Kullanıcı Şubat–Aralık indirme ve prepare işlemlerini tamamladı. Kalıcı yerel
denetim 2018-01-01 dahil / 2019-01-01 hariç çalıştırıldı. Coğrafya, FIRMS,
örtü/MODIS ve meteoroloji denetimleri geçti. 365 günlük dosya, 2.899 hücre/gün,
toplam 1.058.135 benzersiz hücre-gün. Metadata, dosya özetleri, zaman sütunları,
geçerli alan oranları ve 13 özelliğin kaynak rasterlardan yeniden hesabı doğrulandı.

989.150 satırda bütün özellikler dolu; 68.985 satırda eksik veri var. Sıcaklıkta
her gün 2.400 tam kapsamlı, 310 kısmi kapsamlı ve aynı 189 sıfır kapsamlı hücre
bulunuyor. Dolu satır, tam alan kapsamı veya bağımsız yangın örneği anlamına gelmez.
Sıcaklık min/ortalama/max, çiy noktası, rüzgâr ve toprak suyu fiziksel ilişki/aralık
kontrolleri geçti. Alan kapsamı eşit olan kayıtlar arasında ilişkiler karşılaştırıldı.

24 saatlik ham yağışta 1.527 negatif hücre-gün var; minimum -0,0000484151 mm.
72/168/336 saat toplamlarında negatif yok. Ham veri değiştirilmedi ve hiçbir
hücre elenmedi; model öncesi eksik/kısmi kapsam ve yağış düzeltme kuralları açık.

Raporlar:
- outputs/reports/quality/project_audit_2018-01-01_2019-01-01.json
- outputs/reports/quality/weather_diagnostics_2018.json

2018 meteoroloji hazırlaması doğrulandı; nihai eğitim veri seti henüz hazır değil.
Sıradaki çalışma 2019 meteoroloji indirme ve prepare, ardından aynı yıllık denetim.
2020–2023 eğitim ve 2024 doğrulama sonraki dönemler; 2025 final testi kapalı.


### 3 Ekim 2026 — 2019 meteoroloji kontrolü ve kapanış

2019'un 365 günü ve 1.058.135 hücre-gün doğrulandı; 2018–2019 toplamı
2.116.270 satır. Kaynak raster/CSV özetleri, zaman pencereleri, alan oranları
ve bütün özelliklerin yeniden hesabı geçti. Günlük kapsam sıcaklıkta 2.400 tam,
310 kısmi, aynı 189 eksik hücre. 24/72 saat ham yağışta 10.221/909 negatif
hücre-gün; minimum -0,0000163227 mm. 168/336 saat toplamlarında negatif yok.
35 test, lint/format ve paket/kilit kontrolleri geçti. Ayrıntılar 3 Ekim günlüğü
ve outputs/reports/quality altındaki 2019 raporlarında. Eğitim veri seti henüz
nihai değil. Kullanıcı GitHub push sonrası mola istedi; sonraki dönem 2020.
