# V2 erken kapanışı ve salt okunur teşhis — 10 Ekim 2026

Sonraki gerçek kaynak replay'i tarih çözümleme hatasını 184. satırda yeniden
üretti. [Dar düzeltme ve yeni kabul adımı](GCP_SCAN_TIME_FIX_2026-10-10.md)
ayrı kayıttadır; aşağıdaki ilk hazırlık bulguları tarihsel sırasıyla korunmuştur.

## İndirilen snapshot'ın yerel incelemesi

10 Ekim'de indirilen `gcp_v2_failure_snapshot_20261010T011955892163Z.json`
dosyası 8.794 bayt; SHA-256
`43c6a64e6547c2856f7ce39fcf478e12be3df40c8032d80cdfa3daf8e4062e0b`.
V2 wrapper, controller, orijinal kuyruk ve kaynak erteleme kimlikleri eşleşti.
Yerel geri okuma `snapshot_readback.json` içinde tutuldu; kabul edilmiş
snapshot değiştirilmedi. Kullanıcı dosyayı indirdikten sonra VM'nin tekrar
Stopped olduğunu teyit etti; bu kayıt canlı API sorgusu değildir.

İlk kaynak `SNPP:2022252.2230` için bir `ValueError CLASS_ONLY`, diğer
çocuklarda 14 adet `-9` kaydı mevcut. 3.511 kaynak ölçümünde en düşük boş
disk **13,05 GiB**, kullanılabilir RAM **112,08 GiB**, en yüksek süreç ağacı
RSS **11,36 GiB**. Örneklerde VM disk/RAM rezervinin tükenmesi görülmedi;
ölçülmeyen anlar veya çocuk adres alanı limiti bununla kesin dışlanamaz.

İlk çiftin fire dosyası 657.390, geolocation dosyası 180.547.838 bayt;
ikisinin dosya boyutu planla eşleşiyor. İlk audit, merkez tablosu, alan
çıktıları ve `scan_times.csv` var; scan-grid/all-scans/provenance çıktıları
yok. Dondurulmuş `child_audit` sırası, alan hesabından sonraki `source_scans`
çağrısını incelemeyi gerektiriyor. Dosya varlığı/boyutu tek başına kaynak
doğruluğu veya kök neden kanıtı değildir. Uzak kayıtların bildirdiği 14 tam
ay bu küçük teşhis dosyasıyla yeni yerel aylık kabul almadı.

## Tek kaynak için hazırlanan ikinci kontrol

`scripts/cloud/diagnose_gcp_v2_scan_times.py`, aynı başarısız durum ve
Eylül planına bağlı bir salt okunur yeniden üretim aracıdır. Önceden VM'ye
yüklenen snapshot helper'ını hash ile doğrular; yeni özel bağlantı dosyası
istemez. Mevcut iş kilidi üretim çalışırken kontrolü engeller. Bütün paket
ve bilimsel klon üyeleri doğrulanmadan özgün fonksiyon yüklenmez.

Araç kalan iki ham dosyayı ve mevcut bilimsel referansları okur; ağ/DNS
erişimi engellidir. Yeni indirme, OAuth/Earthdata girişi, üretimi sürdürme,
mevcut sonuç yazımı veya bilimsel kod değişikliği yapmaz. GDAL ek dosya
yazımı ve Python bytecode yazımı kapalıdır. Okunan üretim girdilerinin
hash'leri işlem öncesi/sonrası aynı olmalıdır. Çıktı yalnız yeni ev-dizini
JSON'udur. Geçmiş hatanın otomatik kanıtlandığı iddia edilmez.

Yerel sentetik kontrolde tam saniye ve kesirli saniye içeren UTC dizisi,
dondurulmuş kodun varsayılan Pandas çözümlemesinde `ValueError` üretti.
Açık `format="ISO8601"` çözümlemesi aynı nanosaniyeleri korudu. Bu yalnız
bir hipotezdir: gerçek Eylül kaynağı yerelde bulunmadığından henüz denenmedi.
Yeni araç mevcut `scan_times.csv` ile ham geolocation'dan özgün TAI93
dönüşümünü karşılaştırır; ardından **değiştirilmemiş** `source_scans` çağrısını
çalıştırır. Hata olursa yalnız hash ile doğrulanmış bilimsel dosya/fonksiyon/
satır ve güvenli hata sınıfı kaydedilir. Serbest hata metni, traceback
metni, yerel değişkenler veya kimlik bilgileri rapora girmez.

