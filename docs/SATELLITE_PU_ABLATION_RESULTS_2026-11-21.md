# Meteoroloji ve statik bağlam karşılaştırmasının sonuçları

Rapor ve devam kontrolü: **21 Kasım 2026**. Model deneyi ve ayrı ilk
geri okuma **20 Kasım 2026** tarihinde tamamlandı. Limit kesintisi
sonrasında 18 model yeniden eğitilmedi; mevcut modeller, skorlar,
girdi/üretici kimlikleri ve ayrı denetim makbuzu doğrulandı.

Araştırmacının onayladığı 18 ek RF karşılaştırması tamam. Yalnız
statik örtü/arazi modelinin yardımcı aday ayrımı, dokuz ayarın
altısında tam RF'den yüksek. Bu örneklemde güçlü bir alan ayrımı
bulunuyor; günlük yeni yangın riskinin doğrulandığı söylenemez.
**Aynı hücre ve aynı ay içindeki mevcut karşılaştırma yalnız üç
aday–U çiftine dayanıyor.** Sıradaki somut açık, günler arasındaki
ayrımı incelemeye yetecek karşılaştırma desteğidir.

## Gerçekleştirilen sabit deney

Önceki [27 modelin donmuş planı ve sonuçları](SATELLITE_PU_PILOT_RESULTS_2026-11-20.md)
korundu. Dokuz ayarın her birinde yalnız 11 meteoroloji ve yalnız
12 statik örtü/arazi özelliğiyle iki RF kuruldu: toplam 18 yeni
model. Tam 27 özellikli RF yeniden eğitilmedi. Aynı seed, 100 ağaç,
derinlik 6 ve en az 5 yaprak örneği kullanıldı. Medyan doldurma ve
eksiklik göstergeleri yalnız fit kesitinden öğrenildi; dışarıda kalan
özellik grupları yalnız bellek kopyasında boş bırakılıp fit-only
sütun seçimiyle çıkarıldı. Kaynak özellik dosyaları değiştirilmedi.

Fit dönemi 2018–2021; 2022 tanısal incelemesi daha önce görüldüğü
için kör test değil. Her ayarda aynı 1.648 fit / 400 inceleme U
korundu; aday anahtarı sayısı ayara göre değişiyor. Yardımcı S=1
olası uydu önerisi üyeliği; S=0 belirsiz U örneği. Y gerçek yangın
etiketi ve kabul edilmiş L boş. Yeni risk rengi/yangın olasılığı,
2023–2025 erişimi veya nihai birleştirme yapılmadı. Yerel yürütücü
15 dakika üst sınırıyla çalıştı; bulut kullanılmadı.

## Aynı inceleme satırlarındaki yardımcı aday AUC

| Ayar | Yalnız meteoroloji | Yalnız statik örtü/arazi | Önceki tam RF |
|---|---:|---:|---:|
| 500 m / 24 saat | 0,665325 | 0,764509 | 0,748275 |
| 500 m / 48 saat | 0,666836 | 0,758907 | 0,757103 |
| 500 m / 72 saat | 0,665881 | 0,755997 | 0,764061 |
| 1 km / 24 saat | 0,664333 | 0,780272 | 0,768356 |
| 1 km / 48 saat | 0,660925 | 0,778021 | 0,772679 |
| 1 km / 72 saat | 0,666273 | 0,773603 | 0,777376 |
| 2 km / 24 saat | 0,664858 | 0,785273 | 0,778784 |
| 2 km / 48 saat | 0,656835 | 0,780883 | 0,779289 |
| 2 km / 72 saat | 0,658628 | 0,778012 | 0,780221 |

Bunlar yangın tahmini doğruluk yüzdesi değil; gözlenen aday–U
çiftinde skor sırasının, eşitliklere yarım pay veren ölçüsüdür.
Ayarlarda kaynak grubu değiştiğinden tablo üretim ayarı seçimi
veya hiperparametre yarışı yapılmadı. Statik modelin altı ayarda
daha yüksek olması nedensel katkı ya da istatistiksel anlamlılık
kanıtı değil. Fakat mevcut toplam ayrımı doğrudan günlük hava
başarımı diye sunmama gereğini somutlaştırıyor. Aday hazırlığında
2017 örtüsü de kullanıldığından statik bağlam ile seçilme ilişkisi
gerçek yangın eğiliminden ayrıca ayrılmalıdır.

