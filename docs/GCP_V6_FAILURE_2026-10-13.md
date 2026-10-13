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

## Kaynak tanısının yerel geri okuması

Kullanıcı public tanı JSON'unu aktardı ve VM Stop teyidi verdi.
`received/gcp_v6_geolocation_snapshot_20261013T125412909568Z.json`, 7.891 bayt;
SHA-256 `506ec0451d26436c562ab31a5ab74c9fea4a100c860fc4a45fcd59d103b821bc`.
Exact failed final, V6/registry kimlikleri ve 14 korunan dosya hash'i
eşleşti. Üretici raporunda kaynak içerik/kimlik bilgisi okuma ve ağ/üretim
yazımı sıfır; korunan dosyalar değişmemiş. Bu üretici raporunun yerel
geri okumasıdır, bağımsız canlı VM veya kaynak bayt denetimi değildir.

Altı çiftte seçilen ve bildirilen dosyaların sensor, ürün, granül zamanı
ve `021` sürüm alanları aynı; son üretim zaman damgaları farklıdır.
Yangın dosyası 2021 üretimli geolocation adını bildirirken nominal planda
2024 üretimli geolocation seçilmiştir. Her iki kaynak VM'de mevcut ve
raporlanan boyutları planla aynı; boyut eşitliği checksum veya aynı
bilimsel içeriği kanıtlamaz. Örnek 00:18 granülü:

- Bildirilen: `VJ103IMG.A2018164.0018.021.2021041061359.nc`.
- Seçilen: `VJ103IMG.A2018164.0018.021.2024194040130.nc`.

Altı kayıt katalogdaki 13 Haziran NOAA-20 kimlikleriyle eşleşti. Gerçek
declared/selected adları `geolocation_snapshot_readback_20261013.json`
içinde tutulur; rapor SHA-256
`60fb6c66f587611054d8b20184f5c444936fda00520701f642cef5756cbe6c35`.
Sadece aynı collection/granül zamanı olması eski-yeni baytların eşdeğer
olduğunu göstermez. Guard kaldırma veya dosyayı başka sürümün adıyla
yeniden adlandırma uygulanmadı.

## Açık NASA metadata araştırması

Anonim salt okunur CMR sorguları, `short_name=VJ103IMG` ve exact
`readable_granule_name` ile gerçekleştirildi. Altı bildirilen eski adın
her birinde HTTP 200 / sıfır hit, altı seçilen yeni adın her birinde HTTP
200 / bir hit döndü. Yeni concept ID'ler donmuş katalogla aynı; collection
Version=2.1. Güncel revision 4 metadata'sının RelatedUrls GET DATA
alanında seçilen yeni ad ayrıca doğrulandı. İlk sorgu raporunun yalnız
bazı UMM alanlarına bakan exact_name_match=false alanı, bu RelatedUrls
kontrolünün yerine kullanılmadı; ilk rapor değiştirilmeden korunur.

Altı kaydın 1/2/3 metadata revizyonlarının tamamı HTTP 404; revision 4
kayıtları HTTP 200. Bir çiftin eski/yeni NASA cloud adreslerine anonim
HEAD kontrolü aynı CloudFront hostuna 303 yönlendirme verdi; yönlendirmeler
izlenmedi ve source baytları indirilmedi. Bu HEAD sonucu dosya varlığı
veya yokluğunu ayırt etmez. CMR zero hit, bütün NASA arşivlerinden silinme
kanıtı değildir; şu an sorgulanan katalogda exact kaynak bulunamadı.

