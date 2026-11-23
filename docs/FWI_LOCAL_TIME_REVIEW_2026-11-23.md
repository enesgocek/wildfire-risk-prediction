# FWI özgün yerel zaman başlığı ve biçim karşılaştırması

23 Kasım 2026. Kullanıcının teslim ettiği tek günlük GRIB incelendi.
**Başlık farkı açıklığa kavuştu; 1 Haziran'ın 873 sonlu değeri ve
156 eksik noktalık maskesi NetCDF'in ilk bandıyla birebir aynı.**
Bu tek günün kontrolüdür; tüm ayın GRIB başlıkları, gerçek erişim
gecikmesi veya ana yangın hedefinin kabulü değildir.

## Yapılan kontrol ve somut sonuç

Özgün dosya `data/raw/external/cems_fwi_pilot_v1/963fa09b86438339fee3886631262c59.grib`:
2.088 bayt, tek gerçek GRIB2 mesajı; SHA-256
`f98b51cfb5cff1fbfe4bcd37b5160a97248d639a88624b73f7eae8975815245f`.
Küçük boyutu eksik dosya kanıtı değil: mesaj uzunluğu ve bitiş imzası,
tek alan, 49 × 21 ızgara ve sayısal eşitlik ayrıca kontrol edildi.
Kaynak dosyalar değiştirilmedi.

İlk genel GDAL okuması ürünü/saat alanını tam tanımadı:
`GRIB_VALID_TIME=0`, `GRIB_ELEMENT=unknown`. Bu sıfır bir geçerli tarih
veya 1970 kaydı sayılmadı. Ürün tanım şablonu 4.93 için ECMWF'nin
ecCodes kaynak tanımları sabit depo kimliğiyle ayrıca indirildi ve
yalnız metin olarak incelendi; uzak kod çalıştırılmadı.

| Özgün başlık alanı | Gerçek kayıt ve yorum |
|---|---|
| Referans zaman türü | Kod 4: yerel zaman |
| Referans takvim saati | 1 Haziran 2022, yerel 12:00; UTC yayımlanma saati değil |
| Ürün şablonu | PDT 4.93: yerel zamanlı, yatay düzeyde analiz/tahmin |
| Parametre | Disiplin 2 / kategori 4 / numara 5: Canadian Forest Service FWI |
| Yerel zaman yöntemi | Kod 1: belirtilen yerel zaman için enterpolasyon |
| Kayıtlı forcing başlangıcı | 1 Haziran 2022, 00:00 UTC |
| Kayıtlı zaman artımı | 8 artım, 3 saat birimi; başlangıç 00:00 UTC |
| Yayımlanma/gerçek edinim saati | Dosyada doğrulanmış değil |

