# Sonuçlar ve tartışma — mevcut araştırma sürümü

24 Kasım 2026. Tamamlanan yerel hesaplara dayalı bitirme metni taslağıdır.
Danışman/yayın kabulü, nihai yangın etiketli veri seti veya ana araştırma
hedefinin başarıyla tamamlandığı anlamına gelmez. Sayısal ölçüler 2022
keşif takvimlerine aittir; sonraki yıllar bu sonuçlara dahil değildir.

## Veri hazırlığının sonucu

Kaynak/uydu aday bağlamıyla seçilmiş 2018–2022 hücre–ay takvimlerinden
44.082 farklı hücre–gün ve 822 hücre için 27 özellik içeren deneysel
inceleme sürümü hazırlanmıştır. 41.358 satırın 27 alanı tam, 2.724
satırın en az bir alanı eksiktir. Özellik, üyelik ve kaynak izleri
ayrı dosyalarda tutulmuştur. Eksik veya atamasız kayıtlar otomatik
negatif yapılmamıştır. Veri ve model kartları, dosya hash'leri,
ayrı teknik denetimler ve yerel inceleme ekranı teslim bileşenleridir.
[Veri kartı](DATASET_CARD_2026-11-24.md).

Bu veri, dört ilin bütün hücre ve günlerini temsil eden nüfus paneli
değildir. Kaynak takvimine dahil olma süreci örnek seçimini etkiler.
Dolayısıyla bu örneklemdeki kaynak üyeliği oranından saha yangın
sıklığı veya kalibre yangın olasılığı elde edilmemiştir. `target`/L
boş, gözlem durumu unknown ve negatif etikete izin false kalmıştır.

## Günlük sıralama deneyleri

Sabit 15 dinamik alana dayalı dokuz XGBoost modeli, 2018–2021'de
aynı hücre/ay içindeki kaynak-bağlamlı ve atamasız günler üzerinden
öğrenmiştir. Ana tam-alan meteoroloji kuralına uyumlu bu modeller,
önceki geniş meteoroloji destekli XGBoost ve dondurulmuş doğrusal
skorla aynı uygun 2022 karşılaştırma çiftlerinde değerlendirilmiştir.
Önceki geniş destekli model tam-alanla öğrenmiş gibi sunulmamıştır.
[Model kartı ve sabit parametreler](MODEL_CARD_2026-11-24.md).

Kaynak günü diğer günden üstteyse 1, eşitse 0,5 alan yardımcı
sıralama kredisi kullanılmıştır. Bu gerçek yangın AP'si değildir;
ana AP ve yardımcı trapez PR-AUC değerlendirme yönü korunmaktadır.

| Değerlendirme kesiti | Ana tam-alan XGBoost | Önceki geniş-alan XGBoost | Dondurulmuş doğrusal |
|---|---:|---:|---:|
| Dört il, aynı hücre/ayın bütün çiftleri | 0,567280–0,601843 | 0,573270–0,616039 | 0,587311–0,598822 |
| Dört il, yalnız 1–3 gün uzaklıktaki çiftler | 0,514130–0,575943 | 0,532609–0,581918 | 0,518559–0,544276 |
| Ayrı Mersin, aynı hücre/ayın bütün çiftleri | 0,528110–0,566892 | 0,544768–0,577303 | 0,523165–0,536700 |
| Ayrı Mersin, yalnız 1–3 gün uzaklıktaki çiftler | 0,482094–0,542700 | 0,491736–0,545455 | 0,451791–0,468320 |

Aralıklar dokuz ayarın min–maks değerleridir, güven aralığı değildir.
Aynı hücre/ay içindeki çiftler bağımlıdır. Ayrı Mersin kaynağında
günlük yakın karşılaştırmaların daha sınırlı ayrım vermesi, genel ay
sonucunun günlük yangın zamanlama başarımı sayılmaması gerektiğini
gösterir. Parametreler 2022'ye göre seçilmemiş; en iyi ayar üretim
modeli ilan edilmemiştir. Karmaşık modelin her kesitte daha iyi olduğu
veya ana meteoroloji kuralının gevşetilmesi gerektiği sonucu çıkarılmamıştır.

## Kapsam ve örnek düzeyinde inceleme

Ana modelin dört-il genel ölçüsü ayara göre 165–186 kaynak günü ve
135–143 hücredeki 4.702–5.287 karşılaştırmaya dayanır. Ayrı Mersin'de
65 kaynak günü ve 56 hücreden 1.921 çift vardır. En yoğun hücrenin
payı dört ilde %2,65–3,06, Mersin'de %3,12'dir. Hücrelere eşit
ağırlıklı özetler ve tek değerlendirme hücresi çıkarma tanısı
raporlanmıştır; bunlar mekânsal çapraz doğrulama değildir.
[Destek denetimi](../LOCAL_RESEARCH_RELEASE_2026-11-24.md).

Kaynak üyeliği ve karşılaştırma desteği dokuz ayarda da bulunan
165 dört-il ve 65 ayrı Mersin günü ayrıca incelenmiştir. Üye başına
dokuz ayar kredi aralığının medyan genişliği sırasıyla 0,275862 ve
0,310345'tir. Dört ilde 57/165, Mersin'de 27/65 üye için en az bir
ayarın kredisi 0,5'in altında, başka bir ayarın kredisi üstündedir.
Bu hesap karar eşiği veya anlamlılık testi değildir. Ayar farkı,
öğrenilmiş model ve bazı örneklerde diğer günler kümesinin değişimini
birlikte içerir. Tek bir ayar üzerinden örneğe kesin risk sınıfı
vermek desteklenmemektedir.

