# Dört il uydu PU protokolünün başlangıç ve örtü hazırlığı — 20 Kasım 2026

Araştırmacının [A kararı](SATELLITE_PU_DIRECTION_2026-11-20.md) uygulandı.
Yerel fit kaynağının başlangıç geçmişi ve ilk merkezlerin iki tarihsel
haritadaki örtü bağlamı hazır. Bu bir **girdi/protokol hazırlığıdır**;
ana 24 saatlik yeni orman/çalılık yangını hedefi, belirsiz U ve kapalı
gerçek Y/eğitim/birleştirme kapıları korunur. Mesafe/boşluk veya örtü
kabulünün bütün ayrıntıları seçilmedi. Aynı gün sonraki araştırmacı A
kararıyla **2017 ana / 2018 yardımcı örtü bağlamı** ve aşağıdaki olası
L öneri hazırlığı seçildi. Yeni model kurma kararı verilmedi;
birinci aşamanın bilimsel kabulü açık.

## 1. Aynı fit kaynağının dokuz ayarda geçmişi korundu

Type=0 ve nominal/yüksek güvenli aynı **28.396 fit tespiti**, 2018–2022,
dokuz ayarın tamamında kullanıldı. Kaynak seçimi değiştirilmedi.
2023/2024 tarih alanı dışındaki bilimsel değerler kullanılmadı; 2025
erişimi yok. Yerel iş tek süreçte, sıralı yürüdü; bulut veya eğitim yok.

16 Ekim'den beri kullanılan başlangıç/geçmiş çekirdeği değiştirilmedi.
Eşit zamanlı bütün ilk merkezler ve bütün ilk hücreler korunuyor.
Birleşen gruplar önceki başlangıç kimliklerini silmiyor. Her tespitin
alındığı anda bağlı olduğu geçmiş durumu ayrı. Son grafik bileşeni
retrospektif bir alan; kendi başına yeni fiziksel yangın kimliği değil.

| Mesafe / boşluk | Başlangıç hipotezi | Farklı ilk hücre–gün | Aynı girdiyle son bileşen ilk anahtarları | Son birleşmelerde gizlenebilen ek anahtar |
|---|---:|---:|---:|---:|
| 500 m / 24 saat | 8.580 | 6.694 | 6.518 | 176 |
| 500 m / 48 saat | 8.339 | 6.530 | 6.351 | 179 |
| 500 m / 72 saat | 8.125 | 6.368 | 6.177 | 191 |
| 1 km / 24 saat | 6.457 | 6.339 | 6.294 | 45 |
| 1 km / 48 saat | 6.215 | 6.136 | 6.076 | 60 |
| 1 km / 72 saat | 5.939 | 5.894 | 5.820 | 74 |
| 2 km / 24 saat | 6.017 | 6.073 | 6.040 | 33 |
| 2 km / 48 saat | 5.660 | 5.735 | 5.678 | 57 |
| 2 km / 72 saat | 5.275 | 5.360 | 5.267 | 93 |

Bu sütunlar yangın sayısı veya başarı
ölçüsü değil. Her ayarda dört yıl-sonu ilk-hücre satırı sınır incelemesi
olarak korunuyor; 2018–2022 fit hedef önerisine kabul edilmedi. Aynı
hücre-günde birden fazla başlangıç hipotezi bulunabilir; bir hipotez de
birden fazla ilk hücre taşıyabilir. Dokuz ayar arasındaki sayılar toplanmaz.

**Somut katkı:** gelecekte birleşen bir grubun en eski kaydını tüm
başlangıçlara yaymak yerine önceki ayrı başlangıçlar saklanıyor. Aynı
fit girdisinde 33–191 ek anahtar, ayara göre, bu şekilde korunuyor.
Bu sayı “bulduğumuz ek gerçek yangın” veya doğruluk iyileşmesi değil.
Karşılaştırma aynı 28.396 kayıtta yeniden kuruldu; 2018–2023 eski
envanterle farklı dönem etkisi bu farkın nedeni yapılmadı.

Dokuz ayarın ilk anahtar birleşimi 6.694; sınırdaki dört anahtar hariç
6.690 fit-rolü anahtar var. Ayar desteği güven olasılığı değildir.
500 m/24 saat ayarı daha çok hipotez ürettiği için daha doğru seçilmedi.
Son bileşenlere dayalı aynı-girdi birleşimi 6.518; ortak fark 176 anahtar.

