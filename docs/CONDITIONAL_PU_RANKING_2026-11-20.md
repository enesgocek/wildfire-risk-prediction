# Etiketsiz özellik incelemesi ve ilk koşullu sıralama pilotu — 20 Kasım 2026

## Aynı gün A kararı ve tamamlanan ilk pilot

Araştırmacı **A: sınırlı koşullu sıralama pilotunu çalıştır** yönünü seçti.
Yetki [ayrı yürütme kaydına](../configs/conditional_pu_ranking_execution_v1.json)
bağlandı; karar öncesi öneri ayarı ve makbuz değiştirilmedi. Aşağıdaki
karar bekleyen hazırlık açıklamaları önceki durumun kaydıdır. Yardımcı
kaynak üyeliği modeli kurma izni, ana yangın modeli veya gerçek etiket
kabulü olarak genişletilmedi.

708 anahtarla modeller kuruldu; 2022'nin 168 anahtarında kaynak/U ayrımı
incelendi. Yalnız **S** üyelik kodu gözlendi/öğrenildi: kaynak merkezi
hipotezi 1, U örneği 0. Gerçek yangın hedefi **Y bütün satırlarda boş**.
U'daki 0 gerçek yangın yokluğu değildir. 2023/2024/2025 değerleri açılmadı.

| Model / kontrol | 2018–2021 kaynak ROC-AUC | 2022 kaynak ROC-AUC |
|---|---:|---:|
| Lojistik regresyon | 0,851587 | 0,820065 |
| Random Forest | 0,934368 | 0,854264 |
| Yalnız eksiklik işaretleriyle lojistik kontrol | 0,565587 | 0,534483 |

Bu sütunlar **kaynak üyeliği ROC-AUC** değerleridir; gerçek yangın AUC,
AP, doğruluk yüzdesi, risk kalibrasyonu veya günlük yanlış alarm sonucu
değil. Random Forest'ın bu örnekte gözlenen AUC'si daha yüksek; örnek
bağımlılığı ve küçük inceleme havuzu nedeniyle kesin model üstünlüğü
veya istatistiksel anlamlılık ilan edilmedi. Bu sonuçla nihai model seçilmedi.

Eksiklik kontrolü 0,5 çevresinde kaldı; tam modellerin gözlenen ayrımı
yalnız bu beş eksiklik işaretiyle açıklanmadı. Bu bulgu kaynak seçilme
yanlılığını veya veri toplama etkilerini ortadan kaldırmıyor. Random
Forest'ın fit içi bölünme öneminde orman oranı, minimum/maksimum sıcaklık,
yükselti ve ortalama sıcaklık ilk beşte. Bunlar kaynak ayrımı ilişkileri;
yangın nedeni veya değişkenlerin gerçek yangın tahminine katkısı değil.

Medyanlar, eksik göstergesi sütunları ve ölçekleyiciler yalnız 708 fit
anahtarından öğrenildi. 2022 tahmini bu istatistikleri değiştirmedi.
Üç kaydedilmiş model aynı kaynak skorlarını yeniden üretti. 81 kaynak
ile 87 U arasındaki **7.047 çift**, eşitliklere yarım puan verilerek
ayrı sayıldı; üç AUC aynı bulundu. Fit medyanları ve gösterge sütunları
ayrıca yalnız fit verisinden kontrol edildi. Bütün gerçek Y'ler boş.

İlk deneme Random Forest'ın paralel olasılık toplamasında en çok
`2,22e-16` farkla birebir model geri okumasında durdu. Kısmi dosyalar
ve hata notu korundu; tamamlanmış pilot sayılmadı. Fit en çok iki işçi,
tahmin sabit sırayla tek işçi olacak şekilde yeni koşu yapıldı; birebir
kontrol gevşetilmedi. Hiperparametre araması veya başarımı artırmak için
ayar değişikliği yapılmadı. Yalnız tamamlanan koşu aşağıda referanslı.

Özellik hazırlığı, ayrım ve yürütmenin ilgili **120 davranış testi**,
kod/biçim kontrolü ve ayrı geri okumalar geçti. Bu teknik doğrulamalar
bağımsız yangın veya saha doğrulaması değil.

- Tamamlanan koşu: `outputs/reports/dataset/conditional_pu_ranking_run_v1/20261119T211947Z_fa2feb18/readback.json`;
  SHA-256 `a0b049c3e70042a97df40c5b13afc31c06fc35c5a027be5613fc96ba4cf63940`.
- Aynı klasörde `separate_readback.json`; SHA-256
  `56ce86a95eea9f7557489cc16d46f5bcc125ce187c4a827de2e541cc61b79245`.
- Kaynak skoru CSV'si ve `source_membership_diagnostic.png`, aynı koşunun
  hash bağlı çıktıları. Üç `.joblib` yerel kaldı; Git'e eklenmedi.
