# Aynı hücre–gün örtüşmesini ayırma — sonuç

24 Kasım 2026. Araştırmacı, somut öneriden sonra “önerinden devam”
ile önerilen A yönünü seçti. Seçim
`configs/source_disjoint_evaluation_execution_v1.json` içinde hazırlık
ve audit makbuzuna bağlandı. [Önceki protokol](SOURCE_DISJOINT_EVALUATION_PROPOSAL_2026-11-24.md)
değişmeden uygulandı; bu kayıt yeni model eğitimi veya gerçek yangın kabulü değildir.

## Yapılan çalışma

2022 ayrı Mersin takvimindeki kayıtlı skorlar kullanıldı. Dokuz ayar,
üç mevcut skor ve beş mevcut değerlendirme kesiti korundu. Özellik,
üyelik ve kalite kuralı değişmedi; yeni fit/tahmin/indirme yoktur.
2023–2025 değerleri veya nihai etiketli birleştirme açılmadı.

Üç iç içe kaynak kesiti:

| Grup | Kaynak listesinde tutulan tüm günler | Ana kaliteye uygun / katkı veren hücre | Genel çift | 1–3 gün çifti |
|---|---:|---:|---:|---:|
| G0: özgün kaynak takvimi | 81 | 65 / 56 | 1.921 | 363 |
| G1: aynı hücre/günde herhangi bir uydu S önerisi bulunan altı kaynak günü çıkarıldı | 75 | 59 / 54 | 1.744 | 332 |
| G2: dört-il takviminde aynı anahtarı bulunmayan kaynak günleri | 72 | 56 / 51 | 1.656 | 314 |

Çift sayıları tek model/ayar içindir. Karşılaştırılan diğer günler
özgün Mersin takviminin aynı hücre/aydaki uygun atamasız günleridir.
Çıkarılan kaynak günleri kontrol listesine katılmadı; hiçbir gün
yeni U veya gerçek negatif yapılmadı. 16 uygun olmayan kaynak günü
özgün kayıtta korundu. Hedef/L boş, gözlem unknown ve negatif etiket izni false kaldı.

## Ana tam-alan modelinin sonucu

| Kesit | G0: 65 uygun kaynak günü | G1: 59 uygun kaynak günü | G2: 56 uygun kaynak günü |
|---|---:|---:|---:|
| Aynı hücre/ayın tüm çiftleri | 0,528110–0,566892 | 0,529817–0,577408 | 0,523853–0,569444 |
| Yalnız 1–3 gün uzak günler | 0,482094–0,542700 | 0,493976–0,554217 | 0,480892–0,535032 |
| Yalnız 4–30 gün uzak günler | 0,530167–0,572529 | 0,533994–0,582861 | 0,530179–0,577496 |
| Karşılaştırılan gün kaynak gününden önce | 0,597208–0,631605 | 0,600671–0,638143 | 0,589774–0,631986 |
| Karşılaştırılan gün kaynak gününden sonra | 0,436275–0,520697 | 0,451176–0,532941 | 0,450920–0,527607 |

Sayılar kaynak günü diğer günden üstteyse 1, eşitse 0,5 veren
yardımcı sıra kredisidir. Aralıklar dokuz ayarın uçlarıdır; güven
aralığı, gerçek yangın AP'si veya olasılığı değildir. Her ayar için
aynı modelin G0 sonucuyla eşlenmiş genel fark G1'de −0,007404 ile
+0,012454; G2'de −0,013368 ile +0,008340 arasındadır. Aralıkların
uçları farklı ayarlardan gelebilir; uçlar çıkarılarak yeni iyileşme oranı üretilmez.

Önceki geniş meteoroloji XGBoost ve dondurulmuş doğrusal skor da
aynı ortak uygun çiftlerde hesaplandı. Bütün 405 ölçü ve 270 G0 farkı
CSV'de korunur; yalnız daha iyi çıkan model/ayar veya kesit seçilmedi.
Tam senaryo aralıkları 45 satırda, genel/yakın-gün şeklinin değerleri
162 satırda dışa aktarıldı. Geniş meteoroloji modeli ana tam-alanla
öğrenmiş gibi sunulmaz.

## Bulgudan çıkarılabilecek sonuç

**Genel kaynak-bağlam ayrımı yalnız altı aynı-anahtar kayda dayanıyor
görünmüyor.** Bu kayıtlar çıkarıldığında ölçü benzer aralıkta kalmıştır;
bütün dokuz ayardaki eşlenmiş farklar ayrıca korunmuştur. Bu betimsel
bulgu istatistiksel eşdeğerlik, anlamsız fark veya bağımsız kaynak
doğrulaması iddiası değildir.

