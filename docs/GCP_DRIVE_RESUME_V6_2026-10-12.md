# Drive tanısının geri okuması ve V6 devamı — 12 Ekim 2026

## Amaç, kaynak ve kabul sınırı

Temmuz 2020 pair publication sırasında oluşan Drive metadata 404 hatasından
sonra, tamamlanmış işleri ve VM'deki hazır sonuçları koruyarak devam hazırlığı.
Kullanıcı tanı JSON'unu aktardı ve VM Stop teyidi verdi; bu incelemede VM
başlatılmadı, billing veya scheduling ayarı değiştirilmedi.

Gelen dosya `outputs/gcp_acceleration/received/gcp_v5_drive_probe_20261011T235837794613Z.json`,
7.415 bayt; SHA-256 `65694b8707b8c9d39d0cfd1b7cc6719f635ee7c5c3e132b74b29a9ed56eb0d0e`.
Sonuç, hash kontrollü tanı betiğinin VM'de yaptığı salt okunur isteklere
dayanır. Yerelde rapor kimliği, sayımlar ve donmuş katalogla eşleşme
kontrol edildi; araç tarafından bağımsız canlı Drive erişimi yapılmadı.

## Bulgular

- `readonly_checks_passed`, protected files unchanged, üretim/Drive nesne yazımı sıfır.
- OAuth, klasör erişimi, kota ve mevcut üretim listing kontrolü geçti.
- Hesap kotası 429.496.729.600 bayt, kullanım 67.899.895.763 bayt;
  boş alan **361.596.833.837 bayt** (361,60 GB, ondalık). Mevcut tanıda
  depolama doluluğu yok; eski hatanın bütün olası nedenleri bundan çıkarılamaz.
- Üretim scope'unda 24.409 nesne / 33.241.052.115 bayt raporlandı. Bu değer
  bütün hesabın kullanımından farklı kapsamda olup tamamlanmış ay sayısı değildir.
- 31 yerel hazır pair ZIP'i, toplam 81.521.503 bayt; 30 `not_published`,
  bir `payload_without_completion`: `SNPP:2020200.0948`. Hiçbiri completion
  bulunmadan tamamlandı sayılmadı. Katalog gün dağılımı 18 Temmuz 3,
  19 Temmuz 8, 20 Temmuz 9, 21 Temmuz 11.
- Parent kaydı Temmuz/pair_publication/GOOGLE_HTTP_404 ile tutarlı;
  kaydedilmiş zamanı 11 Ekim 21:51:55,624977 UTC / 12 Ekim 00:51:55 Türkiye.
  Çocuk hata dosyası yok; önceki ReadTimeout toplu hatası tekrarlanmamış.

