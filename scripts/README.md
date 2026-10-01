# Betik rehberi

Komutları proje kökünden (`wildfire-risk-prediction`) çalıştır.
Python yorumlayıcısı `.venv/Scripts/python.exe`; JavaScript dosyaları Earth Engine
Code Editor'a kopyalanır. Betikler kendi konumlarından proje kökünü bulur.

## Klasörler

| Klasör | Amaç |
|---|---|
| `environment/` | Earth Engine erişimi ve MLflow altyapı kontrolü |
| `geography/` | AOI/grid doğrulama, hazırlama ve harita |
| `landcover/` | Raster kontrolü, alan ağırlıkları ve hücre örtü oranları |
| `firms/` | Yangın arşivleri, pilot kayıtlar, adaylar ve inceleme |
| `earth_engine/` | Earth Engine inceleme ve dışa aktarma kodları |

`setup.ps1` ortam kurulumu için kökte kalır. Raporlar `outputs/reports/`, görseller
`outputs/figures/`, ara tablolar `data/interim/` altında oluşturulur. Betikler mevcut
çıktılarını yeniden yazabilir; bütün aşamaları tekrar çalıştırmak gerekmez.

## Ortam

- `environment/check_gee_access.py`: mevcut kimlik doğrulamayla API erişimini kontrol eder.
- `environment/smoke_experiment.py`: veri yüklemeden MLflow altyapı deneyi kaydeder.
- `setup.ps1`: kilitli bağımlılıklar ile ortamı kurar.

## Coğrafi hazırlık

Önce Earth Engine'de `earth_engine/define_aoi.js` veya AOI ve grid ihracını birlikte
hazırlayan `earth_engine/build_grid.js` kullanılır. Drive indirmeleri ilgili veri
klasörlerine kaydedildikten sonra yerel sıra:

1. `geography/check_aoi_grid.py`: AOI ve aday grid kontrolü.
2. `geography/prepare_grid.py`: AOI ile kesişen tam hücreler ve alan oranları.
3. `geography/preview_grid.py`: genel grid ve kıyı önizlemesi.
4. `geography/prepare_grid_aoi_parts.py`: örtü hesabına uygun AOI içi geometriler.

## Arazi örtüsü

`earth_engine/inspect_landcover.js` kaynak inceleme ve GeoTIFF ihracı içindir.
Raster indirildikten ve AOI içi geometriler hazırlandıktan sonra:

1. `landcover/check_landcover.py`
2. `landcover/prepare_landcover_weights.py`
3. `landcover/calculate_landcover_fractions.py`
4. `landcover/preview_landcover_fractions.py`

2017 örtü tablosu inceleme adayıdır; model girdisi olarak henüz kesinleşmedi.

## FIRMS

Her sensör için sıra: arşiv kontrolü → pilot alan seçimi → aday seçimi.
Bu üç betik `--help` ile kaynak ve çıktı seçeneklerini gösterir. Parametresiz
çalıştırıldıklarında önceki S-NPP dosyalarını kullanırlar.

S-NPP:

```powershell
.\.venv\Scripts\python.exe scripts/firms/check_firms_archive.py
.\.venv\Scripts\python.exe scripts/firms/prepare_firms_pilot.py
.\.venv\Scripts\python.exe scripts/firms/prepare_firms_candidates.py
```

NOAA-20 için aynı kod, ayrı kaynak ve çıktılar:

```powershell
.\.venv\Scripts\python.exe scripts/firms/check_firms_archive.py --source "data/raw/firms/815590/fire_archive_J1V-C2_815590.csv" --report "outputs/reports/firms_noaa20_archive_check.json" --start "2018-04-01" --end "2025-01-01"
.\.venv\Scripts\python.exe scripts/firms/prepare_firms_pilot.py --source "data/raw/firms/815590/fire_archive_J1V-C2_815590.csv" --output "data/interim/firms_noaa20_pilot_2018_2024.csv" --report "outputs/reports/firms_noaa20_pilot_preparation.json" --start "2018-04-01" --end "2025-01-01"
.\.venv\Scripts\python.exe scripts/firms/prepare_firms_candidates.py --source "data/interim/firms_noaa20_pilot_2018_2024.csv" --audit "data/interim/firms_noaa20_pilot_candidate_audit.csv" --output "data/interim/firms_noaa20_fire_candidates_2018_2024.csv" --report "outputs/reports/firms_noaa20_candidates.json"
```

`--end` hariç sınırdır: 2025-01-01, 2024'ün son gününün tamamını kapsar.

