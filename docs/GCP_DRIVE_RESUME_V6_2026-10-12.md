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

## Sonraki süreç ve progress bildirimi — 12 Ekim

Kullanıcının sonraki SSH çıktısında doğru V6 hash'i
`3e68a8088e2af1b0b6d1e247c72b26caa066e45143f11b52b8bd634ca7a8320c`,
`running`, hata/failed month/failed phase alanlarında `None` bulunuyor.
PID 1683, PPID 1, 53 dakika 52 saniyedir aktif. %74,9 süreç ömrü CPU
ortalamasıdır; bütün VM kullanım yüzdesi değildir. Eski ayların 26'sı
geri okunmuş; yeni ve çift düzeyinde yeniden kullanılan sayaçlar sıfır.
Aylık yeniden kullanım çift sayaçlarına yeni işlem olarak eklenmez.

Progress'teki son sınır `2026-10-12T18:13:37.135464Z`, Türkiye saatiyle
**12 Ekim 21:13:37**. Süre rezervi/hata/erken tamamlanmada daha erken
poweroff isteği mümkündür. Bu bilgi kullanıcı progress bildirimi;
Google API üzerinden yeni bir bağımsız scheduling kontrolü yapılmadı.

Önceki 40 aylık günlük/katalog kabulü azalmaz; yeni ürün bayt kabulü yok.
Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012.json`;
SHA-256 `68c3e0a7c0544210d2f10b9546dc67fa330bc474b702f3faf2e1d1a8ea8267cb`.
Devam komutu ikinci kez çalıştırılmadı; kuyruk ayarları değiştirilmedi.

## 48 aylık uzak ilerleme bildirimi — 12 Ekim

Kullanıcının yeni SSH çıktısında doğru V6 hash'i, `running`, hata/failed
month/failed phase alanlarında None var. Supervisor PID 1683, PPID 1;
8 saat 20 dakika 27 saniyedir aktif ve 18 çocuk süreç görünür. Bu çağrıda
2.115 çift işlenmiş, beş çift yeniden kullanılmış; bunlar ay sayısı değildir.
Tam ay sayısı üretici progress'inde 48. Launcher Kasım 2019 çiftlerini
işliyor; görünen son günlük kapanış 11 Kasım. Tam ayların isim listesi
bu bildirime dahil değil; listesi veya yeni ürün baytları bağımsız kabul edilmedi.

72 eğitim ayı hedefinde üreticinin tam-ay sayacı 48/72, yaklaşık %66,7'dir.
Günlük/aylık işlenmiş kayıtlar bilimsel etiket veya model kabulü değildir.
31 Aralık 2023 kaynak ertelemesi önceki protokolden korunur; bu çıktıda
çözüldüğüne dair kanıt yok. Tek snapshot'tan kalan tüm sürenin veya bu
oturumda bitecek ayların güvenilir tahmini yapılmaz.

Progress'in üst son sınırı yine **12 Ekim 21:13:37 Türkiye**; süre rezervi,
hata veya erken tamamlanmada daha erken poweroff mümkündür. Kullanıcı
bildiriminin gözlem saati yok; yerel kayıt saati uzak ölçüm zamanı değildir.
Yeni bağımsız VM/Drive sorgusu, tekrar başlatma veya ayar değişikliği yapılmadı.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012T083704Z.json`;
SHA-256 `c9e0c28b60a022506e92f212e2313a325996830ba18121b34a423f87e8c65c73`.

## 50 aylık uzak ilerleme bildirimi — 12 Ekim

Yeni kullanıcı SSH çıktısında aynı V6 hash'i, running ve None hata/failed
month/failed phase alanları var. Supervisor PID 1683, PPID 1, elapsed
10:20:59; altı çocuk süreç görünür. Üretici tam-ay sayacı 50/72 (%69,4).
Eylül 2019 işleniyor; görünen son kapanış 18 Eylül. Bu çağrıda 2.727 çift
işlenmiş ve beş çift yeniden kullanılmış. Önceki 48 aylık bildirime göre
iki tam ay ve 612 işlenmiş çift artışı; supervisor elapsed farkı 2:00:32.
Bu aralık bütün dönem hızına veya kalan işin kesin bitişine genellenmez.

