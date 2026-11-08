# Pozitif–belirsiz öğrenme için olay bağlantısı duyarlılığı — 8 Kasım 2026

Kemalpaşa (H12) ve Kaş (H04) başta olmak üzere açık olay bağlamının ne kadar dayanıklı olduğu ölçüldü. İnceleme, aynı bağlantının farklı zaman ve mesafe koşullarında kalıp kalmadığını ve bu küçük havuza yanlış bir bağlantı girerse havuzun nasıl değişeceğini kapsıyor. [Beş adayın olay kanıtı](STRATIFIED_EVENT_CANDIDATES_2026-11-08.md).

## Gerçek katalogda eşleştirme deneyi

Dokuz gruplama ayarında tüm 2018–2023 eğitim adaylarının ilk noktaları kullanıldı. Eşzamanlı ilk noktalar korundu ve eşleşmeler grup bazında sayıldı. Dört tespit için önceki rapordaki yerleşim temsil noktası ve altı kaynak saati ayrı denendi. H12'nin haber saati ve belediye ekip çıkışı, H22'nin iki yaklaşık haber saati ayrı hipotezlerdir. H14 için taramaya uygun tek olay saati bulunmadığından sonuç boş bırakıldı.

Deneme aralıkları 0,5, 1, 2 ve 5 km ile bildirilen saatten sonraki 15, 30, 60, 90 ve 120 dakikadır. Yerleşim merkezi yangın başlangıç noktası değildir. Bunlar yöntem kabulü için seçilmiş eşikler değildir. Eşleşmelerin tanımlı saatten sonrasına bakıldı. Yaklaşık haber zamanlarının öncesi bu tek yönlü denemenin dışında kalır.

| Kaynak ve tespit | Yaklaşık mesafe | Bildirilen saatten sonraki tespit | Dokuz ayarın hepsinde tespiti tutan en dar denenen koşul |
|---|---:|---:|---|
| H03, yaklaşık olay saati | 1,24 km | 16 dk | 2 km ve 30 dk |
| H04, yaklaşık olay saati | 1,60 km | 65 dk | 2 km ve 90 dk |
| H12, yaklaşık olay saati | 0,60 km | 16 dk | 1 km ve 30 dk |
| H12, ekip çıkışı | 0,60 km | 5 dk | 1 km ve 15 dk |
| H22, iki yaklaşık olay saati | 3,74 km | 37 dk veya 7 dk | Sırasıyla 5 km ve 60 dk veya 5 km ve 15 dk |
| H14, çoklu olay bağlamı | — | — | Saat ve olay kimliği yetersiz |

Yaklaşık olay saatini esas alan 1 km ve 30 dk denemesinde H12 kaldı. 2 km ve 30 dk'ya çıkıldığında H03 eklendi, 2 km ve 90 dk'da H04 de eklendi. 5 km ve 120 dk'da saatli dört tespit de kaldı. H03'e ait olası saha olayı tarımdan ormana sıçramayı anlatıyor. Dar bir mesafe ve saat uyumu, yerel başlangıç örtüsü koşulunu çözmüyor. H04'ün daha geniş zaman penceresi ve EFFIS yakınlığı ayrı kanıtlardır. H12'de daha dar pencerenin ekip çıkışından elde edilmesi, çıkış saatinin tutuşma saati olarak kullanılmasını gerekçelendirmez.

En geniş aralıkta, olay günündeki altı kaynak hipotezinin her biri için her ayarda bir aday grup bulundu. Aynı konum ve saatler önceki ve sonraki yedi güne kaydırıldığında, 84 kaynak saati × gün denemesinin hiçbirinde aday grup çıkmadı. Bu günler doğrulanmış yangınsız günler değildir. Aynı tespit kaynağına ve az sayıda amaçlı olaya dayandığı için bu sayı yanlış eşleşme oranı veya yöntemin doğruluğu olarak yorumlanamaz.

## Tek yanlış bağlantı varsayımı

| Varsayımsal havuz | Havuz büyüklüğü | Bir yanlış bağlantı | İki yanlış bağlantı |
|---|---:|---:|---:|
| Güçlü iki bağlam (H12 ve H04) | 2 | %50, geriye 1 kalır | %100, geriye 0 kalır |
| İncelenen beş bağlam | 5 | %20, geriye 4 kalır | %40, geriye 3 kalır |

Paylar, varsayılan yanlış bağlantı sayısının havuz büyüklüğüne oranıdır. Hiçbir bağlantının yanlış olduğu ölçülmedi. Hesap, diğerlerinin geçerli olduğunu varsayarsa kaç aday kalacağını gösterir. Gerçek doğruluk, sınıf oranı veya model başarımı hesaplanmadı.

## PU için iki uygulanabilir karar

1. **Önerilen yol.** H12 ve H04'ü güçlü olay bağlamı olarak ayrı incelemede tutmak. H03'ün başlangıç örtüsü, H22'nin yer/saat farkı ve H14'ün çoklu olay belirsizliği kayıtta kalır. Pozitif–belirsiz araştırmasının sonraki teknik işi, belirsiz hücre-gün havuzunun kapsamını olay seçimine bağlı olmadan tanımlamak ve bölge, yıl, mevsim ve sensör dönemine göre hangi gözlem eksiklerinin değiştiğini ölçmektir.
2. **Sonraki koşullu araştırma seçeneği.** Yeterli ve ayrı denetlenebilir olay kanıtı oluşursa olası bağlantıları, kabul edilmiş olaylardan ayrı bir gürültülü gösterge olarak ele alan duyarlılık deneyi tasarlanabilir. Etki, her bağlantı çıkarılarak ve bağımsız referanslarda karşılaştırılarak ölçülür. Bu seçenek yeni bilimsel karar ve değerlendirme verisi gerektirir.

Klasik PU yaklaşımında pozitif kümenin gerçekten pozitif olması ve pozitiflerin nasıl seçildiğine dair bir varsayım gerekir. SAR yaklaşımı seçilme olasılığının bazı gözlenen özelliklere bağlı olmasına izin verir. Buradaki haber, kurum ve uydu erişim farklarının bu varsayımı karşıladığı gösterilmedi. nnPU'nun eğitim riskini sınırlaması, yanlış bağlanmış olayları veya seçilme yanlılığını kendiliğinden çözmez. [Elkan ve Noto](https://cseweb.ucsd.edu/~elkan/posonly.pdf) · [Bekker ve Davis](https://proceedings.mlr.press/v94/bekker18a.html) · [Kiryo ve diğerleri](https://papers.nips.cc/paper/2017/hash/7cce53cf90577442771720a370c3c723-Abstract.html).

Beş adayda bağımsız başlangıç konumu doğrulaması sıfır. Pozitif ve negatif etiket izinleri `false`, günlük gözlem `unknown`. Ana hedef, 2024 karşılaştırma ve kapalı 2025 ayrımı korunur. Model eğitimi, AP/kalibrasyon hesabı ve nihai birleştirme yapılmadı.

## Doğrulama

Üretici `scripts/quality/audit_pu_link_sensitivity.py`. Yerel çıktı `outputs/reports/dataset/pu_link_sensitivity_v1/20261108T005041Z_7b083915/readback.json`. SHA-256 `39a52dcd71ff5d53b36c507e018991e6608b197d7948ef836beb2af0f628c402`. 14 dosya özeti ve 16.200 pencere kaydı, CSV'deki grup ve ilk zamanlardan ayrı bir hesapla doğrulandı. 114 ilgili test geçti.
