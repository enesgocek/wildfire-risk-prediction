# PU adaylarının toplu zaman ve referans incelemesi — 8 Kasım 2026

Pilotun dokuz ayarda tutarlı **15 hücre-günü ve 18 ilk tespit
noktası** aynı çağrıda denetlendi. İlk nokta üyelikleri 135
vaka×ayar kaydında tekrar kontrol edildi. 2018, 2021 ve 2023'teki
sekiz aydan 48 yerel nominal uydu paketi kullanıldı. Aday günü
ve üç önceki UTC günü için 60 hücre-gün penceresi geri okundu.
Önceden belirlenmiş amaçlı pilot kapsamı korundu.

## Toplu sonuç

- Önceki 72 saatte 2 km içinde veya aynı hücrede daha erken
  **seçili Type 0 katalog tespiti** olan vaka 0/15. 2 km ve
  72 saat kullanılan geniş gruplamanın kenar sınırlarıdır.
  Bu uyum aynı kaynakla yapılan bir tutarlılık kontrolüdür.
- Önceki 45 pencerenin üçünde yüklü termal merkez var. Üçü de
  R05'e ait. Aday günü 15/15 pencerede termal merkez var.
  60 pencerenin tamamında gereken üç nominal paket okundu.
- Önceki pencerelerde en uzun nominal kara merkezi tarama zarfı
  boşluğu 10,64–13,15 saat. 45 pencerenin sekizinde en az 12 saat.
  Bu süreler nokta düzeyinde kesintisiz görüş veya tespit olasılığı
  sağlamaz.

### R05'te katalog filtresinin somut etkisi

İki geniş FIRMS aday denetim tablosu aynı hücre ve `(T,T+24 saat]`
pencerelerinde 60 uydu özetiyle karşılaştırıldı. Nominal/yüksek güvenli
toplam sayılar 60/60 pencerede eşleşti. Bu, günlük sayı uzlaştırmasıdır.
Tek tek tarama pikseli ile FIRMS satırı kimliği eşleştirilmedi.

| UTC günü | Sıkıştırılmış uydu paketi termal merkezi | FIRMS nominal/yüksek güven |
|---|---:|---|
| 12 Ağustos 2023 | 12 | 12 Type 2 |
| 13 Ağustos 2023 | 2 | 2 Type 2 |
| 14 Ağustos 2023 | 5 | 5 Type 2 |
| 15 Ağustos 2023 | 8 | 7 Type 2, 1 Type 0 |

Adaydan önceki tam 72 saatte aynı hücrede bulunan 19 nominal/yüksek
güvenli Type 2 satırın tümü 2 km içinde. En yakın merkez yaklaşık
990 m uzakta. Projenin kaynak filtresi bu türü diğer statik kara
kaynağı olarak ayrı tutuyor. R05'in yeni Type 0 kaydıyla önceki Type 2
kayıtlarının aynı fiziksel kaynağa ait olduğu çıkarılamaz. Görseldeki
yapay yüzey ön notu ve eski CORINE tarım sınıfı ayrı kanıtlar olarak
korunur. R05'in pozitif hedefi açık.

## C için açık olay kanıtı

2021 yazı için yerelde kayıtlı 84 EFFIS sınırının hiçbiri C'nin
merkezini kapsamıyor. En yakın sınır (51931) UTM 36N düzleminde
yaklaşık 27,24 km uzakta ve katalogda 28 Temmuz–6 Ağustos tarihli.
Ağustos için eldeki küçük MODIS raster kesiti C konumuna ulaşmıyor.
EFFIS kapsamı ve uydu veri bağı nedeniyle bu kontroller bağımsız
olay doğrulaması veya yokluk kanıtı sağlamıyor.

