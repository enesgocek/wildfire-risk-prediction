# V6 Haziran 2018 kaynak eşleşme hatası — 13 Ekim 2026

## Kaynak ve kapanış nedeni

Kullanıcı son oturumun arşivini aktardı ve indirme sonrası VM Stop teyidi
verdi. Dosya `outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/received/gcp_v6_session_20261013T095138Z_logs.tar.gz`,
541.148 bayt; SHA-256
`1bae31a2aada315c1e6e0297d935d8594790f88fa4283dca22d60abf5d975444`.

Beş beklenen normal dosya isim/boyut/tekrar sınırlarıyla bellekte okundu.
Üç final JSON aynı: `failed_checkpoints_retained`, RuntimeError,
`failed_month=2018-06`, son kaydedilen aşama `pair_publication`.
Bu aşama tek başına hatanın kesin satırı değildir; child kayıt satırları
gerçek geolocation girdisi kontrolünün hata verdiğini gösteriyor.

Tam günlükte 13 Haziran 2018'e ait altı NOAA-20 çifti ValueError /
`Not the actual geolocation input` bildiriyor:

- `N20:2018164.0018`, `N20:2018164.0024`;
- `N20:2018164.1000`, `N20:2018164.1142`;
- `N20:2018164.2218`, `N20:2018164.2224`.

Donmuş bilimsel kontrol, yangın dosyasının bildirdiği geolocation girdi
adıyla seçilen dosya adını karşılaştırır. Log bu kontrolün başarısızlığını
kanıtlar; gerçek bildirilen/seçilen adları içermez. Bu nedenle kesin sürüm
farkı, doğru dosyanın arşivde bulunabilirliği veya indirilen baytların
bozulduğu sonucu henüz çıkarılmaz. Önceki 31 Aralık 2023 sorununun aynısı
olduğu da varsayılmadı.

Diğer 12 çocuk RuntimeError/CLASS_ONLY ve -9 çıkış satırlarıyla bitmiş.
Supervisor ilk hatadan sonra aktif çocukları da sonlandırır; bu -9
satırları OOM veya 12 ayrı bozuk kaynak kanıtı değildir. Logda daha önce
iki `HTTP_DIAGNOSTIC LIST 500 UNCLASSIFIED` satırı vardır; sonraki üretim
ilerlemiş. Bu iki olay son kaynak eşleşme hatasının kesin nedeni sayılmadı.
`Guest poweroff requested: True` ve final hata satırı, süre dolmadan
hata sonrası otomatik kapatma isteğini doğruluyor.

## İlerleme ve yerel kabul sınırı

Final liste Temmuz 2018–Kasım 2023 arasında **65 tam ay** içeriyor;
72 eğitim ayının %90,3'ü. Önceki 58 aylık kapanışa göre yedi yeni ay:
Ocak 2019 ve Temmuz–Aralık 2018. 57 reused ay + başlangıç Temmuz 2023
referansı + yedi yeni ay, 65 aylık listeyle eşleşiyor.

Bu oturumda 1.841 yeni pair satırı ve 33 katalogdan çıkarılan reused çift
sayacı eşleşti. 213 DAY COMMITTED satırı progress'te var. 254 progress
günü, önceki Ocak 2019 1–11 ve Aralık 2023 1–30 günlerini de içeriyor;
bu 41 gün yeni oturum üretimi sayılmadı. Haziran 2018 1–9 günleri kapalı;
10 Haziran için altı yayımlanmış pair satırı var, nominal dokuz çifte göre
kısmi ve günlük kapanış yok. Hazır yerel ZIP'lerin tam envanteri bu
beş dosyalık arşivde bulunmadığından hesaplanmadı.

Tam kapanmamış yedi ay: Ocak–Haziran 2018 ve Aralık 2023. Haziran kısmi;
31 Aralık'taki iki kaynak ertelemesi korunur. `daily_observation_status=unknown`,
`negative_label_permitted=false`, `full_training_complete=false` değişmedi.
Donmuş üretim/controller paketlerinin hash'leri ve 18.711 nominal çift
kataloğu denetlendi. Tüm yeni pair kimlikleri, ay/gün ve sayaçlar eşleşti.
Önceki launcher çağrısının 5.449 satırı güncel sayımlardan dışlandı;
hata/HTTP satırları ayrıca sınıflandırıldı, ham log düzenlenmedi.

