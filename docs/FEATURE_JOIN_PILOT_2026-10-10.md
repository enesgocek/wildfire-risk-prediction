# Geriye dönük özellik birleştirme denemesi — 10 Ekim 2026

## Amaç ve kapsam

Uydu gözlem ve bitki örtüsü kuyrukları sürerken, tamamlanmış özelliklerin
aynı hücre/tahmin anahtarında birleştirilebildiği kontrol edildi. Deneme
**1 Ağustos 2018, 00:00 UTC** için dört ilin 2.899 hücresini kapsar.
Yangın etiketi, habitat seçimi, imputasyon veya eğitim yapılmadı. Bu,
nihai model veri setinin kabulü değildir.

`feature_join.py` ortak kütüphanede, çevrimdışı çalıştırma/geri okuma
`scripts/quality/verify_feature_join_pilot.py` altında yer alır.
Canlı bulut ve bitki örtüsü üretim dosyaları değiştirilmedi; yeni iş açılmadı.

## Sütun sözleşmesi

Anahtar `(grid_id, prediction_timestamp_utc)`; tahmin saati 00:00 UTC.
Özellik tablosunda anahtarın yanında yalnız aşağıdaki **27 aday sütun** bulunur.
Bu liste, daha sonraki model deneyinde bütün alanların kullanılacağı kararı değildir.

| Grup | Alanlar | Sayı |
|---|---|---:|
| Meteoroloji | `temperature_mean_c`, `temperature_min_c`, `temperature_max_c`, `dewpoint_mean_c`, `wind_speed_mean_ms`, `wind_speed_max_ms`, `soil_water_layer_1_mean`; 24/72/168/336 saat için ayrı `rain_*h_nonnegative_mm` | 11 |
| Örtü | `forest_fraction`, `shrub_fraction`, `herbaceous_fraction`, `agriculture_fraction`, `urban_fraction`, `water_fraction`, `natural_vegetation_fraction` | 7 |
| Arazi | `elevation_mean_m`, `elevation_std_m`, `slope_mean_deg`, `northness_mean`, `eastness_mean` | 5 |
| Bitki örtüsü | `vegetation_30d_ndvi_median_mean`, `vegetation_30d_ndmi_median_mean`, `vegetation_60d_ndvi_median_mean`, `vegetation_60d_ndmi_median_mean` | 4 |

Ayrı `provenance.csv`, aynı anahtarlarla kaynak zamanlarını, görüntü yaşını,
destek oranlarını, eksiklik/meteoroloji uygunluk bayraklarını, manifest
kimliklerini ve işlem sürümlerini taşır. Bunlar model özellik listesine alınmaz.
Girdi tablosuna sonradan eklenmiş hedef/olay/gözlem sütunları açık özellik
listesinin dışında kalır. Hedef penceresinin gözlem tanıları bu denemede okunmaz.

Her kaynak için tam ve tekil hücre anahtarı zorunludur; satır düşüren iç
birleştirme veya çoğaltan eşleşme kabul edilmez. 30/60 günlük pencereler
ayrı tutulur; kısa pencere eksikleri uzun pencereden doldurulmaz.
Meteoroloji politikası yeniden hesaplanarak kaydedilmiş türev alanlarla
eşleştirilir. Son kaynak saati T−1 saat, hava penceresi [T−24 saat,T),
yağış aralıkları kayıtlı geçmiş saat sözleşmesindedir. Bitki örtüsünde
çekim tarihi kesimden önce, kesim T'den sonra olamaz; taşıma en fazla sekiz gündür.
UTC zamanları açık ISO biçiminde nanosaniye birimiyle okunur.

`available_at` alanları bilinmiyor; doldurulmaz. `operational_eligible=false`
ve habitat kararı açık kalır. ERA5-Land yeniden analiz ve 2017 örtü haritası
geriye dönük adaylardır; bu kontrol gerçek zamanda erişilebilirlik kanıtı değildir.
Komut, kaynak okumadan önce tarih kapsamını 2018–2023 ile sınırlar; doğrulama
ve kapalı final test bu denemede kullanılmaz.

## Gerçek veri geri okuması

Son kabul raporu:
`outputs/reports/dataset/feature_join_v1/20261010T120407Z_d4282cbe/readback.json`.
SHA-256 `b1b3f95757e3ce657042a80e086e309e8efa58acced87ef993571dfbd90b71f0`.
Kaynakların 24 dosyalık hash kaydı işlem öncesi/sonrası eşleşti. Meteoroloji
kaynak/türev tabloları ve yöntem hash'leri, arazi manifesti ve kayıtlı geri
okuması, bitki örtüsü ay tablosu ve eski ay kabulü kullanıldı. Ham kaynak
indirimi veya bütün ham integrallerin yeniden hesabı yapılmadı.

Kaydedilen CSV ayrı kod yolunda hücre anahtarına göre kaynak sütunlarıyla
karşılaştırıldı; kaynak değerleri ve NaN konumları korundu. Kalite tablosu
da CSV'den geri okundu. Kabul sırasında soket bağlantıları engellendi;
ağ isteği olmadı. Yeni rapor/dosya dizini kullanıldı, önceki kayıtlar korunur.

| Ölçüm | Sonuç |
|---|---:|
| Korunan hücre-gün | 2.899 |
| Aday özellik | 27 |
| Birincil meteoroloji uygunluğu olan hücre | 2.400 |
| Her meteoroloji adayında eksik hücre | 189 |
| 30 günlük bitki örtüsü desteği olan hücre | 2.896 |
| 60 günlük bitki örtüsü desteği olan hücre | 2.896 |
| Her NDVI/NDMI adayında eksik hücre | 3 |
| Her yön bileşeninde eksik hücre | 3 |
| Operasyonel uygun kabul edilen hücre | 0 |

Uygunluk/eksiklik sayıları bağımsız yangın, negatif etiket veya nihai habitat
uygunluğu sayısı değildir. İki dosyanın SHA-256 değerleri:

- `features.csv`: `b3ddbe51fb8c696555c6b9bfa1bf339558e3724170671edd9c178e37f688da05`.
- `provenance.csv`: `d225fbedc87da4afeaa7d2315fadb0bf8eefd5aadde6746af6f1589b3f0c6afa`.

18 yeni davranış kontrolü dahil **42 ilgili test** geçti; deprecation
uyarıları hata sayılarak çalıştırıldı. Anahtar kaybı/çoğalması, hedef sütunu
sızıntısı, gelecek kesim/çekim, belirsiz zaman, yanlış yaş, türev yağış
değişikliği ve pencere arası eksik doldurma reddedildi. Ruff/biçim kontrolü geçti.

```powershell
.\.venv\Scripts\python.exe scripts/quality/verify_feature_join_pilot.py --day 2018-08-01
```

Bu komut hazır kabul kayıtlarıyla sınırlı bir denemedir; tamamlanmamış
ayları indirmez. Sonraki aşama, diğer hazır günlerde/kesim geçişlerinde
aynı sözleşmeyi sınamak ve etiket/gözlem politikası kabul edildikten sonra
aylık özellik–hedef–split manifestini ayrı hazırlamaktır. Negatif etiket
izni halen false; 2025 final testi kapalıdır.
