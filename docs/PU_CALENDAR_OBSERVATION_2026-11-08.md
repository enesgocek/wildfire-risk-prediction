# PU örnekleme takvimi ve nominal uydu gözlemi — 8 Kasım 2026

## Amaç ve kapsam

Pozitif–belirsiz (PU) yönteminin uygulanabilirliğini incelemek için önce
yangın tespitlerinden bağımsız bir örnekleme çerçevesi kuruldu. Birim,
proje hücresi ile UTC gece yarısında başlayan tahmin gününün birleşimidir.
Antalya, İzmir, Mersin ve Muğla'daki 2.899 hücre ile 2018–2023 arasındaki
2.191 gün birlikte 6.351.709 hücre-gün oluşturuyor. Birden çok ili kesen
hücre, özetlerde çalışma alanı içindeki en büyük örtüşmenin olduğu ilde
tek kez sayıldı. Mevsimler takvim yılı içinde Aralık–Şubat, Mart–Mayıs,
Haziran–Ağustos ve Eylül–Kasım olarak gruplandı.

## Kaynak ve kontrol

72 aylık özellik makbuzunun takvimi, çalışma alanı sürümü ve satır sayıları
kontrol edildi. Mevcut gözlem tabloları ve kompakt tarama paketleri kaynak
özetleriyle eşleştirildi ve dosya özetleri (SHA-256) doğrulandı. Her ayda
hücre-gün anahtarları ve UTC tahmin saatleri kontrol edildi. SNPP ve
NOAA-20 için tarama kayıtlarındaki nominal, artık sinyal hariç tutulan
yangın dışı kara piksel merkezi sayıları ayrı toplandı. Bu iki sayının
toplamı mevcut gözlem tablosundaki değerle her ürün satırında uyuştu.

2018-06-13 ve 2023-12-31 tarihlerinin kaynak ürünleri ertelenmiş durumda.
Bu iki tarihteki 5.798 hücre-gün, ürün bulunan ve seçilen kara merkezi
sayısı sıfır olan satırlardan ayrı tutuldu. Bu denetimde özellik
değerlerinin kaynaktan yeniden hesaplanması kapsam dışındaydı.

## Bulgular

| Ölçüm | Hücre-gün | Ürün bulunan satırlardaki pay |
| --- | ---: | ---: |
| Kaynak ürünü var | 6.345.911 | %100 |
| Seçilen kara merkezi var | 6.088.289 | %95,94 |
| Seçilen kara merkezi sıfır | 257.622 | %4,06 |
| En az bir bulut merkezi kaydedildi | 4.052.772 | %63,86 |
| Nominal kara merkezi aralığı en az 12 saat | 2.078.316 | %32,75 |

Ürün bulunan satırlarda seçilen kara merkezinin sıfır olduğu pay il
bazında Muğla'da %3,06, Antalya'da %3,97, İzmir'de %4,22 ve Mersin'de
%4,92. Aynı pay 2018'de %5,57 ve 2023'te %3,20. Kışın
142.986/1.565.460 (%9,13), yazın 18.315/1.597.349 (%1,15).
İl, yıl ve mevsim birlikte ele alındığında pay Mersin'in 2021 yazında
%0,39 (66.976 ürün satırı) ve 2018 kışında %19,51 (65.520 ürün satırı).
Bu farkın nedenleri bu denetimde ayrıştırılmadı.

2.189 ürün gününün 2.024'ünde iki sensörden, 150'sinde yalnız SNPP'den,
15'inde yalnız NOAA-20'den tarama kaydı bulundu. İki sensör kaynağının da
bulunduğu günlerdeki 5.867.576 hücre-günün dağılımı aşağıdadır.

| Seçilen kara merkezi | Hücre-gün | Pay |
| --- | ---: | ---: |
| İki sensörde de var | 5.281.703 | %90,02 |
| Yalnız SNPP'de var | 185.663 | %3,16 |
| Yalnız NOAA-20'de var | 180.298 | %3,07 |
| İki sensörde de sıfır | 219.912 | %3,75 |

Örneğin 1 Haziran 2019'da 2.899 hücrenin 2.828'inde iki sensör de
seçilen kara merkezi kaydetti. 37 hücrede yalnız NOAA-20, 7 hücrede
yalnız SNPP kaydetti ve 27 hücrede sayı iki sensörde de sıfırdı.
Ayrı kontrolde 96 il-yıl-mevsim grubunun paydaları takvimden yeniden
hesaplandı ve toplamlar doğrulandı. İki örnek günün sensör dağılımı
ham tarama tablosundan ikinci bir yöntemle sayıldı.

## Yorum ve sonraki adım

Bir sensörün kaynak günü, o nominal tarihte çalışma alanı için tarama
kaydı bulunduğunu ifade eder. Piksel merkezi sayımı hücrenin alansal
kapsamasını, hedef 24 saatlik pencerenin yeterli gözlemini veya yangını
tespit etme olasılığını ölçmez. Nominal en uzun kara merkezi aralığı için
12 saat eşiği betimleyici karşılaştırmada kullanıldı. Günlük gözlem durumu
`unknown` ve pozitif ile negatif etiket izinleri `false` kaldı.

Takvim, orman ve çalılık kapsamı ile gözlem katmanlarını dikkate alan,
yangın tespitinden bağımsız bir inceleme örneklemi kurmaya temel sağlar.
Hedef penceresiyle zaman uyumu, örtü uygunluğu ve PU varsayımlarının
desteklenebilirliği ayrıca incelenecek. Bu aşamada yalnız örnekleme
çerçevesi hazırlandı. Nihai birleştirme için ayrı parça denetimi ve bu
denetime bağlı kullanıcı onayı gerekir.

Yeniden üretim komutu `python scripts/quality/audit_pu_calendar_observation.py`.

Yerel çalıştırma kimliği `20261108T010353Z_12368f01`.
Denetim makbuzunun SHA-256 değeri
`e9c7ee3a1cda77371467ecf36d0dc6ddf3615aefe9134f1b7544325ed477129b`.
