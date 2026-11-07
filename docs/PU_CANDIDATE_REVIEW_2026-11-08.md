# PU adaylarının inceleme paketi — 8 Kasım 2026

2018–2023 dönemindeki 156 amaçlı pilot hücre-günün 21'inde ilk olay
adayı vardı. Bu 21 birimin tamamı, 25 ilk tespit noktası, katalog
gruplama bilgisi ve önceki gözlem tanılarıyla eşleştirildi. Bu dar
incelemenin amacı hangi kanıtın hangi karar için kullanılabileceğini
görmek ve üç yeni araştırmacı örtü yorumu almaktır.

## Ayrı değerlendirilecek kanıtlar

| İnceleme | Kullanılan kanıt | Kararı açık bırakan durum |
|---|---|---|
| Yeni olay | Dokuz gruplamada ilk zaman ve üyelik, `(T,T+24 saat]` sınırı, aynı bileşene bağlı ilk hücreler. İleride adayın önceki tespitlerle sürekliliği ayrıca değerlendirilir. | Daha eski bir olayın devamı olasılığı, ayar duyarlılığı, kaynak boşluğu veya bağımsız olay dayanağının eksikliği |
| Hücre ve yerel örtü | 2017 haritasının 5 km hücre bağlamı ayrı tutulur. Her ilk nokta için yaklaşık tespit alanı, CORINE bağlamı ve tarihli görüntü birlikte incelenir. | Karışık doğal ve yönetilen örtü, konum belirsizliği, görüntü kalitesi veya tarih farkı. Birden çok ilk nokta varsa her noktanın yorumu ayrı kalır. |
| Gözlem desteği | Günlük nominal kara alanı, en az 12 saat ayrımlı tekrar, dört dilimin ortak alanı ve herhangi bir kara parçası için tarama zarfları arasındaki boşluk | Geniş günlük alanla birlikte uzun zaman boşluğu veya farklı alanların gözlenmesi. Burada kabul eşiği seçilmedi. |

Dokuz ayarda 15 hücre-gün tutarlı. Dört hücre-günde adayın varlığı,
iki hücre-günde ilk zaman veya üyelik ayara duyarlı. Tutarlı 15 birimin
il dağılımı Antalya 5, İzmir 5, Mersin 4, Muğla 1. Mevsim dağılımı
sonbahar 8, ilkbahar 3, yaz 3, kış 1. İlk nokta sensörü 9 birimde
NOAA-20, 6 birimde S-NPP. Örnekler 2018, 2021 ve 2023'ten geliyor.
Bu dağılım pilotun sınırını gösterir ve hedef nüfus oranına çevrilmez.

R06 örneğinde dokuz ayar aynı ilk adayı veriyor. Günlük nominal
kara desteği yaklaşık %100 iken en az 12 saat ayrımlı tekrar alanı
%0. Herhangi bir kara parçasını içeren tarama zarfları arasındaki
en uzun boşluk yaklaşık 12,35 saat. Birim 15 Kasım 2018, Mersin.
Bu ölçüler gözlem desteğini betimler. Yerel örtü ve yeni olay
değerlendirmesi ayrı dayanaklara bağlıdır.

## Araştırmacıdan istenen kısa inceleme

İlk turda önceki insan yorumu bulunmayan, tek ilk noktası olan ve
dokuz ayarda tutarlı birimlerden üç farklı görsel bağlam seçildi.
Her bağlamda, seçilen kalite işaretleri sıfır olan en az bir görüntüsü
bulunan adaylara öncelik verildi. Sonra en yakın çekim tarihi ve vaka
kodu kullanıldı. Görsel bağlam grupları önceki asistan notlarından
geldi. Bu nedenle seçim amaçlıdır ve kör değerlendirme sayılmaz.

| Vaka | Tahmin günü ve il | Görüntü | Bakılacak panel |
|---|---|---|---|
| R05 | 15 Ağustos 2023, İzmir | 5 Ağustos 2023 | [Sayfa 1, sol alt](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_1.png) |
| R06 | 15 Kasım 2018, Mersin | 6 Ekim 2018 | [Sayfa 2, sol üst](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_2.png) |
| R07 | 15 Kasım 2018, Antalya | 3 Kasım 2018 | [Sayfa 2, sağ üst](../outputs/reports/dataset/remaining_cover_review_v1/20261023T162553Z_e9d8f8dd/sheet_2.png) |

Her vaka için sarı sınırın içindeki görünüm kaydedilir. Yanıt seçenekleri
doğal ağaçlık/çalılık, tarım veya yönetilen bitki örtüsü, yapılaşma veya
yapay yüzey, karışık ve ayırt edilemiyor. Bir kısa gerekçe yeterlidir.
R07 görüntüsünde seçilen kalite işaretlerinin tamamı sıfır değildir.
Görüntüdeki belirsizlik yoruma dahil edilebilir. Üç yorum, görüntüye
dayalı araştırmacı ön notu olarak saklanır. Hedef tablosu boş kalır.

