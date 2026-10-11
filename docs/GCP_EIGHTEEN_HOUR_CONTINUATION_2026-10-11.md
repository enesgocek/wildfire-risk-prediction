# V4 kapanış denetimi ve 18 saatlik V5 devam

İnceleme: 11 Ekim 2026; uzak deney: 10–11 Ekim. Kullanıcı indirme sonrası
VM Stop teyidi verdi. Bu hazırlıkta VM/billing ayarı değiştirilmedi veya
VM başlatılmadı.

## Bulgular ve kanıt sınırı

Arşiv: `outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/received/gcp_v4_failure_20261011T150511Z.tar.gz`;
SHA-256 `44de56e5d1aae43795733c9c3d193d5030c220b34079132b5f3441a2d060af88`.
30 düzenli üye/2.365.515 açılmış bayt, sınırlı okuyucuyla çıkarma yapılmadan
kontrol edildi. Üç final JSON baytları eşit; V4/controller/parser/policy doğru.
Donmuş paket üyeleri ve 18.711 nominal çift kataloğu da geri okundu.

Günlük/katalog karşılaştırması: **40/72 tam ay (%55,6)**, Ağustos 2020–
Kasım 2023; önceki kabul 28 ay. 12 yeni kapanışın Temmuz 2021 kısmı önceden
hazırlanmıştı; artış 12 ayın tüm ham işleminin sıfırdan yapıldığı anlamına gelmez.
3.020 yeni çift, katalogdan çıkarılan 45 yeniden kullanım, 345 günlük commit
ve durumdaki 395 gün tutarlı. Yeni commit satırı olmayan 50 gün önceki kısmi
Temmuz 2021/Aralık 2023 günleridir. Temmuz 2020 tamamlanmadı. Aralık 2023
1–30 korunuyor; 31 Aralık için iki kaynak uyuşmazlığı sürüyor.

Temmuz 2020'de **5 ReadTimeout**, ardından 19 `-9` çocuk çıkışı, üst
RuntimeError ve başarılı poweroff isteği var. Pipeline hata yolu aktif
çocukları öldürür; sıra sonraki çıkışlar için iptal açıklamasını destekler.
`-9` tek başına OOM kanıtı değildir. HTTP adresi/traceback alınmadığından
NASA kesintisi, hız kısıtlaması veya bağlantı sorununun bileşeni kesinleşmedi.
Yerel internet kesintisi bağımsız uzak işin nedeni olarak gösterilemez.

17.868 kaynak örneğinde en düşük boş disk 11,24 GiB, en düşük kullanılabilir
RAM 111,45 GiB, en yüksek süreç ağacı RSS 11,48 GiB; örneklenmiş rezerv ihlali
yok. Örnekler her anı kapsamaz. CPU ortalaması %14,36 geri okuma/metadata
sürelerini de içerir; yalnız işçi verimi veya daha güçlü VM gereksinimi sayılmaz.
Kullanıcının Compute Engine çıktısındaki süre 10:59:48,413; cap'ten
2:00:04,869 önce duruş. Arşiv normal süre kapanışı yerine hata duruşunu doğrular.

Geri okuma: `outputs/gcp_acceleration/source_aware_v4_13h_2026-10-10/failure_readback.json`;
SHA-256 `9d477cd9c388ed2b004ee76b33292ce1de310c9b87e9a37a1bc4d6269f971594`.
Kabul **günlük/katalog** düzeyindedir; ürün ZIP'leri/Drive completion baytları
burada indirilip bağımsız doğrulanmadı. Devam sırasında mevcut bilimsel geri
okuma kuralları yeniden kullanılan ürünlere uygulanır.

## V5 değişikliği ve kontroller

Yeni ayrı giriş `scripts/cloud/run_gcp_source_aware_continuation_v5.py`:

- Gerçek Google deadline en fazla 18 saat + 60 saniye tolerans; 5 dakika
  üst süreç/20 dakika pipeline rezervi ve 24 Ekim konservatif trial sınırı korunur.
- İlk geçiş yalnız bu V4 finalinin tam hash'i/üç eşit dosya ile kabul edilir.
  İncelenen 24 Temmuz tanısı tam hash'lerle `diagnostics/reviewed_v4_timeout/`
  alanına taşınır; değişen/ek tanı durdurur. Ham/checkpoint/ürün değişmez.
- Yalnız çift çocuğunun tam ReadTimeout/CLASS_ONLY şeması iki ek deneme alır:
  30 ve 60 saniye bekleme, toplam en fazla üç çalıştırma. Her denemeye tam
  900 saniye çocuk bütçesi + yayın rezervi kalmalıdır. HTTP/auth, bilimsel
  ValueError, gün azaltma, watchdog, kaynak ihlali ve iptal yeniden denenmez.
  Kalıcı hata yine duruş ve poweroff üretir.
- Deneme tanıları task temizliğinden ayrı `diagnostics/transient_read_timeout/`
  alanında tutulur. Eksik dosya temizliği ve bilimsel kontroller eski çocukta
  uygulanır. Aynı 24 çift/4 gün çalışanı, kilit, paket, parser, checkpoint
  anahtarı ve kaynak ertelemesi korunur. Gözlem unknown/negatif false.

**32 V5 + 20 V4 testi** ve **73 mevcut regresyon testi**, lint/format geçti.
Gerçek arşiv, bozulmuş dosya, idempotent koruma, kalıcı hata, bekleme sırasında
kaynak ihlali, iptal, süre ve başarılı task temizliğinden sonra tanı koruması
sınandı. AST karşılaştırması bilimsel çocuk/yayın/faz ve gerçek subprocess
öldürme/cleanup gövdesini V4 ile eşit buldu. Ağ kapalı yerel testler uzak
18 saatlik başarı veya hız garantisi değildir.

