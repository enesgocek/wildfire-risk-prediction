# Yaklaşık tespit alanlarında CORINE örtüsü — 4 Kasım 2026

## Tamamlanan işlem

Önceden dondurulan 25 ilk tespit noktası / 21 hücre-gün biriminin
yaklaşık alanları CORINE 2018 sınıflarıyla kesiştirildi. Alanlar yeni
yangın sınırları değildir: native merkez ve scan/track tabanlı önceki
yaklaşım korunmuştur; resmî piksel köşesi kabulü yoktur.

Kaynak geometri EPSG:6933'ten rasterın doğrulanmış eski ETRS89/LAEA
tanımına dönüştürüldü. Kenarlar 25 m ve 12,5 m aralıklarla yoğunlaştırılıp
sınıf alanlarının yakınsaması sınandı. Her 100 m raster karesinin alanla
kesişimi hesaplandı; yalnız piksel merkezleri sayılmadı ve kategorik
harita interpolasyonu yapılmadı. Payda bütün yaklaşık tespit alanıdır;
eksik alan ayrıca tutulur. Tespit alanı ile 5 km risk hücresi aynı değildir.

## Sonuçlar ve paydalar

- **25/25** alanda geçerli CORINE sınıfları var; eksik alan yok.
- **17/25** alanda birden fazla harita sınıfı kesişiyor. Çok küçük
  kenar parçaları da korunur: R17'de 242 sınıfı yaklaşık 1,81 m²
  (%0,00070). Bu sayım 17 belirgin ekolojik karışım doğrulaması değildir.
- **4/25** alanda merkez sınıfı, en büyük alanı kaplayan sınıftan farklı:
  R03 (323 → 211), R12 (121 → 321), C (321 → 312), R19 (511 → 212).
  En büyük sınıf bir kabul eşiği olarak seçilmedi.
- 311/312/313/322/323/324 kodlarıyla kesişim **6/25** alanda var.
  Bu yalnız belirtilen harita kodlarının betimsel toplamıdır; doğal
  orman/çalılık kabulü veya diğer alanların doğal örtüsüzlüğü değildir.
- Örneklem amaçlı 2018–2023 incelemesidir; bağımsız yangın sayısı veya
  tüm verisetindeki örtü dağılımı olarak genellenmez.

| Kod | Yaklaşık alan içindeki CORINE payları | Yorum ve açık kalan konu |
|---|---|---|
| C | %77,98 iğne yapraklı orman (312), %22,02 doğal çayır (321) | Merkez çayırda, alanın çoğu haritada ormanda; önceki ağaçlık yorumu otomatik reddedilmez |
| D | %58,55 geçişli ağaçlık–çalılık (324), %22,31 mera (231), %19,15 meyvelik (222) | Karışık kullanım; 324 payı tek başına doğal orman doğrulaması değildir |
| E | %100 tarım + doğal örtü mozaiği (243) | Sınıfın içindeki doğal örtü oranı bilinmiyor; %100 tarım veya %0 doğal örtü denemez |
| F | %100 meyvelik/plantasyon (222) | Tarımsal ağaçlık bağlamı güçleniyor; olay tarihine aktarım ayrıca açık |
| R03 | %38,15 ekilebilir tarla (211), %24,86 karma tarım (242), %0,09 tarım/doğal mozaik (243), %36,90 sklerofil örtü (323) | Merkezdeki odunsu sınıf bütün alanı temsil etmiyor |
| R11 | %77,15 seyrek örtü (333), %18,69 geçişli ağaçlık–çalılık (324), %4,17 sklerofil örtü (323) | Açık/kuru görünüme rağmen haritada odunsu kesişimler var; kuraklık ölçümü değil |
| R15/R16 | Sırasıyla %97,61 / %81,50 iç bataklık (411); kalanı karma tarım (242) | Ortak hücre-gün ilişkisi korunuyor; iki bağımsız olay sayılmadı |

