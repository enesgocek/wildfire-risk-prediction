# Kaynak koşullu PU pilot protokolü — 19 Kasım 2026

**Araştırmacı A'yı seçti:** Mersin arşivini konum/zaman hatası içerebilen
ayrı bir kaynak olarak sınayacak pilot protokolü hazırlandı. Bu karar
genel kaynak kullanımının araştırılması içindir; yeni L üyeliği, Y=1,
eğitim, yöntemin bilimsel kabulü veya nihai birleştirme onayı değildir.
[Kararın sayısal dayanağı](SOURCE_COHORT_DIRECTION_2026-11-19.md).

**Tamamlanan:** sürümlü karar ve protokol, dokuz çevrimdışı duyarlılık
senaryosu, aynı coğrafi alandaki U inceleme kesiti ve olası anahtar
çakışmalarının bölünme hazırlığı. **Açık kalan:** kaynak anlamının ana
24 saatlik hedefe bağlanması, PU varsayımları ve değerlendirme dayanağı.
Birinci aşama tamamlanmadı; gerçek veriyle karışım/model tahmini yapılmadı.

## Sabit kapsam ve korunacak kayıtlar

Kaynak birimi, aynı yayımlanmış arşivin 2018–2022 dönemindeki **424
satırı**; doğrulanmış bağımsız yangın değil. Önceki metadata hesabının
380 satırı duyarlılık odağıdır. 43 metadata sınırı olan satır ve WF1538
ayrı gerekçeleriyle korunur; hiçbir kaynak satırı silinmez. İlk dondurulmuş
10 kontrol satırı değiştirilmez veya ölçülemeyenler yerine başkası seçilmez.
Önceki iki olası L önerisi ve 2.048 U'nun gerçek dosyaları hash ile korunur.

Ana hedef, `(T,T+24 saat]` içinde yeni olayın ilk aktif yangın tespiti.
Kaynak saatinin adı, olay anlatımı veya yayımlanmış nokta bu hedefi
kendiliğinden doğrulamaz. 2018–2022 fit yönü korunur; 2023 kalibrasyon,
2024 karşılaştırma ve 2025 final bilimsel değerleri açılmaz. Bu pilotta
hedef sağ ucu 1 Ocak 2023'e değen pencere fit dışında işaretlenir.

## Ölçülen konum ve zaman duyarlılığı

Merkez ile **250/1.000 m EPSG:6933 düzlem çevreleri**, önceki incelemelerle
uyumlu keşif senaryolarıdır. Çevreler ölçülmüş GPS hata sınırı veya güven
aralığı değildir; izdüşüm düzlemi uzaklığı gerçek jeodezik hata sayılmaz.
Çember 64 çeyrek-daire segmentiyle yaklaşıklandı. Sıfır yarıçapta noktayı
kapsayan, diğerlerinde pozitif alanla kesişen korunmuş hücreler saklandı;
en yakın hücreye zorlama veya birden fazla hücreyi pozitif yapma yok.

| 380 kaynak satırında çevre | Tek hücre | İki hücre | Üç hücre | Dört hücre |
|---|---:|---:|---:|---:|
| Yayımlanmış merkez | 380 | 0 | 0 | 0 |
| 250 m düzlem çevresi | 320 | 58 | 0 | 2 |
| 1.000 m düzlem çevresi | 161 | 169 | 16 | 34 |

250 m senaryosunda **60/380**, 1 km'de **219/380** kayıt birden fazla
hücreyle kesişiyor. Somut olarak, hücre kenarına yakın bir nokta merkez
olarak tek hücre verirken çevresi komşu hücreye taşabiliyor. Bu bulgu
gerçek konum hatasının 250 m veya 1 km olduğunu göstermiyor; merkez
varsayımının duyarlılığını gösteriyor. Hiçbir seçenek gerçek tutuşma yeri
veya kabul edilmiş L ataması olarak seçilmedi.

