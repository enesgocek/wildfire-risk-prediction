# Veri setine geçiş hazırlığı ve işlem rehberi — 12 Ekim 2026

## Amaç ve kabul sınırı

Kuyrukların tamamlanmasından sonra aynı kontrolleri ay ay elle kurmak
yerine, mevcut aday özellik yöntemi kaynak referansları, toplu giriş,
sonuç dizini ve kabul denetimiyle birleştirildi. Yeni kaynak çekimi veya
uzun üretim işi açılmadı. Canlı bitki örtüsü ve VM kodları değişmedi.

Bu hazırlık teknik birleştirme adımlarını azaltır. Nihai eğitim veri
seti, 0/1 etiketleri, habitat kararı veya operasyonel erişilebilirlik
kabulü değildir. Uydu işinin bitişi, eksik gözlemin güvenilir negatif
olduğunu kendiliğinden kanıtlamaz. 2024 doğrulama bileşenleri ayrı
hazırlanmalıdır; 2025 final test dönemi kapalı kalır.

## Tamamlanan mekanik hazırlıklar

| Hazırlık | Uygulama ve kontrol |
|---|---|
| Veri sözlüğü ve roller | `dataset_contract.py`: 27 aday özellik, birim, NaN kuralı, ayrı kalite/kaynak alanları, hedef tablosu taslağı ve altı açık bilimsel kapı |
| Takvim ve kaynak planı | `dataset_batch.py`: 72 eğitim ayı, artık yıllar, beklenen anahtar sayıları ve kaynak/birleştirme referanslarının ayrımı |
| Teslim envanteri | Meteoroloji/statik metadata, bitki örtüsü referansı, aday ay kabulü ve yalnız uydu günlük/katalog kanıtı ayrı alanlarda |
| Toplu yürütme ve devam | `prepare_dataset.py execute`: tek yazar, seri aylar, ayrı kaynak/ürün hash'leri, sonuç tekrar kullanımı, süre/disk kontrolü ve her kapanan ay sonrası kayıt |
| Hedef tablosu eşleştirmesi | `dataset_assembly.py`: hücre/tarih anahtarlarına göre bire bir eşleştirme; mevcut sürümde yalnız nullable Int8 boş hedefler |
| Son aday denetimi | `prepare_dataset.py audit`: veri/parça/source hash'leri, takvim, eksik değer sayımı ve hedef eşleştirme denemesi; tam takvim isteğe bağlı zorunlu kılınır |

Eğitim takvimi **2.191 gün / 6.351.709 hücre-gün**, doğrulama takvimi
**366 gün / 1.061.034 hücre-gün**. Bunlar 2.899 hücre × gün sayısıdır;
habitat ve gözlem dışlamaları sonrasındaki etiketli örneklem değildir.
2024 için yalnız hazırlık envanteri tanımlanır; bu toplu giriş eğitim
aylarıyla sınırlıdır ve 2024/2025 kaynak dosyalarını işleyemez.

