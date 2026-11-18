# Mersin kayıtlarında mevcut kanıt ve yeni tarihli görüntüler — 18 Kasım 2026

479 arşiv kaydı, daha önce incelenmiş üç Mersin vakası ve iki yerel
görüntü paketindeki 14 SCL kesitiyle karşılaştırıldı. Paketler Aydıncık
ve Anamur çalışmalarından geliyor. Bu sınırlı envanter bütün yerel
görüntü koleksiyonlarının kapsam denetimi değildir.

## Önceki kanıtın arşiv noktasına taşınması

Üç vakayla aynı gün görünen arşiv satırları aşağıda listelendi. Gün
eşitliği olay eşleşmesi için yeterli kabul edilmedi.

| Açık vaka | Aynı gün arşiv satırları | Açık konu |
|---|---|---|
| 15 Temmuz 2021 Aydıncık | WF1475, Gülnar orman işletme bölgesi | İdari yer adı ve olay noktası ilişkisi |
| 7 Eylül 2022 Gülnar | WF1578 Gülnar, WF1579 Silifke, WF1580 Bozyazı | Aynı günün üç satırı, başlangıç/yayılma ayrımı |
| 11 Temmuz 2023 Anamur | WF1638 Anamur, WF1639 Tarsus | Anamur ve Tarsus satırlarının olay kimliği |

14 yerel kesitin gerçek raster sınırları, arşiv noktaları ve edinim
zamanlarıyla kontrol edildi. Edinimin her iki saat yorumunda da tahmin
anından önceki 60 gün içinde olması arandı. Tarih ve nokta kapsamı
birlikte sağlanan arşiv kaydı bulunmadı. Eski kesitler, başka noktalardaki
önceki çalışmaların kanıtı olarak kalıyor. Bu sonuç uydu arşivinde
görüntü bulunmadığı iddiası sağlamaz.

Yerel makbuz
`outputs/reports/dataset/mersin_local_evidence_v1/20261118T144216Z_c9063478/readback.json`.
SHA-256 `ea8e7c5460e279fa18687e63447df8529438804d0fa692378492a9987acf8980`.

## İki arşiv koordinatında yeni görüntüler

Gülnar vakasının aynı saatli iki satırı WF1578 ve WF1579, önceki ortak
tabloya dayanarak seçildi. Birinin CORINE 2018 merkezi tarım, diğerinin
orman sınıfında. Kaynak bu iki koordinatın özgün başlangıç ve yayılma
rollerini doğrulamıyor. İnceleme iki ayrı yangın sayısı üretmiyor.

Mevcut kamuya açık Sentinel-2 okuyucusuyla, 7 Eylül 2022 00.00 UTC
öncesindeki 30 gün tarandı. Mevcut seçim yöntemiyle iki ayrı edinim
tarihi alındı. Her koordinat için 250 m inceleme çevresi kullanıldı.
İlk erişim ConnectionError verdi; izinli ağ erişimiyle yeniden deneme
sonucunda dört kesit okundu. Bulut tercihiyle seçilmiş bu iki tarih,
görüntü arşivinin tüm tarihlerini temsil etmiyor.

| Arşiv satırı | Görüntü tarihleri | Yerel SCL bulut/gölge/eksik veri işareti | Otomatik SCL bitkili piksel payı |
|---|---|---|---|
| WF1578 | 31 Ağustos ve 5 Eylül 2022 | İki tarihte de sıfır | %6,5 ve %11,2 |
| WF1579 | 31 Ağustos ve 5 Eylül 2022 | İki tarihte de sıfır | %3,7 ve %29,0 |

SCL bitkili sınıfı orman sınıflandırması sağlamaz. Bu payların görsel
orman oranı olarak yorumlanması uygun değildir. WF1579'un RGB dokusu
ile bu sınıf paylarının farkı, kalite bilgisini habitat kararıyla
karıştırmadan inceleme gereğini gösteriyor.

Görsel ön yorumda WF1578 çevresinde açık alan/yol ve ağaçlık parçalar,
WF1579 çevresinde daha yoğun odunsu doku görülüyor. Bu asistan ön
yorumudur. Araştırmacının görsel değerlendirmesi bekleniyor. Yayımlanan
koordinatın gerçek tutuşma konumunu temsil etmesi ayrıca açık.

Görsel
`outputs/reports/dataset/gulnar_reference_cover_v1/20261118T144358Z_356f9818/cover_review.png`.
İndirme makbuzu aynı dizindeki `readback.json`.
SHA-256 `f733f548278ec58aa8335edbd4c05191ecce49b6f9b3878219c75b0510f39a0e`.

## Kontrol ve devam koşulu

Sekiz RGB/SCL dosyasının hash'leri tekrar doğrulandı. Dört SCL kalite
hesabı kayıtlı arşiv koordinatlarında yeniden üretildi ve makbuzla eşleşti.
37 ilgili görüntü testi ve Ruff geçti. Gerçek yangın etiketi kabulü,
günlük gözlem kabulü veya nihai eğitim birleştirmesi yapılmadı.
Birinci aşama sürüyor. Görsel ön değerlendirmeden sonra örtü notları
mevcut olay kimliği belirsizliğiyle birlikte kaydedilecek.

Doğrulama makbuzu
`outputs/reports/dataset/gulnar_reference_verification_v1/20261118T144517Z_74b50758/readback.json`.
SHA-256 `b23c7784a6c2f2934460b84dc80e6759050b121bbd6b4fd124e050c7acdda74a`.
