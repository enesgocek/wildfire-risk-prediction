# Aynı konumda uydu–CORINE karşılaştırması — 4 Kasım 2026

## Tamamlanan işlem

C/D/E/F için mevcut birer, R03 için üç farklı olay öncesi görüntü
aynı konumdaki CORINE sınıf sınırlarıyla karşılaştırıldı. Beş noktada
yedi nokta–görüntü kaydı ve üç görsel sayfa üretildi. Yeni veri
indirilmedi; mevcut yerel dosyalar kullanıldı. Bu beş örnek amaçlı
seçilmiştir, 25 noktanın veya tüm çalışma alanının dağılımını temsil etmez.

Her satırın solunda mevcut Sentinel-2 TCI, ortasında aynı görüntüye
eklenen beyaz CORINE sınıf sınırları, sağında aynı pencerenin CORINE
haritası var. Sarı/siyah çizgi önceki yaklaşık tespit alanıdır; kırmızı/
mavi çarpı native merkezdir. Üç sütun aynı yerel UTM koordinat sistemi,
aynı sınırlar ve en-boy oranıyla çizildi. Paneller arası görsel karşılaştırma
bu satır içinde geçerlidir; farklı örneklerde ortak ölçek varsayılmaz.

CORINE'in 100 m hücre kareleri kenarları yoğunlaştırılarak görüntü CRS'sine
dönüştürüldü. Renkli harita kategorileri interpolasyona uğratılmadı;
uydu görüntüsü boyanmadı veya keskinleştirilmedi. Orta panelde yalnız
sınıflar arası sınırlar eklendi. Beyaz çizgiler gerçek parsel/orman
sınırının bağımsız ölçümü değildir; 2018 haritasındaki sınıf sınırlarıdır.

## Görseller ve kaynak tarihleri

- [C/D karşılaştırması](../outputs/reports/dataset/habitat_image_overlay_v1/20261103T215921Z_12a5f8fe/C_D.png):
  C — 20 Temmuz 2021; D — 8 Ekim 2021.
- [E/F karşılaştırması](../outputs/reports/dataset/habitat_image_overlay_v1/20261103T215921Z_12a5f8fe/E_F.png):
  E — 19 Aralık 2022; F — 6 Kasım 2018.
- [R03 üç tarih](../outputs/reports/dataset/habitat_image_overlay_v1/20261103T215921Z_12a5f8fe/R03_dates.png):
  27 Mart, 3 Nisan ve 1 Mayıs 2023.

Önceki ortak tablodaki 2018/2021/2023 yılları tahmin yıllarıydı.
Buradaki tarihler görüntü çekimidir; özellikle E'nin görüntüsü 2022
sonundadır, tahmin zamanı 2023 Şubatıdır. CORINE referansı 2017–2018
olarak kalır; çekim tarihleri haritaya aktarılmadı.

## Asistanın görsel ön yorumları

| Kod | Yeni karşılaştırmada görülen bağlam | Kabul edilmeyen çıkarım / kalan soru |
|---|---|---|
| C | Düzensiz koyu yeşil/ağaçlık görünüm ile açık bant birlikte bulunuyor. Merkezin açık sınıfta olması alanın tümünün açık olduğu anlamına gelmiyor. | Görüntüden ağaç türü veya doğal/yönetilen ayrımı kesinleştirilmedi; haritanın %77,98 orman payı 2021 için yeniden ölçülmüş gerçek oran değil. |
| D | Ağaçlık görünüm, yol, açık/parsel benzeri kesimler aynı yaklaşık alan içinde. | Alanın tamamına doğal orman veya tarım etiketi verilemez. CORINE geçişli ağaçlık sınıfı bu görüntünün her ayrıntısını doğrulamıyor. |
| E | Parsel çizgileri ve düzenli arazi kullanımı görülüyor; önceki tarla benzeri insan notuyla uyumlu bağlam. | 243 mozaik sınıfı içindeki doğal örtü oranı bilinmiyor; bütün alanın saf tarım olduğu kabul edilmedi. |
| F | Parsel düzeni ve tarımsal ağaçlıkla uyumlu görünüm; önceki tarla benzeri not ve 222 meyvelik sınıfıyla birlikte okunuyor. | Kesin meyve türü, kullanım statüsü veya yangının bu parselde başladığı doğrulanmadı. |
| R03 | İlk görüntüde geniş bulutlu/parlak alanlar var. Nisan ve Mayıs görüntülerinde aynı yerlerde kalan parlak geometrik yüzeyler ve yeşil/açık alan karışımı görülüyor. | Kalıcı yüzeyleri yalnız beyaz diye bulut saymamak gerekir; sera/yapı yorumu olasıdır, kesin tesis sınıfı veya yeni arazi değişimi kanıtı değildir. |

