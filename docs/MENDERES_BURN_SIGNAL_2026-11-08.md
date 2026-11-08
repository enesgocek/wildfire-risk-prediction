# Menderes'te iki uydu grubunun optik karşılaştırması — 8 Kasım 2026

10 Temmuz 2023 Menderes vakasında, güneydeki 12 ve kuzeydeki
iki VIIRS tespitinin çevresi Sentinel-2 L2A ile incelendi.
Her grubun çevresi, tespit merkezleri etrafındaki 700 m
dairelerin birleşimi olarak tanımlandı. İki çevre aynı
yerel kesitte karşılaştırıldı ve son kesite 750 m bağlam
eklendi. Daireler arama alanını tanımlar.
[Önceki grup denetimi](MENDERES_HONA_CONTEXT_2026-11-08.md) ·
[Arşiv geçmişi](MENDERES_RECURRENCE_2026-11-08.md).

## Görüntü seçimi ve hesap

Beş sahnenin tamamı T35SNC ve R007. Olay öncesi 1 ve 6 Temmuz,
olay sonrası 11, 16 ve 21 Temmuz görüntüleri kullanıldı.
Aynı uyduyla 1→11, 6→16 ve 1→21 Temmuz karşılaştırıldı.
1→6 Temmuz çifti olay öncesi kontrol olarak saklandı.
Beş sahnede de işlem tabanı 05.09, yansıma nicemlemesi
10.000 ve B8A/B12 ofsetleri −1.000. Yerel 20 m ızgarada
NBR farkı, geçerli SCL 4 veya 5 sınıfındaki kara
piksellerinde hesaplandı. Üç olay çiftinde birlikte
geçerli alan, güneyde **9.698/12.303 (%78,8)** ve
kuzeyde **5.042/5.046 (%99,9)** piksel.
[Copernicus L2A ürün tanımı](https://sentiwiki.copernicus.eu/web/s2-products) ·
[EFFIS NBR yöntemi](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/fire-severity).

## İki çevrede gözlenen değişim

| Üç çiftte ortak dNBR alt sınırı | Güneydeki en büyük bitişik parça | Kuzeydeki en büyük bitişik parça | Her iki çevreye değen bitişik parça |
| --- | ---: | ---: | ---: |
| 0,10 | 39,88 ha | 10,88 ha | 0 |
| 0,15 | 35,72 ha | 7,68 ha | 0 |
| 0,20 | 29,60 ha | 3,20 ha | 0 |

Alanlar çevre sınırları içinde ve piksel kenarı bağlantısına
göre ölçüldü. Eşikler duyarlılık denemesidir. 0,15 eşiğinde
güneyde olay sonrası 1.847, olay öncesi kontrolde 30 piksel
eşik üstünde. Kuzeyde bu sayılar 201 ve 39. Aynı geçerli
piksel alanı kullanıldı. Üç olay çiftinin ikisi 1 Temmuz
görüntüsünü paylaşıyor.

Güneyde 11 Temmuz doğal renk görüntüsünde ağaçlık alanda
belirgin koyulaşma var. Bu değişim yanıkla uyumlu. En büyük
ölçülen parça genişletilmiş kesitin kenarına değmiyor.
Ölçülen parçalar, kesit ve geçerli piksel seçimiyle sınırlı.
Kuzeyde, tarım ve yerleşim çevresindeki daha küçük değişimin
nedeni belirsiz. Üç eşikte de iki çevreyi birleştiren bir
parça görülmedi. Bu sonuç, iki uydu grubunun fiziksel olay
kimliğini veya özgün tutuşma konumunu belirlemiyor.
[Önce, sonra ve dNBR görseli](../outputs/reports/dataset/menderes_burn_signal_v1/20261108T041302Z_38822be1/change_review.png).

Olay sonrası görüntüler yalnız olay incelemesinde kullanıldı.
Hedef alanı boş, günlük gözlem durumu `unknown` ve etiket
izinleri kapalı.

Üretici `python scripts/quality/audit_menderes_burn_signal.py`.
Beş kesitin özeti, piksel sayımları ve üç eşikte bitişik
alanlar ayrı hesapla doğrulandı. Sonuç görseli incelendi.
53 ilgili test geçti. Yerel sonuç
`outputs/reports/dataset/menderes_burn_signal_v1/20261108T041302Z_38822be1/readback.json`.
SHA-256 `1cf41777f35c229aff52194e326b7541ef75253fb79c00145ca57f894ce290df`.
