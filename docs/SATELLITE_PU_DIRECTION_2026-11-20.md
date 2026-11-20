# Dört il için uydu adaylarına dayalı PU yönü — 20 Kasım 2026

## Aynı gün sonraki A kararı

Araştırmacı **A: dört ilde uydu adaylarıyla PU protokolünü hazırla**
yönünü seçti. [Yeni sürümlü karar](../configs/satellite_noisy_pu_protocol_v1.json)
yalnız protokol/yerel çevrimdışı incelemeyi yetkilendiriyor. Aşağıdaki
karar bekleyen açıklamalar öneri aşamasının tarihsel kaydıdır.
Ana 24 saatlik yeni orman/çalılık yangını riski hedefi korundu; yeni
L/Y, model eğitimi veya nihai birleştirme izni verilmedi. Aynı 2.048
U ve WF1538 kararı korunuyor. Şimdi sabit fit kaynağının başlangıç
geçmişi, dokuz mevcut ayarda ve aynı kaynak satırlarında incelenecek.

## Yapılan hazırlık: mevcut adayların aynı veri rolüne alınması

Araştırmacının ana 24 saatlik yangın hedefini ve göreli risk sunumunu
koruyarak, Mersin kaynak merkezlerinin dışındaki öğrenme girdileri
somutlaştırıldı. Yeni ham uydu indirmesi, yeni gruplama, etiket veya
model yok. 22 Ekim'deki dokuz ayarlı aday envanteri değişmeden kullanıldı;
eski sayım bugünün yeni yangın bulgusu yapılmadı.

| Aynı envanterin rol hesabı | Farklı aday hücre–gün |
|---|---:|
| Eski 2018–2023 birleşimi | 7.610 |
| 2018–2022 ve sağ ucu 2023'e değmeyen fit-rolü hazırlığı | **6.514** |
| 31 Aralık 2022 sınırı, özgün dosyada korunan | 4 |
| 2023 kalibrasyon rolü; zaman metadata'sı dışında incelenmeyen | 1.092 |

6.514 anahtarın 4.459'unda dokuz ayarın varlık/ilk zaman/üyelik tanısı
aynı; 804'ünde aday var ama ilk zaman/üyelik duyarlı, 1.251'inde aday
varlığı ayara bağlı. Eşitlik doğruluk veya dokuz bağımsız kanıt değil.
**Hiçbiri gerçek yeni yangın etiketi veya kabul edilmiş L yapılmadı.**
Su kuralını geçen 2.889 hücrenin dışında bu fit kesitinde anahtar yok.
Yeni bir asgari orman yüzdesi uygulanmadı; yerel olay örtüsü ayrı açık.

| İl alanıyla kesişen anahtarlar | Sayı |
|---|---:|
| Antalya | 1.409 |
| İzmir | 2.355 |
| Mersin | 2.225 |
| Muğla | 577 |

İl alanları hücre AOI kesişimine dayanır. Sınırda 52 ek il üyeliği
bulunduğu için bu sütun 6.514'e toplanmaz; bağımsız olay sayısı değildir.
Her ilde 2018–2022'nin beş yılından aday var; bu, gerçek olayların tam
kapsandığı veya her alt grupta öğrenme yeterliliği olduğu anlamına gelmez.

## U ile iki örtüşme: kayıtları koruma kontrolü

Özgün 2.048 U anahtarının **ikisi**, bu envanterdeki bir aday anahtarıyla
eşleşti. İki U satırı özgün sırası, örnekleme olasılığı/ağırlığı, boş
hedefi ve `unknown` durumuyla aynen korundu. Geri kalan 2.046 satırın
negatif olduğu veya adaylarla eşleşen ikisinin gerçek pozitif olduğu
sonucu çıkarılmadı. Bu iki eşleşme sınıf oranı, yakalama oranı veya hata
oranı tahmini değildir. İleride L/U kullanılırsa aynı hücre-günün iki
edinim yolunda bulunması gizlice silinemez; protokolde açık temsil edilir.

## Literatürün sağladığı dayanak ve sağlamadığı sonuç

