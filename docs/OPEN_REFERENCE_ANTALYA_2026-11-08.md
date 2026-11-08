# Antalya için açık olay referansı incelemesi — 8 Kasım 2026

Şenlik ve Yılmaz, Antalya Orman Bölge Müdürlüğünden 2000–2022 yangın
kayıtlarını aldıklarını ve konumları kayıt defterlerinden haritaladıklarını
belirtiyor. Makalenin 232. sayfasında 11 seçilmiş olayın günleri ve
Şekil 15'te numaralı başlangıç işaretleri var. On vaka 2022, bir vaka
2021 tarihli. Şekil ve yayın sayfası incelendi. İncelenen yayında bu
11 vakanın özgün koordinatlarını, saatlerini ve konum belirsizliğini
birlikte veren açık olay tablosu bulunmadı. Seçimde büyük yangınlara
öncelik verildiği için örnek, bütün olayların dağılımını temsil etmez.
[Şenlik ve Yılmaz, 2025](https://doi.org/10.21324/dacd.1532721).

## Somut vaka — 31 Ağustos 2022, Akseki/Kuyucak

Makaledeki 5 numaralı olay, AA'nın aynı gün Keleklik mevkisinde
bildirdiği orman yangınıyla yer ve tarih bakımından uyumlu. DHA
haberi yaklaşık 12.00 Türkiye saati, yani 09.00 UTC bildiriyor.
Makalede olay için verilen gün, kesin tutuşma saatini tek başına
sağlamaz. Haritadaki grafik işaret özgün koordinata dönüştürülmedi.
[AA saha kaydı](https://m.aa.com.tr/tr/gundem/antalyada-ormanlik-alanda-cikan-yangin-kontrol-altina-alindi/2673479) · [DHA saha kaydı](https://www.dha.com.tr/gundem/antalyada-cikan-orman-yangini-2-saatte-kontrol-altina-alindi-2123408).

İki yerel FIRMS denetim tablosunda olayın Türkiye takvim günü
tarandı. UTC aralığı 30 Ağustos 21.00 dahil ile 31 Ağustos 21.00 hariç.
Arama merkezi Kuyucak mahalle temsil noktasıdır (37,2250665° K,
31,6381551° D). WGS84 uzaklıkları hesaplandı ve 2, 5, 10 ve 20 km
içindeki sayımlar ayrı bir küresel mesafe hesabıyla doğrulandı.
[Mahalle temsil noktası](https://harita.org/antalya/akseki/kuyucak/).

| Merkeze uzaklık | S-NPP satırı | NOAA-20 satırı |
| --- | ---: | ---: |
| 2 km | 0 | 0 |
| 5 km | 0 | 0 |
| 10 km | 0 | 1 |
| 20 km | 0 | 1 |

Tek NOAA-20 satırı 10.30 UTC'de, mahalle merkezinden 5,90 km uzakta.
Katalog türü `0`, güven sınıfı `nominal`. Olay için bildirilen yaklaşık
saatten 90 dakika sonra geliyor. Keleklik başlangıç koordinatı bilinmediği
için bu satırın olaya ait olduğu veya yangının kaçırıldığı çıkarılamaz.

Mahalle merkezini içeren `E6933_5K_V1_C610_R885` hücresinin ayrı UTC
`(T,T+24h]` penceresinde üç komşu nominal paket de mevcuttu. Pencere
içinde 14 tarama satırında 836 seçili kara merkezi ve sıfır nominal/yüksek
güvenli termal merkez sayıldı. En uzun seçili kara merkezi tarama aralığı
yaklaşık 11,48 saatti. Bu hücreye kesin olay başlangıcı atanmadı ve
gözlem yeterliliği `unknown` kaldı.

## Diğer kaynakların katkısı

- İzmir belediye kayıtları müdahale edilen olayları kapsıyor ve portal
  coğrafi veri içermediğini belirtiyor. İzmir AFAD planı, AYDES'e girilen
  olayları 2020 ve 2023 için ilçe düzeyinde özetliyor. Bu iki yayın
  başlangıç konumu ve zamanı olan bağımsız bir doğrulama tablosu vermedi.
  [Belediye açık verisi](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi) · [İzmir İRAP, bölüm 2.5.1](https://izmir.afad.gov.tr/kurumlar/izmir.afad/E-KUTUPHANE/Il-Planlari/IRAP_Izmir--2024.pdf).
- EFFIS'in ülke bildirimlerinden oluşan Avrupa Yangın Veri Tabanı
  Türkiye'yi kapsıyor. Açık sayfa genel istatistik sunuyor ve ayrıntılı
  veri tabanı kesitleri için talep formuna yönlendiriyor. Bu incelemede
  olay satırı alınmadı. [Veri tabanı](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/european-fire-database) · [Erişim açıklaması](https://forest-fire.emergency.copernicus.eu/applications/data-and-services).

Yeni Antalya kaynağı **11 tarihli olay bağlamı** sağladı. Bir vakada
yerel uydu karşılaştırması yapıldı. Eşleştirme için kesin başlangıç
konumu ve değerlendirme kapsamı açık. Hedef alanı boş kaldı. İlerleme
için yüksek değerli kanıt, bu kayıtların koordinat, zaman tanımı ve
kapsamıyla yayımlanan özgün olay tablosu veya eşdeğer bağımsız kaynaktır.

Yerel makbuz `outputs/reports/dataset/open_reference_antalya_v1/20261108T022002Z_6b97aff6/readback.json`.
SHA-256 `1f45ce37875a869110a45dd134af3bfffdf76b40d9d1d845511fba0557054f57`.
Görsel olarak incelenen yayıncı PDF'sinin SHA-256 değeri
`302a469a8eb22251e000a00ed1b2d62b8247d43aaa4bea29f49b2b68414a635e`.
