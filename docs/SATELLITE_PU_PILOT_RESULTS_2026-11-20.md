# Dört il uydu adaylarıyla yardımcı model denemesinin sonuçları

21 Kasım güncellemesi: aşağıdaki sonraki 18-model önerisi araştırmacı
tarafından ayrıca onaylandı; 20 Kasım deney/ayrı tanısı tamamlanmış
olarak geri okundu. Güncel sonuçlar ve dar zaman desteği açığı
[ayrı rapordadır](SATELLITE_PU_ABLATION_RESULTS_2026-11-21.md).
Aşağıdaki ilk sonuçlar ve o andaki öneri kaydı korunur.

20 Kasım 2026. Araştırmacının yeni A kararıyla dokuz ayarda **27
yardımcı model** çalıştırıldı; tamamı kayıtlı modellerden yeniden
tahmin edilerek doğrulandı. Dört ilin 2022 inceleme örnekleminde
aday üyeliği ayrımı mevcut; yalnız eksiklik bayrakları daha zayıf
ayırıyor. Bu sonuç **gerçek yeni orman/çalılık yangını başarımı veya
yangın olasılığı ölçümü değildir**. Birinci aşamanın bilimsel kabulü
ve nihai eğitim veri seti henüz tamamlanmış sayılmıyor.

## Deneyin girdisi ve değişmeyen kapsam

2017 ana / CORINE 2018 yardımcı örtü kararının
[donmuş girdileri ve somut planı](SATELLITE_PU_PROTOCOL_PREPARATION_2026-11-20.md)
kullanıldı. Her ayarda aynı 1.648 fit U ve 400 inceleme U var;
fit 2018–2021, tanısal inceleme 2022. Ayara göre 1.043–1.428 fit
aday anahtarı, 215–242 inceleme aday anahtarı değişiyor. Bütün
ayarlar korundu; en iyi yardımcı ölçüye bakarak üretim ayarı seçilmedi.

S=1 bu ayardaki olası uydu önerisine ait hücre-gün; S=0 özgün
belirsiz U örneği. S=0 gerçek yangın yokluğu, S=1 doğrulanmış
pozitif değil. Gerçek Y ve kabul edilmiş L boş. Karışık ilk
hücreler ve WF1538'i öneri dışında tutma kararı korundu. Bu,
ağırlıksız vaka örnekleminde yardımcı S ayrımıdır; U edinim ağırlıkları
sınıf ağırlığı yapılmadı ve nüfus yangın oranı tahmin edilmedi.

27 özellikli sabit lojistik, küçük RF ve beş özellik ailesinin
yalnız eksiklik bayraklarıyla lojistik kontrolü çalıştı. RF 100
ağaç, derinlik 6, en az 5 yaprak örneği; lojistik C=1, azami 1.000
iterasyon; seed 20261120. Medyan doldurma, eksiklik göstergeleri,
tamamen eksik fit sütunlarının çıkarılması ve lojistik ölçekleme
yalnız fit kesitinden öğrenildi. Orijinal özellik CSV'leri değişmedi.
Hedef penceresi bilgisi, uydu kalite/başlangıç alanları, tarih/il
etiketleri modele X sütunu olarak verilmedi.

Bulut kullanılmadı. Standart çalıştırıcı yerel alt süreç için 15
dakika üst sınırı, RF fit için iki işçi ve sıralı tahmin kullandı.
Makbuzdaki **4,578 saniye**, model koşusunun kendi ölçülen gövdesidir;
Python açılışı, önceki veri hazırlığı ve sonraki denetimler dahil
bütün proje süresi veya ilerideki veri seti süresi değildir.

## Dokuz ayardaki yardımcı S ayrımı

ROC-AUC, örneklemde bir aday–U çiftinde adayın daha yüksek skor alma
sıklığını, eşitliklere yarım pay vererek ölçer. Yüzde doğru yangın
tahmini değildir. Kaynak/örnek bileşimi ayarlar arasında değiştiği
için tabloyu üretim parametresi yarışması yapmıyoruz. Ana araştırma
ölçütü AP korunuyor; burada gerçek yangın AP'si hesaplanmadı.

| Ayar | Lojistik yardımcı S AUC | RF yardımcı S AUC | Yalnız eksiklik kontrolü |
|---|---:|---:|---:|
| 500 m / 24 saat | 0,732975 | 0,748275 | 0,527743 |
| 500 m / 48 saat | 0,734707 | 0,757103 | 0,527306 |
| 500 m / 72 saat | 0,733565 | 0,764061 | 0,527009 |
| 1 km / 24 saat | 0,751178 | 0,768356 | 0,527367 |
| 1 km / 48 saat | 0,752466 | 0,772679 | 0,529322 |
| 1 km / 72 saat | 0,750973 | 0,777376 | 0,529021 |
| 2 km / 24 saat | 0,756193 | 0,778784 | 0,528869 |
| 2 km / 48 saat | 0,756560 | 0,779289 | 0,530883 |
| 2 km / 72 saat | 0,755709 | 0,780221 | 0,530442 |