Tek anlık çocuk sayısı havuz sınırının düşürüldüğünü veya işin takıldığını
göstermez. Süreç ömrü CPU yüzdeleri bütün VM kullanım yüzdesi değildir.
Progress üst sınırı yine 12 Ekim 21:13:37 Türkiye; rezerv/hata/erken
tamamlanmada daha erken durabilir. 31 Aralık kaynak ertelemesinin çözüldüğüne
dair yeni kanıt yok. Tam ay isim listesi/uzak gözlem saati verilmedi.
Yeni VM/Drive sorgusu, üretim komutu veya makine yapılandırması değişikliği yok.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/progress_user_readback_20261012T103705Z.json`;
SHA-256 `16119b6e7067fec0b3190ced7a97894c62eb239ae84639383f8ae41cb81376b6`.
Kaynak kullanıcı günlük/progress/süreç bildirimi; yerel ürün bayt kabulü değil.

## VM duruş bildirimi — 12 Ekim, kapanış günlükleri bekleniyor

Kullanıcının Cloud Shell `gcloud compute instances describe` çıktısında
TERMINATED, maxRunDuration 64.800 saniye (18 saat), STOP ve automaticRestart
false var. Başlangıç 12 Ekim 03:13:42,804; duruş 20:53:54,458 Türkiye.
Geçen süre 17 saat 40 dakika 11,654 saniye. Google üst sınırı yine
21:13:37,135464 Türkiye; VM bu sınırdan 19 dakika 42,677464 saniye önce durmuş.

Bu zamanlama 20 dakika yayın rezerviyle uyumludur; `describe` çıktısı
kapanışı betiğin istediğini, hata olmadığını veya kuyruğun tamamlandığını
tek başına kanıtlamaz. Son yerel kayıtlı 50 aylık uzak bildirim korunur;
bu duruş çıktısında yeni ay sayısı veya ürün baytı yoktur. Bağımsız canlı
VM/Drive sorgusu yapılmadı; üretim/scheduling veya VM ayarı değiştirilmedi.

Sıradaki işlem VM'yi kısa süre yalnız kapanış kayıtlarını almak için açıp
V6 launcher ve seçilmiş progress alanlarını okumaktır. Üretim betiği tekrar
çalıştırılmaz. Duruş nedeni/eksikler görüldükten sonra arşiv toplama ve
devam kararı hazırlanır; inceleme sırasında VM'nin açık tutulması gerekmez.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/vm_stop_user_readback_20261012T181417Z.json`;
SHA-256 `5ab9627ef285da6a890cef5639bb3b38d17930e2285ea07113669c9f9187f910`.
Yerel kayıt saati uzak API gözlem zamanı değildir. UTC/ofset dönüşümleri
ve süre farkları verilen zaman damgalarından tekrar hesaplandı.

## Kontrollü oturum kapanışı: 58 ay — 12 Ekim

Önceki duruş bildiriminin ardından kullanıcı V6 launcher son satırlarını
ve seçilmiş progress alanlarını paylaştı. Doğru V6 hash'i,
`paused_at_runtime_reserve`, `Guest poweroff requested: True` ve None
hata/failed month/failed phase alanları kontrollü rezerv duruşunu bildiriyor.
Bu kanıt önceki zamanlama yorumunu destekler; özgün kapanış dosyalarının
baytları ve ürün arşivleri henüz yerelde denetlenmedi.

Üretici listesindeki 58 ay, Şubat 2019–Kasım 2023 aralığıyla eşleşiyor.
72 eğitim ayı için tam-ay oranı %80,6; tam kapanmamış ay sayısı 14.
Bunlar 2018'in 12 ayı, kısmi Ocak 2019 ve 31 Aralık kaynak ertelemesi
korunan Aralık 2023'tür. Bu 14 ayın tümü sıfırdan işlenecek aylar değildir.
Launcher'ın görünen son günlük kapanışı 11 Ocak 2019; 12–15 Ocak'a ait
kaydedilmiş çiftler sonraki günlerin tamamlandığını kanıtlamaz.

Bu çağrıda 4.829 çift işlenmiş, beş çift yeniden kullanılmıştır. Önceki
50 aylık bildirime göre sekiz tam ay artışı var. Çift sayısı bağımsız
yangın sayısı veya eğitim örneklemi değildir. `full_training_complete=false`
korunuyor; uydu işlem ilerlemesi etiket/model kabulü olarak yorumlanmıyor.
Unknown gözlem ve negatif etiket engelini değiştiren işlem yapılmadı.