Alt, orta ve üst sıradan deterministik seçilmiş 12 örnek, olumlu
örneklerin yanı sıra belirgin uyumsuzlukları da göstermiştir. Antalya
C596/R882 hücresinde 12 Nisan kaynak günü dokuz modelde 30 günün
sonuncusu, C572/R867 hücresinde 22 Eylül günü ise ortalama 1,222
sıradadır. İlk örneğin 168 saatlik yağışı 12,436 mm, referans medyanı
1,196 mm; ikinci örneğin yağışı 0,018 mm, referans medyanı 0,612 mm'dir.
Bu farklılıklar hava bağlamını belgeler; model kararının nedensel
özellik açıklaması veya yangın olmadığının kanıtı değildir.
[Örnek kuralı, bütün ölçüler ve şekiller](../FROZEN_CASE_REVIEW_2026-11-24.md).

## Bulguların yorumu

Günlük kaynak-bağlam sıralaması bazı kesitlerde ayrım göstermiştir;
bu ayrım bütün kaynak günlerinde tutarlı değildir. Düşük ortalama
krediye sahip kaynak günü ile yüksek puanlı atamasız gün, güvenilir
Y etiketleri bulunmadığından gerçek yanlış negatif/yanlış pozitif
olarak sayılamaz. Kaynak koordinatının rolü, kayıt saati ve kapsamı,
uydu adayının gerçek yeni olayla ilişkisi ve yerel örtüsü açık kalır.

Bu aşamadaki somut çalışma çıktısı, bu belirsizlikleri saklamayan
yeniden üretilebilir veri hazırlığı, kontrollü günlük sıralama
deneyleri ve incelenebilir prototiptir. Bu bir literatürde ilk olma
iddiası değildir. Araştırmanın hedefi yeni orman/çalılık yangını
riskidir; mevcut yardımcı sıralama sonucunun bu hedefe aktarımı
kanıtlanmış kabul edilmemiştir.

## Sınırlamalar ve sonraki bilimsel çalışma

Örneklem kaynakla seçilmiş, 2022 sonuçları daha önce incelenmiş ve
kör final değerlendirme değildir. Aynı hücreler öğrenmede bulunabilir.
Bağımsız yangın doğrulama dayanağı, yeterli günlük gözlem ve etiket
gürültüsü/seçim varsayımları açık kaldığı için kalibrasyon, gerçek
yangın AP'si ve doğrulanmış risk renkleri sunulmamıştır. Retrospektif
ERA5 girdisinin geçmiş tahmin anında erişilebilir olduğu ileri sürülmez.

FWI önceki küçük Haziran karşılaştırmasının referansıdır; o örneklem
bu dokuz modelin tüm 2022 desteğiyle aynı değildir. Ölçülmemiş bir
FWI–XGBoost üstünlük iddiası veya saha erken uyarı sonucu çıkarılmaz.
2023 kalibrasyon, 2024 karşılaştırma ve kapalı 2025 rolleri bu analizde
açılmamıştır. Daha iyi sonuç elde etmek için kaynak günü kaydırılmamış,
örnekler silinmemiş veya kalite koşulu gevşetilmemiştir.

Sonraki bilimsel çalışma, öğrenilmiş kaynak sırasının gerçek yeni
yangın hedefiyle ilişkisini ve günlük yakın ayrımın sınırlarını
destekleyen değerlendirme tasarımına odaklanmalıdır. Mevcut örnek
incelemesi, eksik kanıtı yalnız daha çok model veya rapor üreterek
tamamlamaz. Yerel deneysel teslim hazır olsa da nihai etiketli
birleştirme, güncel ayrı parça denetimi ve rapora bağlı kullanıcı
onayını ayrıca gerektirir. [AI katkı kaydı](AI_USE.md).

## Aynı gün sonraki çalışma: ortak anahtar katkısı

Araştırmacının A seçimiyle, aynı hücre/günde herhangi bir dört-il
uydu adayına denk gelen altı Mersin kaynak günü kaynak listesinden
çıkarılmıştır. Özgün 65 uygun gün/1.921 çifte karşı G1'de 59 gün/
1.744 çift, dört-il takviminde anahtarı hiç bulunmayan G2'de 56 gün/
1.656 çift vardır. Karşılaştırma günleri sabit tutulmuş, dışarıda
kalan kaynak günleri yeni U veya gerçek negatif yapılmamıştır.

Ana tam-alan modelinin genel yardımcı kredisi G0'da
0,528110–0,566892, G1'de 0,529817–0,577408 ve G2'de
0,523853–0,569444'tür. Aynı model/ayarın G0'a göre genel farkı
G1'de −0,007404/+0,012454, G2'de −0,013368/+0,008340 aralığındadır.
Genel kaynak-bağlam ayrımı yalnız altı ortak anahtara dayanmıyor
görünmektedir; istatistiksel eşdeğerlik veya gerçek yangın doğrulaması
iddia edilmemiştir. 1–3 gün kesitinde G1 0,493976–0,554217,
G2 0,480892–0,535032 ile günlük yakın ayrım sınırı sürmektedir.

Dokuz ayar ve üç mevcut skor için 405 ölçü, 47.889 model/grup çift
kaydı, 135 eski ölçü ve 270 fark ayrı hesapla doğrulanmıştır. Yerel
deney kaydında bütün 405 değer geri okunmuştur. Gruplar iç içe,
günler bağımlıdır; anahtar ayrılığı olay veya mekânsal bağımsızlık
değildir. Kaynağın konum/zaman/kapsam belirsizliği aynı durumdadır.
Yeni öğrenme/tahmin, kapalı yıl veya etiket açılmamıştır.
[Protokole bağlı sonuç ve makbuzlar](../SOURCE_DISJOINT_EVALUATION_RESULTS_2026-11-24.md).
