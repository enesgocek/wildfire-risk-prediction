# 13 saatlik VM devam hazırlığı — 10 Ekim 2026

Durum: kullanıcı tarafından istenen yeni oturum için yerel hazırlık.
VM başlatılmadı; canlı Cloud ayarı veya faturalandırma değiştirilmedi.

## Gerekçe ve kapsam

Sekiz saatlik oturumdan sonraki yaklaşık beş saatlik manuel yeniden başlatma
boşluğunu azaltmak için Google STOP sınırı 13 saate çıkarılacak. Saatlik işlem
hızı veya ücret değişmez. Aynı VM 13 saat boyunca çalışırsa sekiz saatlik
çalışmanın 1,625 katı çalışma saati kullanır. Birim çıktı maliyetinde iyileşme
yalnız daha az başlangıç/yeniden doğrulama yükü ölçülürse gösterilebilir.

Son kabul edilmiş durum 28 tam ay, Temmuz 2021 1–20 günlük kapanışı ve
Aralık 2023 1–30 güvenli günüdür. Devam aynı checkpoint anahtarlarını kullanır;
tam aylar yeniden doğrulanarak kullanılır, bekleyen kısmi işlemler tamamlanır.
31 Aralık 2023 ertelenir. Gözlem `unknown`, negatif izin `false`,
2018–2023 eğitim kapsamı ve 24 çift/4 günlük worker korunur.

## Betik sınırı ve V4 geçişi

Dondurulmuş acceleration controller `budget(..., False)` fonksiyonu en fazla
28.860 saniye kabul ettiği için yalnız Google ayarını değiştirmek yeterli değildir.
V3 ve controller dosyaları değiştirilmedi. Ayrı V4, gerçek Google son zamanını
en fazla 46.860 saniye (13 saat + 60 saniye tolerans) olarak kabul eder;
eski minimum 4.200 saniye, timezone zorunluluğu ve 24 Ekim UTC trial güvenlik
sınırı korunur. Supervisor'a verilen süre gerçek kalan süreden 300 saniye kısadır.
Pipeline'ın 1.200 saniyelik yeni iş başlatmama rezervi değişmez. Yaklaşık
12 saat 35–40 dakika kullanılabilir süre hedefidir; başlangıç yükü, erken bitiş,
veri/hizmet hatası veya kaynak rezervi bu süreyi azaltabilir.

V3'ten ilk geçiş, [ikinci oturumda kabul edilen](GCP_SOURCE_AWARE_V3_2026-10-10.md#ikinci-oturumun-kapanışı-ve-gerçek-arşiv-kontrolü)
üç eşit final dosyasının tam bayt kimliğine bağlıdır:
`cb455a47990b44387c9ee50100323b6d4b8e7165bb425da0059917bdc7e107d4`.
Başka V3 durumu, başarısız çağrı veya değişmiş final reddedilir. Sonraki V4
çağrılarında V4 kimliği ve mevcut bilimsel/scope kontrolleri geçerli olur.
Kilit alınmadan reddedilen ikinci supervisor çalışan sahibini kapatamaz;
supervisor'ın hata/rezerv/bitiş sonundaki poweroff yolu korunur.

V4 dosyası:
`scripts/cloud/run_gcp_source_aware_continuation_v4.py`;
SHA-256 `30a6bd4f65830e612dae69102abe3a0802f009c4689f626a2e64a8f165f1b7ef`.
Yüklenecek aynı baytlar
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/package/`
altında hazırlanmıştır. Yeni V4 launcher dosyası ayrı tutulur; eski loglar korunur.
Mevcut V3 çevrimdışı log doğrulayıcısı V4 kimliğini kabul etmez; V4 sonuçlarının
kabulünde yeni sürüm kimliği ayrıca denetlenmelidir. Hazırlık uzak çalışma başarısı değildir.

Yerel V4 testlerinde 20 kontrol geçti: 13 saat/sekiz saat/geçerli kısa süre,
fazla uzun/geçmiş/timezone eksik/trial sınırı, gerçek kabul edilmiş V3 finalinin
geçişi, değişmiş bayt/başarısız durum/eksik eş finalin reddi ve V4'te devralınan
planlama/hata/erteleme davranışları. V3 ile değişmeyen fonksiyonların AST'leri
eşleşti. Ruff lint/format geçti. V3 hash'i, iki donmuş paketin 19 üyesi ve canlı
bitki örtüsü V2/adapter hash'leri ayrıca değişmeden okundu. İlk sandbox test
çağrısı geçici klasör izni nedeniyle kurulamadı; V4 kontrolleri çalışma
alanındaki ayrı geçici klasörde geçti. Geniş sandbox çağrısı tamamlanmadan
sonlandırıldı; alt süreçli regresyon ayrıca host izinleriyle çalıştırıldı.
Bu ortam olayları uzak VM veya üretim başarısızlığı değildir.

Host regresyon çağrısı 298,38 saniyede **59 passed** ile tamamlandı:
ilk 13 V4 kontrolü ve 46 mevcut V3/acceleration testi. V4'e eklenen yedi
planlama/hata davranışıyla ayrı güncel V4 çağrısı **20 passed** verdi;
toplam 66 farklı kontrol geçti. Kapanışta integrity/export/telemetry hatasında
poweroff, reddedilen çift supervisor'ın sahibini kapatmaması, gerçek eski
çift/gün/ay ürününün yeniden kullanımı ve bozuk nested completion'ın reddi
bu regresyonda kontrol edildi. Yeni 13 saatlik VM çağrısı yapılmadı.

Hazırlık kaydı:
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/prepared_readback.json`;
SHA-256 `16a91a44b7bb027de62498945fcb68c9c5303b2c25bb14d9cd99f3cb07fa8e19`.

## VM kapalıyken süreyi ayarlama

