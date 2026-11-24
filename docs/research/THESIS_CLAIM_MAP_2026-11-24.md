# Bitirme iskeleti ve iddia–kanıt haritası

24 Kasım 2026. Mevcut araştırma çıktılarının teslim metnine aktarımı
içindir; kapsam/yöntem, okul biçimi veya danışman kabulü kararı değildir.

## Bölümler ve hazır metinler

| Bölüm | Kaynak metin ve yapılacak ayrım |
|---|---|
| Özet | Sonuçlar tamamlandığında yazılır: amaç, veri ve sınırlı kaynak-bağlam sıralaması; doğrulanmış risk ürünü iddiası eklenmez |
| Giriş ve amaç | `docs/PROJECT.md`, `RESEARCH_PLAN.md`: dört il/5 km/sonraki 24 saatlik yeni orman-çalılık yangını; amaç ve elde edilen sonuç ayrılır |
| Literatür | Önceki gerçek kaynak kayıtları; çalışma/veri/hedef/değerlendirme farkı. Bu iskelet yeni literatür doğrulaması değildir; ilk olma veya üstünlük uydurulmaz |
| Veri ve yöntem | `DATASET_METHODS_DRAFT_2026-11-23.md` ile güncel veri/model kartları: 27 alan, ayrı üyelik/kaynak, zaman, seçim, eksik ve 15 dinamik alan |
| Sonuçlar | `RESULTS_DISCUSSION_DRAFT_2026-11-24.md`: dokuz ayarın tamamı, ortak uygun çiftler, yakın günler, kapsam ve örnekler |
| Tartışma | Aynı taslak: kaynak sırasından gerçek yangına aktarım, ayar duyarlılığı, bağımlılık ve açık gözlem/etiket koşulları |
| Yazılım/prototip | `docs/RESEARCH_PROTOTYPE_2026-11-23.md`: yerel kayıtlı skor/filtre/kaynak inceleme; canlı tahmin servisi değildir |
| Sonuç ve gelecek çalışma | Tamamlanan teknik araştırma çıktısı ile henüz desteklenmeyen gerçek yangın iddiası ayrılır |
| Kaynakça ve ekler | `EVIDENCE_REGISTER.md`, `AI_USE.md`, kartlar, açık parametreler ve hash makbuzları; veri GitHub'da yayımlanmış sayılmaz |

23 Kasım yöntem taslağı ilk geniş meteoroloji koşusunu ve sonraki ana
kalite uyumunu tarihsel olarak birlikte içerir. İlk koşunun sayıları,
ana tam-alan koşusunun sonucu diye kopyalanmamalıdır. Güncel sonuç
tablosunda iki koşu adı ve ortak değerlendirme paydası açık tutulur.

## Kullanılabilecek somut ifadeler