Veri sözlüğü aileleri: 11 meteoroloji (°C, m/s, mm, hacim payı), yedi
arazi sınıfı alan payı, beş topografya (m, derece, boyutsuz yön bileşeni),
dört 30/60 günlük NDVI/NDMI adayı. Toprak suyu kaynak bandı 0–7 cm
katmanında hacim payıdır; [resmî ERA5-Land band tanımı](https://developers.google.com/earth-engine/datasets/catalog/ECMWF_ERA5_LAND_HOURLY)
kontrol edildi. Yerel yöntem sıcaklığı °C ve yağışı mm'ye dönüştürür.
Arazi sınıfı payı ağaç kapalılığı değildir; `natural_vegetation_fraction`
sınıf toplamıdır. Aday listesi nihai model özellik seçimi değildir.

Özellikler kayıtlı grid/AOI alan özetleridir; tek noktada sensör ölçümü
olarak yorumlanmaz. Bitki örtüsünün 30/60 günlük aralığı seçilen geçmiş
kesim zamanında biter. Haftalık kesim sonraki güne taşındığında pencere
her gün T'de yeniden bitmiş sayılmaz; kesim zamanı ve görüntü yaşı ayrı
kalite tablosunda korunur.

## Devam ve veri güvenliği

Plan güncel supervisor JSON'unu bir kez okuyup değişmez kaynak referansı
snapshot'ı oluşturur; canlı progress dosyasının sonradan ilerlemesi hata
sayılmaz. Referans aşamasında aylık tablo baytları yeniden doğrulanmış
gibi raporlanmaz. Üretim veya aday denetimi seçilen ayın gerçek baytlarını
ve bağımlılıklarını hash'lerle kontrol eder. Kayıtlı dosyalar için sessiz
fallback, kaynak değişimini görmezden gelme veya çıktı üzerine yazma yoktur.

Yeni plan, yöntem dosyalarının SHA-256 kimliklerini taşır. Yöntem değişirse
eski plan yürütülmez; yeni plan gerekir. Aynı anda yalnız bir aday batch
yazıcısı çalışabilir. Bu kilit, bitki örtüsü kuyruğunun kilidinden ayrıdır.
Eski kilit hata halinde otomatik silinmez; süreç durumu ayrıca incelenir.

Yeniden kullanımda eski aday ayın bütün günlük parçaları geri okunur.
Yeni ay üretimi yalnız `--build-missing` ile açılır; child süreç ağ kapalıdır
ve kalan süreyle timeout uygulanır. İptal/zaman/disk/hata durumunda kapanmış
aylar korunur. Çocuk ayı tamamlamış fakat üst denetim süreye takılmışsa
aylık builder kabul referansı da korunur; sonraki plan onu yeniden okuyabilir.
Yarım çıktı, bitmiş aylık kabul veya güvenilir hedef sayılmaz.

Eksikler doldurulmaz, imputasyon fit edilmez, olay/canonical hücre seçilmez.
Kalite/gözlem alanları otomatik model girdisine katılmaz. Mevcut hedef
denemesinde 0/1, uydurulmuş olay/habitat veya `observed` iddiası reddedilir.

## Kuyruk sonrasında üç teknik işlem

Aşağıdaki komutlar gelecekteki yerel aday hazırlığı içindir; tüm dönem
yürütmesi bu çalışmada başlatılmadı. Kaynak progress yolu en son tamamlanan
veya incelenen bitki örtüsü çağrısını göstermelidir. Yeni plan, indirilmiş
uydu ürünlerinin bilimsel kabulünün yerine geçmez.

1. **Kaynak planını yenile:**

```powershell
.\.venv\Scripts\python.exe scripts/quality/prepare_dataset.py plan `
  --source-progress outputs/reports/landscape/training_supervisor_v1/training_iso_v2_maintenance_resume_20261011_bd22517d/progress.json
```

İlk kullanım iki kabul edilmiş aday ayı başlangıç dizininden alır. Önceki
batch sonuçları varsa `--candidate-index SONUC_YOLU --expected-index-sha256
SONUC_SHA256` eklenir. Son çağrının dışında kalan eski kayıtlı aylar ve
tamamlanan çocuk kabul referansları korunur; son işlem listesiyle silinmez.

2. **Hazır ayları tek toplu girişle birleştir:**

```powershell
.\.venv\Scripts\python.exe scripts/quality/prepare_dataset.py execute `
  --plan PLAN_YOLU --expected-plan-sha256 PLAN_SHA256 `
  --all-ready --build-missing --hours-limit 2
```

`PLAN_YOLU` ve hash ilk komutun çıktısından alınır. Saat sınırı yerel
batch içindir; VM'nin 18 saat/STOP ayarını değiştirmez. Bütün dönemin iki
saatte biteceği iddia edilmez. Gerektiğinde yeni plan/sonuç diziniyle devam
edilir. Yalnız belirli aylar için `--all-ready` yerine `--months` kullanılır.
`--build-missing` olmadan sadece hazır adaylar geri okunur; eksik üretim
talebinde durulur. Çıkış kodları: başarı 0, süre/disk rezervi 2, kaynak veya
üretim talebi bekleme 3, kontrollü kullanıcı kesintisi 130, diğer hata 1.

3. **Tam eğitim aday takvimini denetle:**

```powershell
.\.venv\Scripts\python.exe scripts/quality/prepare_dataset.py audit `
  --candidate-index SONUC_YOLU --expected-index-sha256 SONUC_SHA256 `
  --require-complete-calendar
```

Bu seçenek 72 ay eksikse CSV okumadan tam takvim isteğini reddeder.
Seçilmiş küçük denemede seçenek kullanılmadan kısmi envanter denetlenebilir.
Tam aday takvimi bile bilimsel etiket kapısını veya model kabulünü açmaz.

## Gerçek yerel deneme ve kanıt

Hazırlık snapshot'ı `20261012T020712Z_ae295f2a` dizininde, kaynak progress
zamanı **12 Ekim 01:58:15 UTC**. 61 bitki örtüsü ayı için referans, iki tam
aday ay ve son kayıtlı uydu günlük/katalog kabulünde 40 ay bulunuyor.
40 sayısı canlı V6'nın yeni ilerlemesi veya bağımsız ürün bayt kabulü değildir.
11 eğitim ayının bitki örtüsü referansı snapshot'ta henüz yok; sonradan
tamamlanınca plan yenilenir. 2024 meteoroloji takvim metadatası mevcut,
2024 bitki örtüsü/gözlem bu envanterde ayrıca kabul edilmiş değil.

Plan, yeniden kullanım ve son denetim yolları **Ocak/Ağustos 2018'in iki
gerçek ayı / 179.738 hücre-gün** üzerinde çalıştırıldı. Yeni ham veri veya
aday ay yeniden üretilmedi. Hedef eşleştirme denemesinde bütün hedefler boş
kaldı. Nihai `model_ready=false` doğru biçimde korundu.

Kanıt kökü `outputs/reports/dataset/`:

- `preparation_v1/20261012T020712Z_ae295f2a/plan.json`, SHA-256
  `a9db3d676b4b663728b1655e2c98a426b5e9b3d3cfc497257a28ef4c71854de6`.
- Aynı dizinde `contract.json`, SHA-256
  `037aea597b455844e6dc3c120176be04daa68f87bc97201c270d3dd4c5a5f8ba`;
  `delivery_inventory.json`, SHA-256
  `09767630dab8d45e97b78551120d6e017f6da2818b72bbcd9d82dd5eaa263f4c`.
- `candidate_batch_v1/20261012T020745Z_d9d2703e/progress.json`, SHA-256
  `b072665e485572c382250e055c447ed6b04390e366dcff34e699dacc81489f73`.
- `candidate_audit_v1/20261012T020959Z_d66107d9/readback.json`, SHA-256
  `b8193ad3829b5d63e3f6d6bb7ec95d505d042dcdd39748ac1a68c80e62f13af7`.
- Birleşik `preparation_v1/20261012T020712Z_ae295f2a/workflow_readback.json`,
  SHA-256 `8791ce3d379776ff49fa4822f827001d741a6001c2b20e3a00cf269628572f84`.

**41 yeni + 66 mevcut = 107 ilgili test**, Ruff ve biçim kontrolü geçti.
Artık yıl/tam takvim, kaynak kaçışı, değişen yöntem hash'i, yeniden kullanım,
eski ayların kayıt korunması, tamamlanan çocuk sonrası üst timeout, disk,
ikinci yazıcı, yanlış hücre/tarih, nullable hedef ve kanıtsız kabul sınandı.
Önceki 165 kaynak/yöntem dosyası aynı hash'te. İlk hazırlık taslakları ve
deneme çıktıları değiştirilmeden korundu; yukarıdaki final yöntem kimliği
ile yeni plan gerekir.

## Nihai veri seti için hâlâ gerekli kanıtlar

Kaynak Type/sürümü, olay/zincir, ilk hücre, habitat, gözlem yeterliliği ve
dönem kenarı kararı açık. Her karar için kapsam, parametre/kural, inceleyen,
tarih, gerekçe, kaynak/kanıt hash'i ve belirsiz/dışlanan örnek politikası
kaydedilmelidir. Hazır 33 habitat/53 olay-senaryo vaka paketi bu incelemenin
girdisidir; form hazırlanmış olması uzman incelemesi yapılmış sayılmaz.

Gerekçeli yeni bilimsel protokol ve gerçek etiket üretimi ardından ayrı
hedef/özellik kabulü, 2024 hazırlığı, olay ayrımı denetimi ve veri sürümü
dondurma aşaması gerekir. Bu sürüm bir onay kutusuyla negatif kapısını
açmaz; [kabul sözleşmesi](DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md) korunur.