OGM'nin Akseki yangın yönetim planında yıllık şeflik sayımları ve
çok yıllı bir konum haritası var. İncelenen bölüm C'yi 15 Ağustos
2021 tarihinde belirli bir olayla eşleştirecek satır vermiyor.
Aynı tarihli Akseki haber arama sonuçları ilçe bağlamında kaldı.
Tam başlangıç saati ve konumu doğrulanmadığı için C'ye bağlanmadı.
[OGM yönetim planı, şekil 13 ve tablo 14](https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/YanginYonetimPlanlari/AntalyaOBM-Akseki%20Yang%C4%B1n%20Y%C3%B6netim%20Plan%C4%B1%20%282026-2030%29.pdf).

## Bulunan idari envanter ve alım koşulları

Bikem Ekberzade'nin OGM kaynaklı 2013–2025 envanteri için ESSD ön
baskısı ve sözlük incelendi. 8 Kasım'da Zenodo açık API'si HTTP 200
döndürdü. Kayıt ambargolu, ambargo tarih alanı **31 Mayıs 2027** ve
listelenen açık dosya sayısı sıfır. Tarih alanı erişim garantisi
değildir. Bu adımda envanter satırı alınmadı. Makale değerlendirme
aşamasındadır. [Ön baskı](https://essd.copernicus.org/preprints/essd-2026-701/essd-2026-701.pdf) · [Zenodo açık kayıt](https://zenodo.org/records/21887740).

Dosya erişilebilir olduğunda önce sürüm, lisans, dosya özeti ve
zaman/konum alanlarının anlamı doğrulanır. İlk inceleme yalnız
2018–2023 ve dört il üzerinden yürütülür. Özgün OGM koordinatı olan
kayıtlarda konum belirsizliği ve olay zamanı ayrıca kontrol edilir.
VIIRS ile düzeltilen konumların uyduya bağımlılığı işaretlenir.
Sınır toleransıyla kabul edilen, kıyıya çekilen veya tahminle
doldurulan konumlar kesin 5 km hücre kanıtı olarak kullanılmaz.
Yazarın sözlüğünde 2019 ve 2020 için olay saati eksik. Bu kayıtlar
belirli saate doldurulmadan yerel gün aralığı olarak değerlendirilir.
OGM olay zamanı ile ilk uydu tespiti ayrı saklanır. Eşleşmeyen bir
kayıt, sicilin kapsamı doğrulanmadan negatif etiket üretmez.

## Kontrol kaydı

| Sonuç | Yerel yol | SHA-256 |
|---|---|---|
| 15 vaka toplu zaman incelemesi | `outputs/reports/dataset/pu_stable_batch_v1/20261107T225006Z_5a7bc291/readback.json` | `52c18d0d64eb6d054d93628f5fae9dfa6c2ef26b6588a6452adcc4f907b94235` |
| FIRMS tür ve tarama sayısı | `outputs/reports/dataset/pu_filter_context_v1/20261107T225355Z_c2fc9d7d/readback.json` | `de9985e8a5412944e18e6df1cda37ba004ce22407d732c5faee08b27299f77f6` |
| Açık erişim metadata | `outputs/reports/dataset/public_administrative_reference_v1/20261107T225218Z_ebfbfe25/readback.json` | `d179128f5935278e9c92c6c212348b13ea36d7593b294eeec05c69fe6f493603` |

Üreticiler `scripts/quality/review_pu_stable_batch.py` ve
`scripts/quality/review_pu_filter_context.py`. 40 ve 5 kaynak
kimliği, 48 günlük iç kaynak, C'nin önceki dört pencere ve komşuluk
sonucuyla tam eşitlik, JSON geri okuması ve Ruff geçti. İlk Type
kontrolünde yanlış aktarılmış bir hash, dosya okunmadan reddedildi.
Doğrudan hesaplanan hash ile düzeltilip iki giriş tekrar denetlendi.
2024 satırları analiz öncesi çıkarıldı. 2025 kapalı kaldı.

Ana hedef için kabul edilebilir pozitif referans ve güvenilir
değerlendirme hâlâ açık. Etiket, eğitim, dış ileti, bulut işi ve
nihai birleşme yapılmadı.