Yüzdeler yuvarlanmıştır; toplam 99,99/100,01 olabilir. E'deki mozaik ve
F'deki tarımsal ağaç sınıfı bu kaynağın kullanım ayrımına katkısını
gösteriyor. Kaynak 2017–2018 referanslı ve 25 ha asgari haritalama
birimlidir; sonraki olay tarihlerindeki gerçeği ve ince sınırları tek
başına doğrulamaz. Yangının bu alanın neresinde olduğu da bu hesapla bilinmez.

## Ayrı hesaplama ve görsel kontrol

Birincil hesap Shapely kare–poligon kesişimleridir. İkinci hesap,
aynı geometrilerde **exactextract** hücre kapsama algoritmasıyla yapıldı.
25 kimlik ve sınıf listesi eşleşti. En büyük sınıf payı farkı
**1,98 × 10⁻⁹**, toplam alan farkı **0,001575 m²**; önceden betikteki
1 × 10⁻⁶ göreli tolerans koşulları sağlandı. Bu sayısal uyum iki
bağımsız arazi doğrulaması değildir; aynı harita/geometri kullanılmıştır.

25 m/12,5 m kenar kontrolünde en büyük toplam pay farkı
**2,60 × 10⁻⁸**; iki eş alan projeksiyonundaki alanların en büyük
göreli farkı **4,21 × 10⁻¹⁰**. Sınıf alanlarının toplamı poligon alanıyla
uzlaştırıldı. Girdi kimlikleri, çıktı hash'i ve JSON geri okumaları
korundu; iki yeni betikte lint/format geçti.

Altı örneğin görseli hazırlandı ve asistan tarafından kontrol edildi:
siyah çizgi yaklaşık tespit alanı, mavi çarpı native tespit merkezidir.
Renkler paket legend'inden gelir; üst etiketlerde CORINE kodu ve alan
payı vardır. Paneller sabit ortak ölçek karşılaştırması olarak sunulmaz.
[Altı alanın görseli](../outputs/reports/dataset/corine_support_verification_v1/20261103T214408Z_8d199d94/six_supports.png).
İlk görselin panel aralığı iyileştirilerek yeni sürüm üretildi; ilk çıktı korunmuştur.

## Kanıtlar ve sonraki adım

- Alan hesabı: `outputs/reports/dataset/corine_support_review_v1/20261103T214155Z_635f0789/readback.json`.
  SHA `20fcc8abd28f541c60fbba7c4dbc9ade10dcf66b976d63ddbfaf33954fd87230`.
  Çalışma öncesi/sonrası 14 kaynak/kod hash'i doğrulandı.
- Ayrı algoritma ve güncel görsel: `outputs/reports/dataset/corine_support_verification_v1/20261103T214408Z_8d199d94/readback.json`.
  SHA `a752caca18482d60b60cfac31def617137cae30bdd11c977a0cb86f318c887df`.
  17 kaynak/kod kimliği kontrol edildi; görsel kimliği bu makbuzdadır.
- Dizin tarihleri UTC, çalışma tarihi Türkiye saatiyle 4 Kasım'dır.

Gözlem unknown, etiketler boş, kabul/dışlama ve nihai birleştirme
kapıları kapalıdır. Önceki insan ön notları 10/25 olarak korunur;
bu yeni sayısal/görsel kontrol yeni insan değerlendirmesi sayılmaz.
Yeni ağ/bulut işi veya 2024/2025 veri erişimi yapılmadı.

Sonraki yöntem adımı, merkez/alan uyuşmazlıkları ve tarım/doğal mozaikler
için bu ölçüleri olay öncesi görüntüler ve haritanın yaşıyla birlikte
karar tablosuna taşımaktır. Araştırmacıya sunulacak kabul/belirsizlik
seçenekleri hücre kapsamı ile aday yerel örtüsünü ayrı tutmalıdır;
tek yüzdeye dayalı otomatik kabul veya dışlama henüz gerekçelendirilmedi.