Kullanıcı bildirimi ayrı JSON'a kaydedildi; ay listesi/sayısı ve yerel V6
betik hash'i kontrol edildi. Kanıt:
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/final_user_readback_20261012T182251Z.json`;
SHA-256 `0666075db8ba27974fe5c66632146980d0cac7392997cc2fbea57839d4d53149`.
Yerel kayıt zamanı uzak gözlem zamanı değildir; canlı VM/Drive sorgusu yok.

Sonraki adım, yalnız progress.json, acceleration_run_summary.json,
continuation_summary.json, resource_samples.csv ve V6 launcher logunu
zaman damgalı kapanış arşivine toplamaktır. İndirme dizini
`outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/received/` hazırlandı.
Arşiv alındıktan sonra VM Stop durumunda tutulur; yerel kapanış/uyumluluk
denetimi tamamlanmadan yeni üretim çağrısı başlatılmadı.

## Kapanış arşivinin yerel denetimi — 12 Ekim

Kullanıcı kapanış arşivini aktardı ve indirme sonrası VM Stop teyidi verdi.
Dosya `received/gcp_v6_session_20261012T182437Z_logs.tar.gz`, 1.190.920 bayt;
SHA-256 `bdca0bccabdc580cf7f0010983985d85066ed97a042370d5d3956b9c5d6ab509`.
Beş beklenen normal dosya, boyut/isim/tekrar sınırlarıyla bellekte okundu;
diske kontrolsüz arşiv açılmadı. Üç final JSON aynı; gerçek progress,
paused_at_runtime_reserve, V6/adapter/proof/registry kimlikleri ve unknown/
negative=false/full_training_complete=false sınırlarını doğruladı.

Donmuş üretim paketi ve controller üyelerinin hash'leri, 18.711 nominal
çift kataloğu ve bütün yeni pair log kimlikleri eşleşti. 4.829 pair satırı
işlenmiş sayaçla, beş katalogdan türetilmiş reused pair de ilgili sayaçla
eşleşti. 39 yeniden kullanılan ay + başlangıç referansı Temmuz 2023 +
18 yeni kapanmış ay, finaldeki 58 ayı oluşturuyor. Yeni kapanmış dönem
Şubat 2019–Temmuz 2020. 541 DAY COMMITTED satırının tamamı progress'te var;
588 progress günü, önceki Temmuz 2020'nin 1–17 günleri ve Aralık 2023'ün
1–30 günleriyle birlikte tutuluyor. Bu nedenle 588 günün tamamı yeni bu
oturumda üretilmiş sayılmadı.

Ocak 2019'un 1–11 günleri kapanmış. 12–15 Ocak için sırasıyla 9/8/8/8
pair satırı, günlük nominal çift sayılarıyla eşleşiyor; bu 33 çift günlük
commit olmadan tamamlanmış gün sayılmadı. Tam kapanmamış 14 ay ve 31 Aralık
2023 ertelemesi korunuyor. Kaynak katalog/liste kabulü, bütün bilimsel
checkpoint ve Drive ürün baytlarının yerel kabulü değildir.

Kaynak CSV'sinde 29.146 örnek var; son örnek 63.453,644 saniye. Tüm
örneklerde en az 9,94 GiB boş disk, 111,31 GiB kullanılabilir RAM;
süreç ağacı RSS tepe değeri 11,68 GiB. Örneklenen 4 GiB rezerv ihlali yok.
Tek örneğin iowait yüzdesi negatif: CSV satırı 12.246, -0,232. Tarihsel
denetçinin bütün alanlarda negatif olmama kontrolü bu nedenle geçmedi;
bulgu gizlenmedi ve ham CSV değiştirilmedi. Aynı iowait farkını kullanan
CPU busy hesabını da etkileme ihtimali nedeniyle o örneğin tamamı CPU
özetinden dışlandı. Kalan 29.145 örnekte ortalama CPU busy %13,92;
bu ortalama geri okuma/metadata aşamalarını içerir ve işlemci darboğazı
kanıtı değildir. RAM/disk rezerv özeti dışlanan örneği de içerir.

Linux belgeleri /proc/stat iowait sayacının bazı koşullarda azalabileceğini
belirtir; mevcut sampler wait farkını doğrudan yüzdeye çeviriyor. Bu,
bulgu için olası açıklamadır; ham sayaçlar olmadan kesin neden belirlenmedi.
[Linux /proc/stat belgesi](https://www.kernel.org/doc/html/latest/filesystems/proc.html#miscellaneous-kernel-statistics-in-proc-stat).
Örnekleme bütün anları kapsamaz; üretim sampler'ı bu incelemede değiştirilmedi.

Yerel denetimde tarihsel V3 okuyucunun yalnız V6 launcher/hash kimliği
ve 18 saate uygun örnek sayısı sınırı bellekte uyarlandı. Eski okuyucu,
canlı V6, paket ve kabul edilmiş dosyalar düzenlenmedi. İşlem ağ bağlantısı
engellenerek yürütüldü. Denetim betiği ve rapor aynı çıktı dizininde:
`audit_received_session.py`, `session_log_readback_20261012.json`.
Rapor SHA-256 `a47aec42c6df357c6284625ddeb09de2909ae82b6d5489ef049182d586b5ba2a`.
İkinci kontrol arşiv/üyelerin hash'lerini tekrar eşleştirdi; yanlış wrapper,
failed durum ve negatif etiketi açma değişiklikleri reddedildi.
`session_log_readback_crosscheck_20261012.json` bu kontrolü kaydeder.

### Aynı sürümle sonraki 18 saatlik devam

Gerçek final baytları aynı V6 reviewed_resume kimlik koşulunu geçti;
yerel kaynak ve yükleme paketindeki V6 betiği aynı hash'te. Yeni sürüm
veya dosya yükleme gerekmiyor. VM Start sonrası, mevcut başlatma
bölümündeki Cloud Shell describe ile RUNNING, 64.800 saniye/STOP,
automaticRestart=false ve yeni terminationTimestamp doğrulanır. Önceki
12 Ekim deadline'ı tekrar kullanılmaz. Ardından aynı hash kontrollü
komut yeni termination değeriyle yalnız bir kez çalıştırılır.

Tamamlanmış aylar/çiftler tekrar doğrulanıp yeniden kullanılır. Gerçek
VM checkpoint baytlarının ve güncel API erişiminin kontrolü başlatma
guard'larına aittir; yerel günlük denetimi bunların yerine geçmez.
Tamamlanma/rezerv/hata poweroff düzeni ve Free Trial sınırı korunur.
Bu incelemede VM açılmadı ve üretim başlatılmadı.

## Sonraki 18 saatlik oturum için scheduling bildirimi — 12 Ekim

Kullanıcı Cloud Shell çıktısında RUNNING, 64.800 saniye, STOP ve
automaticRestart=false bildirdi. Yeni üst sınır 13 Ekim 12:36:04,698919 UTC /
15:36:04,698919 Türkiye. Aynı hash kontrollü V6 komutu bu yeni deadline ile
hazırlandı; üretimin gerçekten başladığı henüz doğrulanmadı. Önceki 58 aylık
yerel günlük/katalog kabulü korunur. Kaynak kullanıcı bildirimi; bağımsız
VM sorgusu veya araç tarafından bulut başlatması yok.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_scheduling_user_readback_20261012T183734Z.json`;
SHA-256 `fccb8adaea815a93fe16569a1bdd328ec81f6448d121c563eab172cf7ecfcc9a`.