**Günlük yakın ayrımın sınırlılığı sürmektedir.** G1/G2'de de 1–3
gün sonuçları genel ay kıyasından daha düşüktür ve ayara duyarlıdır.
Kaynak gününden sonraki atamasız günlere karşı sıra kredisi, önceki
günlere karşı krediden daha düşüktür. Bu farkın yayılma, kaynak saati,
gözlem seçimi veya başka bir mekanizmadan geldiği bu deneyle ayrılmadı.
Günler kaydırılmadı ve daha yüksek skor için hedef penceresi değiştirilmedi.

G2'nin anahtarları dört-il inceleme takviminde yoktur; bu uydu tespiti
veya gerçek yangın yokluğu anlamına gelmez. Komşu hücre/günlerde aynı
olay bulunabilir. G1/G2'de öğrenmede görülmüş hücreler bulunduğu için
mekânsal kör test de değildir. Kaynak koordinatı/zamanı/kapsamındaki
bilinen belirsizlikler korunur. Bu nedenle yeni ölçüler, kaynak
sırasının gerçek yeni yangın riskine aktarımını doğrulamamıştır.

## Doğrulama ve çalışma sınırı

- 405 ölçü: özgün 135 Mersin ölçüsü aynen geri üretildi; 270 iç içe
  alt kesit ölçüsü eklendi. İlk işçi 0,875 saniyede tamamlandı;
  ebeveyn süreçte 900 saniyelik kesin süre sınırı uygulandı.
- 47.889 model/grup çift kaydı vardır; iç içe gruplar ve dokuz ayar
  aynı günleri tekrar içerir. Bağımsız örnek/yangın sayısı değildir.
- Ayrı denetleyici, üretici yardımcılarını kullanmadan özgün skor
  CSV'leri ve kaynak-örtüşme CSV'sinden bütün çiftleri doğrudan kurdu.
  Çift kimlikleri, sıra/sayım/eşitlikler, 405 kesirli ölçü, 135 eski
  sonuç ve 270 fark eşleşti. Çıkarılan kaynaklar kontrol olmadı.
- Üç yeni değerlendirme davranışı, üç mevcut plan davranışı ve
  28 hedef/birleştirme kapısı dahil bu devamda **34 ilgili test** geçti.
- Yerel SQLite deney veritabanı önce yedeklendi; MLflow'a 405 değer
  kaydedilip tamamı tam eşlikle geri okundu. Kayıt ve görseller yereldir.
- Şeklin 162 değerinin kaynak tabloyla eşliği ve çıktı hash'leri
  ayrıca kontrol edildi. PNG asistan tarafından görüntülendi;
  bu uzman yangın/örtü değerlendirmesi veya tarayıcı testi değildir.

## Dosyalar ve makbuzlar

`outputs/reports/dataset/` altında:

1. `source_disjoint_frozen_assessment_v1/20261124T031245Z_91cd329d/`:
   `metrics.csv`, `group_vs_original_delta.csv`, `paired_day_registry.csv`,
   yürütme kararı ve makbuz. Makbuz SHA-256
   `7f6e16ff58084954610dea8ca41d9ca87ece9fd02192b076cfec5973845a5d23`.
2. `source_disjoint_frozen_assessment_audit_v1/20261124T031414Z_9c5bc04c/`:
   ayrı doğrulama. Makbuz SHA-256
   `caf4f7650b1d8c5842e27a14d387081bb1967aa8b728a10e83c82d012afc2275`.
3. `source_disjoint_assessment_closure_v1/20261124T031637Z_136916ba/`:
   45 senaryo aralığı, 162 figür değeri, `source_overlap_comparison.png`
   ve yerel kayıt makbuzu. SHA-256
   `aa2e31f94b371844d4aeb14587dc91fe97011982641515c1942dc67e894023f5`.

Yerel MLflow çalışma kimliği `2bb440a6c05c48b0bce9f04887265cbe`.
Önceki veri/model/prototip arşivleri değiştirilmedi; yeni sonuç ayrı
sürümdür. [Sonuç/tartışma metnine](research/RESULTS_DISCUSSION_DRAFT_2026-11-24.md)
ve [iddia–kanıt haritasına](research/THESIS_CLAIM_MAP_2026-11-24.md) eklendi.

## Sonraki iş

Bu tanı tamamlandı; aynı veride daha iyi çıkan alt grupları aramak
için ek bölmeler açılmaz. Mevcut araştırma teslimi, ölçülen bu yeni
sınırla birlikte hazırlanır. Ana hedefe ilişkin eksik kanıtın hangi
veri/varsayımla desteklenebileceği açık tutulur; daha çok yardımcı
ölçüyle çözüldüğü söylenmez. Risk rengi/olasılık, yeni eğitim/yıl ve
nihai etiketli birleştirme kapıları bu A seçimiyle açılmamıştır.
