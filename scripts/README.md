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
| `meteorology/` | ERA5-Land indirme ve günlük alan ağırlıklı özellikler |
| `quality/` | Tamamlanmış kaynak ve ara tabloların yerel bütünlük denetimi |

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

### İki sensörün eğitim gözlem kapsamı ön incelemesi

`check_firms_coverage.py` eski S-NPP sayımını korur. Yeni yerel tanı:

```powershell
.\.venv\Scripts\python.exe scripts/firms/review_observation_coverage.py snapshot
.\.venv\Scripts\python.exe scripts/firms/review_observation_coverage.py review
```

İlk komut iki resmî NASA kesinti sayfasını internetten kaynak özetleriyle kaydeder;
ikinci komut yereldir. İki uydunun Türkiye/pilot/geçici aday günlük sayımlarını
yalnızca 2018–2023'te üretir. NOAA-20 talep dışındaki ilk 90 gün NaN kalır.
Kesinti tablolarıyla çakışmalar tanısaldır; sensörün/pilotun tam kesinti veya
gözlem kapsamı olduğu varsayılmaz. Hiçbir negatif etiket ya da uygunluk eşiği yok.
Çıktılar outputs/reports/observation_coverage altında. Önceki sayım raporları
korunur. Sonuç ve ilk manuel piksel örneği:
[gözlem kapsamı incelemesi](../docs/FIRMS_OBSERVATION_COVERAGE.md).

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


## Meteoroloji — ERA5-Land geçmiş özellikleri

`scripts/meteorology/prepare_era5_land.py` üç açık aşama içerir:

```powershell
.\.venv\Scripts\python.exe scripts/meteorology/prepare_era5_land.py weights
.\.venv\Scripts\python.exe scripts/meteorology/prepare_era5_land.py download --start 2018-01-01 --end 2018-02-01
.\.venv\Scripts\python.exe scripts/meteorology/prepare_era5_land.py prepare --start 2018-01-01 --end 2018-02-01
```

`weights` yereldir: native 0,1 derece kaynak piksellerini AOI içi 5 km hücre
bölümleriyle EPSG:6933 üzerinde kesiştirir. `download` mevcut Earth Engine
kimlik doğrulamasıyla günlük native rasterları indirir; Drive görevi açmaz.
`prepare` yereldir: geçerli kaynak alanlarıyla ağırlıklı ortalamalar ve her
özellik için geçerli alan oranını çıkarır. Sıfır geçerli alan boş değer kalır.

Bitiş tarihi hariçtir. Yalnızca 2018–2024 tahmin tarihleri kabul edilir; 2025
sorgusu girişte reddedilir. Geçmiş 14 günlük pencere için 2017 saatleri gerekebilir.
T=00 UTC için kullanılan kaynak saatleri kesinlikle T'den öncedir. Saatlik
yağışın zaman damgası saat sonu olduğu için toplam fiziksel pencere
(T-h-1 saat,T-1 saat] olur; tam önceki UTC takvim günü toplamı değildir.

Çıktılar: data/raw/meteorology/era5_land_daily altında günlük TIF+provenance JSON;
data/interim/meteorology/daily altında hücre tabloları; outputs/reports/meteorology
altında kalite raporları. Dosyalar ham saatlik arşiv değil, source-side günlük
agregalardır. Mevcut hash/grid bilgisi doğrulanan indirmeler atlanır; işlem kesilirse
aynı download komutu kalan günlerden devam eder. Ay bazında çalıştırmak ilerlemeyi
izlemeyi kolaylaştırır. prepare komutu aynı günlük ara CSV'leri yeniden üretir.

Sıcaklık/çiy noktası C; rüzgâr m/s; yağış ham saatlik toplamlarından mm; toprak
suyu hacim oranıdır. Yağış 24/72/168/336 saat için saklanır. Negatif yağış
korunur ve negatif-saat sayıları raporlanır; düzeltme/uygunluk eşiği bu betikte
uygulanmaz. Rüzgâr hızı her saatin u/v bileşenlerinden türetilir. Maksimum
sütunları, piksel içi zamansal maksimumların alan ağırlıklı ortalamasıdır;
hücrenin mekânsal maksimumu değildir. Bağıl nem henüz türetilmez.

Bu sürüm retrospective reanalysis araştırması içindir. available_at bilinmiyor
ve boş tutulur; canlı tahmin anında verinin erişilebilirliği iddia edilmez.
İlk doğrulama: 2018-01-01 ve 2018-07-02, 2.899 hücre/gün. Tüm dönem henüz indirilmedi.


