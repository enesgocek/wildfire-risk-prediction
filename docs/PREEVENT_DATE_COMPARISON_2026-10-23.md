# Altı belirsiz noktada olay öncesi tarih karşılaştırması

23 Ekim 2026. Bu çalışma örtü incelemesidir; yangın etiketi, bağımsız olay
doğrulaması veya nihai veri seti kabulü değildir.

## Amaç ve sabit seçim

[Önceki 25 noktalık incelemede](PREEVENT_IMAGE_REVIEW_2026-10-23.md)
yaklaşık piksel alanında SCL bulut/sirüs sınıfı bulunan altı nokta seçildi.
Her biri için önceki 60 günlük donmuş envanterden iki farklı UTC edinim
günü alındı. İlk görüntünün günü ve aynı günün başka ürünleri dışarıda
tutuldu. Sıra sahne bulut yüzdesi, yakın tarih, görüntü kimliğidir.
Yerel yeni kalite ölçümleri seçimde kullanılmadı; 12 işlik plan ilk varlık
okumasından önce kaydedildi. Sonuçlara göre görüntü değiştirip arama
genişletilmedi. Bu amaçlı örneklem bütün veriyi temsil etmez.

12 yeni tarih için 24 küçük TCI/SCL kesiti okundu; altı ilk görüntüyle
birlikte 18 nokta-tarih karşılaştırıldı. Altı kartta bütün tarihler gösterilir.
Yeni sıkıştırılmış TIFF dosyaları toplam 920.252 bayttır; ağ aktarım
miktarı ölçülmedi. Büyük sahne indirmesi veya bulut üretim işi başlatılmadı.

## Ölçülen sonuç

Oranlar yaklaşık alan içinde merkezi bulunan 20 m SCL piksellerinin
sayımına dayanır. Tam alan kesişim yüzdesi veya gerçek bulut doğruluğu
değildir. Bu altı noktada her noktanın üç tarihindeki payda aynı kaldı.

| Nokta | SCL pikseli | İlk tarih / bulut-sirüs % | Alternatif 1 / % | Alternatif 2 / % |
|---|---:|---|---|---|
| SNPP_815579_4958 (önceki A) | 420 | 2018-04-23 / 13,10 | 2018-04-13 / 9,05 | 2018-05-13 / 17,14 |
| N20_815590_33890 | 513 | 2018-09-20 / 0,19 | 2018-11-04 / 0,19 | 2018-09-25 / 0,39 |
| SNPP_815579_128015 | 1.108 | 2021-04-12 / 28,43 | 2021-05-12 / 34,66 | 2021-04-02 / 32,13 |
| SNPP_815579_160544 | 439 | 2021-10-29 / 12,53 | 2021-10-24 / 16,86 | 2021-09-19 / 19,13 |
| N20_815590_159829 | 1.102 | 2021-10-29 / 0,09 | 2021-10-19 / 0,00 | 2021-09-19 / 0,00 |
| N20_815590_200133 | 911 | 2023-03-27 / 62,35 | 2023-04-03 / 0,00 | 2023-05-01 / 0,00 |

İki noktada iki alternatifte de bulut/sirüs sayımı sıfırdır; diğer dört
noktada sıfır değildir. Bu, iki noktanın kabul edildiği anlamına gelmez:
N20_815590_159829'da koyu/gölge sınıfı ilk tarihte %49,18, alternatiflerde
%33,94 ve %34,21'dir; sınıflanmamış payları %12,89 / %14,25 / %18,69'dur.
İlk alternatifte ayrıca %9,80 bulut gölgesi sınıfı vardır.

N20_815590_200133'ün iki alternatifinde bulut/sirüs, bulut gölgesi,
koyu/gölge, sınıflanmamış, veri yok/kusurlu ve kar/buz sayımları sıfırdır.
Bu örnekte ayrıntı görülebilirliği artmıştır; gerçek örtü türü otomatik
olarak kabul edilmemiştir. İlk sahne bulutu %13,70 iken alternatif
sahneler %16,08 ve %17,88'dir. Daha yüksek **sahne** bulutunun daha iyi
**yerel** inceleme sunabilmesi, yerel kontrolün gereğini somutlaştırır.

## Görsel yorum — asistan ön incelemesi

Altı kartın düzeni ve görüntüleri asistan tarafından incelendi. Aşağıdaki
yorumlar araştırmacının yeni teyidi veya bağımsız uzman doğrulaması değildir:

- Önceki A'da yol/yapılaşma çevresindeki parlak yüzey üç tarihte de aynı
  konumdadır. SCL işaretleri değişir. Kalıcı parlak yüzeyle karışma olasılığı
  vardır; yanlış bulut sınıfı olduğu kanıtlanmadı. Araştırmacının **belirsiz**
  ön notu korunur.
