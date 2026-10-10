# Doğrulanmış zaman çözümlemesiyle V3 devam — 10 Ekim 2026

## Paylaşılan oturum kapanışı

Bu ilk kapanış kaydı aşağıda tarihsel olarak korunur. Sonraki oturumun
28 aylık sonuç incelemesi [ayrı bölümde](#ikinci-oturumun-kapanışı-ve-gerçek-arşiv-kontrolü) yer alır.

Kullanıcının Cloud Shell çıktısında VM `TERMINATED`; başlangıç 10 Ekim
01:58:42,563 UTC, duruş 09:36:35,528 UTC. Çalışma 7:37:52,965; Google'ın
09:58:35,730711 UTC sınırından 22 dakika 0,203 saniye önce durmuş.
Son V3 progress `paused_at_runtime_reserve`, launcher ise
`Guest poweroff requested: True` bildiriyor. Bu, hata bildirimi yerine
normal rezerv duruşu kaydıdır. Üst denetleyici gerçek deadline'dan beş dakika
çıkarır; pipeline yeni işe girişte ayrıca 1.200 saniye rezerv bırakır.
Kalan işler/kapanış süresi nedeniyle gerçek poweroff bu eşikle aynı anda
olmak zorunda değildir. Yeni API isteği bu yerel incelemede yapılmadı.

| Ölçü | Paylaşılan uzak kayıt |
|---|---|
| Tam ay listesi | 21: Mart 2022–Kasım 2023 |
| Önceki 14 aya eklenen | 7: Mart–Eylül 2022 |
| Kısmi aylar | Şubat 2022 1–26; Aralık 2023 1–30 |
| Oturum gün listesi | 270; yeniden kullanılan günler dahil |
| Oturum çift sayacı | 2.032 yeni, 9 yeniden kullanılan |
| Politika | Gözlem unknown, negatif izin false |
| Ertelenen | 31 Aralık 2023; iki eski SNPP kaynak bloğu |

Wrapper/adapter/proof SHA'ları hazırlanmış V3 kimlikleriyle eşleşiyor.
Şubat'ın son çiftleri kaydedilmiş olabilir; günlük commit olmadan kalan
iki gün veya ay tamamlanmış ilan edilmez. 72 eğitim ayının 21'i uzak tam ay
listesindedir; kalan 51 ay kısmi ayları da içerir. Bu sonuç, kaynak ürünlerin
yerel bilimsel geri okuması veya tüm etiket veri setinin kabulü değildir.

İlk arşiv yalnız durum, final özetleri, kaynak ölçümleri ve V3 launcher
kaydını alır. Ham NASA girdisi veya özel bağlantı JSON'u dahil edilmez.
VM'nin kısa kontrol açılışında SSH'de:

```bash
tar -czf ~/gcp_v3_session_2026-10-10_logs.tar.gz \
  -C "$HOME/wildfire-gcp-production-v1" \
  progress.json acceleration_run_summary.json continuation_summary.json \
  resource_samples.csv \
  -C "$HOME" gcp_source_aware_launcher_v3.log
```

Komut hatasız bittikten sonra Download File ile bu arşiv alınır ve
`outputs/gcp_acceleration/source_aware_v3_2026-10-10/received/` dizinine
yerleştirilir. VM tekrar Stop yapılır. Kuyruk bu kontrol açılışında
başlatılmaz. Sonraki kabul, arşivin gerçek baytları ve katalog/log
tutarlılığıyla yapılır; bilimsel ürün arşivlerinin kabulü ayrı kaydedilir.

## İndirilen günlük arşivinin yerel geri okuması

Arşiv 496.892 bayt; SHA-256
`19b177afebe1724770307f9e911e103b538ee7a347a283cd294f000cdb5482c7`.
Beş düzenli üye, genişletilmiş boyut 1.562.749 bayt. Link/yol kaçışı,
yabancı veya yinelenen üye ve toplam boyut sınırları denetlendi; diske
tar extract yapılmadı. Progress ve iki final JSON'u birebir aynı.
Orijinal bilimsel paket, controller üyeleri ve hazırlanmış V3 SHA'sı
kontrol edildi. Eğitim kataloğu dışında kayıt okunmadı; 2025 açılmadı.

2.032 yeni çift satırı tekil ve nominal katalog kimliği/ayıyla eşleşiyor.
235 günlük commit satırının nominal çift ihtiyacı 2.023: bu günlerdeki
2.014 yeni çift satırı ile final sayacındaki 9 yeniden kullanım tutarlı.
Kalan 18 yeni çift, Şubat 2022'nin 27 ve 28 günlerinde 9'ar nominal çifti
tam açıklıyor. Günlük commit yok; bu günler tam veya Şubat ayı kapanmış
sayılmadı. Yeniden kullanılan 9 çiftin kimliği katalog/log farkından
çıkarılır; gerçek checkpoint baytları bu arşivde yoktur.

Final gün listesinde 270 kayıt var. Commit satırı olmayan 35 kayıt Eylül
2022'nin 1–5 günleri ve Aralık 2023'ün 1–30 günleridir; önceki kaynakların
yeniden kullanımına dair uzak durumdur. Tam ay listesi, başlangıçta kabul
edilmiş Temmuz 2023 + 13 month-reuse satırı + 7 yeni month-complete satırıyla
eşleşir. Yeni aylar Mart–Eylül 2022; toplam Mart 2022–Kasım 2023 için 21.

11.803 kaynak ölçümü, son örnek 27.296,086 saniye. En az 12,458 GiB boş
disk ve 111,471 GiB kullanılabilir RAM; tepe süreç ağacı RSS 11,290 GiB.
Kaydedilmiş dört GiB rezerv ihlali yok. Örnekler bütün anların garantisi
değildir. Ortalama CPU %17,012; geri okuma/metadata evrelerini de içerir,
yalnız ham işleme CPU verimi veya darboğaz ölçümü sayılmaz.

Araç `scripts/cloud/verify_gcp_v3_session_logs.py`; yeni kaynak verisi
işlemez, ağ/kimlik bilgisi/VM işlemine erişmez. Son launcher'a eklenmiş
eski oturumlar varsa yalnız son başlangıcın sayaçları alınır; önceki
satırlar yeni kabul kapsamına katılmaz. 17 davranış kontrolü yol/link/
boyut/üye saldırısı, çelişen final, değişen etiket/takvim, sahte kaynak,
yanlış sayaç/commit ve eski oturumun iki kez sayılmasını reddetti.
Ruff geçti. Gerçek arşiv sonucu:
`outputs/gcp_acceleration/source_aware_v3_2026-10-10/session_log_readback_accepted.json`.

Bu **günlük ve katalog kabulüdür**; 21 ayın tüm bilimsel ZIP'lerinin yeni
yerel geri okuması, canlı Drive kontrolü veya nihai model veri seti değildir.
Kullanıcı indirme sonrası VM'nin tekrar Stopped olduğunu teyit etti.
Son durum, V3'nin normal rezervden devam guard'ını sağlar. Aynı dosya ve
korunan checkpoint'lerle sonraki oturum, yeni Google durma zamanını kullanır;
27–28 Şubat'ın günlük birleşimleri ve kalan eğitim ayları devam eder.
İlk aşamalar eski ayları doğrularken liste yeniden kısa başlayabilir.

## Sonraki V3 başlangıcının uzak bildirimi

Sonraki devam başlangıcı ayrıca bildirildi: VM PID 1669, süreç 9:20;
progress `running` ve aynı V3 SHA. Yeni deadline 10 Ekim
19:28:19,420127 UTC (22:28:19 Türkiye). Yeni `december_safe_days` girişinden
sonra Ağustos/Eylül/Ekim 2023 month-reuse satırları geldi. İlk kontrol
Drive başlangıç aşamasında eski final/deadline'ı göstermiş, sonraki
kontrolde yeni durum yazılmıştır. Bu ikinci oturum başlangıç kaydıdır;
yeni bitiş veya bütün dönem kabulü değil. Bulut kodu değişmedi.

## Paylaşılan ilk V3 çalışma durumu

Kullanıcının VM sorgusunda üst Python süreci PID 1677 ile canlı, çalışma
süresi 2 dakika 14 saniye. Progress `running`; wrapper ve adapter hash'leri
hazırlanmış sürümle eşleşiyor. Launcher 15 incelenmiş V2 tanısının saklandığını
ve `december_safe_days` aşamasına girişini bildiriyor. Yeni uygulama deadline'ı
10 Ekim 09:58:35,730711 UTC, Türkiye saatiyle 12:58:35. İlk progress okuması
Drive başlangıç kontrolleri bitmeden eski V2 son durumunu göstermişti.
Sonraki çıktı V3 durumunun yazıldığını doğruluyor. Bu uzak çıktı kullanıcı
tarafından paylaşıldı; canlı API denetimi, yeni kaynak işlem başarısı veya
uzun oturum bitiş kabulü değildir. Hazırlık kaydı aşağıda korunmuştur.

## Gerçek kaynak kabulü

Son `gcp_scan_iso_adapter_proof_20261010T014316599475Z.json` dosyası 3.233
bayt; SHA-256 `edfba0a8a87cdbf642e9cfd31a9d7d3115ac3281003b844135e1b127369621ea`.
Üretim girdileri önceki hatalı replay ile birebir aynı hash'lere sahip.
Üç sütunun 203'er UTC zamanı ham TAI93 dönüşümüyle nanosaniyesine kadar
eşleşti. Adapter altında özgün scan fonksiyonu 203 tarama, 1.889 scan–grid
satırı üretti ve native hücre sayımları eşleşti. Pandas isim alanı geri
yüklendi; kaynak dosyaları değişmedi, yeni indirme/üretim yazımı yok.
Yerel geri okuma `scan_iso_adapter_readback.json` içinde tutuldu.

Bu, önceki [tarih biçimi düzeltmesinin](GCP_SCAN_TIME_FIX_2026-10-10.md)
tek gerçek kaynakta kabulüdür. Başka kaynak hatalarının olmayacağı, tüm
ayların tamamlandığı veya uzak listede bulunan 14 aya yeni yerel kabul
verildiği anlamına gelmez. Kullanıcı indirmeden sonra VM'nin Stopped
olduğunu teyit etti; canlı API sorgusu veya yeni üretim oturumu yapılmadı.

## V3 davranışı ve yöntem kaydı

Yeni `run_gcp_source_aware_continuation_v3.py`, V2'nin dönem sıralamasını,
31 Aralık 2023 ertelemesini, 24 çift/4 günlük işçi gate'ini, gizli auth pipe'ını,
tek iş kilidini, rezervleri ve otomatik poweroff davranışını korur. Orijinal
bilimsel/controller paketleri, registry, gate, katalog, checkpoint anahtarları
ve kabul edilmiş ürünler değiştirilmez. Log yeni `gcp_source_aware_launcher_v3.log`
dosyasına yazılır. Yeni ebeveyn hataları ayrı `parent_failure_v3_<UTC>.json`
dosyalarına kaydedilir.

V3 her girişte gerçek başarılı proof dosyasını ve daha önce VM'ye yüklenen
`verify_gcp_scan_iso_adapter.py` dosyasını hash ile doğrular. Çift çocuğunda,
bilimsel klon üyeleri doğrulandıktan sonra yalnız scan modülünün üç UTC
çağrısına sınırlandırılmış adapter uygulanır. Özgün zaman eşitliği, scan
kalitesi/sırası, kaynak kimliği ve hücre sayım kontrolleri aynen çalışır.
Yanlış tarih sessizce eksik değere dönüştürülmez veya yuvarlanmaz.

Yeni hesaplanan çiftlerin `scan_provenance.json` dosyasında
`scan_time_parser_adapter` kaydı adapter/proof/V3 hash'lerini ve uygulanan
çağrıları belirtir. Progress/final durum aynı adapter kimliğini içerir.
Bu kayıt bilimsel kaynak dosyasının hash'i ile çalışma zamanı davranışını
ayırır: eski worker SHA, dondurulmuş kod dosyasının kimliğidir; bütün yürütmenin
adapter kullanılmadan gerçekleştiği iddiası değildir. Eski çift checkpoint'i
geçerli ise native ürünler ve hash'ler değiştirilmeden yeniden kullanılır.

İlk V3 başlangıcında eski son durum ve gerçek proof girdileri tekrar eşleşir.
Yalnız incelenmiş 15 V2 çocuk tanısı, bütün baytları korunarak
`wildfire-gcp-production-v1/diagnostics/reviewed_v2/` dizinine taşınır.
Taşımanın manifesti ve dosya hash'leri `receipt.json` içinde saklanır.
İşlem tek iş kilidi altında gerçekleşir; önce tüm girdiler denetlenir.
Kısmi taşıma sonradan kayıp/üzerine yazma olmadan tamamlanabilir. Ham kaynak,
bilimsel ürün, checkpoint veya tam ay silinmez. Başarılı task'ın normal
cleanup'ı merkezi tanı arşivini silmez. Yeni veya değişmiş başarısızlık
otomatik olarak yeniden denenmez; inceleme gerektirir.

Sonraki normal rezerv duruşlarında V3 kimliğiyle yeniden giriş desteklenir.
Yeni V3 hata durumunda veya bilinmeyen başka çocuk hata dosyasında başlatma
reddedilir. Supervisor kilidi aldıktan sonraki hata, rezerv veya bitiş
kapatma isteğine gider. Başlangıç kontrolünün reddi manuel Stop gerektirir.

## İkinci oturumun kapanışı ve gerçek arşiv kontrolü

Kullanıcının yeni Cloud Shell kaydında başlangıç 10 Ekim 11:28:28,787 UTC,
duruş 19:09:19,084 UTC; VM `TERMINATED`. Çalışma 7:40:50,297, kayıtlı
19:28:19,420127 UTC sınırından 19 dakika 0,336 saniye önce kapanmış.
İndirme için kısa açılış sonrasında kullanıcı VM'yi tekrar Stop yaptığını
teyit etti. Bu VM zamanları kullanıcı tarafından paylaşılan API çıktısıdır;
yerel araç Cloud hesabına bağlanmadı.

Yeni arşiv:
`received/gcp_v3_session_20261010T194058Z_logs.tar.gz`, 482.319 bayt;
SHA-256 `3179ab9ac3f5b7e7c15686240c7f2f891bba1c33746ef06c3b9ddee15ff54199`.
Beş düzenli üye, toplam 1.612.559 genişletilmiş bayt, sınır/boyut/yol
kontrollerinden geçti; diske tar extract
yapılmadı. Progress ve iki final JSON'u aynı; son durum
`paused_at_runtime_reserve`, kapatma isteği `True`, hata alanı yok.
Wrapper/adapter/proof/registry/scope kimlikleri, yerel dondurulmuş paket
ve controller üyeleri eşleşti. Ağ bağlantıları engellenerek aynı kabul
aracı çalıştırıldı; üretim veya canlı Drive okuması yapılmadı.

| Ölçü | Yeni arşivin kabul edilmiş günlük/katalog sonucu |
|---|---|
| Tam ay listesi | 28: Ağustos 2021–Kasım 2023 |
| Önceki 21 aya eklenen kapanış | 7: Ağustos–Aralık 2021, Ocak–Şubat 2022 |
| Kısmi aylar | Temmuz 2021 1–20; Aralık 2023 1–30 günleri listede |
| Yeni çift sayacı ve tekil loglar | 1.863 |
| Yeniden kullanım sayacı | 18; Şubat 2022'nin 27/28 günleriyle katalog farkından eşleşiyor |
| Günlük commit satırları | 206 |
| Final gün listesi | 262; commit olmayan 56 kayıt önceki Şubat/Aralık günleri |
| Kapanmamış son günler | Temmuz 2021 21–25; 45 nominal çift satırı mevcut, günlük commit yok |

Kapanmamış beş gündeki çift sayıları sırasıyla 10, 8, 8, 11, 8; her biri
nominal katalog ihtiyacıyla aynı. Buna rağmen günlük/aylık kapanış kabulü
verilmez. Commit edilmiş günlerdeki 1.818 yeni satır + 18 yeniden
kullanım, nominal çift ihtiyacını açıklıyor; 45 kalan yeni satır
günlük commit dışında tutuluyor. Launcher'a eklenmiş eski oturumun 2.298
satırı yeni çağrı sayaçlarına katılmadı. Tam ay listesi, başlangıç seed'i
Temmuz 2023 + 20 month-reuse + 7 yeni month-complete kaydıyla eşleşiyor.

11.529 kaynak örneği; son örnek 27.131,709 saniye. En az 11,897 GiB boş
disk ve 111,788 GiB kullanılabilir RAM, tepe süreç ağacı RSS 11,280 GiB.
Kaydedilmiş rezerv ihlali yok. Ortalama CPU %16,075; geri okuma/metadata
evreleri dahil olduğundan yalnız işleme darboğazı veya donanım faydası
olarak yorumlanmadı. Örnekler bütün anların garantisi değildir.

Yeni rapor:
`outputs/gcp_acceleration/source_aware_v3_2026-10-10/session_20261010T194058Z_log_readback.json`;
SHA-256 `90989039f9a47425709013a14386bfe86588e52aa9216a2b0560abef74db8c6f`.
Durum `v3_session_log_catalogue_readback_passed`. Üretim/verifier kodu
değişmedi; yeni gerçek arşiv ağ kapalı denetlendi, gereksiz test tekrarı
yapılmadı. Bu günlük/sayaç/katalog kabulüdür; yeni bilimsel ürün ZIP'leri
ve Drive payload/completion baytları ayrıca geri okunmadı.

72 eğitim ayının 28'i tam ay listesinde (%38,89); kalan 44 ay kısmi
ayları da içerir. Gözlem `unknown`, negatif izin `false`, tüm eğitim
kabulü `false`; 31 Aralık 2023'ün iki kaynak bloğu ertelenmiş kalır.
Yeni çağrı aynı V3 ile normal rezervden devam edebilir; yeni VM başlangıcının
gerçek Google deadline'ı gerekir. Bu inceleme yeni VM işi başlatmadı.

## Yerel kontroller

20 yeni V3 kontrolü dahil **94 ilgili test geçti**. Önceki erteleme, sayım,
rezerv, güvenli hata ve kod kimliği kuralları korundu. Yeni testler gerçek
proof/değişmiş proof reddini, adapter factory/isim alanı geri yüklemesini,
provenance kimliğini, yazmayan preflight'ı, tanı baytlarının saklanmasını,
yarım taşımanın devamını ve yeni hata/ham veri/durum değişiminin reddini
kontrol etti. Gerçek eski Kasım checkpoint'iyle V3 çocuk CLI denemesi ağ
engellenerek geçti: native ürünlerin baytları aynı, indirme sıfır.

Ardından aynı integration testine ayrı, yalnız fixture amaçlı provenance
alanı ekleme kontrolü dahil edildi ve test tekrar geçti. Ayrı geçici
üründeki metadata uzantısı dondurulmuş checkpoint/bilimsel geri okumadan
geçti; kabul edilmiş asıl arşiv değiştirilmedi. Günlük birleştirmenin
zaman kontrolü scalar Timestamp kullanır; ilgili kodda ikinci toplu parser
uygulaması gerekmedi. Ruff geçti. Canlı bitki örtüsü hazırlığının kaynak
hash'leri korunmuştur. Bunlar gerçek yeni uzun VM oturumunun kabulü değildir.

## Uzun oturuma geçiş

1. Yeni tek dosyayı hazırla:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\source_aware_v3_2026-10-10\run_gcp_source_aware_continuation_v3.py`.
2. VM Start → SSH → Upload File ile ev dizinine yükle. Önceki helper'lar,
   proof/snapshot JSON'ları, registry ve özel bağlantı dosyası VM'de kalmalıdır.
   Yerel kimlik bilgisi JSON'u yeniden yüklenmez veya paylaşılmaz.
3. SSH'de yeni dosyanın hash'ini kontrol et:

```bash
printf '%s  %s\n' \
  '792d774f53c2a7249a10f4111f2f785e08d5bd2a8153e1151c73efe493b5942e' \
  "$HOME/run_gcp_source_aware_continuation_v3.py" | sha256sum --check
```

OK çıkmazsa uzun komutu çalıştırma; VM Stop ve kısa hata satırı paylaş.

4. **Cloud Shell**'de mevcut oturumun ayarlarını ve gerçek Google durma
   zamanını al. Cloud Shell, VM'nin SSH terminalinden ayrı ortamdır:

```bash
gcloud compute instances describe wildfire-cpu-pilot \
  --project=dogalafetonlemesistemi --zone=europe-west3-c \
  --format='yaml(status,machineType,scheduling.maxRunDuration,scheduling.instanceTerminationAction,scheduling.automaticRestart,resourceStatus.scheduling.terminationTimestamp)'
```

RUNNING, n2-standard-32, 28800 saniye, STOP ve automaticRestart false
beklenir. Yeni `terminationTimestamp` değeri kullanılmalı; eski oturumun
zamanı kullanılmaz. Faturalandırmada Free Trial dışına çıkılmaz; Upgrade yapılmaz.

5. **VM SSH**'de şu satırı ayrı çalıştır; yeni timestamp'i gir ve Enter'a bas:

```bash
read -r -p "Yeni Google durma zamani: " termination
```

Ardından üretimi bir kez başlat:

```bash
~/wildfire-gcp-work/.venv/bin/python ~/run_gcp_source_aware_continuation_v3.py \
  --registry ~/source_blocks.json \
  --registry-sha 6f4eb9fd307ef892a3d3446ef14f32fb758bfd4c59c98b77dce82410e859dd5d \
  --termination "$termination" \
  --poweroff
```

Earthdata kullanıcı adı/parola girişinde karakterler görünmez; bunlar sohbet
ve loga gönderilmez. Detached mesajı başlangıç isteğidir. Gerçek ilerleme:

```bash
tail -n 30 ~/gcp_source_aware_launcher_v3.log
cat ~/wildfire-gcp-production-v1/progress.json
```

İlk aşamada tamamlanmış aylar ve Aralık 2023'ün güvenli günleri doğrulanarak
kullanılır; sonra Eylül 2022'nin kalan kısmına ve diğer eğitim aylarına geçilir.
Ay listesi yeniden doğrulama sırasında kısa başlayabilir; kayıt kaybı değildir.
Kısmi çiftlerde gereken hesap yeniden yapılabilir, tam dönem sıfırlanmaz.

VM işi için ilerleme doğrulanınca SSH sekmesi kapatılabilir; 20–30 dakikada
bir kontrol yeterlidir. Bilgisayarda yürüyen bağımsız bitki örtüsü işi
tamamlanana kadar bilgisayar açık ve uyku dışında kalmalıdır. Bitiş, hata veya rezerv sonrası supervisor kapatma
ister; Google'ın sekiz saat STOP sınırı ek koruma olarak kalır. Sekiz saat
bütün ayların bitiş garantisi değildir. Stop kaynak silme değildir; doğrulanmış
sonuçlar alındıktan sonraki son kaldırma planı [ayrı belgededir](GCP_FINAL_CLEANUP.md).