İki aday tablosu hazır olduktan sonra:

```powershell
.\.venv\Scripts\python.exe scripts/firms/combine_firms_candidates.py
.\.venv\Scripts\python.exe scripts/firms/preview_firms_event_samples.py
.\.venv\Scripts\python.exe scripts/firms/preview_firms_event_samples.py --time-bin 6h
```

Ortak tablo kaynak kimliklerini korur; tekrar temizliği veya olay gruplaması yapmaz.
Örnek görseller yalnızca 2018–2023 eğitim dönemini inceler. Günlük ve 6 saatlik çıktılar
ayrı dosyalara yazılır; 6 saat bir olay gruplama eşiği değildir.

Önceki S-NPP incelemeleri:

- `firms/profile_firms_pilot.py`: S-NPP pilot tür/güven tabloları; sabit kaynak incelemesi eğitimde.
- `firms/preview_firms_candidates.py`: yalnızca S-NPP eğitim adaylarının harita ve aylık grafiği.
- `firms/check_firms_coverage.py`: yalnızca S-NPP eğitim döneminin günlük Türkiye sayımları.

Sıfır tespit günü, doğrulanmış gözlem kesintisi veya güvenilir negatif etiket anlamına gelmez.

## Yanmış alan karşılaştırması

`earth_engine/inspect_burned_area_samples.js` Earth Engine'de MODIS MCD64A1
örneklerini açar. Katman görünürlüğü ile harita merkezleme ayrı işlemlerdir:
2019 bölgesine gitmek o katmanı otomatik açmaz. Kod mevcut haliyle 2019'a merkezlenir;
2019 katmanları Layers menüsünden açılmalıdır.

Bu karşılaştırma yardımcı incelemedir; olay doğrulaması tamamlanmadı. Yangın sonrası
veri tahmin girdisi olarak kullanılmaz. 2025 final test bu hazırlık dosyalarına dahil değildir.


## Olay gruplama ve tarihsel kaynak denetimi

Aşağıdaki işlemler yalnızca eğitim dönemindeki keşif ve etiket incelemesidir;
kesin yangın olayları veya otomatik eleme politikası oluşturmaz.

1. `geography/prepare_burned_area_samples.py`: indirilen beş bantlı MODIS
   örneklerinin ara kopyalarında doğrulanmış sinusoidal CRS tanımını düzeltir;
   ham rasterları değiştirmez.
2. `firms/preview_firms_burned_area_overlay.py`: FIRMS adaylarını hazırlanan
   MODIS örnek pikselleriyle karşılaştırır.
3. `firms/explore_event_grouping.py`: 500/1.000/2.000 metre ve 24/48/72 saat
   ayarlarını karşılaştırır; nihai eşik seçmez.
4. `firms/preview_firms_event_samples.py --grouping`: gruplama örneklerini ve
   uzun zincirleme kümeyi görselleştirir.
5. `firms/profile_firms_pilot.py --source-audit`: eğitimdeki iki sensörün bütün
   türlerini kaynak hücrelerinde inceler.
6. Aynı betiğin `--static-proximity` seçeneği önceki/aynı/sonraki type=2
   yakınlığını; `--historical-review` seçeneği H01–H06 hedefli inceleme
   örneklerini hazırlar. Seçenekler ayrı çalıştırılır.
7. `earth_engine/inspect_historical_sources.js`: Code Editor'da seçili H01–H06
   vakasının tarihli Sentinel-2, örtü ve MODIS değer/maskelerini gösterir.

Bu betikler yerel çıktılarını yeniden yazabilir. Kaynak denetimi için pilot
bütün-tür tabloları; gruplama için ortak aday tablosu önceden hazırlanmalıdır.
HDF4 kaynak okuması için `pyhdf` kilitli bağımlılıklara eklendi. Native HDF
karşılaştırması bu oturumda kısa Python kontrolleriyle yapıldı; henüz ayrı bir
komut satırı betiği yok. Dosya kimliği, SHA-256, piksel adresleri ve sonuçlar
proje rehberinde kayıtlıdır.

1 Ekim 2026 kapanışında FIRMS 815579/815590 Type üretim teyidi için NASA
yanıtı bekleniyor. H01/H03/H04/H05/H06 Nisan native MODIS pikselleri yanmamış
sınıfında doğrulandı; bu durum küçük yangını kesin dışlamaz. Genel EE maskesi
sıfıra doldurulmaz. Kalan aylar ve H02 native kaynak kontrolü bekliyor.