Ocak 2018 toplu kontrolü geçti (31 gün, 89.869 hücre-gün).
Rapor: `outputs/reports/meteorology/audit_2018-01.json`.
2018 yılının kalanını hazırlamak için, indirme başarıyla bittikten sonra
ikinci komutu çalıştırın:

```powershell
.\.venv\Scripts\python.exe scripts/meteorology/prepare_era5_land.py download --start 2018-02-01 --end 2019-01-01
.\.venv\Scripts\python.exe scripts/meteorology/prepare_era5_land.py prepare --start 2018-02-01 --end 2019-01-01
```

Bu aralık uzun sürebilir. İndirme kesilirse aynı komut doğrulanmış mevcut
dosyaları atlar. Ocak denetiminde günlük 189 hücrede eksik veri ve 310
hücrede kısmi sıcaklık kapsamı saptandı; bu kayıtlar henüz elenmedi.

## Yerel veri bütünlüğü denetimi

```powershell
.\.venv\Scripts\python.exe scripts/quality/audit_project.py
```

Varsayılan Ocak 2018 meteorolojisini, AOI/grid, FIRMS, gruplama ve örtü/MODIS
çıktılarıyla birlikte denetler. Yeni veri indirmez; girdileri değiştirmez.
2018 indirme **ve prepare** tamamlandıktan sonra tüm yıl için:

```powershell
.\.venv\Scripts\python.exe scripts/quality/audit_project.py --weather-start 2018-01-01 --weather-end 2019-01-01
```

Eksik/uyumsuz girdi varsa sıfırdan farklı çıkış kodu döner; rapor
`outputs/reports/quality/` altındadır. `passed_with_open_gates`, yapısal
kontrollerin geçtiğini belirtir; etiket doğruluğu veya modellemeye hazır veri
anlamına gelmez. Devam eden indirme aralığı kontrol için seçilmemelidir.


3 Ekim ilk oturum kapanışı: 2018 ve 2019 yılları indirilip hazırlanmış ve denetlenmiştir.
2019 denetim komutu:

```powershell
.\.venv\Scripts\python.exe scripts/quality/audit_project.py --weather-start 2019-01-01 --weather-end 2020-01-01
```

Bu ilk oturumun ardından 2020 kullanıcı tarafından hazırlanmış, 2021–2024
kullanıcının devriyle aşağıdaki tek seferlik akışta tamamlanmıştır.


## Kullanıcının devrettiği 2021–2024 toplu meteoroloji çalışması

2020 yıllık denetimi geçtikten sonra tek seferlik akış:

```powershell
.\.venv\Scripts\python.exe scripts/meteorology/complete_remaining_years.py
```

Yıllar sırayla işlenir. Her yıl en fazla üç bağımsız aylık indirme işlemiyle
hazırlanır; indirmeler bittikten sonra prepare ve yıllık audit çalışır. Denetim
geçmeden sonraki yıla ilerlenmez. Geçici bağlantı hatalarında beşe kadar deneme
vardır; veri/provenance hataları yeniden denenmez. İşlem kesilirse aynı komut
indirilmiş dosyaları doğrulayarak devam edebilir. Günlükler outputs/logs/meteorology,
çalışma durumu outputs/reports/meteorology/remaining_years_run.json altında.
Bu tek çalıştırmadır; zamanlayıcı veya sürekli servis kurmaz. 2025 kapalıdır.
Tüm yıllar bitince kullanıcıyla manuel çalışma düzenine dönülür.

3 Ekim son durum: 2018–2024 dönemi tamamlandı; tüm yıllık denetimler geçti.
Yıllık raporlar outputs/reports/quality altında; tüm dönem özeti
meteorology_2018_2024_summary.json dosyasındadır. Yeni bir indirme yılı kalmadı.
Sonraki işlemler kullanıcıyla yeniden manuel adımlarla yürütülecek.

## VIIRS L2 yerel örnek denetimi

`firms/inspect_l2_observation_sample.py` yalnızca eğitim dönemi S-NPP/NOAA-20
yangın/geolocation çifti açar. İndirme yapmaz. CMR dosya boyutu/kimliği ve varsa
sağlama değeri, gerçek geolocation üretim girdisi, zaman, boyut ve bütün seyrek
yangın koordinatları doğrulanır. Doğal HDF5 satır düzeni kullanılır; pilot il
poligonuna düşen merkezler gridlere sayılır. Alan oranı ve negatif etiket üretilmez.

