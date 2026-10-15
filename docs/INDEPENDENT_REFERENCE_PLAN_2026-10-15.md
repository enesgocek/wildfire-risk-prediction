# Bağımsız referans erişimi ve doğrulama hazırlığı

Tarih: 15 Ekim 2026. Durum: gerçek kamu kaynaklarının kontrolü, bağlam
aktarımı ve veri alım hazırlığı tamamlandı. Bağımsız olay etiketi kabul
edilmedi. İlk hazırlık sırasında kurumsal talep gönderilmemişti;
15 Ekim gece araştırmacı CİMER başvurusunu tamamladığını bildirdi.
Teknik yanıt bekleniyor; makbuz bağımsız okunmadı. Aşağıdaki deney
ve hazırlık kayıtları kendi yürütülme aşamalarının durumunu korur.

## Yeni kaynak kontrolünün sonucu

**OGM Muğla 2023 değerlendirme raporu:** 54 sayfalık PDF gerçekten
indirildi. Sayfa 46'daki 500 hektardan büyük yangın tablosunun 2018-2023
aralığında 11 satırı, sayfa 9'dan bir 2023 anlatımı ayrıldı. İlgili iki sayfa
görüntü olarak da okundu. Böylece **12 kurumsal bağlam kaydı** oluştu;
bir yayının iki bölümü iki bağımsız kaynak sayılmadı.
[Özgün rapor](https://www.ogm.gov.tr/muglaobm/duyurular-sitesi/Documents/mugla-obm-2023-yili-yangin-degerlendirme-raporu/2023%2BYili%2BOrman%2BYanginlari%2BDegerlendirme%2BRaporu.pdf).

Tabloda başlangıç koordinatı/saat yok; 2023 anlatımında saat var ancak
saat dilimi açık değil. 11 satırdan biri Aydın birimine aittir; bölge
müdürlüğü sınırı proje illeriyle aynı değildir. Yer adları hücreye otomatik
çevrilmedi. İncelenen tabloda yalnız büyük yangınlar yer aldığından
listede bulunmamak negatif kanıt sayılmaz. Bunlar 5 km hücre/gün eşlemesi
kanıtlanmış 12 yangın değildir. Rapor 2023 dönemini anlatır; daha önce
alınamayan 2021 raporunun indirildiği söylenmez.

**European Fire Database:** 2014 JRC teknik raporu ve iki güncel EFFIS
sayfası alındı. Teknik raporun sayfa 11/21'i görsel olarak da kontrol edildi.
Şema, ihbar/müdahale/sönme zamanlarını ayırır; ihbar saati yerel saattir.
2014 erişim açıklaması ulusal ham olay kayıtlarının üçüncü taraf paylaşımını
kısıtlar; güncel sayfa genel bilgilerin kamuya açık olduğunu belirtir.
Diğer EFFIS veri talep yolları bu ulusal kayıtların alınabileceğini kanıtlamaz.
[Teknik rapor](https://data.effis.emergency.copernicus.eu/effis/reports-and-publications/effis-related-publications/eudb_tech_spec_final_2register.pdf),
[güncel veritabanı sayfası](https://forest-fire.emergency.copernicus.eu/about-effis/technical-background/european-fire-database),
[veri erişim sayfası](https://forest-fire.emergency.copernicus.eu/applications/data-and-services).

Erişim durumu yeniden teyit edilmeden bu kaynak için bireysel olay verisi
elde edileceği vaat edilmez. Eski EFFIS uydu sınırları ve kapsam dışındaki
FireSpread_MedEU, bağımsız saha kayıtları yerine kullanılmadı.

## Somut kontrol ve kalan boşluk

OGM tablo aktarımı, PDF metninde bütün 31 sıra kimliğinin bulunması ve
seçilen 11 satırın yer/tarih/alanlarının eşleşmesiyle kontrol edildi.
Türkçe ondalık ve binlik ayracı açık biçimde ayrıştırıldı; eksik değerler
sıfırla doldurulmadı. Anlatımdaki tarih/saat/alan görünür sayfayla kontrol
edildi. Bu araç destekli aktarımdır; bağımsız araştırmacı incelemesi değildir.

12 kaydın bildirilen başlangıç tarihleri, sabit gözlem pilotunun 12 hedef
gününden hiçbirine denk gelmez. Bu sonuç aynı bölgede süren yangınları
veya başka yangınları dışlamaz; yeni kayıtlar doğrudan 156 birimin
doğrulaması olarak sunulmadı.

`reference_readiness.matching_readiness`, konum türü ve belirsizliği,
açık UTC zaman sınırları, zamanın anlamı, kaynağa erişim ve belgelenmiş
bağımsız olay kökenini ayrı kontrol eder. Sadece tarih/yer anlatımından
kesin konum veya UTC saati üretmez. Bugünkü **12/12 kayıtta kesin
hücre/zaman eşleştirmesine hazırlık eksiktir**. Uygun bir gelecekteki
ihbar kaydı bile ilk uydu tespitini, gerçek tutuşmayı veya negatif etiketi
otomatik doğrulamaz; bu sürüm yalnız eşleştirme incelemesine hazırlığı ölçer.

## Veri edinimi için hazırlanmış somut yol

[OGM anonim veri talebi taslağı](research/OGM_DATA_REQUEST_DRAFT_2026-10-15.md)
kullanıcı incelemesine hazırdır. İlk hazırlık makbuzu oluşturulurken kanal
henüz doğrulanmamıştı; gönderim yapılmadı.
Kişisel bilgi alanları boş bırakıldı; finansman veya kurum onayı iddia edilmedi.

Öneri, **2018-2023 / Antalya, Muğla, İzmir, Mersin** için paylaşılabilir anonim
olay ve kayıt kapsamı bilgisini talep etmektir. Kurum kapsamı sınırlı tutarsa
önce 2021 dönemiyle teknik uygunluk incelenebilir. Açık kaynak araştırması
bu süreçten bağımsız sürebilir; yanıt veya tam kayıt sağlanacağı garanti edilmez.

İki boş şablon hazırlandı:

- `incident_reference_template.csv`: kimliksiz olay kimliği, ham tarih/saat,
  saat standardı ve anlamı, konum türü/CRS/belirsizliği, kaynak ve kullanım koşulları.
- `reference_coverage_template.csv`: dönem/bölge kapsamı, kayda alınan olay türleri,
  asgari kayıt büyüklüğü, bilinen eksik dönemler ve dışlamalar.

Şablonların boş olması eksik olay sayısının sıfır olduğu anlamına gelmez.
Tüm kayıtlar veya bütün küçük olaylar kapsanmadığında, kayıtta eşleşme
bulunmayan bir aday "yangın yok" diye onaylanmaz.

Veri gelirse önce kaynak/izin ve bağımsızlık, ardından konum/zaman
belirsizliği ve olay kimliği incelenir. Uyduyla zaman/konum bağlantıları
aday eşleşmeler olarak tutulur; toleranslar kaynak hassasiyeti görülmeden
seçilmez. Kapsamı belgelenen bir çerçevede ayrıca olasılıklı hata değerlendirme
örneklemi tasarlanır; mevcut amaçlı pilotun sonuçları hata oranı değildir.
Belirsiz vakalar ve eşleşmesiz kayıtlar ayrı kalır. Güncel son parça
kontrolü ve rapora bağlı kullanıcı onayından önce nihai birleştirme yapılmaz.

## Makbuz ve doğrulamalar

Dört kamu dosyası HTTP 200 ile alındı; saklanan toplam **7.557.028 bayt**
(iki PDF, iki HTML). Bu dosya baytıdır, bütün isteklerin kesin trafik ölçümü değil.
İlk sandbox denemesinde bağlantı hataları kaydedildi; izinli kamu GET
çalıştırması başarılı oldu. Önceki başarısız kayıt korunur; kaynak yokluğu
veya bulut kotası sorunu olarak yorumlanmaz. Hesap girişi veya bulut işi yok.

Kaynak dizini:
`outputs/reports/dataset/reference_access_v1/20261015T144111Z_e70215f0/`.
OGM PDF SHA-256:
`a2e90802a152e9d83ce6f94cb705ac3bc94452819aa36f29acdfc98e0a97018f`.
JRC PDF SHA-256:
`177608efe6ebdb9fafc5d1a44cfbfb93496175d14cbacc2a2e5fb7d724ac6a8e`.

Son hazırlık:
`outputs/reports/dataset/independent_reference_plan_v1/20261015T145033Z_81f53320/`.
Readback SHA-256:
`20e6d42f35c4c7310ef34f980dcb80de589fcc73b839d4daa93cb7185ce40e06`.
Kapanış SHA-256:
`a0f7012b7b3bf77895b5547b00f7215ff974f0665a1abb738d0a9b6fd6cd8213`.
Altı çıktı ve **15 bağlı girdi** kapanışta tekrar hash ile kontrol edildi.
Önceki hazırlık, pilot tarih karşılaştırması eklenmeden önceki ayrı sürümde
korunur; kabul edilmiş JSON/CSV elle değiştirilmedi.

**17 yeni vaka dahil 45 ilgili test** geçti. Dört yeni Python dosyasında
lint/format temiz. UTC'siz saat, yarım konum/zaman, kapsam dışı yıl,
ters zaman sınırı, otomatik hedef, paylaşılan sensör kökeni ve sayı biçimi
kontrol edildi. Şema hazırlığı gerçek bağımsız olay veya negatif kabulü değildir.
Ham PDF/HTML ve aktarılmış olay satırları Git'e eklenmez; küçük kaynak sicili,
kod, testler ve gönderilmemiş talep taslağı izlenebilir kayıtlardır.

`daily_observation_status=unknown`, pozitif/negatif kapıları kapalı,
boş hedefler ve `model_ready=false` korunur. 2024/2025 model kayıtları açılmadı;
eğitim veya nihai birleştirme yapılmadı.

## Hazırlık sonrası araştırmacı kararı ve kanal kontrolü

15 Ekim'de araştırmacı, açık kaynak araştırmasına ek olarak kurumsal kayıt
talebi yolunu kullanmayı ve taslağı kendisinin göndermesini seçti.
OGM'nin resmî e-Devlet kurum sayfası bilgi talepleri için CİMER'e yönlendiriyor;
bağlantılı resmî hizmetin kimlik doğrulama sayfası kontrol edildi.
[Gönderim rehberi](research/OGM_SUBMISSION_GUIDE_2026-10-15.md) ayrı hazırlandı.
Hesaba giriş/form gönderimi yapılmadı; kullanıcıdan gönderim bildirimi yok.
İlk hazırlıkta hash ile bağlanan taslak ve üretilmiş makbuzlar değiştirilmedi.
Bu tercih bağımsız veri sağlandığı veya bilimsel etiket kabul edildiği anlamına gelmez.

Sonraki kullanıcı bildirimi: CİMER başvurusu tamamlandı. Başvuru numarası,
kişisel bilgi veya gönderilen özel kopya depoya alınmadı. Kurumun yanıtı
ve veri paylaşımı henüz yok; hazırlık makbuzunun `data_request_submitted=false`
alanı o makbuzun üretildiği anı yansıtır ve sonradan değiştirilmez.
