# İnsan değerlendirmesi için altı gözlem örneği — 14 Ekim 2026

Sonraki karar kaydı: araştırmacı A seçeneğini kabul etti. Tamamen harita suyu
olan hücreler kapsam dışında, karışık hücreler korunuyor.
[Uygulama ve gerçek etki](WATER_SCOPE_2026-10-14.md). Aşağıdaki hazırlık
soruları önceki inceleme durumunu anlatır; kapsam tercihi, F görüntüsünün
bağımsız doğrulandığı veya 453 kanıt formunun doldurulduğu anlamına gelmez.

Durum: inceleme hazırlığı; aşağıdaki sorular yanıtlanmış veya danışman
tarafından onaylanmış değildir. Dayanak ve ölçülerin sınırı
[400 hücre-gün incelemesindedir](OBSERVATION_PILOT_REVIEW_2026-10-14.md).

Aynı gün kullanıcı açıklamasıyla görev dağılımı güncellendi: asistan
seçenekleri ve gerekçeli önerisini hazırlayacak, nihai proje kararını
araştırmacı verecek. Danışmanın her yöntem kararını incelemesi ilerlemenin
ön koşulu değildir. Bu güncelleme ölçümleri, boş etiketleri veya önceki
çıktılardaki inceleme durumlarını değiştirmez.

## Şimdi araştırmacının bakacağı bölüm

İlk olarak `human_observation_examples.png` görselini ve aşağıdaki A–F
açıklamalarını birlikte incele. Görsel konumu:
`outputs/reports/dataset/observation_review_v1/20261014T174956Z_cca3d882/`.
Mavi/gri çubuklar farklı zamanların nominal kara/bulut alan birleşimleri,
turuncu çubuk seçilmiş merkez zaman zarfları arasındaki en uzun boşluktur.
Bu altı şekle bakarak 0/1 yangın etiketi vermen beklenmiyor.

| Örnek | Hücre / tarih | Neyi inceleyeceğiz? |
|---|---|---|
| A — Kaynak yok | C568_R865 / 13 Haziran 2018 | Boş ölçünün sıfır gözlem veya yangınsız gün sayılmaması. |
| B — Kara ve bulut birlikte %100 | C653_R881 / 27 Ekim 2021 | Farklı geçişlerin alan birleşimleri; aynı anda bulutsuzluk/kapalılık anlamına gelmiyor. Seçilmiş kara zarfları arasında yaklaşık 12,34 saatlik en uzun boşluk var. |
| C — Nominal kara merkezi yok | C636_R876 / 20 Mart 2022 | Bulut alanı yüksek, termal merkez yok; sıfır termal sayım gözlem yeterliliğini kanıtlamıyor. |
| D — Kara alanı var, termal merkez yok | C575_R883 / 4 Ağustos 2018 | Yedi nominal kara taramasına rağmen tam gün/gerçek yangın yokluğu kanıtı ve zaman hizalaması ayrı gerekiyor. |
| E — Gece yarısı | C522_R918 / 18 Ocak 2022 | Bir termal merkez içeren tarama gece yarısını aşıyor. `midnight_boundary_example.png` bunu gösteriyor; piksel zamanını şekle bakarak tahmin etmeyeceğiz. |
| F — Çok küçük su parçası | C542_R880 / 18 Temmuz 2019 | Gridin AOI parçası 88,57 m²; mevcut örtü tablosunda su=1, orman/çalı=0. Hedefimiz olan orman/çalı riski kapsamında bu tür hücrelerin nasıl ele alınacağı açık. |

Kullanıcı olarak şimdi verebileceğin yararlı geri bildirim, özellikle F'nin
üründe göstermek istediğin alanla uyumlu olup olmadığı ve B/D örneklerinin
açıklamasının anlaşılır olup olmadığıdır. Bu geri bildirim bilimsel etiket
doğrulaması yerine kaydedilmez. Alanı su olarak gösteren tabloyu tarihsel
görüntüyle doğruladığın veya yangın görmediğin varsayılmaz.

## Asistanın seçenek ve öneri hazırlayacağı kararlar

1. **Habitat kapsamı:** su, küçük kıyı parçaları, tarım ve orman/çalı sınırları
   için hangi bilimsel kapsam ve harita referans yılı kullanılmalı? F örneği
   tartışma için somut başlangıçtır; henüz alan eşiği seçilmedi.
2. **Gözlem yeterliliği:** B/C/D örneklerinde görüldüğü gibi yalnız alan oranı
   yeterli değil. Hangi geçiş/zaman/bulut koşullarının hangi hedef tanımı için
   gerekçeli olabileceği ve bunların seçim yanlılığı nasıl sınanacağı belirlenmeli.
3. **Bağımsız doğrulama:** örneklerde olay varlığı/yokluğu için hangi tarihli
   resmî olay kaydı, uygun görüntü veya uzman değerlendirmesi kullanılabilir?
   Aynı FIRMS/VIIRS verisini yeniden görmek bağımsız doğrulama sayılmaz.

Bu başlıklarda teknik araştırma ve alternatiflerin hazırlanması asistanın,
nihai proje seçimi araştırmacının sorumluluğundadır. Her öneride seçeneğin
yararı, sınırı, önerilen yol ve gereken kanıt açıkça sunulur. Danışman/uzman
görüşü ek destek olabilir; alınmış varsayılmaz veya zorunlu bekleme nedeni
yapılmaz. Karar, gerekçe, incelenen kanıtın kimliği/tarihi ve açık kalan
noktalar kaydedilir. Bir yöntem tercihi, bağımsız doğrulama yapıldı veya
bütün veri seti bilimsel kabulden geçti anlamına gelmez.

## Teknik olarak devam eden sorumluluk

Pencere uçları, komşu nominal günlerin taramaları ve piksel edinim zamanı
ilişkisi kaynak/kod düzeyinde araştırılmalıdır. Bu, gözle bir tarih seçme
görevi değildir. Otomatik denetimler, testler ve kaynak koruması devam eder.
Bağımsız kanıt yoksa ilgili değerlendirme belirsiz kalır.

Şu an özgün 453 form ve bu altı örnek **not_reviewed** durumundadır.
Araştırmacı veya bağımsız inceleyici gerçekten kanıt incelemeden karar
alanı doldurulmaz. Milyonlarca satırın tek tek elle etiketlenmesi yerine,
gerekçelendirilmiş ve incelenmiş bir protokolün sürümlü uygulanması hedeflenir.