| Kimlik | İfade | Kanıt ve sınır |
|---|---|---|
| T01 | 44.082 farklı hücre–gün, 822 hücre, 27 özellik vardır | Veri kartı ve ayrı S/U audit'i; bütün dört ilin nüfus paneli değildir |
| T02 | 41.358 satır tam, 2.724 satır en az bir alanda eksiktir | Veri kartı; tam alan sayısı bütün model kalite koşullarıyla aynı değildir |
| T03 | Ekranda iki 2022 takvimi vardır: 6.573 ve 2.383 üyelik | Prototip makbuzları; 245 ortak anahtar vardır, toplam farklı yangın sayısı değildir |
| T04 | Dokuz sabit tam-alan XGBoost, 15 dinamik alanla 2018–2021'de öğrenmiştir | Model kartı/koşu audit'i; kütüphane uygunluk işareti yangın Y=1/0 değildir |
| T05 | Ana modelin genel yardımcı kredisi dört ilde 0,567280–0,601843, ayrı Mersin'de 0,528110–0,566892'dir | 270 eski ölçü ve sonuç taslağı; gerçek yangın AP'si/olasılığı değil, dokuz ayar aralığıdır |
| T06 | Ayrı Mersin'de 1–3 gün uzaklıklı ana kredi 0,482094–0,542700'dür | Aynı mevcut ölçüler ve 108 figür değeri audit'i; genel ay ayrımı günlük yangın zamanlama başarımı değildir |
| T07 | Dört ilde 135–143 hücre katkı verir; en yoğun hücre çift payı %2,65–3,06'dır | Destek tanısı/ayrı audit; mekânsal çapraz doğrulama veya saha aktarımı değil |
| T08 | 165 dört-il / 65 Mersin üyenin 57 / 27'sinde ayar kredileri 0,5'in iki tarafındadır | Örnek envanteri/sentez audit'i; karar eşiği veya anlamlılık sonucu değildir |
| T09 | Alt/orta/üst 12 örnek aynı açık seçim kuralıyla gösterilmiştir | 3.132 karşılaştırma, 180 bağlam ve 360 sıra audit'i; temsilî rastgele örneklem veya gerçek hata sayımı değildir |
| T10 | Yerel teslim 198 dosyada paketlenip ZIP/dizin eşliği denetlenmiştir | Teslim/audit makbuzu; nihai etiketli birleştirme veya dış veri yayını değildir |
| T11 | Altı aynı-anahtar kaynak çıkarılınca ana model genel kredisi 0,529817–0,577408; daha dar G2'de 0,523853–0,569444'tür | A ile yürütülen 405 ölçü/47.889 çift kaydı ve ayrı audit; gerçek yangın aktarımı veya eşdeğerlik testi değildir |

Tam kaynak yolları/hash'ler [teslim raporunda](../LOCAL_RESEARCH_RELEASE_2026-11-24.md)
ve [örnek incelemesinde](../FROZEN_CASE_REVIEW_2026-11-24.md) bulunur.
Yeni veri/model gelirse bu eşleme de yenilenir.
Aynı gün sonraki [kaynak-örtüşmesi sonucu](../SOURCE_DISJOINT_EVALUATION_RESULTS_2026-11-24.md)
T11'de ayrıca kaydedildi; önceki G0 sonuçları geriye dönük değiştirilmedi.

## Desteklenmeyen ifadeler

Atamasız günler yangın olmayan günler değildir. Yardımcı ölçü gerçek
yangın AP'si değildir; skor yüzde veya doğrulanmış risk rengi değildir.
En iyi ayar seçilmemiş, mekânsal genelleme kanıtlanmamıştır. 2022 kör
final test değildir; 2023–2025 ile değerlendirme yapıldığı söylenemez.
Yağış/medyan karşılaştırması nedensel model açıklaması değildir.
Literatürde ilk veya ölçülmemiş başka yöntemlerden üstün olma iddiası yoktur.

## Şekiller ve sonraki protokol

Ana sonuç bölümünde `existing_model_comparison.png`: iki takvim,
genel/yakın gün ve üç modelin bütün dokuz ayarı gösterilir; çizgiler
min–maks, güven aralığı değildir. `case_rank_timelines.png` ek/örnek
inceleme bölümünde kullanılabilir; turuncu işaret kaynak günü, yangın
etiketi değildir. Dosyalar yereldir; açık veri deposu/kalıcı yayın
bağlantısı olarak kaynak gösterilmez. [Yerel yollar](../FROZEN_CASE_REVIEW_2026-11-24.md).

Ana açık, kaynak sırasının gerçek yeni yangına aktarımıdır. Yeni deney
önerisi; amaç, mevcut kanıt, sınanacak varsayım, örneklem/yıl,
karşılaştırma ve durma koşulunu birlikte belirtmelidir. Daha çok model
veya daha yüksek yardımcı skor eksik kanıtı tamamlamış sayılmaz.
Yeni eğitim/yıl/etiket/renk yönü kullanıcıya gider; rutin teknik
kontroller ve belge/sayım işleri asistan tarafından yürütülür.
