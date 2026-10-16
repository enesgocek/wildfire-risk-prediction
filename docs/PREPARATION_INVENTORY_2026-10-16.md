# Veri seti hazırlık envanteri ve kalan kabul bağımlılıkları

Tarih: 16 Ekim 2026. Durum: yerel kanıt/manifest ve dosya varlığı envanteri.
**Aday özellik takvimi tamam; etiketli eğitim veri seti hazır değil.**
Bu çalışma nihai parça incelemesi, bilimsel kabul veya birleştirme onayı değildir.

## Hazır olanlar ve sınırları

| Alan | Kayıtlı tamamlanan çalışma | Bugün hâlâ açık olan |
|---|---|---|
| Coğrafi anahtarlar | Dört il, 2.899 aday hücre | Tam su kuralıyla 10 hücre kapsam dışında; kalan 2.889 hücre nihai habitat kabulü değildir |
| Meteoroloji | 2018–2023 adaylarında 11 sütun; 2018–2024 kaynak denetimi önceki raporlarda kayıtlı | Eğitimde her sütunda 414.099 eksik; ERA5-Land retrospektif, canlı tahmin erişimi kanıtlanmış değil |
| Arazi/örtü | Yedi örtü ve beş topografya sütunu | Habitat gerekçesi/tarihsel erişim sınırı; northness/eastness sütunlarının her birinde 6.573 eksik |
| Bitki örtüsü | 72 eğitim ayı; ayrı 30/60 günlük NDVI/NDMI, dört sütun | Her 30 günlük sütunda 439.599, her 60 günlük sütunda 119.012 eksik; gerçek doldurma yöntemi seçilmedi |
| Özellik adayı takvimi | 72 ay, 2.191 gün, 6.351.709 hücre-gün, 27 sütun; feature/provenance ayrı | Son model satır sayısı/özellik seçimi veya kabul edilmiş etiketli örneklem değildir |
| Uydu gözlem tanıları | 72 aylık tablo ve tam takvim için önceki yapısal denetim | İki kaynak günü açık; unknown/negatif izin false; tanı sütunu model girdisi değildir |
| İnceleme önizlemesi | Hash bağlı 400 satırlık, 27 özellikli yerel CSV ve sözlük | 400 hedef boş; amaçlı örneklem, etiket veya popülasyon oranı değildir |
| Gözlem yöntem pilotu | 156 amaçlı hücre-gün/117 hücre/12 tarihte kaynak/alan/zaman tanıları ve grup raporları | Bağımsız olay doğruluğu ve güvenilir negatif kabulü yok |
| Referans alım hazırlığı | 19 alanlı alım şeması; mevcut kamu kaynaklarında 12 bağlam kaydı | Alım makbuzunda eşleştirmeye hazır bağımsız kayıt sıfır; kurum yanıtı canlı kontrol edilmedi |
| Modelleme teknik hazırlığı | AP hesabı, fold sınırları, ön işleme, kayıt, kalibrasyon planı ve grup raporları | Gerçek eğitim/kalibrasyon girişi ve model sonucu yok; hazırlıkların çoğu sentetik sınanmış çekirdekler |

Özellik eksikleri sütun başına, **6.351.709 aday hücre-gün** paydasıyladır.
Sütunların eksikleri toplanarak eksik satır veya tam gözlemli örnek sayısı
bulunamaz. Nihai habitat/gözlem/etiket koşulları uygulanmadan kaç model
satırı kalacağı bilinmiyor; bu envanterde bu sayılar boş bırakıldı.

Su kararı kaynak satırları silmez. İki kaynak günü **2018-06-13** ve
**2023-12-31**'dir; önceki gözlem denetimindeki 5.798 eksik ürün satırı,
iki gün × 2.899 aday hücre paydasıyla kayıtlıdır. Bu günler veya onlardan
etkilenen pencereler otomatik negatif yapılamaz. Bütün 72 ayı baştan işlemek
yerine kaynak istisnası ve hedef pencere etkisi protokole bağlanmalıdır.

## Bugün ne yeniden kontrol edildi?

Son tam günlük içerik denetimi **14 Ekim 2026 20:22 UTC** raporudur.
Bu envanter onu yeni bir içerik denetimi gibi yeniden adlandırmaz.
16 Ekim'de yapılan kontrol:

- Son alt grup hazırlığının 63 girdisi ve dört çıktısı hash ile kontrol edildi.
- İnceleme tesliminin raporu, kapanışı ve dokuz çıktısı yeniden hash'lendi.
- 72 aylık rapor, ay manifesti ve günlük parça manifestleri kontrol edildi;
  bunların takvim/şema/satır sayımları 2.191 günlük indeksle uzlaştırıldı.
- **4.382 günlük feature/provenance dosyasının varlığı ve byte boyutu**,
  indeks/manifest yol ve hash kayıtlarıyla eşleştirildi. Bu dosyaların
  toplam kayıtlı boyutu **9.667.531.505 bayt**; bu miktar yeniden okunmadı.
