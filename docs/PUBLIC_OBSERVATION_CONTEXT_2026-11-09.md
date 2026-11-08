# İzmir kamera kaydı ve Mersin arşivinde gözlem bağlamı — 9 Kasım 2026

İzmir’de bir yer kamerası ekranındaki olay saati ve harita alanı incelendi.
Mersin’de 2018–2023 arşiv kayıtları yayımlanan konum, iki saat yorumu,
nominal uydu tarama tanıları ve FIRMS adayları üzerinden karşılaştırıldı.

## İzmir, Kuşçular — 9 Haziran 2022

Belediyenin olay duyurusundaki beş görselden biri, Seferihisar Telsiz
Kulesi’nin Akıllı İhbar Sistemi ekranını gösteriyor. Panelde **14.59.03**,
kamera karesinde **9 Haziran 2022 15.01.25** okunuyor. Türkiye saati
yorumuyla bunlar **11.59.03** ve **12.01.25 UTC**. Ekip çıkışı, kamera
damgası ve panel saati ayrı kaynak alanlarıdır. Ekran saatlerinin
eşzamanlaması ve tutuşma anı açık. Önceki incelemede ekip çıkışı 14.58
ve ilk mahalle içi FIRMS adayı 12.17 UTC olarak kaydedilmişti.
[Belediye duyurusu](https://www.izmir.bel.tr/tr/Haberler/akilli-ihbar-sistemi-devreye-girdi-buyuk-bir-felaket-onlendi/46807/156) ·
[Ekran görseli](https://www.izmir.bel.tr/YuklenenDosyalar/Haberler/Buyuk/09062022_2152_0.jpg) ·
[Önceki kayıt incelemesi](OPEN_MUNICIPAL_REFERENCE_2026-11-08.md).

Ekranın solundaki harita, Esri World Imagery görünümüyle eşlendi. Kırmızı
katman ve baskın kırmızı pikseller eşleştirme hesabında maskelendi.
En yüksek puanlı üç ölçek ve öteleme çözümünde yol, kıyı ve su alanlarının
yerleşimi karşılaştırıldı. Ekrandaki kırmızı alanın yaklaşık sınırı elle
okundu. Üç çözüm, bugünkü mahalle poligonu ve 5 km proje ızgarası ile
kesildi. Katman kenarına proje koordinatlarında 0, 100, 250 ve 500 m pay
eklenerek toplam 12 senaryo sınandı. Bu paylar yöntem duyarlılığı içindir.
[Esri görüntü kaynağı](https://doc.arcgis.com/en/data-appliance/latest/imagery-elevation/world-imagery.htm) ·
[İzmir mahalle katmanı](https://kentrehberi.izmir.bel.tr/arcgis/rest/services/Rehber/CbsRehberGeoGri/MapServer/139).

- Kırmızı alanın görünür mahalle kesiti, sıfır ek payla **6,30–7,21 km²**.
  Tüm 12 senaryoda bu kesit **üç hücreye** dokundu. Mahallenin
  **24,16–25,47 km²** bölümü ekran dışında. Görülmeyen kesit korunduğunda
  12 senaryonun tamamında **altı hücre** kalıyor.
- Saat 12.17 UTC’deki iki FIRMS adayının ikisi en yüksek puanlı iki
  çözümde, biri üçüncü çözümde görünür kırmızı alan içinde. Bu sonuç
  adayların haritaya göre konum duyarlılığını gösteriyor. Bir FIRMS
  adayından hareketle kamera işareti konumlandırılmadı.
- Ekrandaki iğne, kırmızı alanın köşesinde ve panel istasyon adı
  veriyor. Görselden ayrı bir yangın başlangıç işareti, kırmızı
  katmanın doğrulanmış geometrik tanımı veya dumanın mesafesi okunamadı.
  Diğer dört fotoğraf müdahale ve etkilenen örtü bağlamı sağlıyor.

Ekran, daha önce yaklaşık 15.00 olarak bildirilen olay için dakika
düzeyinde doğrudan gözlem bağlamı ekliyor. Başlangıç hücresi seçimi açık.

## Mersin, arşiv saati ve küçük yangınlar — 2018–2023

Mersin sınırı içinde tek hücreye düşen ve geçici saat bağlantısı olan
**479 arşiv satırı** incelendi. Her satır için yayımlanan saat UTC ve
Türkiye saati olarak ayrı yorumlandı. Proje gününün sonuna kadar aynı
hücrede en az bir FIRMS adayı bulunup bulunmadığı ve varsa en az bir
adayın bildirilen dakikada veya sonrasında olup olmadığı sayıldı.
İki yorum toplam **493 tekil hücre-gün** üretti. Bunlar 64 aylık
dosyadan doğrulandı. Tüm seçili anahtarların nominal ürünü vardı.
[Yüksek vd., veri açıklaması](https://doi.org/10.1177/00368504261495731) ·
[Zenodo arşivi](https://doi.org/10.5281/zenodo.21455927) ·
[Önceki Mersin denetimi](MERSIN_OPEN_INCIDENT_ARCHIVE_2026-11-08.md).

| Yayımlanan saatin yorumu | Kaydedilen son yanan alan | Arşiv satırı | Aynı hücre ve proje gününde aday | Bildirilen dakikada veya sonrasında aday |
| --- | --- | ---: | ---: | ---: |
| Türkiye saati | 1 ha altı | 377 | 23 | 16 |
| Türkiye saati | En az 1 ha | 102 | 45 | 41 |
| UTC | 1 ha altı | 377 | 20 | 0 |
| UTC | En az 1 ha | 102 | 43 | 16 |

Türkiye saati yorumunda, seçili kara merkezi bulunan ve en uzun nominal
aralığı 12 saatin altında kalan alt grupta, bildirilen dakikada veya
sonrasında aday **1 ha altında 16/308 (%5,2)**, **en az 1 ha için
39/94 (%41,5)**. Her iki alan grubunda da aday sıklığı saat yorumuna
duyarlı. Son yanan alan yalnız geriye dönük alt grup tanımıdır. Seçili
kara merkezi ve nominal aralık, olay noktasındaki gözlem yeterliliğini
ölçmez. Katalog adayı aynı olayla eşleştirilmediği için sayılar tespit
oranı olarak kullanılamaz. Küçük olayların katalogda seyrek görünmesi,
özellikle pozitif örneklerin nasıl seçildiğinin ayrıca incelenmesini
gerektiriyor. [NASA FIRMS gözlem ve tespit koşulları](https://firms.modaps.eosdis.nasa.gov/alerts/notes.php).

## Doğrulama ve aşama durumu

Kuşçular hesabı `scripts/quality/audit_urla_camera_map.py` ile iki kez
aynı çıktıyı verdi. Mersin hesabı `scripts/quality/audit_mersin_observation_context.py`
ile yapıldı. Önceki 63 ve 68 aynı gün sayısı yeniden elde edildi. Alt grup
toplamları ve iki saat yorumunun ortak sayıları ayrıca uzlaştırıldı.
106 ilgili test geçti.

| Yerel makbuz | SHA-256 |
| --- | --- |
| `outputs/reports/dataset/open_municipal_reference_v1/urla_media_review/20261108T210329Z_1a016017/readback.json` | `b08d79611587953bbdb54f75bb0d88696b75d709b992bfc52591ec03a0b9969e` |
| `outputs/reports/dataset/mersin_observation_context_v1/20261108T205945Z_d16c3f1c/readback.json` | `d483148677b69f3386e0cce112563e64f63df5511e22c2aac4da0177dfc5573c` |

Birinci aşamanın olay konumu, saat ve dört ilde değerlendirme kapsamı
koşulları açık. Sonraki denetim, Mersin’de küçük ve büyük olaylardan
seçilecek bir alt örnekte bildirilen saate göre ayrı tarama zamanlarını
incelemeye odaklanabilir. Günlük gözlem `unknown`, etiket izinleri kapalı.
