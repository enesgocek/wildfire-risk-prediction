# Menderes uydu tespitlerinin tarihsel yakınlık denetimi — 8 Kasım 2026

10 Temmuz 2023 vakasında güneydeki ilk NOAA-20 piksel merkezi
ile kuzeydeki iki S-NPP piksel merkezi ayrı tarandı. Kaynak,
2018–2023 eğitim dönemine ait iki FIRMS Türkiye arşivindeki
463.178 satırdır. NOAA-20 arşivi 1 Nisan 2018'de başlıyor.
Tüm türler ve güven sınıfları dahil edildi. Mesafeler
WGS84 üzerinde piksel merkezleri arasında ölçüldü.
[Önceki vaka denetimi](MENDERES_HONA_CONTEXT_2026-11-08.md) ·
[FIRMS teslim karşılaştırması](research/FIRMS_REFRESH_COMPARISON_2026-10-21.md).

## Arşivde görülen tespitler

| Tespit merkezi | 10 Temmuz 2023'te 1 km içindeki satır | Diğer günlerde 100 / 250 / 500 / 1.000 m içindeki satır | Diğer günlerde 1 km içindeki benzersiz tarih |
| --- | ---: | --- | ---: |
| Güney, ilk NOAA-20 | 17 | 0 / 1 / 2 / 2 | 1 |
| Kuzey, doğudaki S-NPP | 2 | 0 / 0 / 1 / 1 | 1 |
| Kuzey, batıdaki S-NPP | 2 | 0 / 0 / 0 / 1 | 1 |

Kuzeydeki iki merkezin 1 km çevresinde görülen diğer gün
kaydı **aynı S-NPP satırı**. 21 Nisan 2022 saat 10.56 UTC'de
kaydedilmiş ve iki merkezden sırasıyla 402 m ve 743 m
uzakta. Güneydeki merkezin 1 km çevresinde ise 4 Ağustos
2019 saat 11.26 UTC'de NOAA-20 ve 12.18 UTC'de S-NPP
tespitleri var. Uzaklıklar sırasıyla 151 m ve 466 m.

Diğer günlerin üç benzersiz kaydı da nominal güvenli
Type 0. FIRMS bu kodu olası bitki örtüsü yangını için
kullanıyor. İncelenen üç merkezin 1 km çevresinde diğer
günlere ait Type 2 kaydı görülmedi. Gözlem fırsatları bu
taramada ölçülmediği için az sayıda tespit, sabit ısı
kaynağını dışlamak veya bir olayın yokluğunu kanıtlamak
için kullanılamaz. Daireler kesiştiği için tablonun
satırları toplanarak benzersiz tespit sayısı bulunamaz.
[NASA FIRMS VIIRS alan tanımları](https://firms.modaps.eosdis.nasa.gov/content/descriptions/FIRMS_VIIRS_Firehotspots.html).

## Olay kayıtlarıyla karşılaştırma

4 Ağustos 2019 tarihli AA saha haberi Oğlananası'nda bir
ağaçlandırma sahası yangını bildiriyor. İzmir İtfaiyesinin
indirilebilir dosyasında o gün 48 satır var. Menderes
ilçesindeki tek satır ot kategorisinde ve ekip çıkışı
14.12 Türkiye saati. Saat, saha haberi veya iki uydu
kaydıyla ortak olay kimliği sağlamıyor.
[AA saha haberinin yayımlanan kopyası](https://www.memleket.com.tr/izmirde-agaclandirma-sahasinda-yangin-1826892h.htm) ·
[İzmir İtfaiyesi açık veri dosyaları](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi).

21 Nisan 2022 tarihli indirilebilir dosyada 13 müdahale
satırı var. Hiçbiri Menderes ilçesiyle kayıtlı değil.
Bu sonuç belediye dosyasıyla sınırlı. 2022 uydu
tespitinin fiziksel kaynağı açık kaldı. 2023'teki
kuzey grubunun Hona Boğazı vakasıyla ilişkisi ve
tutuşma konumu için bağımsız kanıt gereksinimi sürüyor.
Hedef alanı boş, gözlem durumu `unknown` ve iki etiket
izni kapalı.

Üretici `python scripts/quality/audit_menderes_recurrence.py`.
12 yarıçap sonucu eski FIRMS arşivlerinden ayrı UTM hesabıyla
yeniden üretildi. İki belediye dosyası ikinci bir okuyucuyla
kontrol edildi. 90 ilgili test geçti.
Yerel sonuç `outputs/reports/dataset/menderes_recurrence_v1/20261108T040337Z_aa27bedc/readback.json`.
SHA-256 `d5cb6c9cb46697b3649505d26775c5c75363d89fa89e57393fc3aeaa10e9cc14`.