- 27 sütunun eksik sayısı bağlı günlük manifestlerden tekrar toplandı ve
  yayımlanmış kalite profiliyle eşleşti. Gerçek sütun değerleri yeniden sayılmadı.
- 400 satırlık inceleme CSV'si okundu; 27 özellik ve boş hedefler korundu,
  bütün tahmin anahtarları eğitim dönemi içindeydi.
- Mevcut inceleme preflight'ı, gerçek onay makbuzu olmadan nihai birleştirme
  kapısına sunuldu ve reddedildi. Bu bir onay üretme veya kimlik doğrulama işlemi değildir.

Boyut eşleşmesi dosya içeriğinin değişmediğini kanıtlamaz. Günlük büyük
tabloların güncel içerik hash'leri ve tüm bilimsel parça kontrolleri,
nihai etiketli birleştirme öncesinde ayrıca yapılmalıdır. Uydu ham
geometrileri ve 72 gözlem CSV'si bu envanterde yeniden işlenmedi/okunmadı.
2024/2025 veri kaynağı, özel posta kutusu ve kişisel yazışma açılmadı.

## Etiket için kapanması gereken bilimsel konular

| Konu | Hazır kanıt | Kapanış için gerekli |
|---|---|---|
| Kaynak semantiği | Kaynak/sürüm kontrolleri ve FIRMS teknik sorusu kayıtlı | Kullanılan Type/sürüm kapsamının doğrulanmış, belgeli yorumu |
| Olay tanımı | Dokuz keşif senaryosu, tekrar/zincir duyarlılıkları | Yeni olay ve devam eden olay ayrımını gerekçelendiren sürümlü kural |
| İlk hücre | Birden çok ilk hücre ve 19 duyarlı örneğin somut tanıkları | Konum/ilk zaman belirsizliğini koruyan tutarlı kural |
| Habitat | Tam su dışlaması seçildi, diğer hücreler korunuyor | Sınır, karışık örtü ve tarihsel harita sınırlamalarının gerekçesi |
| Gözlem/negatif | Alan/zaman/kalite tanıları ve 156 birimlik yöntem pilotu | Sıfır etiketin anlamı, gözlem yeterliliği ve bağımsız sınama/belirsizlik kaydı |
| Dönem kenarı | `(T,T+24h]`, yıl sınırı ve olay kesişimi teknik korumaları | Kabul edilmiş dışlama/embargo ve kaynak boşluğu pencere politikası |

Araştırmacı yöntem kararını verir; otomatik test veya araştırmacının tercihi
tek başına bağımsız doğruluk kanıtı sayılmaz. Kabul edilmiş yeni bir protokol
olmadan mevcut `target_admission` sürümü değiştirilmez. Katalogda aday
olmaması fiziksel yangın yokluğuna çevrilmez; ayrı bir katalog-var/yok
hedefi bu çalışmayla benimsenmedi.

## NASA/OGM yanıtları tam olarak neyi çözer?

Kayıtlı son kullanıcı bildirimine göre NASA/FIRMS teknik incelemesi sürüyor,
CİMER başvurusu gönderildi ve OGM teknik veri yanıtı henüz kayda girmedi.
Bu envanter yeni bir yazışma olup olmadığını kontrol etmedi; yanıt süresi
veya olumlu sonuç tahmin edilmez. Başvuru/ticket kimliği toplanmadı.

NASA'nın kaynak açıklaması Type/sürüm anlamına, kaynak istisnalarına veya
ürün eşleşmesine yardımcı olabilir; bütün olay ve negatif etiketleri
kendiliğinden doğrulamaz. OGM'den kayıt gelirse konum, saat/zaman dilimi,
kapsam, belirsizlik, kullanım koşulu ve referans doğrulaması gerekir.
Mevcut alım şablonu bu incelemeyi kolaylaştırır; gelen dosyayı otomatik
eşleyip hedefe çevirmek için yapılmadı.

**İki yanıtın gelmesi otomatik veri seti kabul koşulu değildir; tek olası
kanıt yolu da bu iki yanıt değildir.** İzinli uygun alternatif kaynak veya
belgeli örnek incelemesi araştırılabilir; eşdeğer bilimsel kanıt olmadan
kurum verisi varmış gibi davranılamaz. Yanıt beklerken olay/ilk hücre/habitat
vakaları ve dönem kenarı kararları mevcut kanıtlarla hazırlanabilir.
Güvenilir negatif sorunu ise daha fazla model koduyla çözülemez.

## Bundan sonraki sıra ve uygulama eksikleri

1. Açık kaynak/olay/ilk hücre/habitat/gözlem/kenar protokolünü kanıtlarla
   sonuçlandırmak; uygun bağımsız referansları değerlendirmek.