Google CLI belgesine göre `set-scheduling` yalnız `TERMINATED` VM'de uygulanır.
`max-run-duration` her başlangıçta gerçek çalışma zamanından itibaren hesaplanır;
yeni başlangıçta yeni `terminationTimestamp` alınır.
[Resmî komut ve süre davranışı](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/set-scheduling).

**Cloud Shell**'de bu komutu tek başına çalıştır:

```bash
gcloud compute instances set-scheduling wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --max-run-duration=13h --clear-termination-time \
  --instance-termination-action=STOP --no-restart-on-failure
```

Ardından ayrı çalıştır:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,scheduling.terminationTime)'
```

Beklenen: `TERMINATED`, n2-standard-32, `seconds: '46800'`, `STOP`,
`automaticRestart: false`; sabit `terminationTime` yok. Ayar komutu VM'yi
başlatmaz. Free Trial ve noncommercial Earth Engine kaydı korunur;
ücretli hesap yükseltmesi bu işlemin parçası değildir.

## Başlatma ve devam

Ayar geri okuması doğru olduğunda mevcut VM'yi Start yap, SSH'ye bağlan.
Yalnız yeni V4 Python dosyasını SSH Upload File ile home dizinine yükle.
VM'deki eski paket/proof/adapter/registry ve özel bağlantı dosyaları kullanılır.

SSH'de dosyayı doğrula:

```bash
printf '%s  %s\n' \
  '30a6bd4f65830e612dae69102abe3a0802f009c4689f626a2e64a8f165f1b7ef' \
  "$HOME/run_gcp_source_aware_continuation_v4.py" | sha256sum --check
```

Cloud Shell'de yeni Google son zamanını al:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING/46800/STOP/false beklenir. SSH'de ilk satırı ayrı çalıştırıp **bu yeni**
`terminationTimestamp` değerini gir; ardından devam komutunu bir kez çalıştır:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

```bash
~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v4.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" --poweroff
```

Earthdata girişleri terminalde gizlidir; sohbet veya loga aktarılmaz.
Başlangıç ve yaklaşık 10 dakika sonraki ilerleme şu salt okunur komutlarla kontrol edilir:

```bash
tail -n 25 ~/gcp_source_aware_launcher_v4.log
cat ~/wildfire-gcp-production-v1/progress.json
ps -C python,python3,python3.12 -o pid,ppid,etime,pcpu,rss,comm
```

V4 `running`, yeni deadline ve doğru wrapper kimliği doğrulanınca SSH sekmesi
kapatılabilir. Yerel bitki örtüsü işi için bilgisayar açık/uyku dışında kalır;
bu değişiklik o işin süresini uzatmaz. VM için otomatik poweroff ve Google
13 saat STOP sınırı birlikte çalışır. Normal rezerv duruşunda kaldığı yerden
devam edilir; hata duruşunda önce teşhis alınır. Stop kaynak silme değildir.

## Kapanış arşivi

VM durmuşsa kısa inceleme için tekrar açıldıktan sonra SSH'de:

```bash
archive="$HOME/gcp_v4_session_$(date -u +%Y%m%dT%H%M%SZ)_logs.tar.gz"
tar -czf "$archive" \
  -C "$HOME/wildfire-gcp-production-v1" \
  progress.json acceleration_run_summary.json continuation_summary.json resource_samples.csv \
  -C "$HOME" gcp_source_aware_launcher_v4.log \
&& printf 'Download: %s\n' "$archive"
```

Download File ile bildirilen dosyayı indir; VM'yi tekrar Stop yap ve arşivi
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/received/` içine koy.
Yeni sonucun bağımsız kabulü bu hazırlıktan sonra yapılır.

## İlk uzak çalışma geri bildirimi

Kullanıcının önceki Cloud Shell çıktısında kapalı VM ayarı 46.800 saniye,
STOP ve automaticRestart false olarak geri okunmuştur. Daha sonra paylaşılan
SSH çıktısında 10 Ekim 20:39:26 UTC'de V4 `running`, faz `remaining_months`,
wrapper hash'i hazırlanmış V4 ile aynıdır; hata alanı `None`. PID 1733,
PPID 1, elapsed 20:29, CPU yüzde 69,4 ve RSS 271.396 KiB görünür.
Log kuyruğunda Ağustos–Kasım 2023 ve Mart–Haziran 2023 aylarının yeniden
kullanımı vardır. Yeni çift sayısı sıfırdır: eski ayların geri okunması
henüz yeni ham işlem sayılmaz. Son kabul edilmiş toplam 28 ay bu gözlemle artmaz.

İlk 17 saniyelik çıktıda progress hâlâ eski V3 finaliydi; yeni geri bildirimde
V4 kimliği ve yeni son zaman görünür. Kayıtlı son zaman 11 Ekim
09:16:26,085080 UTC / **12:16:26 Türkiye**. Mevcut rezervlerle normal
poweroff yaklaşık 11:51–11:56 Türkiye çevresinde beklenir; başlangıç yükü,
erken bitiş veya hata daha erken kapanışa neden olabilir. Bu aralık zamanlama
beklentisidir, gerçekleşmiş kapanış değildir.

Kanıt kullanıcı tarafından paylaşılan çıktıdır; araç canlı VM/API sorgusu
yapmadı. Yerel özet, yalnız bu alanları ve timezone dönüşümünü kayıt altına alır:
`outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/startup_20261010T203926Z_user_readback.json`;
SHA-256 `6dbf75a2d52c2c8f7f3cc50019c4712747adb2935e6b4ddc75f10b9376f7960d`.
Yeni bilimsel ürünlerin/Drive baytlarının kabulü ve yerel bitki örtüsü süreç
kontrolü bu başlangıç geri bildiriminde yapılmadı.