Yorumlar asistanın yeni görsel ön incelemesidir; yeni insan/uzman
incelemesi veya bağımsız örtü doğrulaması olarak sayılmadı. Önceki
araştırmacı yorumları değiştirilmedi, insan notu kapsamı hâlâ 10/25.
Konumsal üst üste çizim, kaynaklar arasındaki gerçek konum hatasının
ölçüldüğü veya giderildiği anlamına gelmez.

Kalite kayıtlarında C/E ve R03'ün iki alternatifinde seçilmiş işaretler
yok; bu örtü doğruluğu garantisi değildir. D'de sınıflandırılamayan,
F'de koyu/gölge ve sınıflandırılamayan piksel işaretleri var. R03'ün
ilk tarihinde bulut/sirüs, koyu/gölge ve sınıflandırılamayan işaretler
korunuyor. SCL yeniden hesaplanmadı; makbuzdaki önceki ölçüler kullanıldı.

## Kontroller

21 kaynak/kod kimliği işlem öncesi ve sonrası doğrulandı. Üç görselin
hash'i kaydedildi; yedi kayıt/beş nokta üyeliği ve JSON geri okuması
geçti. Her görüntünün CRS'si, dönüşümü, boyutu ve byte hash'i makbuzla
eşleşti; görüntü yaklaşık alanın tamamını içeriyor. CORINE–UTM merkez
geri dönüşünün en büyük farkı **1,86 × 10⁻⁹ m**. Bu sayı dönüşümün
sayısal tutarlılığıdır; konumsal arazi doğruluğu değildir. Lint/format
geçti. Üç ilk görsel ve son E/F sayfası asistan tarafından görüntülendi;
son sürümde açıklamalar Türkçeleştirildi ve kategori çizimindeki
görsel hücre dikişleri kaldırıldı. Eski çıktı korunmuştur.

Üretici: `scripts/quality/render_habitat_image_overlays.py`.
Çıktı: `outputs/reports/dataset/habitat_image_overlay_v1/20261103T215921Z_12a5f8fe/readback.json`.
SHA-256 `9c00a056197710f49e6fea5fb47da3e881b7c2295408389271f91eae3f8aff7b`.
UTC tarihli dizin 3 Kasım, Türkiye çalışma tarihi 4 Kasım'dır.

## Sonraki yöntem kararı için sonuç

C için ağaçlık bağlam, E/F için yönetilen kullanım bağlamı, D/R03 için
karışım/belirsizlik önerisi destekleniyor. Bunlar önerilen inceleme
başlıklarıdır; nihai doğal orman/çalılık kapsamı veya aday dışlama kuralı
olarak uygulanmadı. Bu kontrol, 25 noktanın tamamında olay tarihindeki
örtü kabulünü tamamlamaz.

Sıradaki iş, gözlenen farklı kanıt düzeylerini kabul/belirsizlik
protokolüne dönüştürmek için somut seçenekleri ve etkilerini hazırlamaktır.
Kural yalnız bu beş örneğe göre ayarlanamaz; eski harita, görüntü kalitesi,
yaklaşık konum ve insan notu olmayan kalan örnekler ayrıca ele alınmalıdır.
Olay gruplaması, gözlem yeterliliği ve gerçek yangın doğruluğu farklı
iş paketleri olarak açık kalır. Etiket, otomatik dışlama ve nihai
birleştirme yapılmadı; GCP ve 2024/2025 verileri kullanılmadı.