Önceki literatür sicilindeki **R22**, yeni çalışma bulunmuş gibi
sunulmadan yöntem açısından yeniden okundu. Shirazi, Wang ve Bondur
(2021), MODIS yangın konumları ile belirsiz hücreleri kullanarak PU
temelli yangına uygun koşul modellemesi yapıyor. Yöntem ayrıca
öngörülen güvenilir negatifleri üretip etiketliyor. Bu çalışma uydu
adaylarının öğrenmede kullanılması için bir örnek; bizim konum/olay,
gözlem veya seçilme sorunlarımızın çözüldüğü kanıtı değil. Bizde
otomatik negatif üretimine geçilmedi. Makalenin çok günlük tasarımı
ve olay gününü kullanan örnek seçimi, bizim T'den önceki girdilerle
sonraki 24 saat sözleşmemize doğrudan kopyalanmayacak.
[Birincil yayınevi yöntemi, Tablo 1 ve ilgili bölümler](https://www.frontiersin.org/journals/earth-science/articles/10.3389/feart.2021.622307/full).

Aşağıdaki tasarım **proje önerisidir**, makalenin uygulandığı veya
projenin varsayımlarını doğruladığı iddiası değil. Hata içeren L/U
karışımı ve sıralama için önceki Menon/Jain incelemelerinin koşulları
korunuyor; yeni negatif etiketi veya ölçülmemiş hata oranı eklenmiyor.

## İnsan kararı gerektiren yeni yöntem yönü

**A — Uydu adaylarını hata içerebilen pozitif üyelik yönü olarak ele
alan dört il PU pilot protokolünü hazırlamak (öneri).** Ana hedef
sonraki 24 saatte yeni orman/çalılık yangını risk sıralaması olarak
korunur. Uydu adayları hedefin kendisi veya kusursuz Y=1 yapılmadan,
gürültülü/zayıf öğrenme girdisi olarak incelenir. Mersin ve diğer açık
olay kaynakları yardımcı bağlam olarak kalır; dört ilde yalnız Mersin
merkezlerini pozitif, diğer illeri negatif gibi kullanma yapılmaz.

Somut sonraki protokol işleri:

1. Önbellekteki geriye dönük bağlı bileşen ilk anahtarlarını doğrudan
   L saymak yerine, daha önce seçilen başlangıç geçmişini koruyan
   izlemeyle sonraki birleşmelerin başlangıcı değiştirmesini engellemek.
   Aynı ilk andaki bütün hücreler ortak aday kimliğiyle korunacak.
2. Örtü, tarımsal/tekrarlayan sıcak kaynak, yeniden görünme, dönem
   sınırı ve parametre duyarlılığını açık üyelik/belirsizlik alanlarıyla
   taşımak; bütün 6.514 anahtarı otomatik kabul veya yalnız kararlı
   olanları gerçek yangın seçme yapılmayacak.
3. Kaynak seçilmesi ve hatalı pozitiflere ilişkin desteklenen/varsayılan
   koşulları, özellik zamanlarını, U/L örtüşmesini ve gerçek hedef
   değerlendirmesi ile yardımcı katalog değerlendirmesini ayıran
   sınırlı, uygulanabilir pilot dosyası hazırlamak.

**Yarar:** aynı uydu edinim hattıyla dört ilde gerçek mevcut adaylara
dayanır; uygun öğrenme hazırlığı yalnız Mersin kayıt merkezlerine bağlı
kalmaz. **Sınır:** uydu kaçırması, tarım/yayılma ve seçilme yanlılığı
ortadan kalkmaz; gerçek yangın sıralama başarısı otomatik kazanılmaz.
Yöntem uygun çıkmazsa bu durum kaydedilir. Veri varlığı bilimsel kabul
veya eğitime hazır olma iddiası değildir.

**B — Mevcut bağımsız kaynak merkezleri yönünde kalmak.** 374 Mersin
anahtarı ve önceki olası L önerileri korunur; uydu adaylarına genel
L protokolü hazırlanmaz. Kaynak konum/saat ve kapsam soruları açık
kaldığı için dört ilde genişleme mevcut dayanakla sınırlı kalabilir.
Bu seçenek yeni kurumsal yazışmayı otomatik başlatmaz.

A tercihi gerçek hedefi “katalogda yeni kayıt var/yok” hedefine
değiştirmek, bütün adayları gerçek yangın saymak veya aynı uyduyla
ölçülen yardımcı başarımı bağımsız yangın AP'si yapmak anlamına
gelmez. Araştırmacı yönü henüz seçmedi. **Bu soru protokol ve çevrimdışı
hazırlık içindir; yeni model eğitimi, Y etiketi veya nihai birleştirme
onayı değildir.** Asıl hedef ve bu sınır değişecekse ayrıca sorulacak.

## Kayıt ve kontroller

Komut `scripts/quality/prepare_satellite_pu_inventory.py`.
Çıktı `outputs/reports/dataset/satellite_PU_inventory_v1/20261120T002414Z_43a1dc31/`.
`readback.json` SHA-256
`a8c2666a4f36d54224078f2758904fcdfcede5642f12c86aa15df9ccfd0d4cef`.
Beş yeni davranış testi yıl rolü, sınır koruma, yinelenen anahtar,
etiket/saat reddi ve U bağlamının sessiz etiket olmamasını sınadı.
Son birleşik koşuda **233 ilgili test** ve sekiz Python dosyasının
Ruff/biçim kontrolü geçti; bütün depo testleri iddiası değil.
Standart CSV/datetime ile bütün 6.514 anahtar ve 2.048 özgün U
ayrıca uzlaştırıldı. İnceleme CSV'lerinde hem gerçek Y hem önerilen
zayıf pozitif üyeliği boş. Model, yeni grafik veya final erişimi yok.
İlk tanı çıktısı import düzeni kontrolünden önce üretildi; o sürümün
kodu yanında korundu. Kod düzeni kontrolünden sonra yeni kimlikle
üretilen yukarıdaki sonuç referans alındı; eski çıktılar değiştirilmedi.

Önceki kullanıcı UI bildirimi ayrı pakete bağlandı:
`PU_inspection_bundle_v1/20261120T001043Z_80623e41/researcher_ui_check.json`;
SHA-256 `c8bc2f92fb85839b7acf0f9fbb9662b168fadda4dbb9429edbc25762fd04388f`.
Bu yalnız 2.422/503 ekran sayımları ve satır ayrıntısı kontrolü;
buradaki yeni uydu PU yöntem yönünün onayı değildir.
