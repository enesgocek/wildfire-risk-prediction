# Veri hazırlığından sonraki araştırma yönü — somut karar

**Sonraki 23 Kasım kararı: araştırmacı A'yı açıkça seçti.**
Yerel, geçmiş 2022 sonuçlarını gösteren araştırma prototipi
hazırlandı. [Çalışan dosyalar, kontroller ve kullanım](RESEARCH_PROTOTYPE_2026-11-23.md).
Aşağıdaki metin karar öncesi öneriyi korur; seçim gerçek hedef
doğrulaması veya nihai etiketli birleştirme onayı değildir.

23 Kasım 2026 karar öncesi önerisi aşağıda korunuyor; sonraki
açık A seçimi yukarıdaki notta kayıtlı.
Mevcut [veri/yöntem taslağı](research/DATASET_METHODS_DRAFT_2026-11-23.md)
ve [tamamlanan kapsam/kalite çalışması](DATASET_SUPPORT_AND_WEATHER_REVIEW_2026-11-23.md)
esas alınır. Bu metin yeni eğitim, kapalı yıl veya birleştirme izni değildir.

## Sorun veri miktarı değil, savunabileceğimiz sonuç

44.082 satırlık deneysel S/U inceleme paketi teknik olarak hazır.
Kaynaklara bağlanmış 2022 skorları, eksiklikler ve tam alan
meteorolojisiyle kurulan dokuz model de denetlendi. İnsan
kullanılabilirlik kontrolü zaten alınmış eski ekran tekrar sorulmayacak.
Ana 24 saatlik yeni orman/çalılık yangını sorusu korunuyor.

Gerçek Y hâlâ gözlenmiyor. Uydu/kaynak adayının bu hedefle ilişkisi,
seçilme/gürültü koşulları ve değerlendirme kapsamı açık. Bunları
kullanıcının bir seçeneği tercih etmesiyle doğrulanmış yapamayız.
Kırmızı/sarı/yeşil gösterim veya yüzde kullanmamak, hedefe aktarım
gerekçesinin yerine geçmiyor.

## Bilimsel dayanak ve sınır

Menon ve arkadaşlarının 2015 çalışması, ortak sınıf koşullu
karışım modeli altında sıralama/AUC optimizasyonunu incelemektedir.
Bu sonucun bizim kaynak koşullu hücre–ay takvimimize doğrudan
aktarılması gösterilmemiştir; sınırlı çift ölçüsü gerçek AP değildir.
[Birincil yöntem, bölüm 2 ve 3](https://proceedings.mlr.press/v37/menon15.pdf).

Jain, White ve Radivojac 2016, pozitif kümedeki hatayı modelleyen
iki karışımın ortak bileşenlerini, pozitifçe zenginleşmeyi ve oran
tanımlanabilirliği koşullarını açıklar. Hatalı pozitif bulunması
tek başına araştırmayı imkânsız yapmaz; algoritma bizim yangın
sınıfını veya bu varsayımları otomatik doğrulamaz.
[Birincil yöntem, bölüm 2 ve 3](https://proceedings.neurips.cc/paper_files/paper/2016/file/79a49b3e3762632813f9e35f4ba53d6c-Paper.pdf).

Yukarıdakiler evrensel gerekli koşullar veya bütün PU yollarının
reddi olarak kullanılmıyor. Bizim çıkarımımız, mevcut deneyleri
koşullu ve keşif amaçlı raporlamanın mümkün; gerçek yangın riskine
aktarıldığını ilan etmenin ise şu an desteklenmemiş olduğudur.
23 Kasım'da yayıncı kimlikleri ve belirtilen yöntem bölümleri
yeniden okundu; yeni makale başarımı veya yöntem uygulaması yapılmadı.

## A — Önerilen: koşulları açık deneysel yöntemle prototipe geçiş

Araştırmacı bu yolu seçerse, bitirme araştırmasının mevcut deneysel
yöntemi S/U kaynak-bağlamı sıralaması olarak **çalışma yönü** kabul
edilir. Ana yangın sorusu korunur, ulaşılan kanıtın sınırı açık yazılır.
Bu, gerçek pozitifler veya ana yöntemin hedefe aktarımı doğrulandı
demek değildir. Birinci aşamanın teknik teslimi kapanmış olarak,
bilimsel açıklar ise devam eden araştırma koşulları olarak ayrılır.

Somut sonraki işler:

1. Mevcut hash'lerle araştırma veri sürümü ve deney listesi sabitlenir;
   S adayları, atamasız U ve eksiklikler ayrı kalır. Gerçek Y/L boşluğu korunur.
2. Yeni model aramadan mevcut kaliteye uyumlu dokuz modelin
   **geçmiş 2022 sonuçları için** incelenebilir karşılaştırma
   prototipi hazırlanır. Kaynak, tarih, özellik ve kaliteye geri gidilebilir.
3. İlk ekran modelin kaynak-bağlamı puanını veya inceleme sırasını
   gösterir; hesaplanamayanlar ayrı görünür. "Bu hafta yangın
   olasılığı yüksek", doğrulanmış risk renkleri veya canlı tahmin
   iddiası kurulmaz. Dokuz ayar korunur; üretim ayarı seçilmez.
4. Yöntem, bulgular, duyarlılık ve sınırlamalar teslim metnine taşınır.
   Ana yangın riskine ilişkin çıkarımın hangi ek kanıtı gerektirdiği belirtilir.

Yararı, hazır teknik veriden çalışan araştırma çıktısına geçmektir.
Sınırlaması, ilk hedefteki doğrulanmış 24 saatlik risk sisteminin
başarıyla tamamlandığı iddiasını desteklememesidir. Bu seçim ana
ürünün hedefini sessizce katalog tahminine çevirmeyecek; prototipin
gösterdiği şey açıkça ayrı adlandırılacak.

## B — Gerçek hedef kanıtı olmadan aşama geçişi yapmamak

Veri ve modeller korunur; yeni olay/örtü, seçim/gürültü ve değerlendirme
dayanağını geliştirecek açık kaynak kanıtına odaklanılır. Yeni kurumsal
yazışma tercih dışı kalır. Kullanılabilir bağımsız kanıtın ne zaman
bulunacağı bilinmediğinden tamamlanma tarihi verilemez. Yöntem ve
sonuç yazımı yine ilerleyebilir; prototip aşamasına geçilmiş sayılmaz.

## Her iki seçenekte korunan sınırlar

- 2023 kalibrasyon, 2024 karşılaştırma ve 2025 kapalı final değerleri açılmaz.
- Gerçek Y/L, negatif etiket veya eksik değere sıfır üretilmez.
- A seçimi yeni model eğitimi veya olasılık kalibrasyonu açmaz.
- Nihai etiketli birleştirmeden önce ayrı güncel parça denetimi ve
  rapor kimliğine bağlı kullanıcı onayı gerekir; burada böyle bir makbuz yok.
- Tahmini 1 Ocak teslimi için garanti veya doğrulanmış risk başarımı vaat edilmez.

Karar, hazır veri paketinin tekrar hazırlanması için değil;
**hangi bilimsel iddia ve prototip kapsamıyla ilerleyeceğimizi**
belirlemek içindir. Önceki A yalnız inceleme paketini kapsamıştı.
