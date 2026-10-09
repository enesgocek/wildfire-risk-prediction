# Bitki örtüsü eğitim dönemi kuyruğu

Kayıt tarihi: 10 Ekim 2026. Amaç, kabul edilmiş aylık yöntemi değiştirmeden
2018–2023 eğitim aylarına kontrollü genişletme ve kesinti sonrası devam etmektir.
Bu işlem yerel Python/Earth Engine hazırlığıdır; GCP VM uydu gözlem kuyruğu ayrıdır.

## Kapsam ve plan

Eğitim dönemi 72 ay ve 2.191 gündür. Mevcut 2.899 hücre ve iki pencereyle
beklenen günlük aday anahtar sayısı 12.703.418'dir. Bu sayı indirilmiş veri veya
tamamlanmış model satırı sayısı değildir; iki pencere uzun tablo biçiminde ayrı satırdır.

```powershell
.\.venv\Scripts\python.exe scripts/landcover/prepare_vegetation_period.py plan --start 2018-01 --end 2023-12
```

`plan` yalnız seçili eğitim aylarında manifest varlığını inceler; ağ isteği
yapmaz. Varlık, kabul anlamına gelmez (`manifest_present_unverified`). Eğitim
dışı veya bozuk tarih aralıkları dosya erişiminden önce reddedilir. 2024 doğrulama
ve 2025 final test bu komutun kapsamı değildir.

## Sınırlı hazırlık ve devam

```powershell
.\.venv\Scripts\python.exe scripts/landcover/prepare_vegetation_period.py run --start 2018-02 --end 2018-02 --max-new-months 1 --max-run-minutes 45 --min-free-gib 10
```

Aylar sıralı çalışır; aynı anda yalnız bir ay ve en fazla iki Earth Engine
isteği vardır. Varsayılan bütçe bir yeni ay, 45 dakika ve en az 10 GiB boş
disk rezervidir. Süre sınırı seçili aralığın tamamlanma garantisi değildir.
Yeni ay bütçesi yalnız başarıyla hazırlanıp bağımsız geri okunan yeni ayları sayar.

Manifest bulunan ay yeniden hazırlanmaz; kaynak/ham integral/günlük tablo
geri okumasından sonra yeniden kullanılır. Eksik aylarda mevcut aylık betik
yalnız eksik kesim ve ham grupları tamamlar. Kod, yöntem ve grid hash'leri
çağrı boyunca sabit tutulur; değişiklik varsa kabul durur.

Süre sınırında aktif yerel çocuk süreç sonlandırılır ve beklenerek temizlenir.
Tamamlanmış dosyalar silinmez; sonraki çağrı aynı aralıkta bunları doğrulayarak
devam eder. O sırada bitmemiş uzak istek yeniden gerekebilir; bütün iş baştan
başlamasa da sıfır tekrar maliyeti iddia edilmez. Disk rezervi her ayın başında
kontrol edilir; sistem genelinde disk alanı ayırmaz veya diğer uygulamaları kısıtlamaz.

## İş bütünlüğü ve kayıt

- `outputs/cache/vegetation_training_queue.lock` tek yazarı korur. Var olan
  kilit otomatik kaldırılmaz. Zorla süreç/PC kapanırsa süreçlerin bittiği ayrıca
  doğrulanmadan kilit kaldırılmaz veya ikinci hazırlık başlatılmaz.
- Her çağrı `outputs/reports/landscape/period_v1/<run_id>/progress.json`
  ve aya özel hazırlık/geri okuma logları oluşturur.
- Her geri okuma `month_v1/<month>/queue_<run_id>.json` adıyla yeni kayıt
  yazar; kabul edilmiş eski raporlar korunur.
- Kabul listesinde ay, satır sayısı, manifest/tablo/denetim hash'leri bulunur.
  Salt dosya varlığı veya başarısız hazırlık kabul listesine alınmaz.
