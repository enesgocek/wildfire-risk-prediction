# 31 Aralık kaynağını beklemeye alarak üretime devam

9 Ekim 2026: bulunamayan iki kaynağın çözümünü diğer aylar işlendikten sonra
araştırma kararı alındı. Devam işi başlatıldı. Son paylaşılan uzak çalışma
kaydında Haziran–Kasım tam ay listesinde, Aralık 1–30 tamam, Mayıs işleniyor.
Bu yeni oturumun çıktıları henüz yerelde ayrıca kabul edilmedi.
Çalışma n2-standard-32, 24 çift / 4 günlük birleştirme işçisi ve sekiz saatlik
Stop sınırıyla yürütülüyor. Aşağıdaki komutlar kurulum/devam rehberidir;
çalışan oturumda ikinci bir üretim süreci başlatılmamalıdır.

Başlık raporunun CRC/hash denetimi geçti. Kalan 34 çiftin 32'sinde eşleşme
geçti; iki S-NPP çiftinde yangın dosyasının istediği gerçek geolocation
işleme sürümü seçili dosyadan farklı:

| Çift | Yangının istediği geolocation dosyası | Seçili dosya |
| --- | --- | --- |
| SNPP:2023365.0106 | VNP03IMG.A2023365.0106.002.2023365074552.nc | VNP03IMG.A2023365.0106.002.2024006061118.nc |
| SNPP:2023365.1048 | VNP03IMG.A2023365.1048.002.2023365174608.nc | VNP03IMG.A2023365.1048.002.2024006064212.nc |

