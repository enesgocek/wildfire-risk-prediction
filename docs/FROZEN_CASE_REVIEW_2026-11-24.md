# Kaynak-gün sıralamasında örnekler ve duyarlılık

24 Kasım 2026. Mevcut 2022 skorları ve özelliklerinden yapılan posthoc
incelemedir. Yeni öğrenme, tahmin, hedef etiketi, risk eşiği veya kapalı
yıl erişimi yoktur. Önceki [yerel teslim](LOCAL_RESEARCH_RELEASE_2026-11-24.md)
değiştirilmedi; bu analiz ayrı sürümlü ek çıktıdır.

## Amaç ve örnek seçimi

Genel bir ölçünün arkasındaki alt/orta/üst sıralanan kaynak günlerini
görünür yapmak amaçlandı. Gerçek yangın durumu bilinmediğinden düşükte
kalan S önerisi doğrulanmış kaçırılan yangın; yüksek atamasız gün
doğrulanmış yanlış alarm olarak adlandırılmadı.

Kural bu örnek seçimi öncesinde `configs/frozen_case_review_v1.json`
içinde yazıldı; geçmiş sonuçlar daha önce incelendiği için çalışma
önkayıtlı veya kör değildir. Ana tam-alan modelinin kaynak günü başına
diğer uygun günlerden üstün sıralama kredisi, dokuz ayarın eşit
ağırlıklı ortalamasıyla özetlendi. Bu yardımcı ortalama, önceki ana
çift ağırlıklı sonucun yerine geçirilmedi.

Envanter 251 takvim/hücre/gün üyeliğidir: dört-il takviminde 186,
ayrı Mersin'de 65. Dokuz ayarın hepsinde kaynak ve karşılaştırma
desteği olan 165 + 65 üyelik, örnek seçim havuzudur. Dört-il takviminde
yalnız bazı ayarlarda destekli 21 üye envanterde korunur. İki takvimin
aynı anahtarda örtüşebilmesi nedeniyle bu toplam bağımsız yangın sayısı değildir.

Her takvimde ortalama kredi, hücre ve tarih sırasıyla deterministik
dizilim yapıldı: en alt iki, en üst iki ve kalanların sırasal merkeze
en yakın iki örneği alındı. Toplam 12 farklı örnek vardır; seçilenlerde
takvimler arası anahtar tekrarı yoktur. Örnekler nüfusu/illeri temsil
eden rastgele örneklem değildir; Muğla için görsel örnek seçilmemiştir.
Orta örnek, kredisi 0,5 olan örnek demek değildir; havuzun sırasal ortasıdır.

## Ölçülen bulgular

| Dokuz ayarda da destekli kaynak-gün üyeleri | Dört-il aday takvimi | Ayrı Mersin kaynak takvimi |
|---|---:|---:|
| Üye sayısı | 165 | 65 |
| Kaynak-gün ortalama kredisinin medyanı | 0,629630 | 0,525926 |
| Üye başına dokuz ayar kredi aralığının medyan genişliği | 0,275862 | 0,310345 |
| En geniş üye kredi aralığı | 0,896552 | 0,800000 |
| En az bir ayarda 0,5 altı ve başka ayarda 0,5 üstü olan üye | 57 | 27 |

0,5 burada yardımcı karşılaştırma kredisinin betimsel referansıdır;
yangın karar eşiği veya istatistiksel anlamlılık sınırı değildir.
Dokuz ayar bağımsız tekrarlar sayılmaz. Kaynak gününün üyeliği sabit
olsa da öğrenilmiş model ve kimi hücre–aylarda karşılaştırılabilir
diğer günler ayara göre değişebilir. Dolayısıyla fark yalnız model
rastlantısına atfedilemez. Uygunluk/etiket protokolü değiştirilmedi.

### Somut alt, orta ve üst örnekler

- **Antalya, C596/R882, 12 Nisan 2022:** `four_province_01`.
  Dokuz modelde 30 uygun günün sonuncusu; kaynak-gün sıra kredisi
  her ayarda 0. Önceki 168 saat yağış özeti 12,436 mm, aynı hücre/ay
  kararlı atamasız günlerinin medyanı 1,196 mm. Sıcaklık 12,705 °C,
  aynı referansın medyanı 16,227 °C. Bu değerler bağlamdır; yağışın
  model kararına neden olduğunu veya kaydın yangın olmadığını göstermez.
  İkinci alt Antalya örneği de 12 Nisan'dadır; bunlar iki bağımsız
  meteorolojik olay sayılmaz.
- **Antalya, C572/R867, 22 Eylül 2022:** `four_province_06`.
  Ortalama sıra 30 gün içinde 1,222; kredi 0,931034–1,000000.
  168 saat yağış 0,018 mm / referans medyanı 0,612 mm;
  rüzgâr ortalaması 2,723 m/s / referans 1,975 m/s.
  Bu, kaynak bağlamıyla uyumlu üst sıralama örneğidir; gerçek tutuşma
  veya risk olasılığı doğrulaması değildir.
