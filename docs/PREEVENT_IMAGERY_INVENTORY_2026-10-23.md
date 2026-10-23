# Tahmin öncesi görüntü envanteri — 23 Ekim 2026

## Amaç ve kapsam

2017 örtü haritasının yaş sınırını azaltmak için önceki incelemedeki aynı
25 ilk tespit noktası için tarihsel Sentinel-2 L2A görüntüleri arandı.
Örnekler 2018, 2021 ve 2023 eğitim dönemindedir; temsilî/rastgele örneklem
değildir. 2024 ve kapalı 2025 verileri açılmadı.

Bu adım **katalog envanteridir**. Görüntü pikselleri indirilmedi veya
orman/çalılık olarak yorumlanmadı. Etiketler, gözlem kabulü ve nihai
birleştirme kapalı kalır. Ücretli kaynak veya Earth Engine işi başlatılmadı.

## Gerçekleştirilen yöntem

- Önceki native piksel incelemesinin rapor, tablo ve yaklaşık destek
  geometrisi hash ile doğrulandı. Yaklaşık alan resmî piksel köşesi değildir.
- T, ilk tespitin ait olduğu `(T,T+24 saat]` hedefinin 00:00 UTC başlangıcıdır.
  Tam gece yarısındaki tespit önceki hedef güne aittir. Görüntü zamanı T'den
  kesin olarak önce olmalıdır; ilk tespit saatinden önce olmak tek başına yetmez.
- Açık Planetary Computer STAC kataloğunda `[T−60 gün,T)` aralığı tarandı.
  60 gün keşif penceresidir; kabul edilmiş habitat/özellik süresi değildir.
  Son 30 gündeki adaylar da ayrı sayıldı. Sorgunun kapsayıcı üst sınırına
  rağmen yerel kontrolde T ve sonrası elendi.
- Görüntü geometrisinin yaklaşık desteğin tamamını kapsaması ve RGB/SCL
  varlıklarının katalogda bulunması kontrol edildi. Bu, raster içinde veri
  bulunduğunu veya pikselin bulutsuz olduğunu kanıtlamaz.
- Bulut eşiği uygulanmadı. Bütün sonuçlar korundu; ilk inceleme sırası
  sahne bulut yüzdesi, ardından yakın tarih ve kimlikle oluşturuldu.
  Sahne bulutluluğu yerel nokta bulutluluğu değildir. Sıralama nihai seçim değildir.
- Aynı edinimin farklı işleme sürümleri/tile örtüşmeleri birleştirilmedi;
  ayrı kayıtlar ve farklı edinim zamanları ayrı sayıldı. Görüntü sayısı
  bağımsız gün/olay sayısı değildir.

## Ölçülen bulgular

| Ölçüm | Sonuç |
|---|---:|
| Sabit eğitim noktası | 25 |
| Dönen nokta–görüntü kaydı | 523 |
| Farklı katalog görüntü kimliği | 432 |
| Önceki 60 günde metadata adayı bulunan nokta | 25/25 |
| Önceki 30 günde metadata adayı bulunan nokta | 25/25 |
| Nokta başına 60 günlük aday sayısı | 11–44 |
| İlk inceleme adayının T'den önceki yaşı | 5,66–58,66 gün |
| İlk inceleme adayının sahne bulut yüzdesi | %0,003681–%13,699451 |
| İlk adayın ürün üretim zamanı T sonrasında olan nokta | 13/25 |
| Görüntü pikseli/yerel bulut incelemesi | Henüz yapılmadı |

Bulutsuzluğa göre sıralama bazı noktalarda eski görüntüyü öne çıkarır;
her noktada son 30 günde aday olmasına rağmen ilk sıranın 58,66 güne
kadar uzaması bundan kaynaklanır. Arazi incelemesinde birden fazla tarih
ve yerel kalite birlikte değerlendirilecek; tek sıralama sonucuyla örtü atanmayacak.

Somut örnekler:

| İlk tespit kimliği / tarihi | İlk inceleme görüntüsü | T'den önce | Sahne bulutu |
|---|---|---:|---:|
| SNPP_815579_4958 / 15 Mayıs 2018 | 23 Nisan 2018, 35SMC | 21,63 gün | %0,16629 |
| SNPP_815579_17606 / 15 Ağustos 2018 | 9 Ağustos 2018, 36SXF | 5,66 gün | %0,434081 |
| SNPP_815579_146808 / 15 Ağustos 2021 | 20 Temmuz 2021, 36SUG | 25,64 gün | %0,037435 |

