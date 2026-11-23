# Deney verisinin kapsamı, eksiklikler ve meteoroloji kuralına uyum

23 Kasım 2026. Araştırmacının insan müdahalesi gerekene kadar
özerk devam talimatıyla, önceki sabit deneyin ardından birbirine
bağlı üç teknik iş tamamlandı. Yeni kaynak edinimi, bulut veya
2023–2025 bilimsel değeri kullanılmadı. Önceki dosyalar korunuyor.

## 1. Skorlar kaynak satırlarına bağlandı

İki mevcut 2022 takvimi ve dokuz ayarın eski/yeni skorları aynı
anahtarlarla ayrı inceleme çıktısına alındı. Yeni model tahmini
yapılmadı. Özellik, kohort üyeliği, eski dosya/satır yolu, ayar,
aday bağlamı ve skor birlikte takip edilebiliyor.

| Sayım birimi | Sonuç |
|---|---:|
| Dört il takvimi | 6.573 hücre–gün / 185 hücre |
| Ayrı Mersin takvimi | 2.383 hücre–gün / 68 hücre |
| İki takvimde ortak anahtar | 245 |
| Tekil özellik anahtarı | 8.711 |
| Ayrı tutulan kohort üyeliği | 8.956 |
| Dokuz ayarın skor inceleme satırı | 80.604 |

Ortak 245 anahtarın özellikleri, eksiklikleri dahil tam eşleşti;
değerler ortalanmadı. Kohort üyelikleri ve kaynak işaretleri
birleştirilmedi. Mersin'in 81 kaynak gününden dokuzu öbür takvimde
de bulunuyor; aynı fiziksel yangın oldukları çıkarılmadı. Bu iki
inceleme bağımsız veri evreni veya nüfus paneli değildir.

Dört ildeki 185 hücrenin ayara göre 88–101'i modelin öğrenme
satırlarında görülmüştü; 84–97'si görülmemişti. Mersin'in 68
hücresinde karşılıklar 22–26 ve 42–46. Bunlar yerel kimlik
örtüşmesi sayımlarıdır; görülmek tek başına sızıntı, görülmemek
bağımsız saha doğrulaması değildir. 2.889 hazırlık hücresinin
tamamında değerlendirme yapılmış sayılmadı.

İnceleme için, aynı hücre/ay içindeki mevcut günler arasında
betimleyici sıra konumları da hesaplandı. Model skorları birbirine
eklenmedi veya ortalanmadı. En geniş fark örneği, önceki geniş
kapsamlı modellerde `C665_R876 / 2022-07-30`: aynı 31 günlük
grupta bir ayar 1., başka ayarlar 31. sıra veriyor. Bu örnek
en yüksek farkı göstermek için sonradan seçildi; temsil edici
örneklem veya yeni tam-alan modellerinin sonucu değildir. Gün
sırası farkı, gerçek risk için güven aralığı değildir. Tek ayarı
sonuca göre seçerek risk rengi üretmek gerekçelendirilmedi.

## 2. Eksik değerlerin kayıtlı bağlamı ayrıldı

Dört ildeki 591 eksik dinamik satırın 366'sında meteoroloji yok;
30 günlük bitki örtüsü 239, 60 günlük 49 satırda eksik. 60 günlük
eksikler 30 gün grubunun içinde; meteoroloji/30 gün eksikleri 14
satırda kesişiyor: 366 + 239 − 14 = 591. Mersin'deki 60 eksik
satırın tamamında meteoroloji yok; bitki örtüsü alanları tam.

Meteorolojisi eksik 366 kayıt on hücrede, Mersin'in 60 kaydı iki
hücrede bulunuyor. Kaynak provenance'ta bu kayıtların en küçük
geçerli meteoroloji alan payı **0**, eksiklik bayrağı true ve ana
profil uygunluğu false. Veri aktarma sorunu olduğu varsayılmadı.
Bitki örtüsü eksiklerinin tamamında ilgili kayıtlı snapshot'ın
`vegetation_present` bayrağı false. Bunun tek başına bulutun veya
başka fiziksel bir nedenin kanıtı olduğu söylenmedi.