- **Ayrı Mersin, C634/R862, 31 Temmuz 2022:** `separate_Mersin_01`.
  Ortalama sıra 31 gün içinde 30,222; kredi 0–0,100000.
  Sıcaklık 28,797 °C olmasına rağmen üstte sıralanmamıştır.
  Diğer günlerin aynı sıcaklık özeti medyanı 30,072 °C'dir.
  Sıcak bir gün olmasının otomatik yüksek model skoru demek olmadığı
  görülür; bu karşılaştırma özelliğin nedensel katkı hesabı değildir.
- **Ayrı Mersin, C648/R864, 7 Eylül 2022:** `separate_Mersin_03`.
  Kredi 0,241379–0,758621; aynı kaynak günü ayara belirgin duyarlıdır.
  Ortalama sıra 30 gün içinde 14,889'dur. Ayar sonuçlarını tek bir
  kesin kategoriye çevirmek için dayanak oluşmamıştır.
- **Ayrı Mersin, C654/R868, 22 Mayıs 2022:** `separate_Mersin_06`.
  Kredi 0,933333–1,000000; ortalama sıra 31 gün içinde 1,444.
  Bu örnek üstte sıralanırken aynı model ailesi diğer kaynak günlerini
  aşağıda bırakabilmektedir; yalnız iyi örneklerle sunum yapılmamıştır.

`separate_Mersin_04` kaydı kaynak takviminde bulunur; özgün il kesişim
tablosunda eşleşmesi yoktur. İl otomatik Mersin yazılarak düzeltilmedi.
Kaynak takvimi ve coğrafi alan eşlemesi farklı kavramlardır.

## Bağlam tablosu ve şekiller

Özellik karşılaştırmasında aynı takvim/hücre/ayda, ana kaliteyi geçen
ve dokuz ayarın tamamında atamasız olan günler kullanıldı. 15 dinamik
alan için kaynak değeri, referans medyanı ve eşitliklere yarım kredi
veren betimsel karşılaştırma vardır. SHAP, karşıolgusal açıklama,
nedensellik veya modelin özelliği kullanma ağırlığı hesaplanmadı.

Ay grafiğinde bütün uygun günlerin her modeldeki sırası hesaplandı:
1 en üst, eşitlikler ortalama sıradır. Çizgi dokuz sıranın ortalaması,
bant min–maks aralığıdır; güven aralığı ve yangın yüzdesi değildir.
Seçilmiş kaynak günü turuncu işaretlidir. Mevcut modellerin aynı
değerlendirme çiftlerindeki genel ve 1–3 gün kıyasları ayrıca çizildi;
figürdeki 108 değer eski makbuzla tam eşleşir. Özellikle yakın gün
sonuçları genel ay kıyasından ayrı okunmalıdır.

Yerel yollar (`outputs/reports/dataset/` altında):

- `frozen_rank_case_review_v1/20261124T024256Z_abeb3e00/`:
  tam envanter, 12 örnek, 3.132 ayar/karşılaştırma günü satırı,
  180 özellik bağlamı, 360 günlük sıra ve `case_rank_timelines.png`.
  3.132 satır dokuz ayarda aynı günleri tekrar içerebilir; bağımsız örnek sayısı değildir.
- `frozen_rank_case_audit_v1/20261124T024500Z_68829a04/`:
  kaynak JSON skorlarıyla ayrı seçim/çift/sıra/özellik denetimi.
- `frozen_case_result_synthesis_v1/20261124T024652Z_f63eea3c/`:
  iki takvim özeti, 108 eski ölçü ve `existing_model_comparison.png`.
- `frozen_case_synthesis_audit_v1/20261124T024821Z_fd26fbcc/`:
  ayrı standart medyan hesabı ve 108 eski figür değerinin doğrulaması.

İki PNG asistan tarafından görüntülenerek başlık/eksen/işaretler
kontrol edildi; bu yangın/örtü uzman incelemesi veya tarayıcı render
kontrolü değildir. Üç yeni davranış testi ve 28 hedef/birleştirme
kapısı testi bu devamda geçti; toplam 31. Önceki 34 test bugünkü
çalışmanın yeni test sayısı olarak tekrar sunulmadı.

Makbuz SHA-256:

- Örnek üretimi: `a65579afa7165b72a830f22e39367bb9331e100c0b5aa7d0b982bdf8dcc8c4af`.
- Ayrı örnek denetimi: `28ec52a4689ef17b2b5b4754faeb480d3a779cc1a37844c0e3a83e1428a7ad59`.
- Sentez: `02f4b26ca3b8dcb2f8ab8ba24a430d9e7e425538899874fb4d43be8c27513b50`.

## Projeye katkısı ve devam sınırı

Bu inceleme, veri/model tesliminin yanı sıra savunmada gösterilebilecek
olumlu ve zayıf örnekleri ve ayar duyarlılığını hazırlar. Veri paketindeki
etiket boşluğu istatistiksel özetle kapatılmamıştır. Sonuç ve tartışma
taslağı [tamamlanan işlerden yazıldı](research/RESULTS_DISCUSSION_DRAFT_2026-11-24.md).
Yeni öğrenme veya kapalı yıl için bu inceleme yetki sayılmaz; örnekler
gerekçesiz silinmez, tarih/hedef penceresi daha iyi skor için kaydırılmaz.