İlk indirilen örneği yeniden denetlemek için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py
```

İlk çiftin pilotta merkezi yok; indirilen ikinci çifti yeniden denetlemek için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_2019014_1024 --fire-metadata outputs/reports/observation_coverage/G2923107211-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2126423794-LAADS_metadata.json
```

İkinci çift pilotta ağırlıkla bulut sınıfı içeriyor; günlük negatif etiket yok.
İndirilen 00:42 UTC çiftini yeniden denetlemek için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_2019014_0042 --fire-metadata outputs/reports/observation_coverage/G2923104149-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2126422455-LAADS_metadata.json
```

Sınıf bazında QA sayımları ve nominal girdili/artık bowtie olmayan kara merkezi
sayısı tanısal raporlanır. Nominal QA bulutları geçerli kara gözlemi yapmaz.
Kesin il sınırlarına mekânsal indeks hazırlanır; geometri basitleştirilmez.

Denetlenen gece/gündüz örneklerini hücre anahtarıyla karşılaştırmak için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/compare_l2_observation_samples.py
```

Varsayılan örnekler 00:42 ve 10:24 UTC; `--pair-keys` ile aynı eğitim günündeki
diğer denetlenmiş S-NPP/NOAA-20 çiftleri eklenebilir. NOAA-20 anahtarı
`N20:2019014.0930` biçimindedir; sensör verilmezse S-NPP kullanılır. Kaynak/kod/coğrafya özetleri ve
sınıf toplamları yeniden doğrulanır. Hücrede en az bir nominal girdili kara
merkezinin bulunduğu geçişler raporlanır; günlük gözlem/negatif durumu değiştirilmez.
Çıktılar `l2_comparison_2019-01-14_SNPP_2samples.json/.csv` altında.
Bu betik piksel ayak izi veya çok sensörlü günlük kapsam hesabı değildir.

14 Ocak için indirilen beş S-NPP örneğinin tamamı denetlendi. Birlikte karşılaştırmak için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/compare_l2_observation_samples.py --pair-keys 2019014.0042 2019014.1018 2019014.1024 2019014.1200 2019014.2242
```

Çıktı `l2_comparison_2019-01-14_SNPP_5samples.json/.csv`. 2.327 hücrede en az
bir nominal girdili kara merkezi var; 572 hücrede bu örneklerde yok. Günlük
durum hâlâ belirsiz; NOAA-20 ile birleşim aşağıda.

NOAA-20 yangın sürümü `002`, konum dosyası sürümü `021` (CMR: 2.1) olarak
sabitlendi. Yanlış sensör/sürüm ve gerçek konum girdisi olmayan çift reddedilir.
NOAA-20 raporu `l2_sample_N20_2019014.0930_audit.json` gibi adlandırılır.
Hiç yangın içermeyen bütün geçişte boş seyrek diziler geçerlidir; bu durumda
seyrek koordinat yön kontrolü mevcut değildir, raporda açıklanır.

Üç NOAA-20 çifti indirildi ve denetlendi. Kontrolleri yeniden üretmek için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_N20_2019014_0930 --fire-metadata outputs/reports/observation_coverage/G2912390997-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2123967411-LAADS_metadata.json
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_N20_2019014_1112 --fire-metadata outputs/reports/observation_coverage/G2912391046-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2123966370-LAADS_metadata.json
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_N20_2019014_2330 --fire-metadata outputs/reports/observation_coverage/G2912390369-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2123967123-LAADS_metadata.json
```

Sonra aynı günün iki sensöründeki denetlenmiş sekiz örnek birlikte karşılaştırılabilir:

```powershell
.\.venv\Scripts\python.exe scripts/firms/compare_l2_observation_samples.py --pair-keys 2019014.0042 2019014.1018 2019014.1024 2019014.1200 2019014.2242 N20:2019014.0930 N20:2019014.1112 N20:2019014.2330
```

Üç NOAA-20 çiftinin kimlik/boyut, konum MD5, gerçek üretim girdisi ve doğal dizi
denetimleri geçti. Oluşan `l2_comparison_2019-01-14_SNPP_N20_8samples.json/.csv`
raporunda 2.419 hücrede en az bir nominal girdili kara merkezi var, 480 hücrede
yok. NOAA-20 ek 92 hücre sağlıyor; günlük negatif izin hâlâ verilmez. S-NPP
dosyaları genişletilmiş kodla tekrar denetlendi ve önceki CSV/sınıf/QA/kaynak
özetleri birebir korundu.

