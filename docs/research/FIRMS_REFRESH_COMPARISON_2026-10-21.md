# FIRMS yeniden teslim karşılaştırması

Tarih: 21 Ekim 2026. Kaynak: araştırmacının manuel indirdiği iki ZIP,
korunan eski FIRMS CSV'leri ve yerel otomatik karşılaştırma. Bu kayıt
bağımsız saha incelemesi, aylık üretim sürümü makbuzu veya etiket kabulü değildir.

## Sonuç ve kapsam

**Ortak eğitim döneminde iki teslimin bütün kayıt alanları aynı. Yalnız
kayıt sıraları farklı.** Bu karşılaştırma nedeniyle eski aday kataloglarının
ve 72 aylık uydu üretiminin yeniden çalıştırılmasını gerektiren veri farkı yok.

| Kaynak ve Türkiye talebi dönemi | Eski kayıt | Yeni kayıt | Eklenen / çıkarılan anahtar | Alanı değişen kayıt |
|---|---:|---:|---:|---:|
| S-NPP, 2018-01-01–2023-12-31 dahil | 230.286 | 230.286 | 0 / 0 | 0 |
| NOAA-20, 2018-04-01–2023-12-31 dahil | 232.892 | 232.892 | 0 / 0 | 0 |
| Toplam | 463.178 | 463.178 | 0 / 0 | 0 |

Bunlar ülke talebindeki uydu tespit kayıtlarıdır; dört ildeki bağımsız yangın
veya eğitim örneği sayıları değildir. Eski dosyalardaki 47.005 S-NPP ve
52.071 NOAA-20 doğrulama dönemi satırı yalnız tarih alanıyla dışarıda tutuldu;
2024 alanları karşılaştırılmadı, yöntem seçilmedi. 2025 açılmadı.

Yeni teslimler `received/SNPP/DL_FIRE_SV-C2_828284.zip` ve
`received/NOAA20/DL_FIRE_J1V-C2_828274.zip`; kök
`outputs/verification/firms_refresh_2026-10-21/`.
İkisinin CSV şeması aynı 15 alanı içeriyor. Her iki sensörde eşleşmeyen tam
satır, çakışan tespit anahtarı ve mükerrer tam satır yok. Type, confidence,
UTC tarih/saat, koordinat, parlaklık, FRP, scan/track, gündüz/gece ve diğer
alanlar bire bir aynı. Her iki teslimde `version=2` korunuyor.

## Yöntem ve doğrulama

- Eski ham CSV hash'leri önceki denetim pinleriyle doğrulandı. Yeni ZIP'ler,
  iki üye adı/boyut sınırı, CRC ve üye hash'leriyle kontrol edildi; dosyalar
  çalıştırılmadı veya eski veri üzerine çıkarılmadı.
- Sensör + UTC tarih/saat + özgün enlem/boylam anahtarı kullanıldı. Satır
  numaraları ve talep kimlikleri tespit eşleştirmesinde kullanılmadı. Sayısal
  gösterimler Decimal ile eşlendi; tekrar çoklukları korunarak 15 alan
  karşılaştırıldı. Metin alanlarının çoklukları da eşit çıktı; sonuç sayısal
  yuvarlamaya veya yaklaşık konum eşleştirmesine dayanmıyor.
- Konum/zamanı değişmiş olabilecek artık kayıtlar eşleşme kabul edilmeden
  ayrı tanı olarak hesaplanıyor; bu gerçek teslimlerde artık kayıt yok.
- Ayrı uygulamada veri satırları satır sonları çıkarılıp byte olarak
  sıralandı; tekrarlar korunarak tam eşitlik ve uzunluk önekli SHA-256
  doğrulandı. Her iki sensör aynı sonucu verdi. Sıra dahil byte hash'lerinin
  farklı olması, satır kümesinin farklı olduğu anlamına gelmiyor.
- 14 davranış testi; sıra/biçim farkı, Type/güven değişimi, tekrar çokluğu,
  eşleştirilmemiş konum/zaman değişimi, dönem ve bozuk alan reddini sınadı.
  Üç yeni Python dosyasında lint/format geçti. Bütün depo testi değildir.

Ana rapor:
`outputs/reports/dataset/firms_refresh_comparison_v1/20261021T164652Z_313527d8/readback.json`.
SHA-256 `7809413ec37b9a104b6cea36f060f0895e4d6908260a0cdd576ae1e4fa6fc5a7`.
Sekiz girdi başta/sonda hash ile korundu; üç çıktı hash'i ve JSON geri okuması
kapanışta doğrulandı. Artık CSV'ler yalnız başlık içeriyor.

Ayrı byte karşılaştırması:
`outputs/reports/dataset/firms_refresh_comparison_v1/20261021T164759Z_e2a98f0a_independent/readback.json`.
SHA-256 `56e19e9fbd60c400818113dffb099b12a8c97eb30b259d28d52abb6079b606a1`.
Bu ikinci otomatik hesap yöntemidir; bağımsız kurum/uzman doğrulaması değildir.

## Bilimsel yorum ve sonraki iş

Eski eğitim kayıtları yeni FIRMS teslimiyle içerik olarak eşdeğer bulundu.
Destek ekibinin güncel ürün beyanı ve bu eşitlik birlikte kaynak kaygısını
daraltıyor; eski dosyalara özgü bir düzeltme farkı bulunmadı. Bununla birlikte
CSV'de aylık üretim VV alanı yok; v4 bağı yerel metadata ile doğrudan
doğrulanmış gibi yazılmaz. Talep ayarları araştırmacının ekran görüntülerine
dayanıyor; kesin indirme saati ve ülke poligon sınırı bağımsız doğrulanmadı.

Bu bulgu Type=0'ın fiziksel yangın doğruluğunu veya gözlenmeyen yerde yangın
yokluğunu kanıtlamaz. Donmuş hedef kabul kodu değiştirilmedi;
`daily_observation_status=unknown`, pozitif/negatif izinleri false kaldı.
2018-06-13 ve 2023-12-31 L2/geolocation eksikleri bu CSV karşılaştırmasıyla çözülmedi.
Gerçek eğitim, nihai birleştirme, dış ileti veya bulut işi yapılmadı.

Sonraki bilimsel adım, bu eşitliği kaynak kanıtına ekleyerek Type yorumunu
güncel destek açıklamasıyla sürümlü protokolde değerlendirmektir; mevcut kabul
bayrakları kendiliğinden açılmaz. Bağımsız olay/ilk tespit ve gözlem politikası
için OGM üniversite yazısı yolu ayrı sürer. Yeni toplu veri kuyruğu yerine
bu açık yöntem/kanıt kararları ele alınmalıdır.