500 m/24 saat, 1 km/48 saat ve 2 km/72 saat için ayrıca 1 Ocak 2022 UTC kesiminde
kaynak yeniden oynatıldı. O tarihe kadarki başlangıç/geçiş/durum/tespit
alanları tam çalışmanın aynı geçmişiyle birebir eşit. Diğer altı ayarda
bu ek kesim tekrar koşulmadı; makbuzdaki `false` **başarısızlık değil,
ek prefix provası yapılmadığı** anlamındadır. Dokuzunda tam DAG ve
başlangıç−birleşme azaltımı=son bileşen korunumu doğrulandı.

Bu hazırlık 227,468 saniye sürdü; yalnız bu yerel işin ölçümüdür.
Fiziksel olay bağımsızlığı, yeniden görünmenin gerçek yeni olay olması,
uydu kaçırması ve dönem başındaki eksik önceki bağlam çözüldü denmedi.

## 2. Bütün fit tespit merkezlerinde iki harita bağlamı

Her 28.396 tespit merkezinde CGLS 2017 ve CORINE 2018 raster pikseli
okundu. CGLS orman sınıfları/20 çalılık, CORINE 311/312/313/322/323/324
orman/çalılık bağlamı olarak önceki sözlüklerle aynı gruplandı. Ham
raster değeri ile CORINE sınıf kodu ayrıldı. Piksel satır/sütunları ve
kaynak kimliği tutuldu; boş/alan dışı örnek su veya negatif yapılmıyor.

| Merkez harita bağlamı | CGLS 2017 tespit sayısı | CORINE 2018 tespit sayısı |
|---|---:|---:|
| Orman/çalılık | 19.621 | 16.151 |
| Tarım | 5.408 | 8.409 |
| Diğer | 3.367 | 3.836 |

15.787 tespit merkezi iki haritada da orman/çalılık; bu olay sayısı,
yanlış pozitif oranı veya L saflığı değil. Büyük yangın çok sayıda
tespit taşıyabileceğinden piksel ve olay sayımı ayrıdır.

Harita sınıfları, referans tarihleri ve üretim yöntemleri aynı değil;
farkları doğruluk ölçümü yapmıyoruz. Merkez sınıfı bütün VIIRS pikselinin
veya yanan alanın örtüsü değil. **CORINE 2018, 2018 olayından sonra
elde edilen bilgiyi içerebilir.** Bu yüzden onu geçmiş hedeflerde
zorunlu orman kabul filtresi yapma kendiliğinden gerekçeli değil.
2017 haritası da olay günü örtüsü veya konum doğrulaması sayılmaz.
Harita bağlamları yeni model girdisine eklenmedi; burada hedef/örtü
incelemesi alanı. Yeni L/Y atanmadı ve kayıt elenmedi.

## 3. İlk hücrelere bağlanan örtü taslağı ve karar için sayılar

Dokuz ayarda **62.331 ilk-hücre×başlangıç×ayar satırı**, yalnız o
başlangıçtaki gerçek kaynak kimlikleri ve eşit zamanlı ilk merkezlerle
eşleştirildi. Sonraki tespitin örtüsü başlangıcın yerine konmadı;
bütün ilk hücreler aynı başlangıç kimliğiyle korunuyor. Bunlar 62.331
bağımsız yangın/örnek veya kabul edilmiş eğitim satırı değil.

Örnek olarak **1 km / 24 saat tanısı**, üretim ayarı seçilmiş olmadan:

| Fit-rolü hücre-gün inceleme koşulu | Farklı anahtar |
|---|---:|
| Bütün ilk hücre-gün adayları | 6.335 |
| Bir ilk-hücre grubunda en az bir merkez 2017'de orman/çalılık | 1.564 |
| Bir ilk-hücre grubunun bütün merkezleri 2017'de orman/çalılık | 1.357 |
| Bir ilk-hücre grubunun bütün merkezleri iki haritada da orman/çalılık | 491 |

Bir anahtarda birden fazla başlangıç bulunursa bu koşulu sağlayan en
az bir ilk-hücre grubu sayılır; bütün grupların aynı örtüde olduğu
söylenmez. Karışık merkezler ve diğer ilk hücreler dosyada duruyor.
İki harita uyumuyla azalan sayı daha yüksek ölçülmüş doğruluk demek değil.
Dokuz ayarın tüm sonuçları makbuzda; iyi sonuç veren ayar seçilmedi.

**İlk incelemede önerilen, aynı gün araştırmacı tarafından seçilen A yönü:**
2017 haritasını olay öncesi ana
örtü bağlamı, CORINE 2018'i yardımcı/duyarlılık bağlamı olarak tutmak;
karışık/çelişkili adayları incelemede korumak. İki harita uyumunu
zorunlu kabul yapmak alternatif, fakat örnek kaybı ve 2018 için
olay-sonrası harita etkisi taşır. Bu iki yolun karşılaştırılması gerçek
yangın doğrulaması değildir. Seçim olası öneri hazırlığı içindir;
üretim üyeliği, gerçek Y, dokuz ayardan biri veya model seçilmedi.