RF bu örneklemde dokuz ayarda lojistikten yüksek yardımcı AUC verdi;
bu istatistiksel anlamlılık veya gerçek yangın başarım üstünlüğü
kanıtı değildir. Eski Mersin 708/168 pilotu farklı kaynak, anahtar ve
U bileşimine sahip; onun ölçüsüyle iyileşme/kötüleşme oranı kurulmadı.

## Ayrı model ve ön işleme geri okuması

27 model dosyasının ve 27 tahmin CSV'sinin güncel hash'i kontrol edildi.
Her CSV'nin anahtar ve S grubu özgün rol tablosundan ayrı kuruldu.
Modeller yalnız kendi doğrulanmış yerel dosyalarından açıldı;
bütün tahminler kaydedilen CSV değerleriyle birebir eşit.

Fit medyanları doğrudan fit matrisinden yeniden hesaplandı; eksiklik
göstergesi sütunları ve ölçekleme ortalama/varyansları karşılaştırıldı.
Tahmin sonrası öğrenilmiş model durumu değişmedi. ROC-AUC ayrıca
vektör hesabından bağımsız, standart skaler bütün çift döngüsüyle
kontrol edildi. Bunlar teknik tekrar üretimdir; bağımsız fiziksel
olay veya saha doğrulaması değildir.

## Aynı skorların mevsim örtü il ve eksiklik tanısı

Yeni fit yapılmadan kayıtlı RF skorları daha benzer çiftlerde okundu.
2017 hücre orman+çalı oranının %50 bandı yalnız geniş tanısal
sınıflama; habitat dışlama veya yeni kabul eşiği değil. Ortak il
alanı, iki hücrenin en az bir ilde pozitif kesişim alanı bulunmasıdır.
Bir çift sınırda iki ili paylaşsa da yalnız bir kez sayıldı.

| Sabit RF skorlarının karşılaştırması | Dokuz ayardaki yardımcı AUC aralığı | Karşılaştırma desteği |
|---|---:|---|
| Bütün aday–U çiftleri | 0,748275–0,780221 | 86.000–96.800 çift, bütün 400 U |
| Aynı ay | 0,735559–0,772193 | 6.804–7.669 çift, bütün 400 U |
| Aynı ay + aynı örtü bandı + ortak il alanı | 0,727735–0,766310 | 1.027–1.179 çift; 202–228 aday ve 317 U karşılaştırma buluyor |
| İki satırda da 27 özellik tam | 0,741867–0,772878 | 70.350–78.750 çift; 350 U |

Dar karşılaştırmada **83 U ve ayara göre 13–14 aday** karşı grup
bulamıyor; kayıtlar silinmedi. Farklı çift havuzlarının AUC farkı
nedensel yanlılık düzeltmesi veya düzeltilmiş yangın başarımı değil.
Tam özellikli karşılaştırma ve eksiklik kontrolü, gözlenen ayrımın
tamamının bu beş eksiklik bayrağına indirgenmediğini gösterir;
diğer seçilme/örtü/kaynak etkilerini ortadan kaldırmaz.

İl alanı kesitlerinde sabit RF'nin yardımcı sonuçları:

| İl alanı | 2022 aday anahtar aralığı | U anahtarı | Yardımcı S AUC aralığı |
|---|---:|---:|---:|
| Antalya | 55–61 | 144 | 0,802823–0,836742 |
| İzmir | 53–58 | 86 | 0,654771–0,728170 |
| Mersin | 72–77 | 87 | 0,791014–0,820130 |
| Muğla | 36–48 | 90 | 0,711728–0,745185 |

İl üyelikleri sınır hücrelerinde kesişebilir; sütunlar toplanmaz.
Bu tek yılın örneklem tanısı dört ilde eşit genellenebilirlik veya
bağımsız olay başarımı kanıtlamaz. Özellikle İzmir'deki yardımcı
ayrım diğer illerle aynı düzeyde varsayılmamalı.

## Aynı U kayıtlarının sıralama duyarlılığı

Dokuz RF aynı 400 U'yu skorladı. 36 ayar çifti için Spearman
korelasyonu **0,970092–0,990483**, ortanca 0,983725. Bununla birlikte
en yüksek skorlu 40 U'nun **27–38'i** iki ayarda ortak; ortanca 33.
Jaccard aralığı 0,509434–0,904762, ortanca 0,702128.