Tanı, eski 404'ün kesin dosya kimliği/çağrı yerini belirlemez. Özellikle
payload olmadan completion oluşturulmuş sonucu çıkarılmaz; orphan payload
mevcut ve completion yok. Bugünkü erişimin çalışması, geçmişteki gecikme veya
erişim problemini kesin neden yapmaz. Google'ın 404 tanımı mevcut olmayan veya
okunamayan kaynaktır; geçici olduğu varsayılmadı.
[Resmî Drive hata rehberi](https://developers.google.com/workspace/drive/api/guides/handle-errors#404_errors).

Yerel rapor `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/drive_probe_readback_20261012.json`;
SHA-256 `e5dcfdf63931c786f1e50ba1720865104caf8a31f9eee6d4194a75b3c4668112`.
40 tam aylık önceki günlük/katalog kabulü korunur. 31 ZIP'in baytları yerel
makineye gelmedi; bu inceleme yeni bilimsel ürün kabulü değildir. Aralık 31
ertelenmesi, unknown gözlem ve negatif false koşulları değişmedi.

## V6 değişikliği ve iki kontrol

Kaynak `scripts/cloud/run_gcp_source_aware_continuation_v6.py`; yükleme dosyası
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/package/run_gcp_source_aware_continuation_v6.py`.
SHA-256 `3e68a8088e2af1b0b6d1e247c72b26caa066e45143f11b52b8bd634ca7a8320c`.
Eski V5 veya donmuş paketler düzenlenmedi; ayrı sürüm hazırlandı.

1. İlk geçiş yalnız exact V5 final hash'i, aynı üç final, exact başarılı tanı,
   parent ve 31 yerel ZIP hash/boyutunu kabul eder. Temmuz altında yeni veya
   incelenmemiş çocuk tanısı varsa durur. Üretim kilidi altında final/tanı
   kanıtları `diagnostics/reviewed_v5_drive/` içine byte değişmeden kopyalanır;
   hazır çıktılar silinmez. Kopyalama idempotent; gelecekteki keyfi bir V6
   failed durumunun otomatik tekrar başlatılması kabul edilmez.
2. Drive adapter'a yalnız aynı dosyanın metadata GET'inde exact HTTP 404
   için en çok üç ek deneme eklenir. Beklemeler 2/5/10 saniye, dosya ID'si
   ve istek argümanları aynı. Mevcut alt HTTP/token süreleri için 300 saniye
   ek kabul rezervi ile normal 1.200 saniye yayın rezervi korunur; sampler
   veya deadline bozulursa yeniden deneme yapılmaz. Beklemenin son anından
   hemen sonra da kaynak/süre kontrolü tekrar yapılır. Üç denemeden sonra hâlâ
   404 varsa durur. Upload/create/ID allocation/media GET ve diğer HTTP
   sınıfları bu yeni katmanda tekrar edilmez. İstenen kimlik/içerik/completion
   kontrolleri kaldırılmaz; log'a dosya ID'si, URL veya token girmez.

Mevcut completion/payload protokolü orphan payload'ı aynı baytlarla geri
okuyup doğrular, completion'ı en son yayımlar. Yerel native checkpoint
geçerliyse mevcut child_pair yeniden NASA indirmez; ZIP'i doğrulama akışına
hazırlar. ZIP'in hazır olması tek başına native bilimsel checkpoint kabulü
yerine geçmez. Bilimsel kaynak eşleşmesi/tarama zamanı/defer kuralları aynı.

18 saat maksimum, supervisor'ın beş dakika ve pipeline'ın 20 dakika
rezervleri, 24 pair/4 daily worker ve otomatik poweroff korunur. Mevcut
Free Trial dışına çıkılmaz; 18 saatte bütün kalan ayların bitiş garantisi yok.

AST kontrolü bilimsel fonksiyonlar, shutdown, child launcher ve V5 timeout
katmanının aynı olduğunu karşılaştırdı. 29 V6 + 32 V5 + 36 kaynak erteleme,
hata yakalama ve scan adapter testi **97 passed**; lint/format geçti.
İkinci kontrolde eski V5 dahil 25 korunan paket/kod dosyasının hash'i aynı.
Son hazırlık kaydı `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/prepared_readback_v2.json`;
SHA-256 `5ba23563b9cb3eb34a857405224bcb47a7016cbbe9225ad2cab1edd47b1f3daa`.
İlk hazırlık JSON'u değiştirilmeden korunmuştur; son backoff sınırındaki
sampler kontrolü ve ek davranış testi bu ikinci hazırlık kaydında yer alır.

## Kullanıcının başlatma adımları

VM'yi Start yap. SSH'de Upload File ile yalnız yeni V6 `.py` dosyasını home'a
yükle. Eski tanı JSON'u zaten VM home'da bulunur; OAuth JSON'u yüklenmez.

Start sonrası **Cloud Shell**'de:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, seconds 64800, STOP ve automaticRestart false beklenir. Fark varsa
üretim komutunu çalıştırma; VM Stop ve yeni ayar incelemesi gerekir. Yeni
terminationTimestamp değeri alınır; eski 12 Ekim 16:55:48 zamanı kullanılmaz.

**VM SSH**'de aşağıdaki ilk satır tek başına çalıştırılır, ardından yeni
timestamp yapıştırılıp Enter'a basılır:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Sonra yalnız bir kez:

```bash
if printf '%s  %s\n' \
  '3e68a8088e2af1b0b6d1e247c72b26caa066e45143f11b52b8bd634ca7a8320c' \
  "$HOME/run_gcp_source_aware_continuation_v6.py" | sha256sum --check; then
  ~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v6.py \
    --registry ~/source_blocks.json \
    --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
    --termination "$termination" --poweroff
fi
```

Earthdata girişleri görünmeden alınır; sohbete veya dosyaya yazılmaz.
Detached mesajından yaklaşık 10 dakika sonra aşağıdaki salt okunur kontrol:

```bash
tail -n 25 ~/gcp_source_aware_launcher_v6.log
python3 - <<'PY'
import json
from pathlib import Path
p = json.loads((Path.home() / 'wildfire-gcp-production-v1/progress.json').read_text())
for k in ('status', 'continuation_phase', 'continuation_wrapper_sha256',
          'actual_vm_termination_timestamp', 'pairs_processed_this_invocation',
          'pairs_reused_this_invocation', 'error_type', 'failed_month', 'failed_phase'):
    print(k, p.get(k))
print('Tam ay:', len(p.get('existing_months', [])))
PY
```

Başlangıçta eski aylar geri okunurken sayacın düşmesi önceki 40 ayın kaybı
anlamına gelmez. SSH kapansa da detached iş sürer. Tamamlanma, süre rezervi
veya hata halinde mevcut supervisor poweroff ister; Google STOP sınırı
ayrı korumadır. Stop, disk ve diğer kaynakların silinmesi değildir.

## İlk uzak başlangıç bildirimi — 12 Ekim

Kullanıcının SSH launcher çıktısında `Reviewed V5 Drive evidence preserved;
retained pairs: 31` ve iki continuation phase satırı var. Görünen altı eski
ay (2023 Ağustos–Kasım, Haziran ve Mayıs) verified/reused; en son remaining_months
aşamasında. Bu geri okuma yeni aylık üretim değildir; önceki 40 aylık
günlük/katalog kabulü korunur. Görünen bölümde yeni pair/day veya hata satırı yok.

Kaynak kullanıcı günlük bildirimi; canlı süreç, progress wrapper hash'i,
yeni gerçek terminationTimestamp ve yeni ürün baytları bu çıktıda yok.
Bağımsız VM/Drive erişimi yapılmadı. Sonraki kontrol seçilmiş progress alanları,
launcher tail ve Python süreçleridir; ikinci üretim komutu çalıştırılmaz.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/startup_user_readback_20261012.json`;
SHA-256 `c4518db6d02740d9e56108b474b32d0b31904eb487f59cb66edbc637713a74c0`.
