# Komşu günlerle 24 saatlik gözlem penceresi — 14 Ekim 2026

## Amaç ve elde edilen sonuç

Tahmin sözleşmesi `(T,T+24 saat]` olduğundan granül dosyasının nominal günü
ile pikselin hedef günü aynı kabul edilemez. Altı önceki açıklayıcı örnek,
gece yarısı örneğinin ertesi günü, iki kaynak boşluğunun çevresi ve eğitim
başlangıcı için **11 amaçlı pencere** incelendi. 23 farklı eğitim günü
yerel, hash ile kabul edilmiş kompakt paketlerden okundu. Bu, 400 örneğin
veya bütün eğitim takviminin pencere kabulü değildir.

Altı pencerede üç komşu nominal günlük paket mevcut; beşinde kayıtlı kaynak
boşluğu veya dönem sınırı var. İki penceredeki belirsiz termal merkez
**aynı kaynak taramasındaki aynı merkezdir**. İki ayrı yangın veya iki
pozitif etiket sayılmadı. Hiçbir pencereye güvenilir negatif statüsü verilmedi.

## Uygulanan zaman kontrolü

Yeni `src/wildfire_risk_prediction/observation_window.py` mevcut zaman
sözleşmesini uygular; bilimsel bulut paketleri değiştirilmedi:

- Hedef günü için önceki, aynı ve sonraki nominal günlük paketler planlanır.
  2018–2023 dışındaki paketler dosya okunmadan `outside_training_not_read`
  olarak işaretlenir. Kayıtlı iki eksik gün `deferred_source_day` kalır.
- Kapalı tarama zaman zarfı bütünüyle `(T,T+24h]` içindeyse `inside`,
  bütünüyle dışındaysa `outside`, sınırı kesiyorsa `boundary_unknown` olur.
  T anındaki tek nokta dışarıda, T+24h anındaki tek nokta içeridedir.
  Bir nanosaniyelik sınır farkları korunur; orta zamanla gün atanmaz.
- Sensör/granül/tarama/grid anahtarlarıyla yinelenen aynı kayıt bir kez
  sayılır. Zaman/sayım bilgisi çelişen tekrarlar hata verir. Kaynak günlerinin
  kimliği ayrıca korunur. Farklı sensör geçişleri bir fiziksel yangın sayılmaz.
- Piksel merkezi, nominal kara merkezi ve nominal/yüksek güvenli termal
  merkezler için kesin içerideki ve sınırdaki **okunmuş kayıt sayımları** ayrılır.
  Eksik kaynağın sayımı veya küresel üst sınır olduğu iddia edilmez.
- İçerideki seçilmiş merkez taramalarının zaman zarfı birleşimi/boşluğu
  hesaplanır. Bunlar sürekli gözlem veya yangının yaşam süresi değildir.

