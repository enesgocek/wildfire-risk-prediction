# Anamur Belensazak için ardışık UTC gözlem pencereleri — 8 Kasım 2026

OGM, 11 Temmuz 2023 yerel tarihli vaka için yaklaşık 01.30
başlangıç saati bildiriyor. Bu saat 10 Temmuz 22.30 UTC'ye
karşılık geliyor. Önceki incelemede beş FIRMS satırı dokuz
keşif ayarının hepsinde aynı kümeye düşmüştü. Bu çalışmada
satırların dakika ve sensör sayıları, aynı 5 km hücredeki yerel
VIIRS tarama kayıtlarıyla karşılaştırıldı.
[Mersin OBM olay kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx) ·
[Önceki olay eşleştirmesi](JULY_2023_START_CONTEXT_2026-11-08.md).

## Pencere ve tarama sonuçları

Her hedef için `(T,T+24h]` UTC sözleşmesi uygulandı. Tarama
zaman aralığının tamamı pencere içindeyse sayım o pencereye
alındı. İki pencere için toplam dört farklı kaynak günü
okundu. Her pencerenin üç komşu gün paketi mevcuttu.

| Pencere başlangıcı (UTC) | İçerideki taramalar | Sınırla çakışan taramalar | Seçili kara piksel merkezleri | Nominal/yüksek güvenli ısıl merkezler |
| --- | ---: | ---: | ---: | ---: |
| 10 Temmuz 00.00 | 12 | 0 | 648 | 3 |
| 11 Temmuz 00.00 | 11 | 0 | 605 | 2 |

| Tarama başlangıcı (UTC) | Sensör | Katalog satırı | Tarama tablosunda ısıl merkez |
| --- | --- | ---: | ---: |
| 10 Temmuz 22.33.14 | S-NPP | 1 | 1 |
| 10 Temmuz 23.23.24 | NOAA-20 | 2 | 2 |
| 11 Temmuz 00.13.54 | S-NPP | 2 | 2 |

Üç ısıl taramanın her biri bir UTC dakikasının içinde kaldı.
Son iki kayıt, takip eden UTC penceresinde görülen aynı
keşif kümesinin üyeleri olarak saklandı. Eşleşme dakika ve
sensör toplamı düzeyinde. Katalog satırlarının tek tek piksel
kimliği ve fiziksel olayın başlangıç noktası doğrulanmadı.

İlk ısıl taramadan önce hücrede seçili kara pikseli bulunan
son kayıt 10 Temmuz 11.53.23 UTC'de sona erdi. Bu iki saklanan
tarama arasında 10 saat 39 dakika 51 saniye var (en yakın
saniyeye yuvarlandı). Kara piksel merkezi sayıları geçişler
üzerinden toplanmıştır. Bunlar hücrenin kesintisiz izlendiğini,
tutuşmanın bu aralıkta olduğunu veya yangın bulunmadığını
kanıtlamaz. Olay sonrası Sentinel-2 değişimi de özgün
tutuşma noktasını belirlemiyor.
[Olay sonrası değişim incelemesi](ANAMUR_BURN_SIGNAL_2026-11-08.md).

## Veri setine etkisi ve doğrulama

Vaka, bir olay adayının uydu kayıtlarının UTC gün sınırını
aşabildiğini somut olarak gösteriyor. Hedef boş tutuldu,
günlük gözlem durumu `unknown` ve iki etiket izni kapalı.
Özgün konum, başlangıç örtüsü ve değerlendirme kayıtlarının
kapsamı için kanıt gereksinimi sürüyor.

Üretici `python scripts/quality/review_anamur_observation_windows.py`.
Dört kaynak gününün iç dosya özetleri, iki pencere, üç ısıl
tarama ve zaman farkı CSV tablolarından ayrı bir hesapla
doğrulandı. İlgili 54 test geçti.
Yerel sonuç `outputs/reports/dataset/anamur_observation_windows_v1/20261108T033344Z_46e15ad3/readback.json`.
SHA-256 `34a0a2eafa99dcf66f9cd813a8f6c8d6125e99216d24c0600f8d79a117c885f6`.