13 Ocak 2019 01:00 UTC kontrol çifti indirildi ve denetlendi. FIRMS arşivindeki
01:02 termal tespit adayı için piksel eşleşmesi doğrulandı; doğrulanmış orman
yangını etiketi değildir. İki dosya `sample_2019013_0100` klasöründe. Denetimi
yeniden üretmek için:

```powershell
.\.venv\Scripts\python.exe scripts/firms/inspect_l2_observation_sample.py --sample-directory data/raw/firms_observation/sample_2019013_0100 --fire-metadata outputs/reports/observation_coverage/G2923099810-LPCLOUD_metadata.json --geo-metadata outputs/reports/observation_coverage/G2126421215-LAADS_metadata.json
.\.venv\Scripts\python.exe scripts/firms/check_l2_firms_control.py
```

İndirme listesi `control_l2_sample_downloads.csv`, aday ve metadata kaynak
özetleri `control_l2_sample_selection.json` altında. Kalıcı kontrol betiği önce
eğitim dönemi/zaman/sensör ve kaynak özetlerini doğrular; sonra aynı granül
aralığındaki pilot FIRMS kayıtlarını yuvarlama aralığındaki tek seyrek piksele
eşler. Doğal maske/konum/QA geri okunur; güven ve hücre eşleşmesi zorunludur.
En yakın piksele geniş toleransla atama yok. Sonuçta üç kayıt eşleşti; bir
kayda ait artık bowtie bayrağı korundu. Type teyit edilmiş veya yeni etiket
atanmış sayılmaz. Rapor `l2_sample_2019013.0100_firms_control.json` altında.

CMR metadata kopyaları ve çıktılar yerel `outputs/reports/observation_coverage/`
altında, Git dışında tutulur. Kopyalar bu oturumdaki CMR sorgularından geldi;
betik metadata indirme veya günlük gözlem maskesi hattı değildir. Ayrıntılar:
[gözlem kapsamı](../docs/FIRMS_OBSERVATION_COVERAGE.md).

### Tarama içi yaklaşık alan tanısı

Bu adım resmî piksel ayak izi, tam günlük kapsam veya etiket üretmez.
[Yöntem ve açık doğrulama işleri](../docs/OBSERVATION_AREA_METHOD.md).
Dokuz yerel örnek işlendi; yeniden üretmek için kaynak denetimleri mevcut olmalı:

```powershell
.\.venv\Scripts\python.exe scripts/firms/estimate_l2_observed_area.py --pair-keys 2019013.0100 2019014.0042 2019014.1018 2019014.1024 2019014.1200 2019014.2242 N20:2019014.0930 N20:2019014.1112 N20:2019014.2330
.\.venv\Scripts\python.exe scripts/firms/combine_l2_area_estimates.py --pair-keys 2019014.0042 2019014.1018 2019014.1024 2019014.1200 2019014.2242 N20:2019014.0930 N20:2019014.1112 N20:2019014.2330
```

İlk betik aynı 32 satırlık tarama içindeki merkezlerden yaklaşık köşe üretir;
tarama kenarında/eksik komşuda ekstrapolasyon yok. Poligonlar tam AOI parçalarıyla
kesiştirilir, örtüşmeler geometrik birleşimle tek kez sayılır. Sınıf 5 nominal
yangınsız kara, bulut ve yeniden oluşturulan alan ayrı tanı katmanlarıdır.
GPKG/CSV/JSON ve doğal tarama zamanları outputs/reports/observation_coverage altında.

İkinci betik aynı eğitim gününün doğrulanmış kaynak/kod/geometri özetlerini,
hücre anahtarlarını ve kaydedilen alanlarını denetleyip geometrik birleşim üretir.
Farklı sensörlerin alanları doğrudan toplanmaz. `(T,T+24h]` sınırına denk gelen
tarama zarfı `boundary_unknown`; alan veya zaman tanısı negatif izin vermez.
Varsayılan T, örnek günün 00:00 UTC saatidir. 2024/2025 örnekleri reddedilir.

