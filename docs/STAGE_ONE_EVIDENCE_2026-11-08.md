# Birinci aşama için hedef ve değerlendirme kanıtı — 8 Kasım 2026

2018–2023 eğitim takviminde **6.351.709 hücre-günün** gözlem
tanıları, dokuz gruplama ayarının birleşimindeki **7.610 aday
hücre-günle** aynı anahtarlar üzerinden karşılaştırıldı. Amaç,
adayların hangi gözlem koşullarında seçildiğini ve 24 saatlik
yeni orman veya çalılık yangını hedefini kabul etmek için
hangi kanıtın hâlâ gerektiğini belirlemekti. Yerel 2024
doğrulama ve 2025 test verileri açılmadı.
[Aday gruplama denetimi](EVENT_SENSITIVITY_2026-10-22.md) ·
[Gözlem takvimi](PU_CALENDAR_OBSERVATION_2026-11-08.md).

## 72 ayın gözlem karşılaştırması

| Katalog durumu | Toplam hücre-gün | Nominal ürün bulunan | Seçili kara merkezi sıfır | Kara merkezi aralığı en az 12 saat |
| --- | ---: | ---: | ---: | ---: |
| Dokuz ayarda aday, ilk zaman ve üyelik aynı | 5.214 | 5.211 | 4 | 558 |
| Dokuz ayarda aday var, ilk zaman veya üyelik değişiyor | 977 | 977 | 1 | 112 |
| Aday varlığı ayara bağlı | 1.419 | 1.419 | 0 | 126 |
| Dokuz ayarda da aday yok | 6.344.099 | 6.338.304 | 257.617 | 2.077.520 |

7.607 ürünlü aday hücre-günün 796'sında **(%10,46)** en
uzun nominal kara merkezi aralığı en az 12 saat. Aday
bulunmayan ürünlü satırlarda ham oran **%32,78**. İl, yıl
ve mevsim gruplarının her birindeki aday bulunmayan oranlar,
aynı gruplardaki ürünlü aday satırı sayısıyla ağırlıklandırıldı.
Bu karşılaştırmada oran **%24,59**. Aday grubu 96 il, yıl
ve mevsim birleşiminin 92'sinde bu ölçüde daha düşük paya sahip.

Üç aday hücre-günün nominal ürünü eksik. İkisi 13 Haziran
2018'e, biri 31 Aralık 2023'e ait. Üçünün de ilk zaman ve
üyelik tanıları dokuz ayarda aynı. Katalog tutarlılığı,
eksik gözlem ürününü tamamlamıyor. Nominal boşluk ölçüsü
ve karşılaştırma, gerçek olayların tespit olasılığını
hesaplamak için yetersiz. Kesin UTC pencere yönteminin
127 satırlık önceki denetimi ayrı kanıt olarak korunuyor.
[Kesin UTC pencere denetimi](PU_TARGET_WINDOWS_2026-11-08.md).

## Bağımsız kaynak erişimi

| Kaynak | 8 Kasım denetiminin sonucu | Kullanılabilecek kanıt |
| --- | --- | --- |
| Ekberzade'nin OGM kökenli Zenodo envanteri | Kayıt API'si HTTP 200, revizyon 3, ambargo alanı 31 Mayıs 2027, açık dosya sayısı sıfır. Dosya listesi HTTP 403. | Ön baskının sözlüğü ve açık R kodu. Olay verisi erişilebilir olursa özgün konumlar, uyduyla taşınmış ve doldurulmuş konumlardan ayrılabilir. |
| Avrupa Yangın Veri Tabanı | JRC raporu tekil kayıtları sağlayıcı ülke makamlarının mülkiyetinde tuttuğunu ve yıllık veya aylık özet istenebildiğini bildiriyor. | Teknik sözlük başlangıç koordinatı ile ilk ihbar ve ilk müdahale zamanını ayrı tanımlar. |
| Öztürk, Bekar ve Tavşanoğlu | Makale veri erişim beyanı, OGM olay verisinin açık paylaşılmadığını bildiriyor. | Açık analiz kodu ve toplu sonuçlar. |

