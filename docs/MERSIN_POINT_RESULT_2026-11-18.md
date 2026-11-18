# Mersin kaydında gerçek piksel sonucu — 18 Kasım 2026

Kullanıcının tamamladığı `N20:2021228.2312` indirmesi yerelde doğrulandı.
176.557.039 baytlık iki dosyanın boyut ve SHA-256 değerleri kaynak planıyla
eşleşti. Tamamlanma makbuzu, yangın/konum dosyası bağlantısı ve header
kontrolleri tekrar geçti. Kaynak rasteri 6.464 satır ve 6.400 sütun.

WF1487 arşiv satırı 17 Ağustos 2021 00.30 ve son yanan alanı 0,05 ha
(500 m²) bildiriyor. Saatin Türkiye saati olduğu varsayımıyla zaman
16 Ağustos 21.30 UTC. Önceki denetimde iki ayrı arşiv tablosu tarih,
ilçe ve alan imzasıyla bağlanmıştı. Özgün olay kimliği, saat standardı
ve koordinatın tutuşma noktasını temsil etmesi açık konular.

## Ölçülen sonuç

Ham çiftteki 202 taramanın tamamında noktanın 1 km çevresiyle kesişim
arandı. Yaklaşık tarama içi geometrilerde yerel kesişim yalnız 142 numaralı
taramada bulundu. Zamanı 16 Ağustos 23.16.14,006–23.16.14,569 UTC.
Bildirilen zaman yorumundan yaklaşık 1 saat 46 dakika sonra.

| İncelenen alan | Yaklaşık geometriyle temsil edilen pay | Kara sınıfı (5) | Bulut sınıfı (4) | Yangın sınıfları (7–9) |
|---|---:|---:|---:|---:|
| Kayıtlı nokta | Nokta temsil ediliyor | 5 kodu | Görülmedi | Görülmedi |
| 250 m çevre | Yaklaşık %100 | Yaklaşık %100 | %0 | %0 |
| 1 km çevre | Yaklaşık %100 | Yaklaşık %100 | %0 | %0 |

Kara alanının tamamı mevcut girdi QA'sına göre nominal kara koşulunu
sağlıyor. Geolocation scan quality ham değeri 0, sensor mode 5.
Geometri hesabına ek olarak ham dizide en yakın piksel merkezi kontrol
edildi. Merkez projeksiyon düzleminde 288,4 m uzakta, satır/sütun
4554/2108, maske kodu 5 ve QA değeri 0. Bu pikselin 3×3 komşuluğundaki
kodların tamamı da 5. Mesafe gerçek başlangıç konumunun hata payı değildir.

## Veri seti için anlamı ve sınır

Bu kayıt için incelenen geçişte, bildirilen nokta çevresindeki bulut
maskesi uydu yangın tespiti bulunmamasını açıklamıyor. Arşivdeki 500 m²
son yanan alan, o geçiş anındaki etkin yangın alanını veya süresini
belirlemiyor. İncelenen iki CSV'nin alanlarında söndürülme/kontrol altına
alınma zamanı bulunmadı. Yangının tarama sırasında sürüp sürmediği açık.

Geometri önceki merkez orta noktası yaklaşımıyla kuruldu. Her taramanın
dış satır ve sütunları temsil edilmiyor. Çevre yüzdeleri bu yaklaşık
geometriye ait. Bu tek ve saat uçlarına göre seçilmiş örnek, algılama
oranı veya dört ilde etiket güvenilirliği tahmini sağlamaz.

Gözlem incelemesi bir tarama için ayrıntılandı. Gerçek yangın yokluğu,
olay başlangıcı ve günlük gözlem kabulü açık. Günlük gözlem `unknown`,
negatif etiket izni `false`, üretilen etiket sayısı sıfır. Birinci aşama
bağımsız başlangıç ve değerlendirme kapsamı kanıtı üzerinde devam ediyor.

## Yeniden üretim

`python scripts/quality/audit_mersin_point_pixels.py` indirme makbuzunu,
planı ve ham dosyaları doğrular, yeni sonuç üretir. Kod/hash ve native
makbuz bağlantıları sonuçta kayıtlı. 34 ilgili test ve Ruff geçti.
Önceki hazırlık kaydı kendi yürütülme durumunu korur.

Yerel sonuç
`outputs/reports/dataset/mersin_point_pixels_v1/20261118T134113Z_14b2945c/readback.json`.
SHA-256 `f4a227602dc3c817c0587defbf73471a51e1ef1b57e111fe3395a9b239b8dccd`.
