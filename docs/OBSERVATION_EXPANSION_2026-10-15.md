# Gözlem pilotunun kapsam ve kaynak planı — 15 Ekim 2026

Bu çalışma, [üç hücrede çalışan alan/zaman/kalite yöntemini](SCAN_AREA_TIME_2026-10-15.md)
farklı coğrafya ve takvim dönemlerine genişletmenin hazırlığıdır. Ana eğitim
takvimi 2018–2023/72 ay olarak korunur. Buradaki sınırlı gün seçimi yöntem
incelemesi içindir; yeni etiket politikası, eğitim verisinin kabulü veya
bulut işi başlatma kararı değildir.

## İl sınırı ile örnekleme sektörü ayrımı

Mevcut 400 kaydın coğrafi tabakaları, grid sütunlarından üretilen dört
batı–doğu sektörüdür. Bunlar önceki kayıtlarda da il olarak tanımlanmamıştı.
Yeni hazırlıkta aynı AOI kaynağı `FAO/GAUL/2025/level1` içinden dört ilin
ayrı geometrileri salt okunur sorguyla alındı. Earth Engine export görevi
veya VM başlatılmadı; mevcut AOI/grid dosyaları değiştirilmedi.

Kaynak, `ISO3_CODE=TUR` ve dört ilin kaynak adlarıyla filtrelendi;
`GAUL1_CODE`, `GAUL1_NAME` ve geometri saklandı. FAO'nun GAUL 2025
kaynağı birinci düzey idari sınırlar içerir ve CC-BY-4.0 koşuluyla
sunulur. Bu sınırlar coğrafi inceleme metadatasıdır; geçmiş yıllara ait
yeni model girdisi veya tarihsel sınır doğruluğu iddiası değildir.
[Google Earth Engine GAUL 2025 kataloğu, 15 Ekim erişimi](https://developers.google.com/earth-engine/datasets/catalog/FAO_GAUL_2025_level1).

Hücre/il kesişimleri EPSG:6933'te hesaplanır. Örnekleme için birincil il,
AOI ile kesilmiş hücrede en fazla alanı olan ildir. Eşitlikte ad sırası
deterministik bağ çözer; komşu il kesişimleri silinmez. Bütün pozitif
kesişimler ve paylar ayrı tabloda tutulur. 0,05 m² yalnız sayısal alan
raporlama toleransıdır; habitat uygunluğu veya idari sınır kabul eşiği değildir.

## Hesap öncesinde yazılan yöntem pilotu

`configs/observation_expansion_v1.json` seçim kurallarını kaydeder:

- Yıllar: **2018, 2021, 2023**; başlangıç, ara ve son eğitim döneminden
  amaçlı takvim kapsamı. Altı yılın temsili doğruluk örneklemi değildir.
- Her yılda **15 Şubat, 15 Mayıs, 15 Ağustos, 15 Kasım**; kış/ilkbahar/
  yaz/sonbahar için birer sabit gün, toplam **12 hedef gün**.
- Her gün/dört il için nominal üründe seçilmiş termal merkez bulunan ve
  bulunmayan iki ayrı tanı grubu. Bunlar pozitif/negatif gerçeklik değildir.
- Her grup için en çok iki hücre. İlk seçim sabit SHA sırasıyla; mümkünse
  ikinci seçim farklı baskın arazi örtüsü tanı grubundan yapılır.
- Tam su hücreleri önceki kabul edilmiş kapsam kuralıyla çekirdek dışında
  kalır; karışık hücreler korunur. Baskın örtü tanısı habitat kabulü değildir.

Azami **192 hücre-gün kontenjanı** vardır. Bir il/günde termal kayıt
bulunmazsa tarih değiştirilmez, başka mevsimden kayıtla doldurulmaz veya
bilinmeyene sıfır verilmez. Karşılanamayan kontenjan ayrı kaydedilir.
Yerelde hangi ham dosyanın bulunduğu seçim sırasını etkilemez.

Bu yeni kohort, önceki 400 kaydın alt örneklemesi değildir. Önceki pilotun
kimlikleri, tabaka ağırlıkları ve boş inceleme kararları korunur. Yeni
kohort amaçlı yöntem incelemesidir; popülasyon hata oranı veya örnekleme
ağırlığı tanımlanmadı. Önceki 400 kaydın ağırlıkları da seçilen öncelik
alt kümesine doğrudan taşınarak hata oranı hesaplanamaz.

## Karşılaştırılan iş yükleri

1. **Ortak takvim çekirdeği:** aynı 12 günde birden fazla il/hücre
   incelenir. Aynı uydu kaynakları hücreler arasında ortak kullanılabilir.
2. **Mevcut öncelikli vakalar:** olay senaryosu anlaşmazlığı, eksik kaynak,
   nominal kara desteği yokluğu, sınır zamanı ve su kapsamı denetimleri.
   Bunlar ayrı zor vaka kohortudur; olay veya hata sayısı değildir.
3. **Mevcut 400 kaydın tamamı:** yeni ham alan/zaman hesabı yapılması
   halinde gerekecek bölgesel kaynak kapsamı için karşılaştırma referansı.
   Bu hesap, 400 kayıt üzerinde yeni ham işlem başlatıldığı anlamına gelmez.

Her hücre-gün için önceki/aynı/sonraki nominal kaynak günü planlanır.
Eğitim dönemi dışına çıkan kaynak okunmaz. İki ertelenmiş gün kayıtlı
eksiklik olarak korunur. Mevcut kabul edilmiş kompakt ürünlerin içindeki
denetim raporlarından dosya adı, rol, boyut ve SHA-256 çıkarılır. Kaynak
aynı plan içinde birden çok kez kullanılsa da bir kez sayılır; sürüm/hash
çatışması sessizce çözümlenmez.

Kayıtlı bayt toplamları bölgesel AOI granül listesinin referans yüküdür;
hücreye özel geometrik ön elemeden sonraki kanıtlanmış en küçük indirme
miktarı değildir. Güncel NASA erişilebilirliği ayrıca doğrulanmalıdır.
Eksik kaynak günlerinin bilinmeyen boyutu sıfır maliyet olarak yorumlanmaz.

### Ölçülen kapsam ve kayıtlı kaynak baytları

On iki hedef günde **34.788 hücre-gün adayı** tarandı. 192 kontenjandan
**156'sı** seçildi; termal merkez grubunda **36 boş kontenjan** kaldı:
kış 17, ilkbahar 6, yaz 8, sonbahar 5. Günler sonuçlara göre değiştirilmedi.
Bu boşluklar dört ilde yangın bulunmadığı anlamına gelmez; yalnız sabit
günde mevcut tanı grubunun seçim sayısını karşılamadığını gösterir.

Birincil il atamasında 911 hücre Antalya, 728 Mersin, 648 Muğla ve
612 İzmir grubundadır. **42 hücrede** birden fazla ilin alanı bulunur;
çekirdekte bunların ikisi seçilmiştir. İl geometri birleşiminin AOI'de
açık bıraktığı alan toplamı yaklaşık **0,000578 m²**'dir; bu sayısal
fark mevcut AOI'yi değiştirmek için kullanılmadı.

| Plan | Hücre-gün | Hedef gün | Mevcut kaynak günü | Farklı kaynak çifti | Ham dosya | Kayıtlı toplam GB |
|---|---:|---:|---:|---:|---:|---:|
| Ortak takvim çekirdeği | 156 | 12 | 36 | 292 | 584 | 53,52 |
| Mevcut öncelikli vakalar | 48 | 33 | 94 | 756 | 1.512 | 138,83 |
| Mevcut 400 kaydın tamamı | 400 | 348 | 883 | 7.518 | 15.036 | 1.380,16 |

GB burada **10⁹ bayt**tır. Çekirdek için kayıtlı toplam **53.517.820.515
bayt**, 400 kayıt referansında **1.380.155.984.939 bayt**tır. Bu iki
planın dosya baytı oranı yaklaşık **25,79**; örneklem kapsamları farklı
olduğu için bu oran hız artışı veya eşdeğer bilimsel doğruluk ölçmez.
Öncelik planı ve 400 kayıt referansında iki ertelenmiş kaynak gününün
bilinmeyen yükü bu toplama dahil değildir; eğitim dışına çıkan bir kaynak
günü de okunmadı. Çekirdekte ertelenmiş/eğitim dışı kaynak günü yoktur.

Yerel ham dosya envanteri 18 dosyadır; üç plandaki gerekli referansların
hiçbiri bu yerel dosyalarla tam ad/SHA eşleşmesi sağlamadı. Dolayısıyla
bu planlarda geniş ham alan/zaman hesabı yerel önbellekle başlamaya hazır
sayılmaz. Raporlara bağlı kaynak kimlikleri bellidir; güncel uzak erişim
ve dosya baytları ayrıca doğrulanmalıdır.

Çekirdeğin baskın örtü tanıları: orman/çalı 75, tarım 29, otsu 27,
kentsel 21, su baskın karışık 3, diğer 1. Bunlar habitat kabulü veya
farklı arazi türlerinde eşit doğruluk kanıtı değildir. Tam su dışlama
kuralı uygulanırken karışık ve kentsel destekli zor durumlar incelemede
korunmuştur. Nihai habitat uygunluğu açık kalır.

**Öneri:** önce ortak takvim çekirdeğinin tam sürüm/kimlik erişimini
kontrol etmek; sonra sınırlandırılmış ham kaynak önbelleğiyle yöntemi
genişletmek. Öncelikli 48 vaka ayrı zor vaka fazında tutulmalıdır.
Yeni kohort veya bu öncelik alt kümesi için hata oranı ilan edilmez.

Bayt miktarından çalışma saati veya TL fiyatı çıkarılmaz. Gerçek işlem
süresi seçilen hücreler, disk/ağ/CPU ve kaynak sunucusuna bağlıdır.
Gelecekte bir yürütme planı hazırlanırken disk kapasitesi, sınırlı kaynak
önbelleği, checksum, süre sınırı ve checkpoint ayrı doğrulanmalıdır.
Yapılandırma yeni bulut işi veya ücretli yükseltme yetkisi içermez.

## Yeniden üretme

İl kaynağını açıkça almak için:
`.venv/Scripts/python.exe scripts/earth_engine/prepare_province_boundaries.py --fetch`.
Bu adım mevcut kimlik doğrulamayla dört kamu sınırını okur; giriş/anahtar
değerleri yazdırılmaz ve otomatik oturum açma yapılmaz.

Yerel planlama:
`.venv/Scripts/python.exe scripts/quality/plan_observation_expansion.py`.
Planlayıcının ağ erişimi engellidir. Yeni ham uydu indirmez, alan/zaman
üretimi veya model çalıştırmaz. Kaynakların hash ve kapsam bilgilerini
yeni çıktı dizininde kaydeder; kabul edilmiş paketleri değiştirmez.

## Çıktılar ve denetim kapanışı

Yerel il kaynağı:
`data/raw/boundaries/gaul2025/20261014T231843Z_2271840f/`.
Kaynak geri okuma SHA-256:
`cf3a25984d56d3fd4b4658cbf74adfa57f6be1bc667940ab5ad5b5b1d7a64121`.
Bu küçük kaynak hazırlığındaki Earth Engine okuması ile sonraki
çevrimdışı planlayıcı ayrı işlemlerdir.

Plan dizini:
`outputs/reports/dataset/observation_expansion_v1/20261014T233502Z_81275155/`.
UTC dosya zamanları 14 Ekim, Türkiye'deki çalışma tarihi 15 Ekim'dir.

- `calendar.csv`, `calendar_core.csv`, `quota_gaps.csv`: sabit 12 gün,
  seçilmiş 156 hücre-gün ve 96 gruptaki kontenjan denetimi; 20 grupta
  toplam 36 karşılanmamış kontenjan.
- `province_grid.csv`, `province_intersections.csv`: 2.899 hücrenin
  birincil il tanısı ve korunan bütün il kesişimleri.
- `existing_400_geography.csv`, `existing_priority.csv`: önceki 400
  kaydın değiştirilmeden ek coğrafi bilgiyle bağlanması ve ayrı 48 zor vaka.
- `source_day_requests.csv`, `source_day_inventory.csv`: üç planın
  komşu kaynak günleri, eksik/dönem dışı durumlar ve ürün raporu kimlikleri.
- `native_source_queue.csv`, `plan_source_links.csv`: tekilleştirilmiş
  dosya adı/boyut/SHA kayıtları ve hangi plana ait oldukları; güncel uzak
  erişim her dosyada `not_checked` olarak kalır.
- `local_native_inventory.csv`, `workload_comparison.csv`: yerel
  önbellek kimlikleri ve üç planın kaynak baytı karşılaştırması. Bilinmeyen
  süre/fiyat alanları boş sayısal değer, JSON'da `null` olarak korunur.

İlk denemede son JSON geri okuması Türkçe il adlarının platformun
varsayılan kodlamasıyla yanlış okunmasını yakaladı. UTF-8 açıkça
belirtildi; bilinmeyen sayısal bütçe alanlarının geri okuma türü de
düzeltildi. Son sürüm yeni çıktı dizininde uyarısız tamamlandı; kabul
edilmiş bilimsel dosyalar elle değiştirilmedi.

**20 yeni davranış testi dahil 105 ilgili test** geçti; deprecation ve
future uyarıları testte hata sayıldı. Sınır hücresi, il poligonlarının
örtüşmesi, sabit seçim sırası, farklı örtü tanısı, eksik kontenjan,
bilinmeyeni etiket yapmama, kapalı test dönemi, kaynak kimliği/boyutu ve
sürüm çatışması denetlendi. Dört Python dosyasında lint/format geçti.
**175 giriş ve 13 çıktı** hash kapanışından geçti; **22 donmuş bulut
girdisi** korundu.

`readback.json` SHA-256:
`8a29ea70339965497e4e5499ef718c684ecdbc9c833e3e2fa0c0db824a14e7c2`.
`completion_readback.json` SHA-256:
`bd701d4e42ed6fb33ee02273ec74bb9dbf5435722b0aa19bd754f912cbe42c6d`.

`daily_observation_status=unknown`, `negative_label_permitted=false`,
boş hedefler ve nihai birleştirme kapısı korunur. Geniş ham pilot,
indirme, yeni bulut işi, model veya 2024/2025 CSV erişimi başlatılmadı.
Sonraki iş çekirdekteki **584 dosyanın güncel arşiv kimlik/sürüm
erişimini**, veri indirmeden kontrol etmek ve sonrasında sınırlı ham
işleme düzenini hazırlamaktır. Bu teknik hazırlık, yeni bulut işine
otomatik yetki vermez.