Bu yön seçilmiş olsa da bir merkez haritada odunsu göründüğü için
kesin Y=1 denmeyecek. L aday üyeliği ile latent gerçek yangın Y ayrımı,
gözlem kaçırması, yeniden görünme/başlangıç belirsizliği ve parametre
duyarlılığı korunacak. Aynı U örneklemi ve edinim ağırlıkları kalacak;
U/L anahtar örtüşmesi sessiz silinmeyecek. Sınıf/hata oranı harita
uyumu veya aday sayısından çıkarılmayacak.

## 4. Örtü A kararı sonrası tamamlanan somut pilot girdileri

`satellite_pu_cover_direction_v1` kararı yalnız bir ilk-hücre grubunun
bütün gerçek ilk merkezleri CGLS 2017'de orman/çalılık olduğunda
**olası L önerisi** hazırlar. CORINE 2018 uyumu zorunlu değil.
62.331 satırın tamamı korunur; karışık merkezler ve diğer ilk hücreler
aynı başlangıç kimliği altında atamasız kalır. **WF1538'in bilinen
hücre-günü dokuz ayarda da öneri dışında** tutuldu. Önceki Salur ve
Marmaris makbuzları değiştirilmedi.

Dokuz ayardaki önerilerin birleşimi **1.670 farklı hücre-gün**. Bu
birleşim dokuz ayarın seçilmiş üretim hedefi veya 1.670 gerçek yangın
değil. Her satırda gerçek Y ve kabul edilmiş L hâlâ boş. Özgün 2.048
U aynen korundu; bu örtü koşullu öneri birleşimiyle U'nun kesişimi
sıfır. Önceki ham aday havuzundaki iki U örtüşmesi de kendi dosyasında
duruyor; iki farklı havuzun sayımları birbirine karıştırılmıyor.

Bu öneri anahtarlarının 797 günündeki 1.594 özellik/provenance dosyası
güncel hash ve geçmiş pencere kontrolleriyle okundu. Tam U kesiti
önceki donmuş incelemeden birebir aktarıldı: toplam **3.718 benzersiz
özellik anahtarı**. Öneri grubunda 1.581 tam / 89 eksik; U'da 1.763
tam / 285 eksik; toplamda **3.344 tam / 374 eksik** satır var.
Eksik satırlar elenmedi veya doldurulmadı. 27 X sütunu ile hedef/
grup/gözlem/kalite bilgileri ayrı; uydu başlangıcına ait gelecekteki
alanlar girdilere eklenmedi. ERA5 yeniden analiz ve yayın erişim
zamanı belirsizliği korunuyor; bu operasyonel anlık veri kabulü değil.

İlk özellik koşusunda özellik/provenance geri okuması geçti; tamamen
boş hedef sütununun bellek/CSV tür farkında metadata kontrolü durdu.
`20261120T010031Z_61a98344` kısmi dosyaları, eski üretici ve hata
kaydı korundu; kabul makbuzu üretilmedi. Boş hedefin sayısal NaN
gösterimi düzeltildi ve ayrı regresyon testi eklendi. **Yeni kimlikle
797 günün tamamı yeniden okundu**; kabul edilen sonuç aşağıdaki
`20261120T010533Z_6d61c80e` koşusudur. Veriye elle düzeltme yapılmadı.

### Dönem ayrımı ve yeni deney önerisi

2018–2021 fit / 2022 tanısal inceleme önerisi hazır. Hedef penceresi
rol sonuna kesin olarak taşmamalı; sınır kayıtları kullanılmadan
incelemede kalır. Aynı girdinin 2 km / 72 saat gözlenen son grafik
bağlamı iki rol arasında paylaşılırsa ilgili anahtarlar karantinaya
alınacak şekilde tasarlandı. Bu kesitte böyle blok yok; bütün U
anahtarları kaldı. **Gerçek fiziksel olay bağımsızlığı doğrulanmadı.**
2022 daha önce incelendiğinden kör/bağımsız final test sayılmıyor.

| Ayar | Fit olası aday anahtarı | 2022 olası aday anahtarı |
|---|---:|---:|
| 500 m / 24 saat | 1.428 | 242 |
| 500 m / 48 saat | 1.396 | 239 |
| 500 m / 72 saat | 1.374 | 237 |
| 1 km / 24 saat | 1.131 | 225 |
| 1 km / 48 saat | 1.117 | 223 |
| 1 km / 72 saat | 1.098 | 221 |
| 2 km / 24 saat | 1.079 | 220 |
| 2 km / 48 saat | 1.067 | 218 |
| 2 km / 72 saat | 1.043 | 215 |