NASA VNP03IMG teknik tanımında `scan_start_time`, `scan_end_time` ve
`ev_mid_time` alanları `number_of_scans` boyutundadır. Orta zamanın her
termal piksele ait kesin edinim zamanı gibi kullanılması bu tanımdan
çıkmaz. Bu kaynak okuması yerel kompakt dosyadaki eksik piksel zamanını
tamamlamaz; tüm sürümler için piksel zamanının elde edilemez olduğu
iddiası da değildir.
[NASA LAADS teknik tanımı; erişim 14 Ekim 2026](https://ladsweb.modaps.eosdis.nasa.gov/filespec/VIIRS/1/VNP03IMG).

## Gerçek kaynak incelemesi

| Amaçlı pencere | İçerideki okunmuş tarama satırı | Sınırdaki tarama | Sınırdaki termal merkez | Üç nominal paket mevcut mu? |
|---|---|---|---|---|
| A — Eksik gün, 13 Haziran 2018 | 0 | 0 | 0 | Hayır |
| B — Kara/bulut birleşimi, 27 Ekim 2021 | 10 | 0 | 0 | Evet |
| C — Nominal kara merkezi yok, 20 Mart 2022 | 10 | 0 | 0 | Evet |
| D — Kara var/termal yok, 4 Ağustos 2018 | 9 | 0 | 0 | Evet |
| E — Gece yarısı, 18 Ocak 2022 | 14 | 1 | 1 | Evet |
| F — Küçük su parçası, 18 Temmuz 2019 | 0 | 0 | 0 | Evet |
| G — E örneğinin ertesi günü, 19 Ocak 2022 | 10 | 1 | 1 | Evet |
| H — Haziran boşluğundan önce, 12 Haziran 2018 | 10 | 0 | 0 | Hayır |
| I — Aralık boşluğundan önce, 30 Aralık 2023 | 9 | 0 | 0 | Hayır |
| J — Eğitim sonu/kaynak boşluğu, 31 Aralık 2023 | 0 | 0 | 0 | Hayır |
| K — Eğitim başlangıcı, 1 Ocak 2018 | 6 | 0 | 0 | Hayır |

E ve G aynı gridde (`E6933_5K_V1_C522_R918`), aynı
`SNPP:2022018.2354` granülünün 202 numaralı taramasını içerir:
başlangıç `2022-01-18T23:59:59.481722951+00:00`,
bitiş `2022-01-19T00:00:00.045531034+00:00`.
Bir nominal güvenli termal merkez iki komşu pencere için de belirsizdir.
Bu 11 örnekte komşu nominal günden tamamen içerideye taşınan tarama yok;
taşıma ve yinelenen kayıt kontrolünün davranışı sentetik sınır testiyle
ayrıca sınandı. Bütün eğitimde böyle kayıt bulunmadığı sonucu çıkarılmaz.

Kaynak planının 33 pencere/gün rolünün 27'si okunabilir, dördü ertelenmiş,
ikisi eğitim dışı olduğu için okunmamıştır. Bunlar 33 farklı gün değildir;
ortak günler tek kaynak önbelleğinde tutulur. 2017-12-31 ve 2024-01-01
adları yalnız plan kaydıdır, veri erişimi yapılmadı.

F, kabul edilen su kapsamı kararına göre modelleme dışında olsa da
denetim izi için tabloda korunur. Üç paketin mevcut olması ve sıfır
merkez sayımı yangınsız gün kanıtı değildir. A/J'deki sıfırlar yalnız
**okunmuş komşu paketlerden hedef içine düşen kayıt sayısıdır**; eksik
ürünün sayısal ölçülerinin sıfırla doldurulması değildir. Asıl aylık
gözlem tablosundaki eksik değerler aynı kaldı.

## Test, geri okuma ve çıktı kimliği

65 ilgili test geçti: yeni pencere mantığı, önceki gözlem incelemesi,
su kapsamı ve hedef kabul korumaları. İlk test çalışmasında zaman farkı
oluşturmanın kütüphane kullanımdan kaldırma uyarısı hata olarak yakalandı;
açık `unit` kullanımıyla düzeltildi, aynı test kümesinin tamamı geçti.
Üç yeni Python dosyası lint ve format kontrolünden geçti. Testler nanosecond
sınırlarını, zaman dilimi eksikliğini, ters zaman aralığını, çelişen
tekrarları, eksik kaynakları ve eğitim dışı erişim planının reddini kapsar.

Çalıştırma: `.venv\Scripts\python.exe scripts/quality/review_observation_windows.py`.
Yeni sonuç:
`outputs/reports/dataset/observation_windows_v1/20261014T190400Z_25bfc71a/`.
`window_summary.csv`, `window_scan_rows.csv`, `source_day_schedule.csv`
geri okundu. 58 giriş ve üç çıktı hash ile kapanışta kontrol edildi;
bunların 22'si donmuş bulut girdisidir. Önceki yedi gözlem inceleme çıktısı
ve kabul edilmiş su kapsamı tablosu değişmedi. Yeni hesaplar yereldir;
kompakt paketlerin ham uydu geometrisi veya alan birleşimi yeniden hesaplanmadı.

`readback.json` SHA-256:
`3be2b93d9fe3e048d6429d94380e49280f4b9e7b04546265ee501e59b7a1b689`.
`completion_readback.json` SHA-256:
`89210f08e243c79eec892baa6b042052ddca1315408ad8488ab877920f40aa2a`.
Günlük iç rapor ve scan_grid kimlikleri ayrıca `inner_daily_sha256` alanındadır.

## Açık kalan iş ve önerilen devam

Bu işlem **merkez zamanlarını tarama zarfı düzeyinde** hedefe göre ayırır.
Alan birleşimleri hedef penceresine yeniden kırpılmadı. Pikselin kesin
zamanı, kaynak katalog kapsamı ve gözlem yeterliliği ayrı konulardır.
Üç komşu paket varlığı tam fiziksel gözlemi veya yangın yokluğunu kanıtlamaz.
Zaman penceresine ait tanılar tahmin anında bilinen model girdileri değildir.

Sonraki teknik adım aynı kontrolü sabit 400 örnekli pilotun tamamına
uygulayıp sınır/eksik kaynak etkisini orijinal tabaka ve ağırlıklarla
raporlamaktır. Öneri, sınır kayıtlarını belirsiz tutarak bu incelemeyi
ilerletmek; kesin zaman/bağımsız kanıt bulunmadan bunlardan 0/1 hedef
üretmemektir. Bu matematiksel zaman kontrolü kullanıcıdan görüntüye
bakarak pikselin gününü tahmin etmesini gerektirmez. Yeni bir bilimsel
gözlem eşiği veya olay politikası seçimi gerektiğinde seçenekler ayrıca sunulur.

453 insan kanıt formu aynı durumda; bağımsız gözle inceleme yapılmış
sayılmadı. `daily_observation_status=unknown`, pozitif/negatif izinleri
`false`, hedefler boş ve `model_ready=false` kaldı. 2024/2025 veri erişimi,
bulut işi, ücretli yükseltme veya model eğitimi yoktur.