Bağımsız geri okuma betiği yerel outputs/verification/check_l2_area_saved_outputs.py
altında; hesap tutarlılığını sınar, fiziksel ayak izi doğruluğunu sertifikalandırmaz.
Üç kontrolün boyut karşılaştırması ayrıca control_scan_geometry_crosscheck.json altında.

### Genişletilmiş yerel geometri tanısı ve katalog kapasitesi

4 Ekim'de dokuz örneğin 1.176 seyrek termal tespiti incelendi. 1.145 tespitte
tarama içi geometri ölçüldü; 31 kenar kaydı ölçümsüz tutuldu. Bu fiziksel ayak
izi sertifikası değil; boyut referansı hâlâ üç eski FIRMS kontrol kaydıdır.
Konum ürünündeki ölçek/ofset ve fill değerleri doğal okuma sonrası uygulanır.

```powershell
.\.venv\Scripts\python.exe scripts/firms/audit_l2_geometry.py --pair-keys 2019013.0100 2019014.0042 2019014.1018 2019014.1024 2019014.1200 2019014.2242 N20:2019014.0930 N20:2019014.1112 N20:2019014.2330
.\.venv\Scripts\python.exe scripts/firms/snapshot_l2_capacity.py
```

İlk betik kaynak denetimlerini ve önceki kontrol raporunu doğrular; yeni
CSV/JSON tanısı üretir, eski alan çıktılarını veya aday tablosunu değiştirmez.
İkincisi mevcut örnekleri doğrular ve dört açık CMR metadata sayım sorgusu
yapar. S-NPP 2018-01-01, NOAA-20 mevcut FIRMS talebiyle aynı 2018-04-01
başlangıcından 2023 sonuna kadar sorgulanır; ham dosya indirilmez. Sonuçlar
l2_geometry_diagnosis ve l2_training_capacity_snapshot adlı yerel raporlarda.
Katalog sayımı eşleşmiş girdi listesi değildir; boyutlar dokuz yerel örnekten
ölçeklenen senaryolardır. Her iki araç negatif etikete izin vermez.
[İnceleme ve sınırlar](../docs/GEOMETRY_DIAGNOSIS_2026-10-04.md).

## Model için meteoroloji kullanım kuralı

Kurallar ve kapsam: [WEATHER_POLICY.md](../docs/WEATHER_POLICY.md).
Ham günlükler değiştirilmez. Bütün kayıtlar ayrı model_v1/daily dizininde tutulur;
meteoroloji kullanım profilleri ve türetilmiş yağış sütunları eklenir. Etiket
üretilmez; bu henüz nihai eğitim tablosu değildir.

Kural incelemesi yalnızca 2018–2023 eğitim verisini tarar ve kaynak/kod özetli
manifest oluşturur. 3 Ekim'de bu adım tamamlandı; yeniden üretmek gerektiğinde:

```powershell
.\.venv\Scripts\python.exe scripts/meteorology/prepare_model_weather.py review
```

3 Ekim'de kullanıcı sabit kuralı 2018–2024'e manuel uyguladı; bütün günlük
çıktılar denetlendi. Yeniden üretmek için inceleme manifesti ve yıllık kaynak denetimleri
mevcut olmalıdır:

```powershell
.\.venv\Scripts\python.exe scripts/meteorology/prepare_model_weather.py prepare --start 2018-01-01 --end 2025-01-01
```

End hariçtir; 2025 günü okunmaz. Sonuçlar data/interim/meteorology/model_v1/daily,
dönem raporu outputs/reports/meteorology/model_weather_2018-01-01_2025-01-01.json
altında. Doğrulama her gün kaynak özetini, anahtar/tarih/sürümü, geri okunan
özgün sütunları ve uygun kayıtların model değerlerini kontrol eder. Hata olursa
işlem durur. Yeniden çalıştırma kaynakları doğrulayıp ayrı türetilmiş dosyaları
yeniden üretir; ham gözlemleri değiştirmez.

Tam dönem kapanış kontrolü 2.557 günlük kaynak/çıktı CSV'sinin özetlerini,
özgün sütunların korunmasını, tarih/anahtar/şema/sürümü ve bağımsız hesaplanan
yağış/alan kapsamı bayraklarını doğruladı. Rapor:
outputs/reports/quality/model_weather_2018_2024_audit.json.
Yerel kontrol betiği outputs/verification/audit_completed_model_weather.py altında;
ara veriler ve yerel raporlarla birlikte Git kapsamı dışındadır. 2025 okunmadı;
nihai yangın etiketleri oluşturulmadı.
