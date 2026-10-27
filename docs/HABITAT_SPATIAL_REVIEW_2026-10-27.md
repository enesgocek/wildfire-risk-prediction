# Hücre ve tespit alanı örtüsünün ayrılması — 27 Ekim 2026

## Sonuç ve araştırmacı kararı

2018–2023 eğitim dönemi içinden önceden seçilmiş 25 ilk tespit noktası,
21 hücre-gün inceleme birimi ve 20 farklı grid üzerinde mevcut 2017
örtü ölçüleri karşılaştırıldı. Hücrede orman/çalılık bulunması, ilişkili
tespitin aynı örtü üzerinde bulunduğunu göstermiyor: 21 birimin 8'inde
hücrede kesişim varken hiçbir ilişkili yaklaşık tespit alanında kesişim yok.
Bu amaçlı örneklem tüm veri setinin hata oranını ölçmez.

Araştırmacı iki ayrı kontrol tasarımını kabul etti:

1. Risk hesaplanacak hücrelerin orman/çalılık kapsamı değerlendirilecek.
2. Her yangın adayının ilk tespit noktalarındaki yerel örtü ayrıca
   değerlendirilecek. Belirsiz adaylar korunacak.

Bu karar oran eşiği, otomatik dışlama, yangın etiketi veya nihai birleştirme
onayı değildir. Sürümlü kayıt:
[`habitat_spatial_review_design_v1.json`](../configs/habitat_spatial_review_design_v1.json).

## Ölçülen fark

| Eski haritaya uygulanan tanımlayıcı kontrol | Nokta sayısı / 25 | En az bir ilgili noktası bulunan birim / 21 |
|---|---:|---:|
| Tespit merkezi orman/çalılık sınıfında | 4 | 4 |
| Yaklaşık tespit alanında herhangi bir orman/çalılık kesişimi | 13 | 13 |
| Yaklaşık tespit alanının en az yarısı orman/çalılık | 4 | 4 |

Hücrelerin çalışma alanıyla kesişen haritalanmış kısmında herhangi bir
orman/çalılık payı bulunan birim sayısı **21/21**, payı en az %50 olan
birim sayısı **5/21**. Bunlar aynı sorunun eşdeğer cevapları değildir.
`>0` kesişim ve `>=0,5` çoğunluk, farkı göstermek için tanımlayıcı
kesimlerdir; bilimsel kabul eşiği olarak seçilmedi veya optimize edilmedi.

Paydalar açıkça ayrıldı:

- Merkez sınıfı tek konumun 2017 harita sınıfıdır; alan oranı değildir.
- Tespit alanı paydası yaklaşık native piksel desteğinin tamamıdır.
  Bu alan gerçek yangın sınırı veya kesin resmî piksel köşeleri değildir.
- Hücre oranının paydası gridin dört illik çalışma alanıyla kesişen
  haritalanmış kısmıdır. Her durumda tam 25 km² kabul edilmez.

## Somut örnekler

| Örnek | Merkez sınıfı (2017) | Yaklaşık tespit alanında orman/çalılık | Hücrenin haritalanmış çalışma alanı kısmında orman/çalılık |
|---|---|---:|---:|
| C | Orman | %100,00 | %89,78 |
| R03 | Otsu örtü | %29,87 | %68,20 |
| R11 | Tarım | %20,87 | %43,34 |
| R15 | Otsu sulak alan | %0,00 | %21,28 |
| R16 | Tarım | %0,00 | %21,28 |
| R08 | Otsu örtü | %5,07 | %58,53 |
| R09 / R10 | Tarım / otsu örtü | Her ikisi %0,00 | %58,53 |

R15/R16 aynı hücre-gün birimidir; iki bağımsız olay sayılmaz.
R08/R09/R10 da ortak birimde bulunur. Bu birimde yalnız R08'in yaklaşık
alanında kesişim vardır. En az bir noktasında kesişim olan birim sayısı
13, bütün noktalarında kesişim olan birim sayısı 12'dir. Bir noktadan
diğerlerine örtü kabulü taşınmamalı; bütün ilk noktalar kimlikleriyle
korunmalıdır. Bu birliktelik fiziksel olay kimliğini de kanıtlamaz.

E/F'nin eski haritada yüksek orman/çalılık payı taşımasına rağmen insan
ön incelemesinde tarla benzeri görülmesi, yalnız oran büyüklüğünün doğal
örtü kabulüne yetmediğini gösteren bir inceleme çelişkisidir. Hangi kaynağın
doğru olduğu bu çalışmada belirlenmedi. Görsel ön yorumlar bağımsız
gerçeklik verisi yapılmadı; harita yaşı ve odunsu tarım ayrımı açık kaldı.

## Kontrol ve kabul sınırı

Yedi kaynak/kod kimliği işlem öncesi/sonrası doğrulandı. 25 tekil nokta,
21 birim ve 20 grid ayrımı, nokta–birim üyelikleri, boş hedefler ve kapalı
kabul alanları kontrol edildi. Tespit alanı payları alan değerlerinden
yeniden hesaplandı; hücre çoğunluk sayısı ve sekiz uyuşmazlık kaynak
tablolarından ayrı bir hesapla uzlaştırıldı. JSON geri okuması ve yeni
betiğin lint/format kontrolü geçti. Eski bilimsel test sayıları bu
çalışmanın testi olarak kullanılmadı. Üretim veya bulut kuyruğu açılmadı.

Çıktı dizini:
`outputs/reports/dataset/habitat_spatial_comparison_v1/20261027T185016Z_8d78e5a8/`.

- `readback.json` SHA-256: `5a6de697874a697f7bc37afa7c2d6ddab478edf0d06934a9b2acd7b4fa397288`.
- `decision_and_audit.json` SHA-256: `88e0aeaa80af5172b6ef2e18cf9ec6d1b605f28b3330e6aa7eea508900125eb0`.
- Tasarım ayarı SHA-256: `e7ebdbc621aa6e2fc5945db0f86c0c0fc5aa2240fb9ca12c11d14a4dbde4f5f9`.

Veri setine katkı: hücre uygunluğu ile olay adayının yerel örtüsünü
birbirinin yerine koyan etiketleme hatası için somut kontrol tanımlandı.
İlk habitat iş paketi henüz kapanmadı. Sıradaki iş, her kontrolün ihtiyaç
duyduğu zamana uygun örtü kanıtını ve belirsizlik işlemini somutlaştırmak,
ardından kapsam etkisini eğitim adayları üzerinde değerlendirmektir.
Oran eşikleri, harita güncelliği ve yeni/devam eden olay ayrımı çözülmeden
bu tanımlayıcı karşılaştırma otomatik eğitim filtresine dönüşmeyecek.