- SNPP_815579_128015'te kıyı, iskeleler, düzenli tesis yapıları ve dairesel
  yapılar üç tarihte de görülür. Endüstriyel çevre ön incelemesine uygundur;
  tesis kimliği, sıcak kaynağın nedeni veya yangın türü doğrulanmadı.
- SNPP_815579_160544'te uzun parlak yapılar ve yollar kalıcıdır.
  N20_815590_159829'da yapı çevresindeki koyu yüzey üç tarihte de vardır;
  bunun yanık alan olduğu sonucuna varılmadı.
- N20_815590_33890'da seyrek/çıplak görünümlü engebeli arazi ve kalıcı
  açık lekeler görülür; orman/çalı ayrımı kesinleştirilmedi.
- N20_815590_200133'ün alternatiflerinde yeşil alanlar, parseller ve
  düzenli parlak yüzeyler daha açık görülür; karışık örtü incelemesi gerekir.

[Önceki A'nın üç tarihi](../outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/SNPP_815579_4958.png),
[bulutlu ilk görüntünün alternatifleri](../outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/N20_815590_200133.png),
[kıyı/tesis çevresi](../outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/SNPP_815579_128015.png).

Kartlarda sarı sınır yaklaşık native piksel desteğidir, yangın sınırı değildir.
TCI ve SCL yalnız gösterimde ilk görüntünün 10 m gridine en yakın komşuyla
taşındı; SCL ölçümleri özgün 20 m gridde yapıldı. Bu işlem SCL'nin gerçek
çözünürlüğünü yükseltmez ve hassas görüntü eş-kaydı kanıtı değildir.
Kısa renk notundaki bulut grisi açık gridir (`#cccccc`); orta gri
(`#999999`) **sınıflanmamış**, çok koyu gri (`#333333`) **koyu/gölge**,
kahverengi bulut gölgesi, mavi sudur. Yeşil sınıf orman/tarım ayrımı yapmaz.

## Doğrulama ve izlenebilirlik

Çıktı: `outputs/reports/dataset/preevent_date_comparison_v1/20261023T154219Z_144befb7/`.
Readback SHA-256:
`f50778b9bd1a344c35336273fb46d19258481dc50676a692682e8772bd8b468d`.

143 girdi ve 45 çıktı hash'i yeniden doğrulandı. 18 nokta-tarihin tamamında
SCL sayımları diskten ayrı işlemle tekrar hesaplandı; tablo/makbuzla eşit.
TCI veri maskesi yaklaşık destek içindeki bütün merkezlerde geçerli.
Üç farklı UTC günü, aynı nokta paydası ve kapalı etiket alanları doğrulandı.
Bu, 18 görüntünün gerçek atmosfer/örtü doğruluğunu kanıtlamaz.

Ek denetim: `outputs/reports/dataset/preevent_date_comparison_audit_v1/20261023T154357Z_ba87b759/readback.json`.
SHA-256: `d272add3e786ce13b797c2a4f7b95eb3f313a2c73d094fa44e472576c9a6dc66`.
14 yeni davranış vakası dahil **65 ilgili test** geçti: aynı gün tekrarları,
önceki tarih, sıralama, eksik kapsam/varlık, kapalı final dönem, izinli
varlık erişimi, mevcut kalite ve etiket/birleştirme kapıları. Dört yeni
Python dosyasında lint/format denetimi yapıldı.

12 alternatifin yedisinin işlenmiş ürünü T sonrasında üretilmiştir.
Hiçbiri tarihsel erişilebilir model girdisi olarak kabul edilmedi.
Görüntülerin edinim tarihleri T öncesindedir; kullanım geriye dönük örtü
incelemesidir. 2024/2025 açılmadı; eğitim yapılmadı.

## Veri setine katkı ve sonraki karar

Tek sahne bulutu veya tek SCL sınıfıyla örtü uygunluğu verme yaklaşımının
bu örneklerde güvenilir bir kabul kuralı olmadığı somutlaştı. İki noktada
alternatif görünüm sağlandı; dördünde tekrar eden işaretler korunuyor.
Üç eski araştırmacı notu değişmedi; kalan 22 nokta insan tarafından
incelenmiş sayılmadı. `daily_observation_status=unknown`, pozitif/negatif
etiket kapalıdır; otomatik silme ve nihai birleşme yoktur.

Sonraki adım, bu görsel bağlamı mevcut olay adaylarıyla aynı inceleme
tablosunda tutarak orman/çalılık, tarım/yapılaşma ve belirsiz örneklerin
hangi gerekçeyle değerlendirileceğini somut protokole dönüştürmektir.
Kalıcı tesis benzeri görünüm tek başına olayı dışlamaz. Yeni 0/1 etiketi
için olay gruplaması, yeterli gözlem ve olay kanıtı açık kalmaktadır.