- Üretici: `scripts/quality/run_conditional_pu_ranking_pilot.py`.
  Python 3.12.14, scikit-learn 1.9.1, NumPy/pandas sürümleri ve fit
  istatistikleri makbuzda; model dosyaları kaynak üyeliği amacıyla kayıtlı.
- Yerel MLflow deneyi `conditional-source-ranking-pilot`, run
  `c44b7931ea194d5bb1655a9143b02d4a`, durum `FINISHED`. Mevcut SQLite
  veritabanı önce yedeklendi; yalnız çalışma alanındaki dosya/artifact
  deposu kullanıldı. Haricî servis veya model registry kaydı yok.
  Aynı koşunun `mlflow_record.json` makbuzu SHA-256
  `fe8976e8776b1f426618501834791f08142cfd256e82fadee8fe5a52a38ea9cd`.

**Kapanan iş:** kaynak koşullu yöntemin küçük veriyle teknik öğrenme ve
zamanla ayrılmış inceleme provası tamamlandı. **Açık kalan:** kaynak
hücre/gününün gerçek yeni orman/çalılık yangınıyla ilişkisi; ortak sınıf
koşulluları/pozitifçe zenginlik ve gerçek AP/kalibrasyon değerlendirme
dayanağı. Birinci aşama bilimsel olarak kapatılmadı. Sonraki iş bu
anlam/değerlendirme boşluğunu hedeflemeli; yalnız model büyütmek veya
aynı AUC'yi yeniden hesaplamak bu açığı kapatmaz. Ana 24 saatlik hedef,
AP tercihi, eski L/U ve WF1538 kararı, son parça kontrolü ve kullanıcı
onayına bağlı nihai birleştirme kapısı korunuyor.

## Karar öncesi hazırlık ve bilimsel gerekçe

**Tamamlanan:** sabit kaynak/U anahtarlarına ait 27 özellik ve ayrı
provenance tablosu hazır; geçmiş zaman kontrolleri ve somut pilot ayrımı
geçti. **Karar bekleyen:** ilk küçük yardımcı model pilotunu çalıştırmak.
Önceki A kararı protokol hazırlığıydı; buradan model kurma yetkisi
çıkarılmadı. Birinci aşamanın bilimsel kabulü ve nihai veri seti açık.

Çıktı kimlikleri UTC 19 Kasım 21.01/21.06; Türkiye saatiyle 20 Kasım
00.01/00.06. Kayıt bugünün çalışmasıdır; 19 Kasım bulguları değiştirilmedi.
Tahmini 1 Ocak 2027 teslimi ve 26–29 Kasım karar hedefi korunuyor.

## Gerçek inceleme tablosu hazır

380 kaynak satırı, aynı hücre-gündeki kayıtları ayrı gözlem saymadan
**374 farklı merkez anahtarına** bağlandı. Kaynak kimliklerinin tümü
ayrı mapping dosyasında korundu. Mersin kapsamındaki **503 U anahtarı**
ile birlikte **877 farklı anahtar** var; merkez anahtarlarında kaynak/U
kesişimi sıfır. WF1538 önceki kararla odak dışında; 424 satırlık kaynak
havuzundan hiçbir kayıt silinmedi.

667 seçili günde 1.334 feature/provenance dosyasının güncel hash'leri
kontrol edildi. Yalnız seçili hücrelerin 27 izinli özelliği ile ayrı
zaman/kalite kayıtları alındı. 2023 kalibrasyon, 2024 karşılaştırma ve
2025 final değerleri bu incelemeye alınmadı. İşlem 182,406 saniye sürdü;
bu yalnız bu küçük bağlantının süresidir, tam veri seti/eğitim tahmini değil.

| İnceleme grubu | Farklı anahtar | 27 özelliği tam | En az bir eksik |
|---|---:|---:|---:|
| Kaynak merkezi hipotezleri | 374 | 362 | 12 |
| Coğrafi U kesiti | 503 | 428 | 75 |
| Toplam | 877 | 790 | 87 |

Kaynak grubunun 12 anahtarında meteoroloji ailesi eksik. U'nun 17
anahtarında meteoroloji, 59'unda 30 günlük ve 19'unda 60 günlük bitki
örtüsü eksik. Bunlar örtüşen marjinal sayılardır; toplanarak eksik satır
sayısı yapılmaz. Eksikler doldurulmadı, sıfır yapılmadı ve satır çıkarılmadı.

`inspection.csv` incelenebilir sürümdür: 27 özelliğin yanında yalnız
inceleme kökeni, kaynak kayıt sayısı, boş hedef ve `unknown` gözlem
durumu var. Bu ek inceleme sütunları model girdisi değildir. Kaynak
grubuna ait olmak Y=1, U grubuna ait olmak Y=0 sayılmadı. Bu sınırlı,
etiketsiz örnek bağlantısı nihai etiketli eğitim birleştirmesi değildir.