13.253 kaynak örneğinde minimum 9,83 GiB boş disk ve 111,66 GiB
kullanılabilir RAM; süreç ağacı RSS tepe değeri 11,56 GiB. Örneklenen
4 GiB rezerv ihlali yok. Ortalama CPU busy %12,18 bütün restore/metadata
aşamalarını içerir; daha büyük VM gerekliliği veya darboğaz kanıtı değildir.
Örnekleme bütün anları veya çocuk adres alanı sınırını kanıtlamaz.

Yerel denetim ağ erişimi engellenerek yürütüldü. Betik/rapor:
`outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/audit_failure_session.py`
ve `failure_session_readback_20261013.json`; rapor SHA-256
`ba030461e6bcdfbb6efb915f24c42da35b2fee88695499f5f7896c9b58e9af54`.
Final progress bayt SHA-256
`4bdaf1626e02194cd862e15a5bb4d7e500560b9661020720d892b42b0ca9031d`.
Bu günlük/katalog kabulüdür; yeni bilimsel ürün baytları ve canlı Drive
geri okuması yapılmadı. VM kaynakları silinmedi; kullanıcı Stop teyidi var.

## Salt okunur kaynak adı tanısı

Yeni `scripts/cloud/collect_gcp_v6_geolocation_snapshot.py` yalnız bu exact
finali, aynı üç özeti, V6/registry ve paket hash'lerini kabul eder. Mevcut
Linux iş kilidi shared/nonblocking alınır; aktif üretim varsa çalışmaz.
Altı görevin kayıtlı `continuation_failure.json` dosyalarından yalnız
izinli ürün adları/guard sınıfı çıkarılır; ilgisiz alanlar dışlanır.
Kaynakların yalnız boyut/stat bilgisi alınır, ham dosya içerikleri açılmaz.
OAuth, token, kullanıcı adı veya parola okunmaz; ağ, üretim ve VM kontrolü
yoktur. Yalnız home dizinine yeni zaman damgalı public tanı JSON'u yazar.
Okunan korunan dosyaların hash'leri işlem sonunda yeniden karşılaştırılır.

Sekiz davranış kontrolü geçti: kaynak/özel dosya okumama, değişmeme,
başka final/paket reddi, URL/serbest metni dosya adı olarak aktarmama,
header yokluğunu belirtme, raw boyut uyuşmazlığını raporlama, path sınırı
ve işlem sırasında değişen kanıtı reddetme. Lint/format geçti. Windows
ortamında gerçek Linux kilidi/VM çalıştırması sınanmadı; tanı betiği henüz
VM'de çalıştırılmadı. Canlı wrapper ve bilimsel kontrol değiştirilmedi.

Hazırlık kaydı `snapshot_prepared_readback_20261013.json`; aynı çıktı
dizininde, SHA-256
`5a511d084d9fd439ec5a764029a9eb4f098793244aee92f45cc8277abf7f6554`.

1. VM Start → SSH → Upload File ile yalnız şu dosyayı home'a yükle:
   `outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/package/collect_gcp_v6_geolocation_snapshot.py`.
2. SSH'de:

```bash
if printf '%s  %s\n' \
  'b321b30a2bf81dea0c64d6da9239fd43bfb7207a7199ea0d7e39341e03ea2268' \
  "$HOME/collect_gcp_v6_geolocation_snapshot.py" | sha256sum --check; then
  timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
    ~/collect_gcp_v6_geolocation_snapshot.py
fi
```

3. `Download:` yolundaki JSON'u indir; aynı yeni oturumun `received/`
   dizinine aktar ve VM Stop yap. Üretim betiğini tekrar çalıştırma.

JSON geri okununca bildirilen gerçek girdi adı ve seçilen ad yerel katalogla
karşılaştırılacak; gerektiğinde gerçek sürümün erişimi araştırılacak.
Yeni kaynak ertelemesi veya uyumlu sürüm değişikliği, kanıt ve bilimsel
kapsam kaydı olmadan uygulanmayacak. Geolocation kontrolü kaldırılmayacak;
başarısız checkpoint durumu silinmeyecek.
