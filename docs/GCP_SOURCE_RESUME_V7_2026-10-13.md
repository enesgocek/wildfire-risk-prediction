# V6 tanısının geri okuması ve iki eksik günle V7 devamı — 13 Ekim 2026

## Amaç ve kanıt sınırı

Kullanıcı ikinci tanı JSON'unu aktardı ve VM Stop teyidi verdi. VM/API'ye
bağımsız bağlantı yapılmadı; yeni üretim başlatılmadı. Amaç, Haziran 2018
kaynak uyuşmazlığının diğer gün/ayları durdurmasını önlemek ve hazır işleri
korumaktır. [Önceki hata ve CMR incelemesi](GCP_V6_FAILURE_2026-10-13.md)
tarihli bulgudur; eski kaynakların bütün NASA arşivlerinden yokluğu kanıtlanmadı.

Alınan `outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/received/`
altındaki `gcp_v6_resume_snapshot_20261013T131934138747Z.json`, **15.843 bayt**;
SHA-256 `a98692817bb6a9f6288a645c6123d5d2d5fe4432f38e366b061515094be26de3`.

Yerel geri okumada exact final/ilk tanı/ay planı, altı kaynak hatası ve
12 iptal kimliği, tanı yolları/hash'leri, tek Haziran parent kaydı ve
22 hazır ZIP envanteri eşleşti. ZIP'ler 10–12 Haziran günlerine aittir;
toplam **65.888.711 bayt** (65,89 MB, ondalık). Kaynak hataları 13 Haziran;
iptaller 13–14 Haziran görevidir. -9, Python tanısı olmadan sonlanmadır;
RAM yetersizliği diye kabul edilmedi. Tanı toplayıcı ağ/üretim yazımı sıfır,
credentials/raw içerik okunmadı ve protected dosyalar değişmedi bildiriyor.

Bu üretici tanısının katalogla yerel geri okumasıdır; ZIP baytları yerel
bilgisayara gelmedi, native bilimsel restore veya yeni ürün kabulü yapılmadı.
**65 tam ay** önceki günlük/katalog kapsamıyla korunur; yeni ay tamamlanmadı.
Geri okuma kaydı aynı çıktı kökünde `resume_snapshot_readback_20261013.json`.

## Ayrı V7 sürümü

Kaynak `scripts/cloud/run_gcp_source_aware_continuation_v7.py`; açık kaynak
istisna kaydı `configs/gcp_source_blocks_2026-10-13.json`. Eski V6, eski
registry, donmuş bilimsel kod/paketler ve kabul edilmiş sonuçlar düzenlenmedi.

- Ertelenen günler **13 Haziran 2018** ve **31 Aralık 2023**; altı NOAA-20
  ve iki SNPP kaynak kimliği kayıtlı. Tam günün bütün sensör çiftleri ve
  günlük indirgeme çocukları başlatma kapısında dışlanır; kısmi gün tam sayılmaz.
- Üç aşama: Aralık'ın uygun günleri ve ilk dört mevcut ay; Haziran'ın 13'ü
  dışındaki 29 günü; Haziran dışındaki kalan aylar. Donmuş 71 kuyruk ayı
  birer aşamaya atanır, Temmuz 2023 referansı ayrı korunur. Katalog ve kaynak
  nesneleri değişmez; nominal planın bayt/hash'i veya checkpoint anahtarı değişmez.
- Haziran ve Aralık'ta tam-ay completion yayımlanmaz. Pipeline uygun bütün
  günleri kapatsa da ay sonucu `deferred_source_lineage` olur; asıl üretici
  bu durumu tam-ay paketleme için kabul etmez. Sonraki aşamaya ancak güvenli
  günlerin tamamı geri okunmuşsa geçilir; süre rezervinde sonraki çağrı devam eder.
- İlk geçiş exact V6 final, iki public tanı, 14 protected hash, 18 çocuk,
  parent ve 22 ZIP hash/boyut/popülasyonuna bağlıdır. Yeni/incelemesiz çocuk
  hatası, değiştirilmiş bayt, ilave ZIP veya arşiv çakışması varsa durur.
  Üretim kilidi altında 27 kanıt dosyası ve receipt
  `diagnostics/reviewed_v6_geolocation/` içinde korunur. 18 çocuk tanısı
  aynı baytla taşınır; bu, kaynak hatasını kabul etmek değil iptal edilen
  diğer gün görevlerini yeniden çalıştırabilmek içindir. Final/parent/tanı
  JSON'ları kopyalanır; ZIP/raw kaynaklar silinmez. Kısmi arşiv taşıması
  exact hash'lerle yeniden devam edebilir; ilk kontrol yazım yapmaz.
- Sonraki V7 devamı yalnız aynı wrapper/registry/policy ve aynı kanıt arşiviyle,
  non-failed durumlarda kabul edilir. Yeni failed durumlar otomatik yeniden
  başlatılmaz; inceleme gerekir. Yayımlanmış görev scratch'i normal bilimsel
  doğrulama sonrası temizlenebileceği için 22 ZIP sonsuza dek yerelde aranmaz.
- Native actual-geolocation, sayım, checksum, tarama zamanı ve completion
  kontrolleri kaldırılmadı. Hazır ZIP/native checkpoint yalnız asıl doğrulama
  akışını geçerse kullanılır. Gözlem `unknown`, negatif etiket `false` kalır.