İki saat yorumu korunarak odaktaki ortak pencereye **−1/0/+1 gün**
kaydırma uygulandı. Bunlar ölçülmüş uydu gecikmeleri değil; kaynak zamanını
ilk tespit zamanına eşitlemenin etkisini araştırmaya hazırlık. Uyduya
eşleşen gün seçilmedi. 3 konum × 3 gün = dokuz senaryo var.

| Konum senaryosu | −1 gün farklı fit anahtarı | Aynı gün | +1 gün |
|---|---:|---:|---:|
| Merkez | 374 | 374 | 373 |
| 250 m çevresi | 436 | 436 | 435 |
| 1 km çevresi | 671 | 671 | 669 |

Sayılar farklı **hipotez hücre-günleri**, yangın veya eğitim satırı değil.
+1 günde bir kaynak kaydının alternatifi fit sağ ucunun dışına çıkıyor;
silinmeden `inside_fit=false` tutuldu. Merkez/+1 gün anahtarlarından biri
mevcut U ile kesişiyor. U örneği çıkarılmadı; U'nun gerçek negatif olduğu
varsayılmadığından bu tek başına çelişkili etiket değildir.

## Kaynak ile belirsiz havuzun coğrafi karşılaştırması

U'nun 2.048 anahtarı dört ilin 2.889 su-kuralını geçen hücresinden
seçilmişti; kaynak yalnız Mersin. Bu iki kapsam doğrudan aynı sınıf
koşullu nüfus sayılmaz. Sadece coğrafi destek incelemesi için, Mersin ile
pozitif alan kesişimi olan **734 korunmuş hücre** tanımlandı. Sınırdan
yalnız çizgiyle değmek bu alan kuralını karşılamıyor. Karma hücreler
orman yüzdesiyle elenmedi; bu yeni kabul edilmiş risk yayımlama alanı değil.

Önceki U'nun **503 satırı** bu hücrelerde. Bu satırlar özgün sıra ve
değerleriyle ayrı CSV'ye kopyalandı; 2.048 satırlık asıl U değişmedi.
Yeniden örnekleme, yangın/uydu/örtü filtresi veya anahtar çakışması silme
yapılmadı. CSV'deki özgün örnekleme olasılığı/ağırlığı da korundu;
bunlar yeni Mersin eğitim ağırlıkları olarak kabul edilmedi. Kesitin
büyüklüğü istatistiksel yeterlilik veya gerçek pozitif/negatif kanıtı değil.

Kaynak satırı, farklı merkez anahtarı ve U kesiti için yıl/ay sayımları
ayrı saklandı. Marjinal takvim dağılımlarının farklı olması tek başına
seçilme yanlılığı veya ortak sınıf koşullu dağılım ihlali testi değildir;
yangın sıklığı ve karışım oranı da farklı olabilir. Coğrafi kesit almak
SCAR, sınıf koşullu eşitlik veya pozitifçe zenginleşmeyi doğrulamıyor.

## Aynı devamda mevcut örtü kanıtının fit havuzuna aktarımı

Yeni raster üretmeden, önceki hash ile bağlı CORINE ortak kanıt tablosu
bu havuza bağlandı. Önce kaynak yılı ve kimliği seçildi, sonra yalnız
odaktaki 380 satırın örtü alanları kullanıldı. 2023 satırlarının örtü
değerleri bu hesapta kullanılmadı. 380 satırın tamamının önceki harita
kanıtı var; eksik olanları sessizce düşüren alt küme yapılmadı.

| CORINE 2018 merkez bağlamı | Kaynak satırı |
|---|---:|
| Orman/çalılık | 266 |
| Tarım | 103 |
| Diğer | 11 |

Orman/çalılık merkezli 266 satırın **102'sinde 250 m**, **202'sinde 1 km**
çevrede tarım piksel örneği var. Tarım merkezli 103 satırın **63'ünde
250 m**, **96'sında 1 km** çevrede orman/çalılık örneği var. Bunlar eski
üreticide çember içinde kalan raster piksel merkezlerinin varlık sayımları;
örtü alan oranı, yangın tipi veya başlangıç alanı değil. Yeni 64 segmentli
geometri hesabıyla aynı piksel örneklemesi yeniden yapılmış sayılmadı.