## Belirsiz havuz ve değerlendirme sınırı

Belirsiz havuzun aday kataloglarından bağımsız örnekleme çerçevesi,
2018–2023 özellik takviminin nihai hücre uygunluğu belirlendikten
sonraki hücre-günleridir. İl, mevsim ve sensör dönemine göre seçim
olasılıkları belgelenir. Genel hedef dağılımından örnek isteyen
iki örneklemli nnPU tasarımında yalnız tespit kaydı olmayan birimleri
almak farklı bir dağılım oluşturur. Buradaki 156 pilot birim ve üç
görsel bu çerçevenin yerine kullanılmaz. Çerçeve tasarımı açık,
sınıf oranı ve değerlendirme dayanağı henüz belirlenmedi.
[nnPU örnekleme tanımı](https://papers.nips.cc/paper/2017/file/7cce53cf90577442771720a370c3c723-Paper.pdf).

## Doğrulama

Üretici `scripts/quality/prepare_pu_candidate_review.py`.
Yerel çıktı
`outputs/reports/dataset/pu_candidate_review_v1/20261107T213328Z_29cb887c/readback.json`.
SHA-256 `5b7fd0cc69efe03ff73dac67e65d58878add917f0a133917fe204715d07824ce`.
Dokuz dosya kimliği, 21 hücre-gün anahtarı, 25 nokta üyeliği, ilk
tespit zamanları, 15/4/2 sayımı ve boş araştırmacı yanıtları kontrol
edildi. Kaynak CSV'ye karşı ikinci anahtar ve grup sayımı geçti.
JSON geri okuması ve Ruff kontrolleri geçti. Kaynak tablodaki
senaryo sayısının `9.0` biçimi sayısal eşitlikle karşılaştırıldı.

2024/2025 erişimi, model eğitimi ve nihai birleşme yapılmadı.
`daily_observation_status=unknown` ve `negative_label_permitted=false`.
İnsan ön notları alındığında mevcut kaynaklar ve bu makbuz korunarak
yorumlar yeni tarihli bir kayıtta karşılaştırılacak.

## Araştırmacı yanıtları ve örtü karşılaştırması — 8 Kasım 2026

| Vaka | Araştırmacı ön notu | CORINE 2018 ve yorum sınırı |
|---|---|---|
| R05 | Yapılaşma veya yapay yüzey görünümü | Haritada yaklaşık alanın tamamı sulanmayan ekilebilir arazi. 2023 görüntüsündeki görünümle eski harita arasında bağlam farkı var. Bu kanıt arazi değişiminin tarihini veya termal kaynağı belirlemiyor. |
| R06 | Tarım görünümü | Haritada yaklaşık alanın %66,02'si sürekli sulanan arazi, %33,98'i meyvelik. Görüntü tarımsal bağlamla uyumlu. Haritanın referans dönemi tahmin zamanının ötesine uzanıyor. |
| R07 | Çevrede tarım görülüyor. Sarı alan karışık ve örtü ayırt edilemedi. | Haritada yaklaşık %54,99 tarım, %37,18 akarsu, %7,83 kesintili kentsel doku. Görüntüde gölge veya koyu alan ve sınıflandırılmamış piksel işaretleri var. Yerel örtü belirsiz kaldı. |

İnsan ön notu kapsamı 10/25'ten 13/25 noktaya ve 9/21'den 12/21
hücre-güne çıktı. Üç yanıt ayrı bir yerel kayıtta, önceki kaynakların
kimlikleri ve görüntü tarihleriyle saklandı. Önceki aday makbuzu,
örtü matrisi ve iki görüntü sayfasının SHA-256 değerleri kontrol
edildi. Üyelik, önceki notların sayısı, JSON geri okuması ve R07
belirsizlik alanı doğrulandı.

Yerel kayıt
`outputs/reports/dataset/pu_researcher_cover_notes_v1/20261107T220751Z_2b5bf4b1/readback.json`.
SHA-256 `b9f5e68587bb278719f3e9e787bdd66ead3b7c2d4798d106ee758358d0b96898`.

Üç vakada da hedef boş ve habitat kabulü açık. Görüntü yorumları
örtü incelemesine ek kanıt sağlıyor. Sıradaki teknik inceleme, doğal
örtü bağlamı daha güçlü olan C gibi tutarlı adayların önceki
tespitlerle devam ilişkisini ve kaynak boşluklarını değerlendirmektir.