Her satırda aynı **1.648 fit / 400 inceleme U** korunur. Dolayısıyla
ayar başına 2.691–3.076 fit ve 615–642 tanısal inceleme anahtarı
öneriliyor. U edinim ağırlıkları özgün kaynakta değişmeden kalır;
önerilen bu yardımcı ayrım deneyi ağırlıksız vaka örneklemidir,
sınıf/nüfus oranı veya nüfus başarımı tahmini değildir.

Somut yeni deney planı: bütün dokuz ayarda sabit lojistik regresyon,
100 ağaçlı küçük Random Forest ve yalnız beş aile eksiklik bayrağını
kullanan kontrol; toplam **en fazla 27 yardımcı model**. Ön işleme
yalnız fit kesitinde öğrenilecek; hiperparametre/iyi sonuç veren
ayar araması yok. Uygulama hazırlanıp test edildi, **gerçek veriyle
yeni fit yapılmadı**. Standart çalıştırıcı toplam 15 dakika yerel alt
süreç sınırı, RF fit için iki işçi ve sıralı tahmin kullanır; kısmi
çıktılar başarısızlıkta korunur. Bulut/ücretli iş yok.

Sonuç alanı yalnız **uydu öneri üyeliği S için yardımcı ROC-AUC**
olacak; S=0 belirsiz U örneği, gerçek yangın yokluğu değil. Yeni
önerilerin gerçek pozitifliği kabul edilmeyecek. Renkler, gerçek
yangın AP'si/olasılığı, 2023–2025 değerleri ve nihai birleştirme
açılmayacak. Önceki Mersin 708/168 denemesi izni bu yeni kaynak ve
ölçeği kapsamıyor; **yeni yardımcı model denemesi için ayrı araştırmacı
kararı bekleniyor**. Hazırlığın A kararları bu iznin yerine yazılmadı.

## 5. Öğrenme ve değerlendirme için açık kalan bilimsel sınır

Yüzde olasılığı ilk ürün için zorunlu değil; AP ana sıralama ölçütü
korunuyor. Bununla birlikte, gözlenen aday üyeliğinden gerçek yeni
orman/çalılık yangını sıralamasına geçişte zenginleşme, ölçüm/seçilme
ve ortak sınıf koşullu dağılım gibi varsayımlar gerekçelendirilmeli.
Bütün U'nun gerçek negatif veya bütün L'nin kusursuz pozitif olması
şartı getirilmiyor. Bu çalışmanın sayımları bu varsayımları ölçmüş değil.

Gelecekteki ilk PU deneyinin yardımcı aday ölçütleri, gerçek hedef
AP'si/bağımsız yangın başarımı diye raporlanmayacak. Hedef, zaman
rolleri, geçmiş 27 özellik sözleşmesi ve 2025 kapalı final korunur.
Bu girdilerle otomatik eğitim veya kırmızı/sarı/yeşil yangın ürünü
üretilmedi. Nihai etiketli birleştirme için güncel parça denetimi ve
rapora bağlı araştırmacı onayı hâlâ gerekir.

## Yeniden üretim ve kontrol

- Başlangıç: `scripts/quality/replay_satellite_pu_lineage.py`;
  `satellite_PU_lineage_v1/20261120T003414Z_a21f7422/readback.json`, SHA-256
  `b13d15d640f51662bd75fc65a25769ca02ceb69c80836c4fe2b99e788ae2e530`.
  Ayrı CSV/DAG/üyelik/ilk-hücre sayımı SHA-256
  `574dbaca37941f680f1e91b917955927aa309f59596d2f7d52087ef72e2dde4f`.
- Örtü: `scripts/quality/prepare_satellite_pu_cover.py`;
  `satellite_PU_cover_v1/20261120T003942Z_3f82694d/readback.json`, SHA-256
  `ae771636b7c230afe7b9603b00f266eab3a3a3fa408a56f9b765a27f6da34900`.
  Her iki haritada her merkez, ayrı affine piksel hesabı ve doğrudan
  1×1 pencere okumasıyla doğrulandı: 26.578/25.937 farklı raster pikseli.
  Ayrı kontrol SHA-256 `2219538a703c0339c77ca5445125718ed96f2f2e83bd5b85e5ef604db733883d`.