Bütün işlenebilir işler biterse **70 tam ay** ve iki kısmi ayda **59 uygun gün**
(29 Haziran + 30 Aralık) geri okunmuş olmalıdır. Son durum
`processable_months_verified_source_resolution_pending`,
`full_training_complete=false` olur. 70 ay sayısı tek başına bu son durum
kapısını açmaz; 59 uygun gün de gerekir. Nihai etiket/model kabulü ayrı ve açıktır.

## Süre, kapanma ve kontroller

18 saat üst sınır, beş dakika supervisor ve 20 dakika pipeline rezervi,
24 pair/4 daily worker, salt metadata GET 404 ve ReadTimeout sınırlı
tekrarları korunur. Native supervisor, işlerin bitmesi, süre rezervi veya
hata sonrası poweroff ister; Google STOP sınırı ayrı korumadır. İşin
18 saatte bitmesi garanti edilmez. VM Stop kaynak silme değildir; Free Trial
sınırı ve [son kaynak temizliği planı](GCP_FINAL_CLEANUP.md) değişmedi.

Yeni geçiş testleri ile mevcut V6/V5 erteleme, tanı, parser ve snapshot
kontrolleri birlikte **156 passed**; lint/format geçti. 22 donmuş
paket/kod dosyasının hash'i aynı. Son hazırlık kaydı
`outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/prepared_readback_20261013.json`.
SHA-256 `00df6f85ed95430f52357c522f2d2598986a18b328ff9fb07e17339beecb3e92`.
AST kontrolü
bilimsel adaptör, retry, shutdown/pipe/lock ve main akışını karşılaştırır;
main yalnız yeni log adına geçer. Sentetik testler gerçek bilimsel payload
kabulü veya gerçek Linux VM çalışması değildir. Gerçek Linux toplayıcı tanısı
alındı; V7 yürütmesi henüz yapılmadı.

Yükleme dosyaları `outputs/gcp_acceleration/source_aware_v7_18h_2026-10-13/package/`:

| Dosya | SHA-256 |
|---|---|
| `run_gcp_source_aware_continuation_v7.py` | `37a4c4c904b49cac1bb4bc690b485fea19b41e922f24002526ca5ad9d6d0bc3b` |
| `gcp_source_blocks_2026-10-13.json` | `c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95` |

## Kullanıcının başlatma adımları

VM Start yapıp **yalnız yukarıdaki iki yeni dosyayı** SSH Upload File ile
home'a yükle. Eski `source_blocks.json` üzerine yazma; yeni JSON'un adı
ayrı kalır. İki public tanı ve eski helper zaten VM home'dadır. OAuth
bağlantısı/giriş dosyası yükleme veya içeriğini paylaşma gerekmez.

Start sonrasında **Cloud Shell**'de yeni Google üst sınırını al:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, seconds 64800, STOP ve automaticRestart=false beklenir. Ayarlar
farklıysa üretimi başlatmadan Stop yapıp değerlendir. Eski timestamp
kullanılmaz. **VM SSH**'de şu satırı tek başına çalıştır; çıkan isteme yeni
`terminationTimestamp` değerini yapıştırıp Enter'a bas:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Ardından yalnız bir kez:

```bash
if printf '%s  %s\n' \
  '37a4c4c904b49cac1bb4bc690b485fea19b41e922f24002526ca5ad9d6d0bc3b' \
  "$HOME/run_gcp_source_aware_continuation_v7.py" \
  'c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95' \
  "$HOME/gcp_source_blocks_2026-10-13.json" | sha256sum --check; then
  ~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v7.py \
    --registry ~/gcp_source_blocks_2026-10-13.json \
    --registry-sha c5dcb61b6ccd0c6055f96a929cebcbdc6cea41857270b8581ba7a519495aec95 \
    --termination "$termination" --poweroff
fi
```

Earthdata kullanıcı/parola gizli isteme girilir; sohbete yazılmaz. Başlangıçta
eski aylar geri okunur; bu çağrı sayacının küçük görünmesi 65 ayın silindiği
anlamına gelmez. SSH/bilgisayar kapanması detached üretimi durdurmaz.

Yaklaşık 10 dakika sonra salt okunur kontrol:

```bash
tail -n 25 ~/gcp_source_aware_launcher_v7.log
python3 - <<'PY'
import json
from pathlib import Path
p = json.loads((Path.home() / 'wildfire-gcp-production-v1/progress.json').read_text())
for k in ('status','continuation_phase','continuation_wrapper_sha256',
          'actual_vm_termination_timestamp','pairs_processed_this_invocation',
          'pairs_reused_this_invocation','error_type','failed_month','failed_phase'):
    print(k, p.get(k))
print('Bu çağrıda doğrulanan tam ay:', len(p.get('existing_months', [])))
print('Ertelenen günler:', p.get('deferred_days', []))
PY
```

İlk geçişte `Reviewed V6 lineage evidence preserved; children: 18; retained
ZIPs: 22` beklenir. Yeni hash/phase/policy ve None hata alanlarıyla birlikte
çıktı paylaşılır. Başlangıç komutu ikinci kez çalıştırılmaz. Duruşta final
ve günlük arşivi yine yerel geri okumaya alınır; VM tümden silinmez.