17 yeni davranış kontrolü dahil snapshot/V2/gizlilik ile **60 test geçti**.
Karışık hassasiyet, bir nanosaniyelik sapmanın reddi, UTC şeması, özel hata
metninin dışlanması, ağ engeli, değişmiş helper/girdi ve salt okunur replay
kontrol edildi. Gerçek dondurulmuş yerel paketler doğrulanıp ayrı klonda
bilimsel import denemesi geçti. Ruff kontrolü geçti. Canlı üretim paketleri
ve yerel bitki örtüsü hesaplama dosyaları değiştirilmedi. Bunlar VM'de tek
kaynak denemesinin yapıldığı veya sorunun giderildiği anlamına gelmez.

### Sıradaki kullanıcı adımları

1. VM'yi Start yapıp SSH'ye bağlan; üretim komutunu çalıştırma.
2. Upload File ile yalnız yeni aracı ev dizinine yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_v2_2026-10-10\diagnose_gcp_v2_scan_times.py`.
   Önceki `collect_gcp_v2_failure_snapshot.py` aynı ev dizininde kalmalıdır.
3. Şu komutu çalıştır; `Download:` satırı gelene kadar SSH'yi açık tut:

```bash
if printf '%s  %s\n' \
  '308c301a837924286dcce398685ff64c2b97da64f5fd373204b6bdfef029e1b1' \
  "$HOME/diagnose_gcp_v2_scan_times.py" | sha256sum --check; then
  timeout 240s ~/wildfire-gcp-work/.venv/bin/python \
    ~/diagnose_gcp_v2_scan_times.py