Eski adlar güncel CMR sorgularında bulunamadı; mevcut seçili ad ile pozitif
sorgu sonucu alındı. LAADS güncel geolocation dizininde de eski adlar yok,
seçili sürümler var. Aynı saatlerdeki güncel yangın kayıtları eski girdileri
isteyen dosyalar. Bu, eski dosyaların hiçbir yerde bulunamayacağı anlamına
gelmez. Dosyayı yeniden adlandırmak bilimsel eşleşmeyi düzeltmez.
[CMR arama API'si](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html),
[geolocation dizini](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/VNP03IMG/2023/365/),
[yangın dizini](https://ladsweb.modaps.eosdis.nasa.gov/archive/allData/5200/VNP14IMG/2023/365/).

NASA FIRMS'ın 815579/815590 teslimlerindeki **Type sınıflandırma sürümü**
için gönderilen eski e-posta ayrı bir konu. 9 Ekim'de yaklaşık
altı gün sonra incelemeye başlandığı yanıtını aldığımı bildirdim. Teknik
sonuç henüz gelmedi; bu bildirim Type değerlerini veya bu iki L2 kaynak
eşleşmesini doğrulamıyor.

## Devam davranışı

1. Ağustos–Kasım tam aylık kayıtları mevcut bilimsel geri okumadan geçirir.
   Aralık 1–30 günlerini doğrular/tamamlar; mevcut günlük ve çift checkpoint'lerini
   yeniden kullanır. 31 Aralık hesaplamaya/günlük birleştirmeye gönderilmez.
2. Aralık 1–30 tamamlandıktan sonra Haziran 2023'ten başlayıp mevcut sırayla
   Ocak 2018'e kadar kalan 66 ayı işler. Süre rezervi önce dolarsa aynı
   komut sonraki oturumda kayıtları doğrulayarak devam eder.

Aralık aylık completion kaydı oluşturulmaz; `deferred_days=["2023-12-31"]`
ve `full_training_complete=false` raporda kalır. Diğer 71 ay tamamlandığında
durum `processable_months_verified_source_resolution_pending` olur.
31 Aralık çözülmeden bütün 72 ay tamamlandı denmez. Gözlem durumu hâlâ
`unknown`, negatif etiket izni `false`.

Orijinal kaynak CSV'leri, bilimsel işçi, paket hash'leri, checkpoint anahtarları
ve hazır-kayıt aynı. Yeni araç yalnız ay/gün çalışma sırasını ve güvenli
çocuk hata kaydını yönetiyor. Yeni bir eşleşme hatası olursa gerçek kontrol
adı ve ilgili NASA dosya adları görevde `continuation_failure.json` olarak
saklanır; iş yine durur. Bilimsel kontroller kaldırılmadı.

## 1 — VM'yi aç ve iki dosyayı yükle

Compute Engine → **wildfire-cpu-pilot → Start → SSH**.
Mevcut ayarlar **n2-standard-32, 8 saat, Stop, Automatic restart Off** olmalı.
Yeni makine veya disk oluşturma; ücretli Upgrade yapma.

SSH → **Upload File** ile yalnız bu iki dosyayı ev dizinine yükle:

- `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\source_aware_2026-10-09\run_gcp_source_aware_continuation.py`
- `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\source_aware_2026-10-09\source_blocks.json`

Buradaki `source_blocks.json` yalnız kamuya açık NASA dosya adları ve
doğrulama özetlerini içerir. OAuth bağlantı JSON'u değildir. Mevcut
`drive_connection.json` ve `production_readiness.json` VM'de kalır;
orijinal/controller ZIP'lerini veya Python ortamını yeniden kurma.

**VM SSH terminalinde**, yüklenen dosyaları kontrol et:

```bash
printf '%s  %s\n' \
  'b6abd44acf85c0cff5763d5da5463d3c24750f6b65371b04a28047f15f978bda' "$HOME/run_gcp_source_aware_continuation.py" \
  '6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d' "$HOME/source_blocks.json" \
  'ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef' "$HOME/production_readiness.json" \
  | sha256sum --check
```

Üç satırda da **OK** beklenir. Hata varsa başlatma; dosya adını/yüklemeyi
düzelt. Araç registry, gate ve mevcut iki paketi başlatırken tekrar doğrular.

## 2 — Yeni Google durma saatini al

**Cloud Shell'de** aşağıdaki tek satırı çalıştır:

```bash
gcloud compute instances describe wildfire-cpu-pilot --project=dogalafetonlemesistemi --zone=europe-west3-c --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,resourceStatus.scheduling.terminationTimestamp)'
```

**RUNNING**, **n2-standard-32**, **seconds: 28800**, **STOP** beklenir.
Yeni `terminationTimestamp` değerini tırnaklar olmadan kopyala.
Önceki oturumun tarihi kullanılmaz.

## 3 — Üretimi bir kez başlat

**VM SSH'de** bu tek satırı ayrı çalıştır:

```bash
read -r -p "Google durma zamani: " termination
```

İstenen yere yeni `terminationTimestamp` değerini yapıştırıp Enter'a bas.
Ardından aşağıdaki bloğu ayrı çalıştır:

```bash
~/wildfire-gcp-work/.venv/bin/python \
  ~/run_gcp_source_aware_continuation.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" \
  --poweroff
```

Earthdata kullanıcı adı/parola gizli girişle istenir; yazılan karakterler
görünmez. Her birini yazıp Enter'a bas. Sohbete veya günlük dosyasına koyma.

`Detached continuation requested` yalnız başlatma isteğidir. Gerçek
ilerlemeyi bir sonraki adımla kontrol et. Aynı komutu çalışan kuyruğa
tekrar gönderme; mevcut tek iş kilidi korunuyor.

## 4 — Yeni günlükten ilerlemeyi kontrol et

```bash
tail -n 25 ~/gcp_source_aware_launcher.log
cat ~/wildfire-gcp-production-v1/progress.json
```

İlk aşamada `CONTINUATION PHASE december_safe_days`, tam ayların
`Month verified/reused` satırları ve Aralık günlerinin doğrulaması beklenir.
Sonra `CONTINUATION PHASE remaining_months` ve Haziran 2023 görünür.
Eski `gcp_acceleration_launcher.log` bu yeni çalışmayı göstermez.

Gerçek ilerleme doğrulanınca SSH sekmesi ve bilgisayar kapatılabilir.
Yaklaşık 20–30 dakikada bir kontrol etmek yeterli; sürekli açık sekme
gerekmiyor. Sekiz saat bütün ayların bitme garantisi değildir.

Normal bitiş, uygulama rezervi veya yürütme hatası sonrasında mevcut
supervisor VM'yi kapatmayı ister; Google'ın sekiz saatlik **Stop** sınırı
ayrıca durur. Yeni iş alımı yaklaşık 25 dakika önce kesilir; aktif işlere
tamamlama payı ayrılır. Uygulama ayrıca mevcut 24 Ekim UTC sınırını korur.
Başlangıçta hash/kimlik/hazır-kayıt kontrolünde reddedilir ve iş başlamazsa
VM'yi kendin Stop yap. Sonuçtaki `TERMINATED` durumunu Console/Cloud Shell
ile doğrula. Stop durumunda disk saklanır; bütün sonuçlar alınıp kabul
edildikten sonra kaynakları silme ve faturalandırmayı kapatma işi yapılacak.

## Yerel doğrulama ve sınırlar

Yeni devam aracı için 10 test geçti: tam katalog/kaynak kimliğinin korunması,
31 Aralık'ın hesaplama/kapanıştan dışlanması, kapsamın genişletilememesi,
iki aşamanın canlı sayaçları, hata sonrası kayıtların korunması, rezervde
devamın ertelenmesi ve güvenli hata kaydı. Gerçek VM checkpoint'iyle yeni
çocuk giriş noktası ağ kapalıyken denendi; mevcut 10 native çıktı baytı
aynı kaldı, ham veri tekrar indirilmedi.

Mevcut controller'ın supervisor/bütçe/paket/gate/ay doğrulamasından 8 seçili
test geçti; finalizasyon hatasında kapatma ve yinelenen kilidin çalışan
işi kapatmaması kontrol edildi. Ruff geçti. Gerçek Linux uzun devam işi
henüz yapılmadı; bu araç için ilave hız artışı ölçülmüş değil. Önceki 24/4
deneyinin aynı VM bazına karşı 1,4655 kat hız ölçümü aynen geçerli.

Başlık ZIP SHA256:
`46cc7e2d296a4bcceb1d7d76abf6be9916e4b9658fda7f8bc1439e8871a745ae`.
Aralık plan SHA256:
`7f44606b19aab60fe75392f8df7e6951143892caf94e58eb6b23b2bfc5f19685`.
Public registry'nin sürüm kontrolündeki kopyası:
`configs/gcp_source_blocks_2026-10-09.json`.
