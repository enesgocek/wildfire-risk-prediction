# Urla ilk tespitinde kara ve deniz ayrımı — 8 Kasım 2026

14 Ağustos 2021 10.44 UTC S-NPP tespitlerinden biri, CORINE 2018'de deniz sınıfına düşüyordu. Bu merkez dokuz gruplamanın altısında ilk nokta setine girer ve son yangın sınırının dışındadır. İnceleme, tespit merkezine göre karar vermenin kıyıda yaratacağı hatayı iki harita ve iki olay öncesi görüntüyle ölçer. [Önceki örtü incelemesi](PUBLIC_EVENT_COVER_2026-11-08.md).

## Piksel boyutu ve yönelim belirsizliği

Katalogdaki `scan` ve `track` değerleri 410 ve 450 m. Merkez sabit tutularak yerel UTM projeksiyonunda 180 dikdörtgen hesaplandı. Yönler 0–179 derece arasında birer derece aralıklı. Bu örnekleme, gerçek VIIRS pikselinin yönü, köşeleri veya konum hatası için bir model değildir. Her varsayımsal dikdörtgen 205 m yarıçaplı iç daireyi kapsar ve yaklaşık 304 m yarıçaplı dış daireye sığar. Dönüşten bağımsız yorum yalnız bu sabit merkezli dikdörtgen varsayımı için geçerlidir. [NASA FIRMS alan açıklamaları](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html).

| Kaynak | Merkezin sınıfı | 180 yönelimde kara payı | 180 yönelimde su payı |
|---|---|---:|---:|
| CORINE 2018, 100 m | Deniz | %51,6–52,7 | %47,3–48,4 |
| Copernicus CGLS 2017, yerel 100 m raster | Sınıf 126, orman grubu | %56,3–61,1 | %38,9–43,7 |
| Sentinel-2 L2A SCL, 5 Ağustos 2021, 20 m | Bitki örtüsü dışı kara | %46,3–47,9 | %50,4–51,1 |
| Sentinel-2 L2A SCL, 10 Ağustos 2021, 20 m | Bitki örtüsü dışı kara | %47,5–48,8 | %49,9–50,7 |

Yüzdeler her döndürülmüş dikdörtgenin tamamına göre hesaplandı. Sentinel-2'de bitki örtüsü ve bitki örtüsü dışı sınıflar kara olarak toplandı. Su sınıfı ayrı tutuldu. Kalan bulut ve sınıflandırılmamış alan, 5 Ağustos'ta %1,7–2,6 ve 10 Ağustos'ta %1,3–1,7 aralığındaydı. Her sütundaki uç değer farklı bir yöne karşılık gelebilir.

CORINE'de en yakın kara hücresinin sınırı merkezden 6,7 m. CGLS'de en yakın su hücresinin sınırı 16,0 m. Her iki Sentinel-2 tarihinde de merkez, SCL su hücresinin kenarına 5,6 m uzaklıkta. Bunlar raster hücresi kenarlarına uzaklıktır. Haritaların mekânsal çözünürlüğü ve sınıflandırması nedeniyle kıyının gerçek konumunu metre hassasiyetinde vermez. İki doğal renk kesitinde de kıyı, iç daireyi kesiyor. [Sentinel-2 L2A kataloğu](https://planetarycomputer.microsoft.com/dataset/sentinel-2-l2a).

## Sonuç ve açık koşul

İki eski harita merkezde uyuşmuyor. Buna karşılık dört kaynakta da piksel boyutlarıyla uyumlu her örnek yönelimde kara ve su birlikte bulunuyor. Merkez denize denk geldiği gerekçesiyle otomatik dışlama yapılmadı. Kıyıdaki karışım, noktanın doğal örtüdeki bir ısı kaynağına ait olduğunu veya aynı yangının başladığı yeri kanıtlamaz. Ortak olay adayındaki belirsiz konum korundu. Günlük gözlem `unknown`, pozitif ve negatif etiket izni `false`.

NASA CMR, aynı altı dakikalık geçiş için birer kayıt döndürdü. Jeolokasyon dosyası `VNP03IMG.A2021226.1042.002.2021263230604.nc`, aktif yangın dosyası `VNP14IMG.A2021226.1042.002.2024074080005.nc`. Anonim sınırlı arşiv istekleri 303 yönlendirme döndürdü. Ham dosya, yerel eşleşen piksel satırı ve doğal geometri doğrulanmadı. [NASA VNP03IMG ürün bilgisi](https://data.nasa.gov/dataset/viirs-npp-imagery-resolution-terrain-corrected-geolocation-l1-6-min-swath-375-m-45b94).

## Yerel doğrulama

Üretici `scripts/quality/review_urla_coastal_detection.py`. Yerel çıktı `outputs/reports/dataset/urla_coastal_detection_v1/20261107T234917Z_ca86f9d4`. Okuma kaydının SHA-256 özeti `e9d5cfc4052503463923e7d10dacb296a09f5f674d1c331a558d7dec24f739ea`. Girdi, kesit ve görsel özetleri tekrar kontrol edildi. Dört kaynaktaki 720 yönelim kaydının alan payları ve iki görüntünün tarih ile piksel toplamı denetlendi. İlgili 56 test geçti.