Liste kuralı 40. sıradaki bütün eşit skorları korur; bu koşuda sınır
eşitliği olmadığı için her ayarda liste 40 kayıttır. Bunlar yangın
vakası/uyarı doğruluğu değil, aynı U havuzunun model sırası tanısıdır.
Yüksek genel korelasyon üretim uyarı listesinin değişmez olduğu
anlamına gelmiyor. Bu nedenle tek ayarı doğru ilan etmek veya renk
eşiği seçmek için kullanılmadı.

## Sonraki sınırlı araştırma sorusu

Bu deney tamamlandı. Açık kalan somut konu: yardımcı ayrımın ne
kadarı değişen hava koşullarından, ne kadarı statik orman/çalılık
ve arazi bağlamından geliyor? Öneri seçimi 2017 örtüsünü kullandığı
için statik örtü üzerinden adaylığı ayırmak tek başına ertesi gün
yeni yangın riskine ilişkin zamansal kanıt değildir. Geniş örtü
bandındaki tanı bu iki katkıyı doğrudan ayırmıyor.

Bir sonraki somut öneri, bütün dokuz ayarda aynı satırlarda **yalnız
11 meteoroloji özelliği** ve **yalnız 12 statik örtü/arazi özelliği**
ile aynı küçük RF'yi kurmak: en çok **18 ek yardımcı fit**. Mevcut
tam RF sonuçları yeniden fit edilmeden karşılaştırılacak. Seed,
hiperparametre, zaman/satır rolleri ve U aynen kalacak; veri dosyaları
değişmeyecek. Kullanılmayan X grupları yalnız bellek kopyasında boş
bırakılıp fit-only sütun seçimiyle modele girmeyecek. Bu ablation
nedensel özellik etkisi, PU varsayımlarının kanıtı veya gerçek yangın
başarımı sağlamaz; statik seçilme ile günlük bilgi ayrımını sınar.

Yeni plan hazır ve ek **fit yapılmadı**. Önceki izin en çok 27 modeli
kapsadığından bu 18 ek model için ayrı araştırmacı kararı gerekir.
2023–2025 değerleri, yeni Y/L, ana yangın modeli, risk renkleri ve
nihai birleştirme kapıları kapalı kalır. Gerçek hedefe aktarım/PU
varsayımları ve uygun değerlendirme dayanağı birinci aşamanın açık
bilimsel konularıdır; bu model sayımları onları kapanmış göstermiyor.

## Yeniden üretim ve yerel deney kaydı

`outputs/reports/dataset/` altındaki kimlikler:

- Deney: `satellite_PU_ranking_run_v1/20261120T012805Z_04789b23/readback.json`,
  SHA-256 `971b85def11809d0d48f4a3618233588e6a7022e7ddea5861fb94054cbcb84a1`.
  Yeni A kararı `configs/satellite_pu_ranking_execution_v1.json` içinde,
  önceki donmuş plan SHA'sına bağlıdır; hazırlık ayarı değiştirilmedi.
- Ayrı model/ön işleme/skaler AUC ve bağlam tanısı:
  `satellite_PU_ranking_audit_v1/20261120T013224Z_b8a45358/readback.json`,
  SHA-256 `19f67bcfecf918804a7365ee1c7d7bfc53da3e9956a87004ac275aa29f2f8f47`.
  `auxiliary_diagnostics.png` görsel olarak okundu; eksenler, başlık,
  dokuz ayar ve gerçek yangın başarımı olmadığı notu görünür.
- Yerel MLflow: `satellite-source-ranking-pilot` deneyi, 27 yardımcı
  ölçü geri okundu; `mlflow_record.json` SHA-256
  `1aac39c8e350cad316c7763333d3fac8b2486c69de32c3ceef85b3cc7e6592b6`.
  Yazmadan önce SQLite yedeği alındı. Dış izleme sunucusu/ortam URI'si
  kullanılmadı; ana model registry kaydı oluşturulmadı.
- Yeni ablation önerisi:
  `satellite_PU_ablation_plan_v1/20261120T013805Z_c4e80dce/readback.json`,
  SHA-256 `408ca6c8edba32c7c67668819fc9588868b3bce358cd38fcfe06d64a6b93d0f5`.
  `run_satellite_pu_ablation_pilot.py` varsayılan olarak yalnız hazırlık
  yapar; önceki 27-fit kararıyla yeni modeli başlatmayı reddeder.

Son koşuda sekiz yeni davranış dahil **54 ilgili test** geçti.
Üç yeni betik ve iki test dosyasının (beş Python dosyası) kod/biçim
kontrolü geçti. Eşit skor, eşit olmayan tabaka büyüklükleri, boş
karşılaştırma, ortak il sınırında çift saymama, liste sınırı eşitliği,
yanlış özellik grubu ve eski izinle yeni fit başlatmama sınandı.
Geliştirme sırasında yakalanan döngü değişkeni bağlama/uzun satır
uyarıları gerçek denetim çıktısı üretilmeden düzeltildi. Önceki
289 test bu koşunun yeni test sayısı gibi sunulmadı.