fi
```

4. `Download:` satırındaki `gcp_v2_scan_time_probe_<UTC>.json` dosyasını
   indirip aynı `continuation_failure_v2_2026-10-10/received/` klasörüne koy.
5. VM'yi Stop yap. Araç otomatik kapatmaz. Süre sınırı veya kısa hata nedeniyle
   JSON oluşmazsa VM'yi yine Stop yapıp yalnız kısa terminal sonucunu paylaş.

Gerçek kaynağın çıktısı incelenmeden parser düzeltmesi, yeni üretim paketi
veya uzun oturum başlatılmayacak. Checkpoint'ler ve ertelenen gün korunacak.

## Paylaşılan durum ve kanıt sınırı

Kullanıcının Cloud Shell sorgusunda VM `TERMINATED`. Son başlangıç
9 Ekim 20:43:22,175 UTC, son duruş 23:10:27,747 UTC; çalışma yaklaşık
2 saat 27 dakika 5,6 saniye. Planlı Google Stop sınırı 10 Ekim
04:43:15,426586 UTC (07:43 Türkiye) ve `maxRunDuration=28800`.
Dolayısıyla bu kapanış sekiz saatlik sınırla açıklanmıyor.

Paylaşılan V2 günlüğünde ilk görünen başarısız çocuk
`SNPP:2022252.2230`, `ValueError CLASS_ONLY`. Kaynak günü 9 Eylül 2022.
Sonrasında diğer çocuklarda `-9`, `RuntimeError CLASS_ONLY`, ebeveynde
`PARENT_FAILURE RuntimeError CLASS_ONLY` ve
`Guest poweroff requested: True` kaydedilmiş. Son satır devam işleminin
durdurulduğunu bildiriyor. Kapatma isteği günlükte var; temel ValueError'ın
nedeni henüz belirlenmedi.

Dondurulmuş `accelerated_production.py`, hata durumunda aktif çocukları
durduruyor; controller da finally aşamasında kapatma istiyor. Bu nedenle
sonraki `-9` kodları temizleme sırasında oluşabilir. Tek başına RAM tükenmesi,
NASA kaynak bozukluğu, Drive sorunu veya kaynak limiti kanıtı değildir.
İlk kaynak hata ayrıntısı ve ölçümler alınmadan neden ilan edilmez.

Uzak progress, Ekim 2022–Kasım 2023 için 14 tam ay listeliyor. Bu çağrıda
Eylül 2022 1–5, Ekim ve Kasım 2022'nin bütün günleri ve Aralık 2023 1–30
günleri doğrulanmış gün listesinde. Sayaç 510 yeni çift, 15 yeniden kullanım;
başarısız ay Eylül 2022, son kayıtlı aşama `pair_publication`.
Bu aşama adı ilk çocuk hatasının mutlaka Drive yüklemesinde olduğunu göstermez;
çift işleme ve yayımlama aynı zaman diliminde ilerler. Tam ay listesi yeni
yerel sonuç kabulü sayılmadı. 31 Aralık 2023 ertelenmiş, negatif izin false,
gözlem unknown ve tam eğitim bitişi false olarak korunuyor.

Kullanıcı günlükleri aldıktan sonra VM'yi tekrar Stop yaptığını teyit etti.
Bu bir manuel bildirimdir; canlı API sorgusu yapılmadı. İndirilecek teşhis
dosyası bu ilk hazırlık aşamasında henüz üretilmiş veya yerelde incelenmiş değildi;
sonraki yerel inceleme üst bölümde ayrı kaydedildi.

## Hazırlanan araç

Yeni `scripts/cloud/collect_gcp_v2_failure_snapshot.py`, bu V2/Eylül 2022
hatasına bağlı, tek dosyalık salt okunur araçtır. Eski V1 forensic aracı
V2 kimliğini kabul etmediği için ayrı araç hazırlandı; eski hash kuralları,
üretim kodu ve checkpoint kayıtları değiştirilmedi.

Araç orijinal/controller manifestlerini ve bütün üyelerini, V2 wrapper ve
registry hash'lerini kontrol eder. Çalışan işi engelleyen mevcut lock üzerinde
paylaşımlı, beklemesiz kilit alır; iş çalışıyorsa raporlamaya geçmez. Üç son
durum dosyasının seçili güvenli alanları eşleşmelidir. Running, yanlış wrapper,
başka başarısız ay, değişmiş kaynak veya belirsiz kimlik reddedilir.

Yeni JSON yalnız seçili durum alanlarını, ilk kaynak ve kardeş çocukların
izinli hata sınıf/kontrol/exit kodlarını, son ebeveyn tanılarını, ilk kaynağın
dosya varlığı/boyutlarını ve kaydedilmiş RAM/disk özetlerini içerir. Serbest
exception metni, traceback, URL, OAuth/Earthdata bilgisi veya özel bağlantı
JSON'u kopyalanmaz. Ham NASA dosyalarının ve bilimsel sonuçların içeriği
okunmaz; yalnız ilk kaynağın dosya stat bilgileri alınır. Orijinal paket
bütünlük kontrolü bilimsel kod/paket üyelerini okur. Ağ isteği, iş başlatma,
üretim dosyasına yazma, silme veya kaynak yönetimi yoktur.

Rapor küçük bir JSON'dur; büyük sonuç arşivi değildir. Birkaç KB olması
beklenebilir. Çıktı yeni UTC adıyla ev dizinine yazılır ve eski raporun
üzerine yazılmaz. Script haricinde yeni helper veya özel dosya yüklemek gerekmez.

## Kontroller

20 yeni test, kimlik/tarih/deferral ihlali, değiştirilmiş paket/son durum,
aktif iş kilidi, serbest hata metni ve kimlik bilgisi dışlama, ham dosyanın
okunmaması ve üretim dosyalarının aynı kalması davranışlarını sınadı.
Mevcut V2/gizlilik testleriyle birleşik kontrolde 43 test geçti.
Yerelde gerçek dondurulmuş orijinal ve
controller paketlerinin hash kontrolleri geçti; gerçek wrapper hash'i
eşleşti. Canlı yerel bitki örtüsü kaynak hash'leri değişmedi. Bunlar VM
üzerindeki hatanın çözümü veya gerçek teşhis sonucu değildir.

## İlk snapshot için uygulanan toplama adımları

1. VM'yi Start yapıp SSH'ye bağlan. **Üretim komutunu çalıştırma.**
2. Upload File ile yalnız şu dosyayı ev dizinine yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_v2_2026-10-10\collect_gcp_v2_failure_snapshot.py`.
3. SSH terminalinde:

```bash
if printf '%s  %s\n' \
  'f4d9d13494f552fe178d19041cd0b2e3d5c0d2c0be08f6440aa9464de35cee83' \
  "$HOME/collect_gcp_v2_failure_snapshot.py" | sha256sum --check; then
  timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
    ~/collect_gcp_v2_failure_snapshot.py
fi
```

4. `Download:` satırındaki `gcp_v2_failure_snapshot_<UTC>.json` dosyasını
   SSH Download File ile indir; mevcut özel bağlantı JSON'unu indirme/paylaşma.
5. Dosyayı
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_v2_2026-10-10\received\`
   dizinine koy ve VM'yi tekrar Stop yap.

Araç hata verirse yalnız kısa hata satırı paylaşılır; üretim veya cleanup
komutu çalıştırılmaz. Rapor alındığında ilk hata/çocuk exit/ölçüm kayıtları
çapraz okunacak. Ham dosyalar kalmışsa ayrı, izole ve ağ kapalı bilimsel
yeniden üretim değerlendirilebilir; tamamlanmış kayıtlar silinmez.
