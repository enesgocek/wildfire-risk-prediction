# V2 erken kapanışı ve salt okunur teşhis — 10 Ekim 2026

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
dosyası henüz üretilmiş veya yerelde incelenmiş değildir.

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

## Kullanıcı adımları

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