## Yeni oturum başlangıç bildirimi — 12 Ekim

Kullanıcının SSH çıktısında running, december_safe_days, yeni üst sınır
13 Ekim 12:36:04,698919 UTC ve None hata/failed alanları var. Son görünen
yeniden kullanılan aylar Ağustos–Ekim 2023; çağrı sayacı dört tam ay ve
sıfır yeni çift. Önceki 58 aylık yerel günlük/katalog kabulü korunur;
sayaç bu çağrının geri okumasını gösterir, ay kaybı kanıtı değildir.
Log eklenerek yazılır: eski Guest poweroff satırından sonra yeni phase
satırı vardır; bu satır yeni oturumun kapanış bildirimi sayılmadı.
Süreç snapshot'ı veya wrapper hash'i bu çıktıda yok; bağımsız canlı sorgu
yapılmadı. Yeni üretim çiftleri/ayları henüz kabul edilmedi. Aynı başlatma
komutu tekrar çalıştırılmaz; sonraki ilerleme kontrolü beklenir.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_startup_user_readback_20261012T184921Z.json`;
SHA-256 `53ec23a2ed04ada3e5b6ede9f01bef59d81b0bb563dee1198549b00b292d967c`.

## 59 aylık uzak ilerleme bildirimi — 13 Ekim

Kullanıcı SSH çıktısında running/remaining_months, aynı yeni deadline ve
None hata/failed alanları var. Üretici tam-ay sayacı 59/72 (%81,9),
302 yeni işlenmiş çift. Aralık 2018 işleniyor; son görünen günlük kapanış
17 Aralık. Önceki yerel kapanışta 58 ay vardı; yeni sayaç bir tam ay
artışı bildiriyor. Donmuş iş sırasına göre Ocak 2019 kapanışıyla uyumlu;
ancak ay isim listesi ve Ocak kapanış satırı bu tail'de yok.

13 ay henüz tam kapanmamış; Aralık 2018 kısmi, Aralık 2023 kaynak
ertelemesi önceki protokolden korunur. Ay sayacı ve çift sayıları bilimsel
etiket/model kabulü değildir. Süreç/hash snapshot'ı veya ürün baytları
gelmedi; bağımsız VM/Drive sorgusu yapılmadı. Yeni komut çalıştırılmadı.
Son sınır 13 Ekim 15:36:04 Türkiye; normal ilerleme kontrolü sürer.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_progress_59_user_readback_20261012T214509Z.json`;
SHA-256 `371077849e58bb1704b2346d29cdbfcfd22cb24676f8ec9197521c0dda4da4b2`.