Bu bulgu, tarım merkezini otomatik silmemenin somut gerekçesini gösteriyor:
yakınında odunsu örtü bulunabiliyor. Tersi de geçerli; orman merkezli kayıt
tamamen doğal örtülü bir başlangıcı doğrulamıyor. 2018 haritası olay günü
örtüsü değildir; orman/çalılık sınıf grubu 311/312/313/322/323/324,
tarım grubu 200–299. Kabul edilmiş bir eşik veya filtre uygulanmadı.
WF1538 odak dışında, diğer 43 kaynak satırı ana protokolde korundu.

## Aynı belirsizliğin eğitim ve karşılaştırmaya dağılmasını önleme hazırlığı

Her kaynak satırının alternatifleri kendi kimliğine bağlı. 1 km ve üç
gün hipotezlerinde ortak hücre-gün taşıyan satırlar için olası bağımlılık
bağlantıları hesaplandı. Geçişli bağlantıda **31 kaynak satırı, 14 çoklu
blokta**; kalan tekillerle toplam 363 hipotez bileşeni var. Bunlar 363
bağımsız yangın değildir. Kaynak kayıtları birleştirilmedi/silinmedi.

İleride gerçek fold tasarımında aynı kaynak alternatiflerini veya
anahtarı paylaşan bu kayıtları karşılıklı eğitim/değerlendirme tarafına
dağıtmamak için bu liste kullanılabilir. Gerçek fold ataması, fiziksel
olay gruplaması veya bağımlılığın tamamen giderildiği kabulü yapılmadı.
Bu bloklar daha geniş mekânsal/zamansal bağımlılığı da tek başına çözmez.

## Geçiş, durdurma ve başarısızlık koşulları

| Konu | Şimdi | İleri kullanım koşulu |
|---|---|---|
| Dosya, kapsam, anahtar, boş hedef | Teknik kontrol geçti | Her yeni üretimde güncel hash ve şema yeniden kontrol edilir |
| Kaynak noktası ve kayıt birimi | Anlam/hata sınırı açık | Hücre üyeliğinin neyi temsil ettiği ve yanlış eşleşmenin nasıl ele alınacağı gerekçelendirilir |
| Kaynak saati → ilk yeni tespit | İlişki doğrulanmadı | Kaydırma sayısı kanıt yerine konmaz; başlangıç/devam ve hedef penceresi açıklanır |
| Yerel orman/çalılık | Bu çalışmada kabul edilmedi | Hücre kapsamından ayrı, mevcut örtü kanıtı ve belirsizlikleriyle incelenir |
| L'nin pozitifçe zenginliği, ortak sınıf koşulluları | Doğrulanmadı | Seçilecek yöntemin ilgili varsayımları için destek ve duyarlılık gerekçesi gerekir |
| Sınıf/gürültü oranları ve bileşenlerin anlamı | Tahmin yok | Tahmin edilebilirlik ve yangın sınıfına karşılık gelme gerekçesi kurulmadan oran raporlanmaz |
| AP/kalibrasyon ve değerlendirme | Çalıştırılmadı | U'yu negatif saymadan uygun referans veya gerekçeli PU düzeltmesinin koşulları sağlanır |

