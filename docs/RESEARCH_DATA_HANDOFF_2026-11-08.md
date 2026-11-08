# Denetlenmiş araştırma verisi ve devam koşulları — 8 Kasım 2026

Araştırmacı A yönünü seçti. Antalya, Muğla, İzmir ve Mersin için 24 saatlik
yeni orman ve çalılık yangını riski ana araştırma sorusu olarak kalır.
Mevcut çalışma, kaynakları izlenebilir bir inceleme paketi ve yöntem
çıktısı olarak kullanılabilir. Katalogda ilk uydu tespiti görülüp
görülmediğini modelleyen ayrı deney bu çalışma planına alınmadı.

## İnceleme dosyaları

| Dosya | İçerik |
| --- | --- |
| [400 satırlık özellik önizlemesi](../outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/candidate_inspection_preview_400.csv) | 2018–2023 adaylarından meteoroloji, arazi, örtü ve bitki örtüsü değerlerinin incelenebileceği örnek |
| [Özellik sözlüğü](../outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/feature_dictionary.json) | 27 aday özelliğin anlamı, birimi ve eksik değer kuralları |
| [96 ana örnek](../outputs/reports/dataset/pu_calendar_sample_v1/20261108T013027Z_d2b1102c/sample.csv) | Tespit kataloğundan bağımsız il, yıl ve mevsim örneklemi |
| [31 karşılaştırma satırı](../outputs/reports/dataset/pu_calendar_sample_v1/20261108T013027Z_d2b1102c/contrasts.csv) | Ürün boşluğu, tek sensör, örtü ve gözlem farkları |
| [127 pencerenin denetimi](../outputs/reports/dataset/pu_target_windows_v1/20261108T013906Z_90d21c5b/windows.csv) | Ana örneklem ve karşılaştırmaların UTC zaman sınırı ve kaynak boşluğu |
| [11 açık vaka kaydının alım denetimi](PUBLIC_START_EVIDENCE_INTAKE_2026-11-08.md) | Dört il için başlangıç saati, konum bağlamı ve eşleştirme eksikleri |
| [23 açık vaka kaydının dağılımı](PUBLIC_CASE_DISTRIBUTION_2026-11-08.md) | Yeni erken dönem vakaları ve inceleme listesinin il-yıl ve mevsim dağılımı |
| [Sonbahar yangın tabloları](AUTUMN_REFERENCE_TABLES_2026-11-08.md) | 98 kaynak satırı, iki metin farkı ve 96 kaydın alım sonucu |
| [Birinci aşamanın kanıt ve kabul durumu](STAGE_ONE_EVIDENCE_2026-11-08.md) | 72 aylık gözlem karşılaştırması ve bağımsız olay kaynağına erişim koşulu |

İlk beş dosyanın SHA-256 değerleri bağlı makbuzlarla eşleşti. Dört tabloda
satır sayıları ve hedef alanlarının boş olduğu tekrar kontrol edildi.
127 pencere, 96 ve 31 satırın zaman denetimidir. Bu tablolar ayrı
inceleme amaçları taşır ve satır sayıları toplanarak benzersiz gözlem
sayısı bulunamaz. 72 aylık özellik arşivinin tamamı bu teslimde yeniden
okunmadı. Gözlem yeterliliği `unknown`, etiket izinleri kapalıdır.
[Özellik envanteri](PREPARATION_INVENTORY_2026-10-16.md) · [Pencere denetimi](PU_TARGET_WINDOWS_2026-11-08.md).

## Yeni kanıt geldiğinde uygulanacak sıra

1. **Kaynağın kökeni ve kullanımı.** Olay kimliği, belge sürümü, kullanım
   izni, yer ve zaman alanlarının anlamı kaydedilir. Konum veya zamanın
   incelenen uydu tespitinden türetilip türetilmediği ayrıca kontrol edilir.
   OGM kaynaklı bir envanterin açık dosyaları ambargo altında. Saat
   verilmediğinde yerel tarih iki UTC penceresiyle ilişkilendirilir.
   [Erişim ve iki vaka üzerinde tarih denetimi](JULY_REFERENCE_ACCESS_2026-11-08.md).
2. **Olayı hedefle eşleme.** Başlangıç konumu veya konum belirsizliği,
   zaman aralığı ve saat standardı, ilk olay ile devam eden olay ayrımı ve
   başlangıç örtüsü birlikte incelenir. Belirsizlik birden fazla hücreye
   veya güne uzanıyorsa kayıtta korunur. Alım kontrolünü geçen kayıt
   önce eşleştirme incelemesine alınır. [Mevcut alım kontrolü](REFERENCE_INTAKE_2026-10-15.md).
   Menderes ve Anamur karşılaştırması, ilk tespit, etkilenen hücre
   ve ertesi UTC penceresindeki devam kayıtlarının ayrımını gösterir.
   [İki vaka için kabul koşulları](JULY_CASE_ADMISSION_2026-11-08.md).
3. **Değerlendirme dayanağı.** Referans kaydının kapsadığı iller,
   yıllar, olay türleri ve bilinen eksikler belgelenir. Örneğin yalnız
   büyük yangınları içeren bir liste, küçük olaylar için yokluk kanıtı
   vermez. PU yaklaşımı için pozitif kümenin niteliği, pozitiflerin nasıl
   seçildiği ve olay sıklığına ilişkin dayanak ayrıca sınanır. Tek bir
   güçlü olay eşleşmesi değerlendirme kümesini açmaz. Muğla'daki
   resmî büyüklük dağılımı, büyük olay seçiminin etkisini sayıyla
   gösterir. [Açık kaynak kapsam denetimi](PUBLIC_FIRE_SOURCE_COVERAGE_2026-11-08.md).
   OGM'nin 2018–2023 il tablolarındaki 24 satır, aynı il
   sınırı ve kayıt tanımıyla oluşturulmuş bir olay listesi
   için toplu kapsam karşılaştırması sağlar.
   [İl-yıl toplamları ve sınırları](OGM_PROVINCE_YEAR_2026-11-08.md).
   İzmir İtfaiyesinin aynı 2023 yayınına ait API ve indirilebilir
   dosyası 736 satır farklı. Yıllık raporla tutarlı dosya vaka
   bağlamı için kullanılır. [Yayın kapsamı karşılaştırması](IZMIR_DISPATCH_COVERAGE_2026-11-08.md).
4. **Parçaların son kontrolü ve onay.** Hedef protokolü kabul edilebilirse
   meteoroloji, arazi/örtü, bitki örtüsü, gözlem ve hedef parçaları güncel
   dosya kimliği, anahtar, şema, eksik değer, zaman ve dönem ayrımıyla
   ayrı denetlenir. Nihai birleştirme araştırmacının bu denetim raporuna
   bağlı onayından sonra yapılır. 2024 karşılaştırma ayrıdır ve 2025 kapalıdır.

İlk olay kanıtı için tek bir kurum zorunlu kaynak olarak belirlenmedi.
Yeni bir kurumsal talep açma kararı alınmadı. Eldeki çalışma bitirme
raporunda veri hazırlığı, gözlem boşlukları ve hedefin doğrulanma sınırı
olarak kullanılabilir.