[Resmî CMR sorgu ve revizyon yöntemi](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html#granule-search-by-parameters)
ve [örnek güncel metadata](https://cmr.earthdata.nasa.gov/search/concepts/G2122801517-LAADS/4.umm_json).
Açık metadata kayıtları aynı çıktı dizininde `cmr_revision_metadata/` altındadır.
Kaynak aramaları kullanıcı kimlik bilgisi, GCP kaynağı veya raw indirmesi
kullanmamıştır. Zaman damgalı araştırma kayıtları:

- `cmr_exact_lineage_lookup_20261013.json` SHA-256
  `782fc746f24974056f001cb54015871f1bf6dbd15dd45eb81a0a889de5e39117`.
- `cmr_lineage_revision_lookup_20261013.json` SHA-256
  `fbcfb947026e633bbc0c28fcd854e1000d1ab2cf96148ff32a71e7423de83b34`.
- `cmr_lineage_supplement_20261013.json` SHA-256
  `169f9288000cca9c90a42a2247cd235197214d64d9267917b5bab5b3278f8829`.

## Devam için iptal tanılarını ve hazır çıktı hash'lerini toplama

Önerilen sonraki sürüm, 13 Haziran'ı eksik kaynak günü olarak ayrıca
tutarken diğer gün/ayları ilerletecektir. Bu erteleme henüz uygulanmadı;
Haziran ve Aralık tam kabul edilmeyecek, unknown/negative=false korunacak.
İlk public tanı yalnız altı kaynak hatasını içerir. Güvenli geçiş için
logdaki diğer 12 iptal görevinin gerçek tanı bayt/hash'leri ve mevcut
pair ZIP envanteri de gerekir; bunlar varsayılıp failed durum silinemez.

Yeni `scripts/cloud/collect_gcp_v6_resume_snapshot.py`, önceki tanı JSON'u
ve helper hash'iyle başlar; aynı final/plan/korunan dosyalar eşleşmelidir.
Haziran görev dizinini nominal planla sınırlar. Yalnız bilinen altı kaynak
hatası ve 12 RuntimeError/CLASS_ONLY/-9 iptali kabul edilir; yeni veya
incelenmemiş tanı varsa durur. Tek Haziran parent tanısı ve eldeki pair
ZIP'lerinin boyut/hash bilgisi aktarılır. Bu ZIP hash envanteri, native
bilimsel restore kabulü yerine geçmez. Ham kaynak ve credentials okunmaz;
ağ, üretim başlatma, kaynak değiştirme veya tanı taşıma yoktur. İş kilidi
altında okunup hash'ler yeniden karşılaştırılır; yeni küçük JSON yazılır.

Yeni altı + önceki sekiz davranış testi birlikte **14 passed**; lint/format
geçti. Ek tanı, iptal sınıfı değiştirme, eski proof değiştirme, işlem
sırasında payload değiştirme ve farklı parent hatası reddedildi. Gerçek
Linux VM kilidi bu yeni betikte henüz çalıştırılmadı. Canlı V6 ve donmuş
paketler aynı hash'te; source registry ve checkpointler değiştirilmedi.
Hazırlık `resume_snapshot_prepared_20261013.json`, SHA-256
`36b643bb4df3a60b97879eb3007cdff59c1f7355ff6d3ce9ad2a701507c9e822`.

VM Start → SSH Upload File ile yalnız yeni şu dosyayı home'a yükle:
`outputs/gcp_acceleration/source_aware_v6_session_2026-10-13/package/collect_gcp_v6_resume_snapshot.py`.
Önceki helper ve public JSON zaten VM home'da olmalıdır; tekrar yüklenmez.

```bash
if printf '%s  %s\n' \
  'f680a08a26ab2b9c7b755dbf3891629a1c356b98903dbd2281bad8328cd09a54' \
  "$HOME/collect_gcp_v6_resume_snapshot.py" | sha256sum --check; then
  timeout 240s ~/wildfire-gcp-work/.venv/bin/python \
    ~/collect_gcp_v6_resume_snapshot.py
fi
```

Download satırındaki JSON aynı received dizinine aktarılır; VM Stop yapılır.
Yeni snapshot kabul edilince exact başarısız tanılar ve hazır çıktı hash'leri
korunan ayrı devam sürümü hazırlanır. Bu aşamada üretim yeniden başlatılmadı.

## İkinci snapshot kabulü ve V7 hazırlığı

13 Ekim'de kullanıcı `gcp_v6_resume_snapshot_20261013T131934138747Z.json`
dosyasını aktardı, VM Stop teyidi verdi. 15.843 bayt; SHA-256
`a98692817bb6a9f6288a645c6123d5d2d5fe4432f38e366b061515094be26de3`.
Exact final/ilk tanı/plan, 18 çocuk kimliği/hash yolu, tek parent ve
22 hazır ZIP envanteri katalogla eşleşti. 65.888.711 bayt / 10–12 Haziran;
ZIP baytları yerel bilgisayara gelmedi, bilimsel restore kabulü yapılmadı.
İptal kimlikleri 13–14 Haziran'a aittir; -9 OOM diye sınıflandırılmadı.

[Ayrı V7 devam paketi](GCP_SOURCE_RESUME_V7_2026-10-13.md) hazırlanıp
156 birleşik kontrol ve lint/format geçti. V7 çalıştığında iki eksik gün
ve iki kısmi ay ayrı tutulur; mevcut 65 ay silinmez. Yeni remote üretim,
Drive kabulü veya kaynak guard değişikliği yapılmadı. Önceki hazırlık ve
NASA arama bulguları yukarıda kendi tarihli sınırlarıyla korunur.