## 61 aylık uzak ilerleme bildirimi — 13 Ekim

Kullanıcı SSH çıktısı running/remaining_months, aynı yeni deadline ve
None hata/failed alanları gösteriyor. Üretici 61/72 tam ay (%84,7) ve
715 işlenmiş çift bildiriyor. Önceki kullanıcı snapshot'ına göre iki
tam ay ve 413 çift artışı var. Ekim 2018 işleniyor; son görünen günlük
kapanış 1 Ekim. Sonraki günlerin kaydedilmiş çiftleri günlük kapanış
sayılmadı. 11 ay tam kapanmamış; kaynak ertelemeli Aralık 2023 ayrı kalır.

Ay isim listesi, wrapper hash'i ve süreç snapshot'ı alınmadı. Uzak
bildirim yerel ürün bayt kabulü değildir. Uzak gözlem saatleri olmadığı
için artışlar hız veya bitiş tahminine çevrilmedi. Üst sınır 13 Ekim
15:36:04 Türkiye. Yeni başlangıç/VM ayarı/API sorgusu yapılmadı.

Kanıt `outputs/gcp_acceleration/source_aware_v6_18h_2026-10-12/next_session_progress_61_user_readback_20261012T231032Z.json`;
SHA-256 `aca4da4d729f5d33fef14805724f78cb880623b9f5ede475a80bc09682292a24`.

## Yeni oturumun VM duruş bildirimi — 13 Ekim

Kullanıcı Cloud Shell describe çıktısı TERMINATED, 64.800 saniye/STOP ve
automaticRestart=false gösterdi. Ofsetli zaman damgaları Türkiye saatine
çevrildi: başlangıç 12 Ekim 21:36:10,056; duruş 13 Ekim 06:00:30,264.
Geçen süre 8 saat 24 dakika 20,208 saniye; duruş Google üst sınırından
9 saat 35 dakika 34,434919 saniye önce. 18 saatlik sınıra ulaşılmamış.

Bu bildirim erken tamamlanma, betik poweroff isteği veya hata durumunu
tek başına ayırmaz. Son 61 aylık uzak sayaç ve önceki 58 aylık yerel
günlük/katalog kabulü kendi kapsamıyla korunur. Kapanış arşivi bekleniyor;
yeni ay/ürün kabulü veya bağımsız canlı VM sorgusu yapılmadı. Sonraki adım
VM'yi kısa süre açıp yalnız beş kapanış kaydını indirmek ve Stop yapmaktır.
Üretim betiği yeniden çalıştırılmaz. Yeni teslim dizini
`outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/received/`.

Kanıt `outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/vm_stop_user_readback_20261013T094943Z.json`;
SHA-256 `abf76179d989ebeb6390444defeae627d8f3af1c8607c865c6355ca391fa3a37`.