2. Kabul edilen protokolle hedef parçalarını üretip olay, anahtar, zaman,
   dışlama ve belirsizlik manifestlerini oluşturmak.
3. Meteoroloji, arazi/örtü, bitki örtüsü, gözlem ve hedef için **yeni son
   kontrol** raporu hazırlamak; bugün yapılan envanteri onun yerine koymamak.
4. O raporun hash'ine bağlı **açık araştırmacı onayı** almak. Hazır son rapor
   olmadığı için bu aşamada onay istenmiyor; genel “devam” onay yerine geçmez.
5. Gerçek nihai birleştiriciyi güncel dosya doğrulaması ve mevcut kapıyla
   tamamlayıp ancak bu koşullarla çalıştırmak. Henüz böyle bir son birleştirme yok.
6. Gerçek eğitim/kalibrasyon girişini kabul edilmiş veri ve seçilmiş ayarlara
   bağlamak. Mevcut değerlendirme/ön işleme kayıtları bitmiş eğitim hattı değildir.

Araştırmacının **2018–2022 temel fit / 2023 kalibrasyon / 2024 karşılaştırma**
hazırlık yönü korunur; olay ve iki sınıf desteğiyle uygunluğu sınanacaktır.
2024 için meteoroloji kaydı bulunması tüm 2024 özellik/gözlem/hedef hazırlığının
kabul edildiği anlamına gelmez. İncelenen kanıtlarda bütün 2024 veri seti
hazır değil; yeni takvim işi öncesinde donmuş protokol ve ayrı kabul gerekir.
2025, model/veri/kalibrasyon sürümleri donduruluncaya kadar kapalıdır.

Nihai birleştirme ve eğitim girişlerinin korumalı kod hazırlığı paralel
yürütülebilir; bu gerçek çalıştırma izni değildir. Operasyonel ürün için
ise retrospektif ERA5-Land'den ayrı, tahmin anında yayınlanmış meteoroloji
girdisi ve hizmet doğrulaması gerekecektir. Bu sonraki ürün konusu,
retrospektif araştırmayı kendiliğinden geçersiz yapmaz.

Makine listesinde **15 açık iş kaydı** vardır; bunlar aynı büyüklükte veya
tamamı sıralı 15 adım değildir. Geneline yüzde veya bitiş tarihi atanmadı.
Sonraki önerilen öncelik, mevcut 19 duyarlı olay tanığı üzerinden olay/ilk
hücre seçeneklerini anlaşılır karar tablosuna taşımaktır; yalnız yeni
model iskeleti üretmek kabul edilmiş etiketi ilerletmez.

## Araştırmacının açıp bakabileceği somut dosyalar

- [400 satırlık yerel inceleme önizlemesi](../outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/candidate_inspection_preview_400.csv)
- [Özellik sözlüğü](../outputs/reports/dataset/release_readiness_v1/20261014T202658Z_0c89a9de/feature_dictionary.json)
- [19 olay örneğinin kaynak/zincir incelemesi](SENSITIVE_PILOT_TRACE_2026-10-14.md)
- [Son gözlem yöntem pilotu ve somut örnekler](OBSERVATION_PILOT_RESULTS_2026-10-15.md)

Önizlemede anahtar/tarih, birimler, NaN–ölçülmüş sıfır ayrımı ve 30/60 gün
sütunları incelenebilir. `target` boşluğu korunmalıdır. Bu okunabilirlik
incelemesi 400 yangın etiketinin veya 6,35 milyon satırın insan tarafından
doğrulandığı anlamına gelmez. Şu anda bu dosyayı açmak birleştirme onayı değildir.

## Çalıştırma ve kanıt

Yeni betik: `scripts/quality/audit_preparation_inventory.py`.
**303 dosya kimliği/beş çıktı** kapanışı kontrol edildi; ayrıca büyük günlük
dosyalara yalnız 4.382 varlık/boyut kontrolü uygulandı. Yeni betikte lint/
format ve mevcut hedef/son onay kapılarının **28 ilgili testi** geçti.
Önceki 253 testlik sonuç bu aşamanın yeni test çalıştırması olarak sunulmaz.
İlk geliştirme çıktısı korundu; güncel kodla yeni dizin üretildi.

Çıktı: `outputs/reports/dataset/preparation_inventory_v1/20261016T145525Z_f9625e9e/`.
Readback SHA-256:
`1832b3b6426030ffc5165c600c593e877c7ab88ebba185469c51258ceb55a73e`.
Kapanış SHA-256:
`82029c218d046414e4eb80db3b6157ee94f6959eff6f227885063d4e0f6b3895`.
Ağ, bulut işi, kimlik yenileme, kaynak silme, imputasyon, hedef üretimi,
nihai birleştirme ve model/kalibratör fit yapılmadı. İndirilen/üretilen ham
ve ara dosyalar Git'e gönderilmeyecek; yalnız kod ve araştırma kaydı paylaşılır.