- Birlikte ilk-hücre incelemesi: `scripts/quality/audit_satellite_pu_preparation.py`;
  `satellite_PU_preparation_v1/20261120T004314Z_88c008ce/readback.json`, SHA-256
  `1288a62e58f3982ca1b64147d2a36542a685117f770fa118259d8055ca619d8e`.
  62.331 satırın ilk kaynak kimliği/saat/hücre ve iki harita sayımları
  ayrı standart CSV döngüsüyle doğrulandı; SHA-256
  `1bfec3b85c4844b0df7a95403199204c1e7a377bb2c3ec6b2a906c8a6ce5ae9a`.
- 12 yeni dahil **271 ilgili test** geçti. Başlangıç, eşit ilk hücre,
  sağ kapalı gece yarısı, yıl sınırı, yanlış izin, karışık ilk merkez,
  geç tespit ikamesi, maske/alan dışı raster ve legend dönüşümü sınandı.
  Raster geliştirmesinde toplu `index` çağrısının skaler API hatası
  sentetik testte yakalandı; veri koşusundan önce vektör `rowcol`
  hesabıyla düzeltildi. Donmuş bilimsel çekirdekler değiştirilmedi.

Sonraki A uygulamasının kimlikleri (`outputs/reports/dataset/` altında):

- Öneriler: `satellite_PU_L_proposals_v1/20261120T005519Z_62f3f815/readback.json`,
  SHA-256 `679a5ad9eab6342fa153c46cbbcc8f1e494b92256b592ba84f24823d0c0a4a85`;
  ayrı geri okuma `2aec8faa3b06def62ee8a1b6ef2bc388ff75ff6ddc6236c1ac0a1137c4c0ec0c`.
- Özellikler: `satellite_PU_feature_review_v1/20261120T010533Z_6d61c80e/readback.json`,
  SHA-256 `64262888976fe43530897f9c069eb73866dea42003ffc4fd31fcfa17ddd74138`;
  ayrı geri okuma `65893266c9364cef0ac2e402cfd4cea4999cdca129605134a8cf2f6262d7021b`.
- Dönemler: `satellite_PU_partition_v1/20261120T010148Z_74c8eee5/readback.json`,
  SHA-256 `7f8169cf0dbc365ea576e722c66e018d63812829be1810f1bf90bd3dfebef7ff`;
  ayrı geri okuma `db3d1ee15385fbee04d1b36254e1ffafc744e9abbaad4294af505f4a04153c1b`.
- Deney önerisi: `satellite_PU_ranking_plan_v1/20261120T012319Z_6b617502/readback.json`,
  SHA-256 `cbc928c456464d80118afafd304a9981c004bec7ba3f42d2acab75e0ad568e24`.
  `configs/satellite_pu_ranking_pilot_v1.json` ve
  `scripts/quality/run_satellite_pu_ranking_pilot.py` varsayılan olarak
  yalnız hazırlık yapar; fit için ayrı plan-bağlı yürütme kararı gerekir.
  Önceki `20261120T012041Z_50bb86e6` taslağı ve üreticisi korundu;
  güncel plan yeniden kullanılacak bilimsel yardımcı modüllerin hash'lerini
  de bağlıyor. Her iki taslakta da model fit edilmedi.
- `scripts/quality/verify_satellite_pu_pilot_inputs.py` bütün öneri
  bayraklarını, korunan ilk satırları, ham kimliklerden dönem grafik
  bağlamını, üç tablo anahtarını, özgün U değerlerini ve geçmiş
  zamanları ayrı yöntemle doğruladı. Bu ikinci kontrolde ham günlük
  büyük dosyalar tekrar hash edilmedi; yeni koşu zaten 1.594 dosyayı
  güncel hash ile okumuştu. Ayrı tarih okuyucusunun kesirli/kesirsiz
  ISO saniye biçimi varsayımı, makbuz yazılmadan yakalanıp standart
  `datetime.fromisoformat` hesabıyla düzeltildi; kaynaklar değişmedi.
- Son birleşik koşuda **289 ilgili test** geçti; ilk 271'den sonraki
  sekiz veri/rol ve on deney-izin davranışı testi bu sayıya dahildir.
  Sekiz yeni görev betiği/yedi test dosyasının (15 Python dosyası)
  kod ve biçim kontrolü geçti. Son bağımlılık-pini eklemesinden sonra
  ilgili on deney-plan testi yeniden geçti; bilimsel koşular tekrarlanmadı.

Ayrı DAG okuyucusunun tarih yardımcı hesabı yerel NumPy sürümünde bir
deprecation uyarısı verdi; bütün değer/sayım eşitlikleri geçti. Bu
okuyucu üretim kodu veya veri değişimi değil. Teknik test, hash ve
raster örneği kontrolleri bağımsız saha/yangın/insan doğrulaması sayılmaz.