## Aynı yer ve benzer mevsimde ne kadar karşılaştırma var

Yeni model kurmadan üç sabit RF sürümü aynı kayıtlarda incelendi:

| Karşılaştırma | Yalnız meteoroloji yardımcı AUC | Yalnız statik yardımcı AUC | Destek |
|---|---:|---:|---|
| Bütün aday–U çiftleri | 0,656835–0,666836 | 0,755997–0,785273 | 86.000–96.800 çift; 400 U |
| Aynı ay ve ortak il alanı | 0,631506–0,658248 | 0,773637–0,804550 | 1.786–2.023 çift; bütün adaylar ve 353 U karşı grup buluyor |
| Aynı hücre, farklı veya aynı ay | 0,728571–0,785714 | 0,500000 | 34–35 çift; 29–30 aday ve 29–30 U |
| Aynı hücre ve aynı ay | 0,666667 | 0,500000 | Yalnız 3 çift, 3 aday ve 3 U |

Ortak il, hücrelerin en az bir ilde pozitif alan kesişimi bulunması;
sınırda iki ortak il olsa da çift bir kez sayıldı. Kısıtlı
karşılaştırmada karşı grup bulmayan kayıtlar silinmedi. Tabakalar
arasında çift bileşimi değiştiği için farklar nedensel düzeltme
veya düzeltilmiş yangın başarımı değildir.

Statik model, dokuz ayarın tamamında aynı hücreye bütün incelenen
günlerde **birebir aynı skoru** verdi; statik girdiler de aynı.
Bu yüzden aynı hücredeki çift AUC'sinin 0,5 olması beklenen ve
doğrulanmış bir özelliktir. Bu model alanları ayırabilir, tek
hücrenin hangi gün daha riskli olduğunu kendi başına ayıramaz.

Üç çiftte 0,666667, üç sıralamanın ikisinde adayın yüksek olmasıdır;
güvenilir bir günlük genelleme sonucu değildir. Tam RF'nin sekiz
ayarda 2/3, bir ayarda 3/3 vermesi de bu eksik desteği kapatmaz.
Mevcut 400 U, alan genelindeki örneklem amaçlı seçilmişti; bu
dar zaman karşılaştırması için yeterince aynı hücre–ay karşılığı
sağlamıyor. Bu bulgu veri bozulması veya meteorolojinin işe
yaramadığı sonucu olarak yorumlanmadı.

## Teknik kapanış

18 model ve 18 tahmin CSV'si güncel hash'leriyle doğrulandı.
Öngörüler kayıtlı modellerden birebir yeniden üretildi; yalnız
izin verilen 11/12 özelliğin tutulduğu, medyanlar ve eksiklik
göstergelerinin fit matrisinden geldiği ayrıca kontrol edildi.
Tahmin model durumunu değiştirmedi. AUC, bağımsız skaler bütün
çift hesabıyla yeniden doğrulandı. Önceki tam RF skorları salt
okundu. Bu teknik doğrulamalar bağımsız saha/olay doğrulaması değil.

21 Kasım'da yerel MLflow'a 18 ölçü kaydedilip geri okundu; önce
SQLite yedeği alındı. Dış izleme hizmeti veya model registry kaydı
yok. Grafik asistan tarafından görsel olarak okundu; bu kullanıcı
veya saha uzmanı onayı olarak yazılmadı.

## Seçilmemiş sonraki yöntem önerisi

Öneri, olası adayların bulunduğu **aynı hücre, aynı yıl ve aynı
aydaki bütün uygun günleri** ayrı bir takvim kontrolü için
incelemek. Aday günü de havuzda kalacak; uydu tespiti veya aday
varlığı nedeniyle gün ayıklanmayacak. Yalnız mevcut dönemlerin
hedef pencere sınırını geçen günler kullanılmayacak.

21 Kasım metadata hazırlığında somut kapsam hesaplandı:

- Dokuz ayarın 1.670 olası öneri anahtarından **1.443 hücre–yıl–ay**.
- **44.082** takvim hücre-günü: 37.509 fit-rolü / 6.573 adet 2022
  inceleme-rolü. Gerçek Y ve kabul edilmiş L tamamında boş.
- Mevcut X incelemesinden 1.689 anahtar var: 1.670 öneri ve özgün
  U'dan 19 anahtar. **42.393 ek X anahtarı** incelenmesi gerekir.
- 1.824 farklı gün için 3.648 günlük özellik/provenance dosyası
  yerel indeks ve dosya boyutunda mevcut. Tamamı okunsa indeksli
  kaynak boyutu 8.036.952.623 bayt; bu ağ indirmesi veya tahmini
  çalışma süresi değil. Bu hazırlıkta günlük dosya içerikleri
  açılmadı/yeniden hash edilmedi; varlık/boyut kontrolü yapıldı.

Bu bir **yöntem yönü önerisi**, seçilmiş yeni U örneklemi veya
kabul edilmiş özellik kohortu değil. Özgün 2.048 U ve edinim
ağırlıkları değişmeden kalıyor. Aday görülmüş hücre/aylara
koşullandığı için yeni havuz dört ilin tüm hücre/günlerini temsil
eden veya operasyonel/kör başarı testi sayılmayacak. Aday bulunmayan
günlere yangın yok etiketi atanmayacak; gözlem durumu unknown kalacak.

Araştırmacıya A olarak bu ayrı kontrolün yalnız özellik/zaman/
eksiklik hazırlığı, B olarak havuz açmadan mevcut bulguları görüşme
seçenekleri sunuldu. Henüz yeni yön seçilmedi; yeni özellik
çıkarımı, ek model veya nihai birleştirme başlatılmadı. Bu kontrol
tek başına gerçek pozitiflik, PU karışım varsayımları ve uygun
bağımsız değerlendirme sorunlarını çözmüş sayılmayacak. Birinci
aşamanın bilimsel kabulü açık kalıyor.

## Yerel makbuzlar ve kontroller

`outputs/reports/dataset/` altında:

- Deney: `satellite_PU_ablation_run_v1/20261120T014426Z_44c25642/readback.json`,
  SHA-256 `fa9321e6268ffba478c6250d6cc32b0d5516ce3b872b9a8271920edb9d1d3324`.
  Yeni 18-fit A kararı `configs/satellite_pu_ablation_execution_v1.json`;
  önceki hazırlık planı değiştirilmedi.
- Ayrı kontrol: `satellite_PU_ablation_audit_v1/20261120T014740Z_3cdb2359/readback.json`,
  SHA-256 `783d2678aa895aafcf3a388e634ac12fe567fb0e40a3affcdbeae7c450fd45c0`.
- Yerel MLflow makbuzu: deney klasöründeki `mlflow_record.json`, SHA-256
  `632380c9a0ca4391377252adbe711c08d40d4d3ce2fdfa921e11732954477278`.
- Seçilmemiş takvim kontrolü kapsamı:
  `source_calendar_control_proposal_v1/20261121T160611Z_9e76a4ab/readback.json`,
  SHA-256 `ee08ef36aefab7ae66b2c2c7ff87f0cc5d10d8d077e1cafad61c5d202ca9a6e5`.
  Metadata CSV'si anahtar ve boş hedefler düzeyinde geri okundu;
  yeni X veya S/Y kabulü içermez.

21 Kasım son koşuda **62 ilgili test** geçti. İki ablation tanı testi
ile altı takvim kapsamı testi bu sayıya dahil; önceki 56 test
güncel yeni test sayısı gibi sunulmadı. Beş Python dosyası kod ve
biçim kontrolü geçti. Aynı hücrede statik skor değişmezliği, ince
karşılaştırmada kayıt koruma, Şubat artık günleri, kaynak gününü
dışlamama, yıl/24 saat sınırı, kapalı yıllar ve hazırlık iznini
kendiliğinden açmama sınandı. Model üreticileri ve geçmiş sonuç
makbuzları değiştirilmedi.