İlk iki örnekte arşiv ürününün üretimi 2020'dedir. Görüntünün edinimi 2018
olsa da bu işlenmiş sürüm 2018 tahmin anında varmış gibi kullanılamaz.
Diğer 12 ilk adayda üretim zamanı T'den önce görünmesi de tek başına
kullanıcı erişilebilirlik zamanı kanıtı değildir. Bütün kayıtlarda
`historical_available_at_verified=false` kalır. Geçmiş örtü incelemesi ve
operasyonel model girdisi uygunluğu farklı değerlendirmelerdir.

## Çıktılar ve kontroller

Tamamlanan çıktı:
`outputs/reports/dataset/preevent_imagery_inventory_v1/20261023T150758Z_56f8c769/`.
Rapor SHA-256:
`dedc117b117dca2b1751b54a044de648b1305672495e0c11d32703ae13e727dc`.

`scene_inventory.csv` bütün nokta–görüntü kayıtlarını, `point_summary.csv`
nokta başına adayları ve ilk inceleme sırasını içerir. `metadata/` özgün
katalog yanıtlarını ve sorgu parametrelerini korur. Yaklaşık 8,17 MB
metadata vardır; görüntü rasterı indirilmedi. 56 girdi ve 54 çıktı
dosyasının hash değerleri tamamlanma sonrasında bağımsız geri okumayla doğrulandı.

İlk toplamada 26 anonim HTTP sorgusu yapıldı. İki ön erişim/şema denemesi
de başarılıydı; kısıtlı ortamın ilk DNS denemesi başarısızdı. Toplama sonunda
CSV geri okuması `02.12` sürümünün sayıya dönüşmesini yakaladı. İlk dizin
`20261023T150637Z_ec0e0215` eksik çıktı olarak korundu. Okuma şeması düzeltildi;
aynı özgün yanıtlar yeni dizinde, sorgu/başlangıç zamanı ve hash kontrolüyle
yeniden işlendi. Kabul edilmiş çıktı elle değiştirilmedi. Son rapordaki
`network_requests=0`, bu çevrimdışı yeniden işlemeyi ifade eder; tüm çalışma
boyunca hiç ağa çıkılmadığı anlamına gelmez.

13 yeni davranış vakası dahil 53 ilgili test geçti. Testler gece yarısı,
T sınırı, eğitim dışı zaman, kısmi kapsama, eksik kalite varlığı, bilinmeyen
bulut ve edinim/üretim zamanı ayrımını kapsar. İlk kısıtlı test denemesi
Windows sistem tanıtıcısı hatasıyla test toplamada durdu; aynı kontroller
normal yerel süreçte tamamlandı. Üç yeni Python dosyasında lint/format geçti.

## Sonraki işlem ve insan incelemesi

Envanterdeki adaylardan küçük yerel RGB ve sahne sınıflandırma (SCL)
pencereleri okunacak; nokta/alan üzerindeki bulut, gölge, veri dışı alan
ve tarih yakınlığı incelenecek. Uygun örnekler araştırmacıya aynı alanın
eski haritası ve olay öncesi görüntüsüyle yan yana sunulacak. Beklenen
karar, görünür örtünün orman/çalılık, tarım/yerleşim veya belirsiz olarak
inceleme kaydına alınmasıdır; bu tek başına yangının varlığı/yokluğu etiketi değildir.
Şimdilik görüntü gösterilmediği için araştırmacıdan görsel onay istenmedi.

Bağımsız olay kanıtı ve günlük yeterli gözlem koşulları hâlâ ayrı açık
konulardır. Bu envanter onları çözmüş veya veri setini eğitime hazır hâle
getirmiş sayılmaz.

## Birincil kaynaklar

23 Ekim 2026 erişimi:
[anonim katalog kullanımı](https://planetarycomputer.microsoft.com/docs/),
[STAC API arama tanımı](https://planetarycomputer.microsoft.com/docs/reference/stac/),
[Sentinel-2 L2A koleksiyon metadata'sı](https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a).
Yerel bulgular bu belgelerin genel açıklamasından değil, saklanan gerçek
katalog yanıtlarından hesaplandı. Hizmetin kataloğunda bulunmak bilimsel
doğrulama veya geçmiş erişilebilirlik garantisi değildir.