Önemli ayrı bulgu: dört ilde meteoroloji vektörü dolu **1.188**,
Mersin'de **394** kayıt kısmi alan desteğine sahip. En küçük
paylar sırasıyla 0,034763 ve 0,291792. Dolu olmak hücrenin
tamamını temsil etmek değildir. 15 alanı tam kayıtların içindeki
kısmi alanlı sayılar sırasıyla **1.141** ve **394**.

[3 Ekim meteoroloji kuralındaki](WEATHER_POLICY.md) üç profil
değişmeden incelendi. Tam alan ana başlangıç; en az %90 ayrı
duyarlılık; pozitif alan izleme profili. Bunlar yeni başarıya göre
seçilmiş eşikler değil. Önceki yardımcı modeller dolu 15 alanı
kullanıyordu; onların ana profil ile öğrenildiği iddia edilmedi.

| 2022 kapsamı | Dört il: tam 15 alan | Mersin: tam 15 alan |
|---|---:|---:|
| Pozitif geçerli alan | 5.982 | 2.323 |
| En az %90 alan | 5.096 | 2.142 |
| Tam alan ana profil | 4.841 | 1.929 |

Önceki model skorları bu üç sabit alt kümede, aynı çiftlerin
alt kümeleriyle incelendi: **54 alt küme / 540 sonuç satırı**
ayrı hesapla doğrulandı. Pozitif alan profili önceki sonuçları
birebir geri verdi. Sadece değerlendirme satırlarını süzmek,
modellerin geçmişte kısmi alanlarla öğrenilmiş olmasını düzeltmez.
Bu yüzden sonraki kalite uyumu ayrı öğrenme koşusuyla yapıldı.

## 3. Aynı modeller tam alan kuralına uygun öğrenmeyle kuruldu

Kullanıcının uzun özerk devam talimatı, önceden seçilmiş sabit
sıralama yaklaşımını mevcut ana meteoroloji kuralına teknik uyum
kapsamında uygulandı. Bu, kullanıcının yeni bir A harfi veya yeni
bir dokuzlu deney sorusuna ayrı yanıt verdiği biçiminde yazılmadı.
Yürütme `configs/primary_weather_rank_execution_v1.json` ile ayrı
kaydedildi. Kalite eşiği, model ailesi, parametreler ve araştırma
hedefi değiştirilmedi; ana PU yöntemi bilimsel kabul edilmiş sayılmadı.

Aynı XGBoost 3.4.1 / 15 dinamik alan / 100 ağaç / derinlik 3 /
seed 20261123 ve dokuz gruplama ayarı kullanıldı. Yalnız tam alan
meteorolojisi ve tam dinamik alanları bulunan 2018–2021 satırları,
bilgi taşıyan hücre–ay gruplarında kaldı. Ayara göre **23.280–29.140
satır / 777–967 grup / 805–1.146 aday-bağlamı satırı** var.
Dokuz yeni model 900 saniye sınırında **28,48 saniyede** tamamlandı.

Aşağıdaki bütün modeller **aynı tam alan 2022 çiftleri** üzerinde
karşılaştırılır. Eski modelin önceki daha geniş paydasındaki sayı
buraya taşınmamıştır. Aralıklar dokuz ayar; güven aralığı değildir.

| Yardımcı çift AUC | Eski doğrusal | Eski geniş-alan XGBoost | Yeni tam-alan XGBoost |
|---|---:|---:|---:|
| Dört il, genel / 4.702–5.287 çift | 0,587311–0,598822 | 0,573270–0,616039 | 0,567280–0,601843 |
| Dört il, 1–3 gün | 0,518559–0,544276 | 0,532609–0,581918 | 0,514130–0,575943 |
| Mersin, genel / 1.921 çift | 0,523165–0,536700 | 0,544768–0,577303 | 0,528110–0,566892 |
| Mersin, 1–3 gün | 0,451791–0,468320 | 0,491736–0,545455 | 0,482094–0,542700 |