Kod 4'ün anlamı resmî [referans zaman tablosuyla](https://codes.ecmwf.int/grib/format/grib2/ctables/1/2/)
doğrulandı. Yerel zaman şablonunun yapısı ve alan adları
[sabit ecCodes 4.93 tanımından](https://github.com/ecmwf/eccodes/blob/454ac2a4a66d6b12cd1a85e688c68dc0c3ab6cca/definitions/grib2/templates/template.4.93.def),
[yerel zaman alanlarından](https://github.com/ecmwf/eccodes/blob/454ac2a4a66d6b12cd1a85e688c68dc0c3ab6cca/definitions/grib2/templates/template.4.localtime.def)
ve [yerel zaman yöntem tablosundan](https://github.com/ecmwf/eccodes/blob/454ac2a4a66d6b12cd1a85e688c68dc0c3ab6cca/definitions/grib2/tables/28/4.248.table)
okundu. [Parametre tablosu](https://github.com/ecmwf/eccodes/blob/454ac2a4a66d6b12cd1a85e688c68dc0c3ab6cca/definitions/grib2/tables/28/4.2.2.4.table)
GRIB değişken kimliğini ayrıca destekliyor. NetCDF paramId numarasının
ayrı parametre veritabanında doğrulanmış olduğu iddia edilmiyor.

Önemli düzeltme: 4.93 şablonundaki 46. baytın adı **zaman artımı
sayısıdır**; bu alan doğrudan sekiz kullanılmış zaman dilimini veya
son dilimin 21:00 olduğunu kanıtlamaz. Sekiz × üç saatlik muhafazakâr
aralık sınırı 2 Haziran 00:00'dır; bu da doğrulanmış son kullanılan
alan veya yayımlanma saati değildir. İlk ayrı makbuzdaki 00–21
sıralaması bu nedenle kabul edilmiş zaman kanıtı olarak kullanılmaz.
[NOAA/NCEP resmî 4.93 şablon tablosu](https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_temp4-93.shtml).

Yerel öğlenin hesaplanma yöntemi, iki tahmin adımı arasındaki
enterpolasyon ve forcing metadata'sının amacı
[ECMWF'nin açıklamasıyla](https://www.ecmwf.int/en/newsletter/173/news/fire-can-now-be-found-mars)
da tutarlı. Yerel öğlen, Türkiye'nin resmî saat dilimindeki 12:00 ile
eşitlenmedi. Zaman artımı kaydı, bu bölgedeki her noktanın bütün
alanları kullandığı veya geçmiş nem durumunun yalnız o gün oluştuğu
anlamına gelmez.

## NetCDF ile sayısal karşılaştırma

İki dosyanın ilk gün ızgara boyutu ve koordinat dönüşümü aynı;
yeniden örnekleme veya yeniden projeksiyon yapılmadı. 873 sonlu
değer tam eşit; en büyük ve ortalama mutlak fark 0. 156 noktalık
eksik maskesi de aynı. DRT 5.0 paketlemesindeki nicemleme aralığı
2⁻¹⁰ = 0,0009765625; izin verilen karşılaştırma farkı bundan ve
float32 hassasiyetinden hesaplandı, veriye uyacak eşik aranmadı.
Ölçülen fark zaten sıfırdır.

GRIB CRS başlığı yarıçapı 6.367.470 m olan küre içeriyor; NetCDF'te
önceden görülen CRS `None` korunuyor. Sayısal ızgara eşitliği,
WGS84 veya projenin projeksiyonuyla tam jeodezik eşdeğerlik kanıtı
sayılmadı. Projenin 5 km hücrelerine henüz bağlama yapılmadı.

## Bu bulguyla hangi zaman yönü savunulabilir?

**Aynı gün nominal 00:00 kaydını o anda hazır günlük FWI kabul etme
yönü uygun değil.** NetCDF'teki 00:00, bu örnekte forcing başlangıcıyla
örtüşüyor; karşılık gelen değer yerel öğlen koşullarını temsil ediyor.
Resmî tarihsel ürün de ERA5 simülasyonlarıyla hesaplanan bir yeniden
kurmadır; gerçek zamanlı teslim kaydı değildir.
[Tarihsel CEMS ürün yöntemi](https://confluence.ecmwf.int/spaces/CEMS/pages/340779714/User+Guide+for+Fire+danger+indices+historical+data+from+the+Copernicus+Emergency+Management+Service).

Önerilen sınırlı yön: yalnız geriye dönük referans karşılaştırmasında
2 Haziran 00:00 hedefi için 1 Haziran FWI alanını kullanmak; sonraki
günleri aynı açık geçmiş-gün kuralıyla ele almak. Bu bir takvim
referansı önerisidir; başlık tek başına bütün forcing bilgilerinin
hedef başlangıcından kesin önce kaldığını kanıtlamaz. Muhafazakâr
artım sınırı hedef başlangıcına eşit olduğundan üç saat güvenlik payı
iddia edilmez. Bu, bütün ayın forcing kayıtlarının aynı olduğunu veya ürünün
2 Haziran 00:00'da gerçekten yayımlandığını kanıtlamaz. Böyle bir
pilot **operasyonel geçmiş tahmin testi** diye sunulmayacak.
Model girdisi olarak kabul veya otomatik T−1 kuralı henüz yok.

## Araştırmacının kararına hazır küçük karşılaştırma

Yeni indirme ve yeni model eğitimi gerekmiyor. Mevcut ayrı Mersin
takviminin 2–30 Haziran 2022 kesiti, dokuz sabit modelin her birinde:

- 7 hücre / 203 hücre-gün; mevcut 15 dinamik model alanı bu kesitte tam.
- 7 kaynak takvimi anahtarı; bunlar doğrulanmış 7 bağımsız yangın değil.
- FWI desteği incelenmeden önce 196 aynı-hücre/ay karşılaştırma çifti.

Sayılar dokuz önceki puan dosyasının güncel hash'i doğrulanarak
yalnız anahtar/tamlık/üyelik alanlarından sayıldı. FWI örneklenmedi,
yeni karşılaştırma skoru veya başarım hesabı yapılmadı. Her ayar aynı
203 anahtarı içeriyor. FWI eksikliği sonraki ortak örneklemi azaltabilir.

**A önerisi:** En fazla 15 dakika, yerelde, yeni fit olmadan;
önceki gün FWI'sini en yakın özgün ızgara noktasından alarak dokuz
kayıtlı model skoru ile aynı sonlu anahtar ve çiftlerde karşılaştırmak.
Eksik kıyı noktasına başka komşudan değer taşınmayacak; fiziksel
çözünürlük artmış sayılmayacak. Eşit uzaklık, koordinat dönüşümü,
ızgara kapsamı ve eksik destek ayrıca raporlanacak. Kaynak üyeliği
Y=1, diğer günler Y=0 yapılmayacak; AP/gerçek yangın olasılığı veya
renk yayımlama kabulü olmayacak. Ana zaman/PU hedefi değişmeyecek.

**B:** Bu günlük eşleştirmeyi henüz seçmeden FWI'yi yalnız inceleme
dosyası olarak korumak. Ana yöntem boşluğu böylece de kapanmaz.

Bu tercih zaman eşleştirme ve değerlendirme yöntemi kararı olduğu
için araştırmacıya sunuluyor; dosya teslimi veya genel devam talimatı
bu yeni karşılaştırmanın yöntem kabulü sayılmadı. FWI sonucu gerçek
yangın etiket/gözlem boşluğunu tek başına kapatmayacak.

## Yerel makbuzlar ve teknik kontrol

Yollar `outputs/reports/dataset/` altında:

| Makbuz | SHA-256 |
|---|---|
| `fwi_grib_metadata_v1/20261123T001516Z_7c2202c2/readback.json` | `90a4b8c054f34eb3bc6140b5e3a6a930dd2e4b3bba6a487b322a2008c6cf7d1c` |
| `fwi_grib_definition_sources_v1/20261123T001639Z_61612b3f/readback.json` | `ed4014d5fd2e81c3e309ed6c6470cafef4b64a97fc0bc758123633b89ae0aabe` |
| Aynı dizinde `additional_definitions.json` | `c8c30e9e1d6786cd4fcd4a5f34a76d963a11444d12b69c97d42e648b1bf8e82b` |
| `fwi_local_time_review_v1/20261123T001956Z_0458f2b3/readback.json` | `41b6fd67ef5455bf9af4706fea67a4b519c939dce922158994f7abef0ada4e01` |
| `fwi_increment_interpretation_v1/20261123T002508Z_5c7204e9/readback.json` | `befa8ecc8e7da5dbc580aa379530ba3ea0426879f2b5411c74a525b86e236ea3` |
| `fwi_reference_comparison_plan_v1/20261123T002128Z_66578e13/readback.json` | `d8326d3bd0b54a5b95cdf66e5309b6e6138e7b49f6a06574ba8c37f26b67bdbf` |

Yeni `review_fwi_local_time.py` dar kapsamlı 4.93 okuyucusu desteklenmeyen
şablon, yanlış zaman türü, eksik/tekrarlı mesaj ve maske/fark uyuşmazlığında
durur. Genel GRIB başlık makbuzu değiştirilmedi. İlk inceleme denemesi
NumPy float32 toleransının JSON yazımında durdu; kabul makbuzu oluşmadı.
Boş deneme dizini `20261123T001930Z_20c719db` korundu. Sayısal tür açık
Python float'a çevrildi ve regresyon kontrolü eklendi; yeni koşu ayrı
kimlikle tamamlandı. Kaynak veri değişmedi.

İlk 00–21 enumerasyonu kaynak baytlarını doğru ayırsa da artım
sayısını alan sayısı yorumladı; bu bilimsel çıkarım geri çekildi.
Kaynak kod ve ilk makbuz korunuyor; ayrı düzeltme üreticisi
`review_fwi_increment_boundary.py` güncel zaman yorumudur. İlk
okuyucunun enumerasyon testi yalnız eski davranış kaydıdır, bilimsel
zaman doğrulaması sayılmaz. Düzeltme testi artık kesin son saat ve
kesin geçmiş-gün erişimi iddiasının kurulmadığını sınar. GEFF'nin açık
`mo_io_eccodes.f90` dosyası da incelendi; ilgili alanların yazımını
açıklamadı, ilave doğrulama sayılmadı.

Beş yeni davranış testi dahil **41 ilgili test** geçti. Yeni üç
üretici ve iki test dosyası Ruff kod/biçim kontrolünden geçti. Yeni
2023–2025 bilimsel değeri, model eğitimi, etiket, risk rengi veya
nihai birleştirme yapılmadı. Kaynak tanımları ve ham veri Git'e eklenmez.