- Dış hata metni genel rapora veya terminale yazılmaz; yalnız hata türü ve
  korunan checkpoint durumu raporlanır. Veri ve makine raporları Git dışındadır.

`selected_training_range_verified`, yalnız çağrının seçili aralığının geçtiğini
gösterir. `paused_*` bütçe nedeniyle durmayı, `failed_checkpoints_retained`
başarısızlığı ve `interrupted_checkpoints_retained` kullanıcı kesintisini ayırır.
Aylar yerel süreç bitene kadar çalışır; bu komut zamanlanmış veya bilgisayar
kapalıyken devam eden bir hizmet değildir. VM'nin süre/kapanma ayarlarını değiştirmez.

## Gerçek denemeler ve sınırlar

Ağustos 2018 yeniden kullanım çağrısı geçti: 179.738 satır, sıfır yeni ay,
10,656 saniye. Manifest ve tablo hash'leri önceki kabul kaydıyla aynı kaldı.
Çağrı raporu:
`outputs/reports/landscape/period_v1/20261009T215904Z_f9e24a5e/progress.json`.

Şubat 2018, önceki mevsim denemesindeki sabit kış ayı olarak geniş kapsam
hazırlığına alındı; yangın etiketleri veya model performansına göre seçilmedi.
Hazırlık ve kuyruk kabulü tamamlandı: 162.344 satır, dört yeni kesim,
1.059,188 saniye. [Kış–yaz destek/yaş sonucu](VEGETATION_TRAINING_SUPPORT_2026-10-10.md)
iki ayın tekrar bağımsız geri okumasını ve açık sınırlamaları kaydeder.

İlk yeni kesim (1 Şubat 2018) 5.798 satırla bağımsız geri okumadan geçti.
30 günlük pencerede 626, 60 günlük pencerede 32 hücre desteksizdi; AOI'nin en
az %90'ında destek bulunan hücreler sırasıyla 1.138 ve 2.168. Ham hazırlama
süresi 260,062 saniye. Bu bir kesim ölçümüdür; aylık eksiklik oranı değildir.
Destek farkı yalnız buluta atfedilmez: kar, su, yansıtım ve kaynak kapsamı
dışlamaları da politikaya dahildir. Kaynak:
`outputs/reports/landscape/full_grid_v1/2018-02-01_b64/preparation.json`.

Kuyruğun 19 davranış kontrolü, destek/yaş incelemesinin 7 kontrolü ve ilgili
aylık/seri/gizlilik kontrolleri birlikte 55 testi geçti. İlk sandbox koşumunda atomik rapor değiştirme için Windows
izin hatası oluştu; çalışma alanındaki geçici dosyalarla izinli koşum geçti.
Bu kontroller saha doğrulaması veya bütün dönem başarı garantisi değildir.

Haftalık kesim, sekiz günlük saklama ve ayrı 30/60 günlük pencereler korunur.
Her ayın günlük seçimi o ayın hazırlanmış kesimleri içinde yapılır; önceki ayın
özetleriyle eksik gün doldurulmaz. Tarihsel erişim zamanı bilinmediğinden
özellikler geriye dönük adaydır. Negatif etiket izni ve 2025 erişimi değişmez.

Aylık karşılaştırma betiği seçili eğitim aylarını bağımsız geri okumadan
geçirdikten sonra destek eksiklerini ve görüntü yaşı yüzdeliklerini raporlar:

```powershell
.\.venv\Scripts\python.exe scripts/quality/review_vegetation_months.py --months 2018-08 --report-name august_training_2018_v1.json
```

Ağustos kaydı geçti. Günlük taşınan satırlarda piksel medyan yaşı özetinin
medyanı 30 günlük pencerede 18,24; 60 günlük pencerede 31,30 gün. Bunlar
hücre-gün dağılımıdır; tekil görüntüler veya görüntünün tam yayımlanma yaşı
değildir. `%90` eşiği tanıdır, habitat veya model kabul kuralı değildir.