Hazırlık: `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/prepared_readback.json`;
SHA-256 `ec5ef9bdd2c946eb10b7dd0469354305ce0f9a247f9a19f65d39c4546b450c49`.
19 donmuş paket üyesi ve beş runtime kod kimliği kaydedildi. Yüklenecek dosya:
`outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/package/run_gcp_source_aware_continuation_v5.py`;
SHA-256 `f168692eb4aeda1eb7e00e72340a81d35f1a6701617a13da237e9376495ebf45`.

## Uygulama: kapalı VM'de süreyi kaydet

Cloud Shell'de komutları **ayrı ayrı** çalıştır. Ayar VM'yi başlatmaz.
[Resmî komut belgesi](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/set-scheduling)
bu değişiklik için VM'nin TERMINATED olmasını gerektirir.

```bash
gcloud compute instances set-scheduling wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --max-run-duration=18h --clear-termination-time \
  --instance-termination-action=STOP --no-restart-on-failure
```

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart)'
```

Beklenen TERMINATED, `seconds: '64800'`, STOP, automaticRestart false.
Free Trial korunur; ücretli hesap Upgrade bu planın parçası değildir.
18 saat üst sınırdır; birim fiyat indirimi veya tüm kuyruğun bitiş garantisi yok.

## Başlat, yükle ve yeni deadline'ı kullan

Ayar doğruysa VM'yi Start yap, SSH'ye bağlan. **Yalnız yeni V5 `.py` dosyasını**
Upload File ile home dizinine yükle. Özel JSON/OAuth veya veri paketleri
yeniden yüklenmez. Eski V4 dosyasını tekrar çalıştırma.

SSH'de:

```bash
printf '%s  %s\n' \
  'f168692eb4aeda1eb7e00e72340a81d35f1a6701617a13da237e9376495ebf45' \
  "$HOME/run_gcp_source_aware_continuation_v5.py" | sha256sum --check
```

Cloud Shell'de yeni gerçek son zamanı al:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING/64800/STOP/false doğruysa SSH'de ilk satırı **tek başına** çalıştır;
eski deadline yerine yeni terminationTimestamp değerini gir:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Ardından bir kez:

```bash
~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v5.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" --poweroff
```

Earthdata girişleri terminalde görünmez; yazıp Enter'a bas. Kimlik
bilgilerini sohbete/dosyaya aktarma. Yaklaşık 10 dakika sonra SSH'de:

```bash
tail -n 25 ~/gcp_source_aware_launcher_v5.log
python3 - <<'PY'
import json
from pathlib import Path
p = json.loads((Path.home() / 'wildfire-gcp-production-v1/progress.json').read_text())
for k in ('status', 'continuation_phase', 'continuation_wrapper_sha256',
          'actual_vm_termination_timestamp', 'pairs_processed_this_invocation', 'error_type'):
    print(k, p.get(k))
print('Tam ay:', len(p.get('existing_months', [])))
PY
ps -C python,python3,python3.12 -o pid,ppid,etime,pcpu,rss,comm
```

Yeni V5 hash'i/deadline/running/canlı süreç görülmeden eski progress'i yeni
başlangıç sayma. İlk eski ay geri okuma uzun sürebilir. VM işi SSH sekmesi
kapansa sürer; yerel bitki örtüsü için bilgisayar açık/uyku dışında kalır.
Normal rezerv duruşu cap'ten yaklaşık 20–25 dakika önce beklenir; kalıcı hata
veya erken bitiş daha erken durdurabilir. Google STOP ikinci üst sınırdır;
Stop kaynak silme değildir. Hata tanıları incelenmeden tekrar başlatılmaz.

## İlk V5 uzak başlangıç geri bildirimi

Kullanıcı SSH çıktısında tam hazırlanmış V5 hash'ini, running ve
remaining_months fazını paylaştı. İncelenen 24 V4 tanısı korunmuş;
Ağustos–Kasım 2023 geri kullanımı günlükte var. PID 1681, PPID 1,
elapsed 15:02, CPU %63,9 ve RSS 290.536 KiB; hata alanı None.
Yeni çift sıfır ve bildirilen ay sayısı beştir.

Bu beş ay önceki 40 ayın kaybolduğunu göstermez. Donmuş controller her
çağrıda Temmuz 2023 seed'iyle başlar; yeniden geri okunmuş ayları ekler.
İlk dört yeniden kullanım + seed beşi açıklar. Güncel oturumun geri okuması
henüz tamamlanmamış; daha önceki yerel günlük/katalog kabulü 40 ay olarak
korunur. Çift çocukları başlamadan yalnız supervisor'ın CPU kullanması bu
geri okuma aşamasıyla uyumludur; tek snapshot gelecekteki hata yokluğunu
garantilemez.

Kaydedilmiş son zaman **12 Ekim 13:55:48 UTC / 16:55:48 Türkiye**.
Normal rezerv duruşu yaklaşık 16:30–16:35 Türkiye çevresinde beklenir;
hata veya erken bitiş daha erken kapatabilir. Yeni Cloud Shell scheduling
geri okuması bu çıktıda yok; son zaman p alanından alınmıştır. Canlı VM/API,
Drive veya yeni ürün baytları araç tarafından bağımsız okunmadı.
Kanıt `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/startup_user_readback_20261011.json`.
SHA-256 `295596772dfcead6b0d71999d71bfc0914c933cdacead345c437934af1a35761`.