Meteoroloji son kaynak saati T'den önce, pencere sonu T ile uyumlu;
bitki edinimi kendi kesim zamanından kesin önce ve kesim T'den sonra
değil. Yayın/operasyonel erişilebilirlik bilinmiyor ve bilinmeyen olarak
korundu; ERA5-Land retrospektif araştırma girdisidir. Statik harita
referans yılı 2017; bu kontroller olay günü örtüsünü doğrulamıyor.

## Yöntem için yeni, birincil dayanak

Menon, van Rooyen, Ong ve Williamson'ın ICML 2015 çalışması,
[PMLR kaydı](https://proceedings.mlr.press/v37/menon15.html) ve
[tam metni](https://proceedings.mlr.press/v37/menon15.pdf) üzerinden
doğrulandı. Ortak sınıf koşullu dağılımlar ve uygun karışım yönü altında
ROC-AUC optimizasyonu için gürültü oranlarını önceden bilmek gerekmiyor.
PDF s. 3'teki Sonuç 3 ve s. 4'teki Önerme 5 metinden ve görüntüden
incelendi. Bu nüfus düzeyindeki ilişki, sonlu bir modelin başarılı
olacağını veya projede koşulların sağlandığını göstermiyor. Sayısal
gürültülü AUC gerçek AUC ile aynı değil; AP/kalibrasyon muafiyeti çıkarılmadı.

### Proje notasyonuyla koşullu çıkarım

`a=P(Y=1|U)`, `b=P(Y=1|L)` olsun; burada L şimdilik **önerilen** kaynak
havuzudur, kabul edilmiş gerçek pozitif küme değil. Eğer L ve U aynı
gerçek pozitif/negatif özellik dağılımlarının karışımlarıysa ve `0<a<b≤1`
ise `r(x)=p_L(x)/p_U(x)` için:

`r(x) = (1-b)/(1-a) + [(b-a)/(a(1-a))] · P(Y=1|X=x,U)`.

Katsayı pozitif olduğundan ideal kaynak/U ayrım skoru gerçek posteriorla
aynı sıralamayı taşıyabilir. Benzer biçimde bu ortak karışımda:

`AUC_L,U(s) = (b-a) · AUC_Y(s) + (1-b+a)/2`.

Bu, değer eşitliği değil; varsayımlar altında optimizasyon yönü ilişkisi.
`a`, `b` burada tahmin edilmedi. Makalenin alpha/beta sembolleri farklı
anlamdadır; yukarıdaki notasyonla karıştırılmadı. Yalnız yüksek kaynak
ayrımı gözlemek, bu kaynakların gerçek yangın sınıflarına karşılık
geldiğini veya karışım varsayımını doğrulamaz. Konum/zaman ölçüm hatası,
kaynağın yer/mevsim/büyüklüğe bağlı seçilmesi ve yıllar arası değişim
bu ilişkinin projeye aktarımını bozabilir.

Bu ayrım gereksiz bir ön koşulu kaldırıyor: **ilk sıralama deneyi uygun
varsayımlarla önceden bilinen kesin hata oranı olmadan tasarlanabilir.** Buna karşılık gerçek
yangın olasılığı, AP, kalibrasyon ve günlük yanlış alarm iddiası için
uygun değerlendirme dayanağı hâlâ gerekiyor. AP ana araştırma ölçütü
olarak korundu; ROC yalnız önerilen yardımcı pilotun tanısıdır.

## Somut ve sınırlı pilot önerisi

Teklif [ayrı ayarda](../configs/conditional_pu_ranking_pilot_v1.json)
kayıtlı; bütün yürütme/etiket izinleri kapalı. Kaynak ve U kökeni için
yardımcı üyelik S öğrenilmesi öneriliyor; Y bütün satırlarda boş kalır.
U'ya verilen olası S kodu gerçek yangın yokluğu etiketi değildir.

| Önerilen bölüm | Kaynak anahtarı | U anahtarı | Toplam |
|---|---:|---:|---:|
| 2018–2021 model kurma | 292 | 416 | 708 |
| 2022 zamanla ayrılmış yöntem incelemesi | 81 | 87 | 168 |
| Sınır nedeniyle pilotta kullanılmayacak, dosyada korunan | 1 | 0 | 1 |

WF1608'in +1 gün alternatifi fit üst sınırına değdiği için tek anahtarı
önerilen pilot dışında tutuldu. Kaynak alternatifleri ve 14 olası
bağımlılık bileşeninin hiçbirinin iki bölüme dağılmaması kontrol edildi.
Anahtar ve olası 1 km/üç-gün desteklerinin bölümler arası kesişimi sıfır.
Bu, gerçek fiziksel olay veya bütün mekânsal bağımlılıkların çözüldüğü
anlamına gelmez. Gerçek bir fold/eğitim henüz çalıştırılmadı.

2022 verileri fit havuzu incelemelerinde daha önce görüldü. Bu bölüm
bağımsız/kör test değildir; 2024 karşılaştırma ve 2025 finalin yerine
geçmez. Mersin pilotu dört ilde başarı veya risk yayımlama izni sağlamaz.

Önerilen uygulama: sabit ayarlı lojistik regresyon ve küçük Random
Forest; ayar araması yok, tek tohum ve en çok iki işçi. Medyan doldurma,
eksik göstergeleri ve lojistik ölçekleme yalnız 2018–2021 parçasında
öğrenilir. İnceleme raporundaki tüm-dönem medyanları doldurma/ölçekleme
parametresi olarak kullanılmaz. Fit parçasında tamamen eksik sütun yok.

Eksikliğin kaynak ayrımını sürükleyip sürüklemediğini görmek için yalnız
beş özellik ailesinin eksik işaretlerinden oluşan küçük lojistik kontrol
önerildi. Bu işaretler gerçek yangın/gözlem doğruluğu değil; ölçüm
sürecine duyarlılık tanısıdır. Yardımcı ROC-AUC gerçek yangın AUC'si
veya AP'si diye adlandırılmaz; model skoru yüzde yangın riski sunulmaz.

**Öneri A:** bu sınırlı yardımcı sıralama pilotunu çalıştırıp veri/ölçüm
etkilerini ve zamansal aktarımı incelemek. Küçük bir modelin gerçekten
nasıl davrandığını görürüz; ana hedefe geçişin kanıtı ayrıca açık kalır.
**B:** model kurmadan kaynak–hedef ve gerçek değerlendirme kanıtını
incelemeye devam etmek. Bu yol doğrudan hedef dayanağına odaklanır;
kullanılabilir ek kanıt gelmezse yöntem denemesine geçiş sınırlı kalabilir.
Araştırmacının yönü bekleniyor. Tercihi bilimsel koşulların doğrulanması
veya nihai birleştirme onayı sayılmayacak.

## Kontroller ve izlenebilirlik

**112 ilgili davranış testi**, Ruff ve biçim kontrolü geçti. Rol sınırı
kaynak erişiminden önce kontrol edildi; anahtar, dosya değişimi, dizin
dışı yol, yinelenen kayıt, boş hedef ve sınır/bağımlılık davranışları
sınandı. Ayrı standart-kütüphane zaman hesabı 877 provenance satırını
kontrol etti. Görsel/otomatik okumalar bağımsız insan/saha doğrulaması değil.
İlk ayrı doğrulayıcı değişken kesirli ISO zaman biçimini tek biçim sanınca
durdu; kaynak değiştirilmeden açık ISO ayrıştırmayla kontrol tamamlandı.

- Özellik incelemesi: `outputs/reports/dataset/source_pu_feature_review_v1/20261119T210151Z_3e99d4a1/readback.json`;
  SHA-256 `ccc9086c505e22028a670ab9451e2323f429cd8048b83b4c2361519ec2916405`.
- Aynı klasörde `inspection.csv`; SHA-256
  `039b2aa8fc71a711fae990d545afb72cc1dbfdde1dd20ebee139d43556d5e4b2`.
- Özellik ayrı geri okuması SHA-256
  `747e211ff4149fee92be7511ca869b594b3dd7dd19e9c40d9cbb137f5e992562`.
- Ayrım önerisi: `outputs/reports/dataset/conditional_rank_partition_v1/20261119T210609Z_511e5d9f/readback.json`;
  SHA-256 `c2ffa568ec7138c734b71a70d5091ba1ca1de46c38e67d58dd90fcd00eb1a391`.
- Ayrım ayrı geri okuması SHA-256
  `c5384aaefaf0a8ca680022d15a6a7e5f487262151fc9e51fe2ab0efa30b53cd8`.
- [Birincil yöntem ve görsel inceleme kaydı](research/conditional_pu_ranking_evidence_2026-11-20.json).
  PDF 10 sayfa/344.714 bayt; SHA-256
  `5c20f1f2bd415493bbb77966ab9b6b1d1f26b8a4323206dae3df9172e96ded2f`.

Önceki L/U dosyaları ve WF1538 kararı korunuyor. Yeni L/gerçek ikili
etiket yok; yardımcı model/preprocessing kurulmadı. Gözlem `unknown`,
pozitif/negatif izinleri kapalı. Nihai parça denetimi ve rapora bağlı
birleştirme onayı geçerlidir; bu çalışma o onayı tüketmez.