Kusursuz kaynak koordinatı, hatasız bütün pozitifler veya kesin dış sınıf
oranı tüm PU yöntemlerine zorunlu koşul yapılmıyor. Ancak seçilen yöntemin
kendi varsayımları gerekçelendirilmeli. Önceden incelenen
[hata içerebilen PU çalışmaları](NOISY_POSITIVE_PU_PILOT_2026-11-19.md#yöntem-için-yeni-kanıt)
bu varsayımları otomatik sağlamıyor. Kalite uyarısı, harita yüzdesi,
uydu eşleşme payı veya senaryoların aynı sonucu vermesi `beta` ya da
yanlış etiket oranı sayılmaz. L/U ayırt etme başarısı gerçek yangın AP'si
veya kalibrasyonu olarak raporlanmaz.

Dosya/hash veya kapalı izin kontrolü bozulursa teknik işlem durur. Kaynak
rolü ile ana hedef arasındaki ilişki ya da yöntem varsayımları desteklenmezse
bu kaynak yolu eğitim için kullanılmaz; aynı kontrolleri tekrar saymak
eksik kanıt yerine konmaz. Başka hedefe geçiş veya yeni bilimsel varsayım
ayrı somut karardır. Bu protokolün hazırlanması böyle bir kabul değildir.

## Yerel çıktı, kontroller ve katkı

Karar ve sınırlı çalışma düzeni [yeni ayarda](../configs/source_conditioned_pu_protocol_v1.json)
kayıtlı. Keşif geçmişi biliniyor; bu kör veya ön kayıtlı bir deney olarak
sunulmadı. Çalışma yalnız açık yerel metadata/geometriyi kullandı; yeni
indirme, özel giriş, yazışma veya ücretli bulut işi yok.

Üretici `scripts/quality/prepare_source_conditioned_pu_protocol.py`.
Yeni protokol, örtü aktarımı ve ilgili önceki kodlarda **74 davranış testi**, Ruff ve biçim
kontrolü geçti. İlk yazımın JSON anahtar türü uyuşmazlığı geri okumada
reddedildi; eski çıktı korundu, açık metin anahtarlarıyla yeni sürüm
üretildi. Başarısız ilk çalışma başarılı makbuz sayılmadı.

Ayrı tüm-grid kesişimi 1.140 konum seçeneğini, saat hesabı dokuz senaryoyu
ve CSV geri okuması 503 özgün U satırını doğruladı. Son bağımlılık listesi
ayrıca bütün kaynak çiftlerinin ortak anahtarlarıyla kurulan grafik
üzerinden kontrol edildi. Aynı geometri kütüphaneleriyle otomatik geri
okuma, bağımsız saha veya insan doğrulaması değildir.

- Sonuç klasörü: `outputs/reports/dataset/source_conditioned_pu_protocol_v1/20261119T200942Z_3bc1ded8`.
- `readback.json` SHA-256:
  `c22b246a5f93563115a193de7022d63accdabb18938ac5a635f4916ff3951df9`.
- `verification.json` SHA-256:
  `a2194ad02da69cec261e2cd0688b1beba194eb812cc706ef0f0914dd533bbcb5`.
- `separate_readback.json` SHA-256:
  `372ff58247852a65d474bb1f62f3bf1e4054eb1bcf1af39203ec671b157b28b7`.
- `U_Mersin_geographic_review_slice.csv` SHA-256:
  `2f335ecd407d7ad24995fb241f29f03d99b81e5a09e7632faf5d39c6eff4fe5c`.
- Örtü aktarımı: `outputs/reports/dataset/source_conditioned_cover_v1/20261119T201522Z_a6cfc04a/readback.json`;
  SHA-256 `7d5e8bf54466057e7ebcc282e61f0fd8f5fcfd64a134eb2771f9fb154627709f`.
  Aynı klasördeki `separate_readback.json` SHA-256
  `535aac33e87e3fa7672f2c94c2622208fce6853520ef39bb64fe183912ca8c55`.
  380 kaynak anahtarı, eski piksel sayımları ve boş hedefler ayrıca geri okundu;
  bu yeni saha veya olay örtüsü doğrulaması değildir.

Protokol ve otomatik ölçümler yapay zekâ desteğiyle hazırlandı; A yönü
araştırmacıya ait. Yeni L ve ikili etiket **0**; bütün kaynak hedefleri
boş, üyelikleri incelemede. Günlük gözlem `unknown`, pozitif/negatif
izinleri kapalı. Önceki öneriler/U ve nihai birleştirme onay kuralı korundu.
