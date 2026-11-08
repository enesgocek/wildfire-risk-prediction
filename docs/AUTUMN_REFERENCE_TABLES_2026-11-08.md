# Sonbahar yangın kayıtlarının alım denetimi — 8 Kasım 2026

Tayfun Turnalı'nın 2020 tarihli yüksek lisans tezindeki iki
sonbahar tablosu incelendi. Tez, satırları OGM'nin dönemin
internet yayınlarından derlediğini belirtiyor. Tablo 2.3,
1–24 Kasım 2018 arasındaki 78 satırı, Tablo 2.4 ise
10–31 Ekim 2019 arasındaki 174 satırı içeriyor. 252 sıra
numarası tablolar içinde kesintisiz. İl alanı çalışma
illerinden biriyle birebir eşleşen 98 satır ayrıldı.
Bu iki tarih aralığının dışında kayıt kapsamı incelenmedi.
[Sakarya Üniversitesi tez arşivi, Tablo 2.3–2.4](https://acikerisim.sakarya.edu.tr/bitstream/handle/20.500.12619/97033/T09215.pdf?sequence=1).

| Kaynak dönemi | Antalya | Muğla | İzmir | Mersin | Seçilen satır |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1–24 Kasım 2018 | 24 | 9 | 1 | 1 | 35 |
| 10–31 Ekim 2019 | 16 | 23 | 1 | 23 | 63 |
| **Toplam** | **40** | **32** | **2** | **24** | **98** |

## Satır farkları ve saat denetimi

Arşivin doğrudan indirme bağlantıları doğrulama sayfası
veya HTML yanıtı döndürdü. Özgün PDF baytları alınamadı.
Yayımlanan iki bağlantının erişilebilir metin görünümleri
kullanıldı. 96 satırda sıra numarası, il, tarih ve çıkış
saati alanı eşleşti. İki Antalya satırı alımdan ayrıldı.
Tablo 2.3'ün 61. satırında müdahale saati bir görünümde
11.40, diğerinde 14.40. İntikal süresi de farklı. 68.
satırda tarih bir görünümde 3 Kasım, diğerinde 4 Kasım.
Her iki değer korundu ve farkın kaynağı açık bırakıldı.
[Tezin ikinci arşiv bağlantısı](https://acikerisim.sakarya.edu.tr/bitstream/handle/20.500.12619/97033/T09215.pdf?isAllowed=y&sequence=1).

Ekim 2019'da aynı il, tarih ve dakikayı taşıyan beş çift
var. Örneğin Antalya'da 13 Ekim 12.30 için 18 ve 20
numaralı satırlar bulunuyor. Mersin'de dört benzer çift
var. Tablodaki sıra numarası, olayın OGM sicil numarasını
vermiyor. Çiftlerin aynı fiziksel olaya ait olup olmadığı
açık bırakıldı. Yayımlanan saatler Türkiye yerel saati
kabul edilirse altı Ekim satırı bir önceki UTC takvim
gününe düşer. Kaynak saat standardı doğrulanamadığı için
bu sonuç saat dilimi duyarlılığı olarak tutuldu.

## Veri setine katkısı ve sonraki kontrol

İki metin görünümünde uyuşan **96 satırın tamamı kaynak
incelemesinde kaldı**. Tablolarda il düzeyinden daha
ayrıntılı bir başlangıç konumu, özgün olay kimliği,
belgelenmiş konum belirsizliği ve UTC zaman sınırı yok.
Hiçbir kayıt 5 km hücre ve 24 saatlik hedef eşleştirmesine
hazır bulunmadı. Günlük gözlem yeterliliği `unknown` ve
etiket izinleri kapalı. Tablo satırları, önceki 23 seçili
vakanın listesine eklenmedi. İki listenin olay kimliği ve
yayımlanma kapsamı ayrı incelenmeli.
[Önceki vaka listesi](PUBLIC_CASE_DISTRIBUTION_2026-11-08.md) ·
[Alım kuralları](REFERENCE_INTAKE_2026-10-15.md).

Bu kaynak, Temmuz ve Ağustos dışındaki aramayı belirli il,
gün ve saatlere daraltıyor. Aynı döneme ait konumlu bir
müdahale kaydı bulunursa önce ortak olay kimliği ve
saatin anlamı incelenir. İl ve dakika eşitliği tek başına
eşleme ölçütü olarak kullanılmaz.

## Yeniden üretim

Seçili alanların metin dökümü yerelde
`outputs/reports/dataset/autumn_reference_audit_v1/table_projection.json`
dosyasında. SHA-256
`ccc0810bef22dbbf37f84ba027a8c7a8a9be02c77691381bba4bb93745d39de6`.
`python scripts/quality/audit_autumn_reference_tables.py` bu
girdiyle 98 satırın sayımını ve 96 satırın alım denetimini
üretir. 85 ilgili test geçti. Yerel sonuç
`outputs/reports/dataset/autumn_reference_audit_v1/20261108T131902Z_62b559e1/readback.json`.
SHA-256 `9d03ead60beebeba4d894ce47d285767889bdcdbe9ce1c0f48a6cb29383d9a19`.