Tam alanla öğrenme otomatik iyileşme sağlamadı. Mersin genelinde
yeni modellerin dokuzu da eski doğrusal skoru geçiyor; eski geniş
alan XGBoost'u ise yalnız bir ayarda geçiyor. Bu sonuçla daha
yüksek ölçü verdiği için kısmi alan profili ana kural yapılmadı.
Kaynak seçimi ve gerçek hedefe aktarım sorunu bu teknik uyumla
çözülmüş sayılmadı. Bunlar yangın doğruluğu veya olasılık değildir.

Yeni dokuz model yeniden yüklenerek tam alan öğrenme satırları,
parametreler, kaydedilmiş skorlar, ortak çiftler ve **270 sonuç
satırı** ayrı doğrulandı. Yerel MLflow 270 ölçüyü tam geri okudu;
veritabanı öncesinde yedeklendi. Grafik asistan tarafından incelendi.
**Dokuz yeni davranış testi dahil 63 ilgili test**, yeni 13 Python
dosyasında kod/biçim kontrolleri geçti. Otomatik teknik kontroller
araştırmacı veya saha doğrulaması değildir.

## Ne kapandı, ne kaldı?

Mevcut deneysel verinin skor/kaynak bağlantısı, kapsam/eksiklik
açıklaması, önceden tanımlı meteoroloji profillerinin etkisi ve
tam alanla uyumlu sabit öğrenme provası kapandı. 44.082 satırlık
paket, önceki modeller ve asıl U ağırlıkları değiştirilmedi.
Hiçbir satıra gerçek Y/L veya negatif yangın etiketi yazılmadı.

Yeni olay/yerel örtü anlamı, PU hedefe aktarım varsayımları ve
gerçek hedef değerlendirmesinin üç bilimsel koşulu açık.
[İlerlemek için somut yöntem/teslim kararı](RESEARCH_TRANSITION_DECISION_2026-11-23.md)
bu sonuçlarla hazırlandı. Teknik inceleme sürümünün hazır olması
ana yangın riski hedefinin başarıyla tamamlandığı anlamına gelmez.

## Makbuzlar

Tablodaki dizinler `outputs/reports/dataset/` altındadır. Her hash
ilgili `readback.json` dosyasına aittir.

| İş | Dizin | SHA-256 |
|---|---|---|
| İnceleme dışa aktarımı | `evaluation_review_package_v1/20261123T141815Z_be04a5fe` | `4c1ddd5be410efd3d7dfe1f44324db4046f2dfb2fc4058b718519d654473e05e` |
| Ayrı dışa aktarım denetimi | `evaluation_review_audit_v1/20261123T142016Z_d7e03899` | `a380b44c870f999924a66cc4adfe9a07fbc4d01ab83eb2b76d3970e8c1a0f5b3` |
| Meteoroloji profil tanısı | `weather_score_support_review_v1/20261123T142800Z_8725a867` | `42c3536ebe1b27e2e7c1703082494422f500f52e1e00b60d50140deacfe8463d` |
| Ayrı profil denetimi | `weather_score_support_audit_v1/20261123T143011Z_0df65000` | `792ea4e55ddf0a1ea53fe21eb6992797c4b25a7a5929e243becb9bccf9d6926b` |
| Tam alan modelleri | `primary_weather_rank_run_v1/20261123T143258Z_35678270` | `004f7d27d6b0f1825b2b00d7a2825b311e2483b5f2d73c7063cadd9b45b2946d` |
| Ayrı model denetimi | `primary_weather_rank_audit_v1/20261123T143500Z_2b454296` | `9aef378d9d3ecf90a515717dd6a1e70a1259fc960374c4026b16239252f2e468` |
| Ortak kapanış | `dataset_support_review_closure_v1/20261123T143653Z_f90b45fa` | `a85c9f271e93776ca377df99c6c7b66ed7575cf452831349d8fd73a5adef0592` |

Yerel MLflow `d68ab6d7656e4580ab1f33f3ee9f5cde`.
İnceleme dizininde `features.csv`, `record_memberships.csv`,
`record_provenance.csv`, `score_review.csv`, `support_summary.csv`
ve `scenario_position_review.csv` bulunur. Bunlar yeni nihai
etiketli birleştirme değildir. Kapanış dizinindeki
`quality_aligned_comparison.csv` üç modelin aynı-payda kıyasını,
`weather_quality_aligned_comparison.png` tüm ayarları gösterir.