[Zenodo kaydı](https://zenodo.org/records/21887740) ·
[Ekberzade ön baskısı](https://essd.copernicus.org/preprints/essd-2026-701/) ·
[Açık yöntem eki](https://essd.copernicus.org/preprints/essd-2026-701/essd-2026-701-supplement.pdf) ·
[JRC raporu, bölüm 4.4](https://publications.jrc.ec.europa.eu/repository/bitstream/JRC144093/JRC144093_01.pdf) ·
[JRC teknik sözlüğü](https://publications.jrc.ec.europa.eu/repository/handle/JRC88884) ·
[Öztürk ve diğerleri, veri erişimi](https://yunus.hacettepe.edu.tr/~ctavsan/papers/Ozturk_etal_2024.pdf).

LSA SAF'ın 15 dakikalık Meteosat yangın pikseli ürünü,
uygun vakalarda VIIRS'ten ayrı bir aktif yanma zamanı
karşılaştırmasına aday. Sağlayıcı bunu yanma piksellerinin
tespit ürünü olarak tanımlıyor. Kaynak sayfasında veri
sunucusu için kayıt gerekiyor. Bu çalışmada ürün dosyası
alınmadı. Tutuşma noktası, fiziksel olay kimliği ve kayıt
kapsamı için yer kaydı ihtiyacı açık.
[LSA SAF yangın ürünleri](https://lsa-saf.eumetsat.int/en/data/products/fire-products/).

Son açık vaka listesindeki 23 kayıt ve sonbahar tablosunda
metinleri uyuşan 96 satır ayrı incelemelerdir. İki listede
de 5 km başlangıç hücresi ve zaman penceresi eşleştirmesine
hazır satır bulunmadı. OGM'nin 4.449 il-yıl kaydı toplamı
idari kapsam denetimine yarar. Hücre-gün olay oranı için
olay kimliği, zaman ve konum eşlemesi ayrıca gerekir.
[Açık vaka dağılımı](PUBLIC_CASE_DISTRIBUTION_2026-11-08.md) ·
[Sonbahar alımı](AUTUMN_REFERENCE_TABLES_2026-11-08.md) ·
[OGM il-yıl kapsamı](OGM_PROVINCE_YEAR_2026-11-08.md).

## Birinci aşamanın kabul koşulu

1. Özgün olay kimliği, bağımsız başlangıç konumu veya
   belgelenmiş konum belirsizliği, zaman tanımı ve saat
   standardı olan bir kaynak incelenir. İlk ihbar ve ilk
   müdahale, tahmini tutuşma zamanından ayrı saklanır.
   Birden çok hücre veya pencereye uzanan belirsizlik
   korunur.
2. Yeni olay ve devam ayrımı ile olay başlangıcındaki
   orman veya çalılık örtüsü, bağımsız kaynağın izin verdiği
   ölçüde sınanır. Gözlem koşulları ve katalog eşleşmesi,
   doğrulanmış olaylar için ayrı kaydedilir.
3. Seçilecek öğrenme yaklaşımı için olay kayıtlarının
   coğrafi ve zamansal kapsamı, küçük olayların kayda
   alınması ve pozitiflerin seçilme koşulları incelenir.
   PU için sınıf oranı veya desteklenebilir belirsizlik
   sınırları ve değerlendirme dayanağı ayrıca gerekir.
   Mevcut gözlem farkları bu değerleri tek başına belirlemez.
   [Pozitiflerin seçilme varsayımları](https://proceedings.mlr.press/v94/bekker18a.html).

Mevcut araştırma kararı ana hedefi korumak ve yeni
kurumsal talep açmadan PU uygulanabilirliğini araştırmaktır.
Bu denetimde olay kabulü ve değerlendirme kanıtı açık
kaldı. Birinci aşama tamamlanmış olarak kaydedilmedi.
Günlük gözlem `unknown`, etiket izinleri kapalı.
Kullanılabilir bağımsız bir kesit için iki yol var.
Kamuya açık yayını beklemek veya araştırmacının seçimiyle
veri sahibinden izinli pilot kesit olanağını sormak.
Önceki CİMER yanıtının işaret ettiği üniversite kanalı,
araştırmacı bu yolu yeniden seçerse kullanılabilir.
[Önceki araştırma kararı](LABEL_PROTOCOL_DECISION_2026-11-04.md) ·
[CİMER yanıtının kayıtlı özeti](research/OGM_UNIVERSITY_ROUTE_2026-10-19.md).

## Yeniden üretim

`python scripts/quality/audit_stage_one_selection.py`,
72 aylık kaynak tablonun SHA-256 değerlerini ve tekil
hücre-gün anahtarlarını doğrular. Sonuç, önceki gözlem
denetiminin 96 grubuyla ikinci bir hesapta uzlaştırıldı.
85 ilgili test geçti. Yerel sonuç
`outputs/reports/dataset/stage_one_selection_v1/20261108T133434Z_305831ac/readback.json`.
SHA-256 `6fb3783f4ab12d630bb8530432304f537f6a289ea9fb4b3c3c4d04a6cb9efba3`.

## Aynı gün kamuya açık kaynaklarla devam

Araştırmacı açık kaynak yolunu seçti. Dört İzmir çalışma
kitabı, dört Mersin raporu ve Urla için yer kamerası
duyurusu ile belediye sınırları incelendi. Kuşçular için
bağımsız gün bağlamı elde edildi. Güncel mahalle sınırı altı
proje hücresini kapsıyor ve başlangıç noktasını belirlemiyor.
Kayıt kapsamı dört ilde değerlendirilebilir düzeye ulaşmadı.
Birinci aşama açık ve ikinci aşama hedef kabulünü bekliyor.
[Belediye kaynakları denetimi](OPEN_MUNICIPAL_REFERENCE_2026-11-08.md).
