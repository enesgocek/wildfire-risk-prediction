# Yerel araştırma prototipi — geçmiş 2022 sonuç incelemesi

23 Kasım 2026. Araştırmacı **A: koşullu araştırma prototipine geç**
yönünü açıkça seçti. [Yöntem/teslim önerisi](RESEARCH_TRANSITION_DECISION_2026-11-23.md)
bu kararla uygulandı; `configs/research_prototype_direction_v1.json`
kararı ve sınırlarını ayrı kaydeder. Ana 24 saatlik yangın sorusu
korunur; kaynak-bağlamı skorunun gerçek yangın riskine aktarımı
doğrulanmış sayılmaz. Yeni model veya tahmin işi çalıştırılmadı.

## Açılış ve somut kullanım

Yerelde şu dosya kendi tarayıcında açılır:
`outputs/reports/dataset/historical_research_prototype_v1/20261123T144811Z_555ee371/inceleme.html`.
HTML ile üç JS dosyası aynı klasörde kalmalı; kurulum, giriş veya
ağ bağlantısı gerekmez. Bunlar çalışma alanındaki çıktılardır;
ham/ara veri ve bu payload GitHub'a gönderilmez.

İlk ayar 1.000 m / 24 saat görünümüdür; üretim ayarı seçimi değildir.
Filtreler temizken beklenen kartlar:

| Takvim | Kayıt | Ana kalite kuralında puanlanan | Kaynak/aday bağlamı | Hücre |
|---|---:|---:|---:|---:|
| Dört il | 6.573 | 4.841 | 225 | 185 |
| Ayrı Mersin | 2.383 | 1.929 | 81 | 68 |

Dokuz ayardan biri, il alanı, hücre, tarih, girdi uygunluğu ve
kaynak bağlamı seçilebilir. Aday olmayan gün "yangın yok" değildir.
Sayfalı tabloda satır seçimi şu bilgileri açar:

- Aynı hücre ve ayın tam alan meteorolojisine ve tam 15 dinamik
  girdiye sahip günleri için üç modelin sıra karşılaştırması.
- Seçili kaydın meteoroloji alan desteği ve 30/60 günlük bitki
  örtüsü eksikliği; destek uygun değilse puanın hesaplanmama nedeni.
- Dokuz ayarın aynı kayıttaki ham skorları ve kaynak üyelik bağlamı.
- Birimleriyle 27 özellik ve özgün özellik/üyelik CSV veri satırı.

Örnek: alan desteği %3,5 olan dolu meteoroloji kaydı silinmez;
ana kural tam alan istediği için yeni model puanı gösterilmez.
Bu alan yüzdesi yangın olasılığı değildir. Grafik yalnız ana
kaliteye uygun günleri kullanır; kaynak filtresini daraltmak sıra
hesabının paydasını değiştirmez. 1. sıra aynı hücre–aydaki daha
yüksek **kaynak-bağlamı** puanıdır; bütün ilde veya farklı
modeller arasında karşılaştırılabilir bir risk oranı değildir.

## Veri ve kapsam

İki kohort 8.956 üyelik, 245 ortak anahtar ve 8.711 farklı
hücre–gün içerir. Özellikler ve kaliteye uyumlu model sonuçları
[önceki denetlenmiş çıktılardan](DATASET_SUPPORT_AND_WEATHER_REVIEW_2026-11-23.md)
kopyalandı. Yalnız geçmiş 2022 değerleri kullanıldı. Model
dosyaları tarayıcıya taşınmadı; prototip yeniden tahmin üretmez.
Yaklaşık 10,9 MB veri JS dosyası yerel kalır.

Gerçek Y ve kabul edilmiş L boş; günlük gözlem durumu unknown,
negatif etiket izni false. Bilinmeyen veya hesaplanamayan gün
yeşil/düşük risk yapılmadı. Risk renkleri, olasılık yüzdesi,
"bu hafta yangın olasılığı yüksek" veya canlı tahmin iddiası yok.
2023 kalibrasyon, 2024 karşılaştırma ve 2025 final açılmadı.

A seçimiyle teknik deneysel veri teslimi tamamlanmış çalışma
olarak ayrıldı ve prototip hazırlığına geçildi. Birinci aşamanın
üç bilimsel koşulu ve nihai etiketli birleştirme kapısı açık.
Bu prototip ana yangın riski hedefinin başarıyla tamamlanması değildir.

## Gerçekte yapılan kontroller

İki Python prototip koruma testi ve yedi Node testi geçti.
Önceki kapsam/kalite çalışmalarındaki 63 Python testiyle toplam
65 farklı ilgili Python testi vardır; hepsi bu devamda çalıştırıldı,
farklı komutların ortak testleri tekrar sayılmadı. JavaScript
kaynakları ayrıca sözdizimi kontrolünden geçti.

Ayrı okuyucu payload'daki **8.956 üyeliği, 241.812 skor değerini,
241.812 özellik değerini**, kalite alanlarını ve kaynak satırlarını
dosyalardan geri hesaplamadan birebir eşleştirdi. HTML kimlikleri,
JS'nin statik DOM başvuruları ve ağ bağlantısını kapatan CSP
kontrol edildi. Gerçek payload ile iki takvimin filtre sayımları,
eksiklerin null kalması, eşit sıralar ve filtre değişiminin yanlış
şekilde ay içi sıraları değiştirmemesi sınandı.

**Doğrulama sınırı:** tarayıcıda render ve gerçek kullanıcı
kullanılabilirliği bu otomatik kontrollerle doğrulanmış sayılmadı.
Önceki yerel dosya erişim reddi alternatif tarayıcı/localhost
sunucusuyla aşılmadı. Araştırmacıya yeni prototipteki sayım,
grafik ve özellik ayrıntısını kontrol etmesi soruldu; bu metin
yazılırken yanıt bekleniyor. Eski v2 ekran onayı bu yeni ekranın
onayı olarak kullanılmadı. Sites becerisinin yerel depo akışı
kullanıldı; barındırma, yeni Site veya dış veri yüklemesi yapılmadı.

## Tekrarlanabilirlik

Üretici `scripts/quality/build_research_prototype.py`; veri denetimi
`audit_research_prototype.py`; kalıcı gerçek Node test makbuzu
`close_research_prototype.py`. Ekran kaynakları aynı dizindeki
`research_prototype_template.html`, `research_prototype_core.js`,
`research_prototype_app.js`; davranış testleri `tests/js/` altındadır.

| Makbuz | `outputs/reports/dataset/` altındaki dizin | SHA-256 |
|---|---|---|
| Üretim | `historical_research_prototype_v1/20261123T144811Z_555ee371` | `37b544bd96a9cd74ef5cb4ec30185bb401363bfae5b9acf3caded4008204e6ea` |
| Ayrı veri/DOM denetimi | `historical_research_prototype_audit_v1/20261123T145102Z_d2d682ba` | `90899ccd6c960125033448b5c82077d318a56dfe506ad8c1821c0ee2575edabc` |
| Gerçek Node mantık testleri | `historical_research_prototype_logic_v1/20261123T145137Z_c68e784a` | `790b254519e8eaf6c5e6c50b89d088cb99f51055d4114db5bb6adde05faafc6a` |

Hash'ler ilgili `readback.json` dosyasına aittir. Bilimsel veri ve
skorlar değiştirilmedi; görüntüleme dosyaları ayrı sürümde tutuldu.
