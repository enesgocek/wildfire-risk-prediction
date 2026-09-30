# Proje Rehberi

Kapsam, veri kuralları ve mevcut durum tek belgede toplanmıştır.

- [Proje tanımı](#proje-tanımı--güncel-pilot-kapsamı)
- [Veri ve değerlendirme kuralları](#veri-ve-değerlendirme-protokolü)
- [Çalışma alanı](#çalışma-alanı-kararı)
- [Sıradaki işler](#ikinci-haftaya-geçiş)
- [Kurulum durumu](#ilk-hafta-durumu)
- [Servis erişimleri](#dış-servis-erişim-durumu)

Başlangıç prensibi: yalnızca kullanılan kod ve klasörler tutulur. Veri/model/arayüz
klasörleri ihtiyaç doğduğunda oluşturulur. Üretilen dosyalar `outputs/` altında toplanır.

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

İl sınırlarını içeren gerçek AOI ve 5 km grid henüz üretilmedi. Boş veya tahmini GeoJSON
dosyaları gerçek teslimat olarak sunulmayacaktır. İkinci haftaya başlarken:

1. Tek bir güvenilir idari sınır kaynağı seç; lisansını, sürümünü ve indirme tarihini kaydet.
2. Dört ilin sınırlarını doğrula, geometri hatalarını gider ve birleşik AOI oluştur.
3. Metre tabanlı uygun projeksiyonu seç ve grid başlangıç noktasını sabitle.
   EPSG:4326 üzerinde dereceyi 5 km kabul etme. Grid üretim CRS'si henüz seçilmedi.
4. Benzersiz ve tekrar üretilebilir `grid_id` üret; il sınırını aşan gridlerde il eşleştirme
   kuralını önceden belirle. Grid geometrisi, AOI kesişimi ve alan oranını sakla.
5. Arazi örtüsü kaynağı/sürümü ile vegetation uygunluk eşiğini belgeleyerek gridleri işaretle.
   Tüm gridleri sakla; uygunluk bayrağı ile model kapsamını belirle.
6. `data/aoi/aoi.geojson`, `data/aoi/grid_5km.geojson` ve AOI manifestini üret/doğrula.

Bu işlemler tamamlanmadan il sınırları ve gridler kesinleşmiş kabul edilmez.


## İkinci Haftaya Geçiş

1. Google Earth Engine project/auth ve non-commercial erişimini tamamla.
2. İl sınırları, AOI/grid ve vegetation uygunluk kriterlerini üretip sürümle.
3. FIRMS 2018–2024 veri bulunabilirliğini il/yıl/sensör bazında incele. NRT yerine
   mümkün olduğunca standard/science-quality geçmiş veri kullan. 2025 final verisinin
   bulunabilirliği kontrol edilebilir; model geliştirmede performans veya içerik keşfi yapılmaz.
4. EFFIS geçmiş perimeter erişimini doğrula; gerekiyorsa kullanıcı tarafından veri isteği başlat.
5. Coverage/missingness raporu çıkar. Ham veri formatını ve provenance manifestini sabitle.
6. Tekrarlı hotspot temizliği ve olay gruplama kurallarını train dönemi üzerinde geliştir.
   Yıl sınırını aşan olayları ayrı denetle.
7. `fire_event_catalog.parquet` üret; event_id, first_detection_time, lat/lon,
   ülke/il, sensör, confidence ve mümkünse EFFIS/alan alanlarını sakla.
8. Train/validation olay ve grid dağılımı yeterlilik raporu çıkar. Dış ülke verisi gerekip
   gerekmediğini bu raporla değerlendir. Türkiye 2025'i kararı vermek için kullanma.

İlk haftadaki klasörler gerçek AOI veya fire dataset yerine geçmez. Gerçek veri ve
leakage denetimi tamamlanmadan model eğitimine başlanmaz.


## İlk Hafta Durumu

30 Eylül 2026 — yerel kurulum. GitHub yüklemesi kullanıcıya bırakılır.

### Hazırlananlar

- Kullanılan Python modülleri ve sade klasör yapısı; boş gelecek klasörleri kaldırıldı.
- Dört il ve 24 saatlik tahmin için merkezi YAML yapılandırması.
- Proje tanımı, AOI kararı, veri protokolü ve ikinci hafta iş listesi.
- `.gitignore`, `.env.example`, Python sürüm kaydı ve bağımlılık tanımı.
- Tek komutluk Windows kurulum betiği.
- Yapılandırma doğrulama ve final test erişim kontrolü.
- MLflow altyapı deneyi ve noninteractive GEE erişim kontrolü.

### Doğrulama

| Kontrol | Sonuç |
|---|---|
| Ortam | Python 3.12.14; bağımlılıklar kuruldu |
| Kilit | `uv.lock`; 110 package çözümü (platform/build dahil), kurulu ortamda 109 package |
| Ana klasörde setup.ps1 | Başarılı |
| pytest | 18 test geçti |
| Ruff lint ve format | Başarılı |
| MLflow smoke | FINISHED; `b329fff5c0cb43468c56fe66c7954cef` |
| MLflow sağlık ve arayüz | İkisi de HTTP 200; API üzerinden run FINISHED okundu |
| Temiz kopya | Git'e girecek dosyalarla yeni ortam, setup, 18 test ve smoke başarılı |
| GEE kontrolü | `not_configured`; gerçek API erişimi doğrulanmadı |
| Git | main üzerinde yerel depo; commit ve remote yok |
| Ignore kontrolü | .env, .venv, büyük veri/model, MLflow ve yerel raporlar hariç |

Kurulum Windows üzerinde doğrulandı; farklı işletim sisteminde henüz denenmedi.
Gerçek bağımsız bilgisayar clone testi, GitHub yüklemesinden sonra yapılabilir. Yerel temiz
kopya doğrulaması mevcut sanal ortamı kopyalamadan yapıldı. Geçici doğrulama kopyaları
temizlenir; sonuç kaydı `outputs/reports/reproducibility.json` içinde saklanır.

MLflow sunucusu kontrol sonrası kapatıldı; README komutuyla tekrar başlatılabilir.
İlk smoke run commit öncesinde üretildiğinden `git_revision=uncommitted` içerir.

Sandbox hesabıyla oluşturulan Git deposuna erişim için yalnızca bu proje yolu kullanıcı
Git ayarındaki `safe.directory` listesine eklendi. Yerel Git config yazma işlemi doğrulandı;
kullanıcı terminalinden commit/push için Git kimliği ve GitHub authentication ayrıca gerekir.

### Kullanıcı hesabı gerektirenler

- GitHub repo oluşturma, commit ve push.
- Google Cloud/Earth Engine kaydı ve non-commercial uygunluk doğrulaması.
- `GEE_PROJECT_ID` ve authentication tamamlandıktan sonra gerçek GEE API kontrolü.

İlk hafta GEE erişimi doğrulanmadıkça tüm dış erişim işleri tamamlanmış kabul edilmez.


## Dış Servis Erişim Durumu

İlk kurulum tarihi: 30 Eylül 2026.

| Servis | Durum | Gereken işlem |
|---|---|---|
| GitHub | Kullanıcı tarafından yapılacak | Boş repo oluştur, remote/commit/push |
| MLflow | Doğrulandı: smoke FINISHED, sağlık/arayüz HTTP 200 | README ile yerel sunucuyu başlat |
| Earth Engine | Proje kimliği verilmedi | Google Cloud projesi, kayıt, API ve authentication |
| GEE non-commercial | Doğrulanmadı | Google hesabında uygunluk doğrulaması |
| NASA FIRMS | Veri erişimi henüz denenmedi | İkinci hafta tarihsel veri erişimini incele |
| EFFIS | Erişim/istek henüz başlatılmadı | Geçmiş perimeter erişimi ve gerekirse data request |

`scripts/check_gee_access.py` gerçek API erişimini test eder, non-commercial hesabın
uygunluğunu otomatik onaylamaz. Google hesabı/Cloud project bilgisi sağlanmadığından
Earth Engine erişimi tamamlandı olarak işaretlenemez. Bu işlem kullanıcı hesabıyla yapılmalıdır.

Resmî kaynaklar:
- https://developers.google.com/earth-engine/guides/access
- https://developers.google.com/earth-engine/guides/auth
- https://mlflow.org/docs/latest/self-hosting/architecture/tracking-server/

Yerel makinedeki güncel API sonucu `outputs/reports/gee_access.json` içinde bulunur;
bu dosya Git'e yüklenmez. API kontrolü, non-commercial kayıt durumu ve kaynak veri
erişimi birbirinden ayrı kontrollerdir.

