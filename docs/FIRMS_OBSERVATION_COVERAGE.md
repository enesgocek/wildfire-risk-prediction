# FIRMS gözlem kapsamı — eğitim dönemi ön incelemesi

3 Ekim 2026. İnceleme dönemi 2018-01-01 dahil / 2024-01-01 hariç.
2024'ten kural seçilmedi, 2025 final test verisi okunmadı. Bu çalışma günlük
tespit tanısıdır; henüz hücre bazında doğrulanmış gözlem maskesi veya etiket değildir.

## Earthdata destek kaydı

Kaydedilen ekran görüntüsündeki otomatik bildirim, sorunun Earthdata Support'a
ulaştığını ve **#115134** kaydının açıldığını doğruluyor (2 Ekim 2026).
FIRMS 815579/815590 teslimlerinde Type alanının düzeltilmiş üretimden geldiği
konusunda teknik yanıt bekleniyor. Otomatik alındı, bu sorunun cevabı değildir.

## Tamamlanan kontroller

İki arşivin kaynak özetleri, pilot kayıtlarının ham kayıtlarla eşleşmesi,
adayların mevcut seçim kuralıyla uyumu ve günlük toplamların korunması doğrulandı.
4.382 sensör-gün satırı üretildi. Ham veriler ve önceki inceleme dosyaları korunuyor.

| Eğitim dönemi | S-NPP | NOAA-20 |
|---|---:|---:|
| Arşiv talebinin kapsadığı gün | 2.191 | 2.101 |
| Türkiye tespiti | 230.286 | 232.892 |
| Dört ilde bütün türlerden tespit | 31.010 | 32.716 |
| Geçici aday tespit | 14.833 | 15.462 |
| Talep içinde Türkiye'de sıfır tespit günü | 26 | 12 |
| Sıfır günlerden resmî kesinti tablosuyla çakışan | 16 | 1 |

NOAA-20 talebimiz 1 Nisan 2018'de başlıyor; ilk 90 gün sayımları **NaN** ve
talep dışında. Bu, uydunun o dönemde çalışmadığı anlamına gelmez.
İki talebin de kapsadığı ve ikisinde de Türkiye tespitinin sıfır olduğu tek gün
14 Ocak 2019. S-NPP için 10, NOAA-20 için 11 sıfır gün kesinti tablosundaki
aralıklarla çakışmıyor; bunların nedeni henüz belirlenmedi.

## Sayımların sınırı

Türkiye'de veya dört ilde tespit bulunması, her pilot hücrenin açık ve geçerli
gözlendiğini kanıtlamaz. Sıfır tespit de kesinti ya da yangın yokluğu kanıtı değildir.
Resmî tablolar başlıca kesintileri listeler; bazı satırlar belirli bant/ürün veya
granüllerle ilgilidir. Tablo çakışması yalnızca tanısal işarettir; bir pilot
yangın pikselinin kaybedildiği veya bütün sensörün çalışmadığı hükmü verilmez.
Çakışan zamanlar birleşimle sayılır; gece yarısında biten aralık sonraki güne taşınmaz.
Tablodaki saatler tanısal `[başlangıç,bitiş)` zarfı olarak kullanılır; yorumlardaki
granül sınırları piksel incelemesi öncesinde nihai dışlama kuralına dönüştürülmez.

Sayımlar UTC takvim günü `[gün,gün+24h)` içindir. Model hedefi `(T,T+24h]`
olduğundan bunlar doğrudan etiket penceresi maskesi olarak birleştirilmeyecek.
Her satırda `pixel_observation_status=unknown`, `negative_label_permitted=False`.
Bu, bütün günlerin kullanılamaz olduğu kararı değil; mevcut CSV'lerin gözlem
paydasını doğrulamaya yetmediğini gösterir. Hiçbir negatif etiket üretilmedi.

## Sonraki örnek için veri bulunabilirliği

NASA CMR'de üç eğitim günü ve pilotun sınırlayıcı kutusu için metadata sorgulandı:

| Gün | Amaç | S-NPP eşleşen yangın/konum granülü | NOAA-20 eşleşen granül |
|---|---|---:|---:|
| 2019-01-13 | Önceki gün kontrolü | 3 | 5 |
| 2019-01-14 | İki CSV de sıfır | 5 | 3 |
| 2022-07-28 | Uzun S-NPP kesintisi | 0 | 3 |

14 Ocak için ürün metadata'sı bulunması, CSV'nin sıfır olmasından tam veri
kesintisi çıkarılamayacağını gösterir. Katalog kaydı tek başına bulutsuz pilot
gözlemi değildir. 14 Ocak için kutu sorgusunda bulunan beş S-NPP çifti indirildi
ve denetlendi; üç NOAA-20 çifti ve 13 Ocak kontrol çifti de incelendi.
Sonuçları aşağıdaki ilgili bölümlerde kayıtlı.
Sınırlayıcı kutu kesişimleri pilot hücreyle kesin kesişim sayılmaz.

İlk örnek: S-NPP, **2019-01-14 10:18 UTC**, aynı sensör/zaman anahtarıyla:

- `VNP14IMG.A2019014.1018.002.2024086175855.nc` — yaklaşık 3,1 MB.
- `VNP03IMG.A2019014.1018.002.2021102055836.nc` — yaklaşık 167,9 MB.

CMR'nin doğruladığı HTTPS adresleri yerel
`outputs/reports/observation_coverage/first_l2_sample_downloads.csv` dosyasında.
İndirdiğim dosyalar proje kökünde
`data/raw/firms_observation/sample_2019014_1018/` altında tutuluyor. Earthdata
oturumu gerekebilir; giriş bilgileri kod veya Git'e yazılmayacak.

VIIRS L2 ürünü yangın maskesi ve piksel QA alanı içeriyor; yangın noktalarının
koordinat dizileri yalnızca tespit edilen pikselleri kapsadığından diğer pikseller
için eşleşen geolocation gerekir. Maske ve QA ile bulut, işlenmemiş, sınıflanamamış,
kara ve yangın pikselleri ayrılacak. Geçiş zamanları ve alan payları incelenmeden
günlük negatif için eşik seçilmeyecek. Gözlenmiş yangın olmayan piksel de gerçek
24 saatlik yangın yokluğunu kesin olarak kanıtlamaz.
[VIIRS C2 kılavuzu, bölüm 3.1](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf).

## İndirilen ilk çiftin sonucu

Yangın/konum dosyalarının boyutları CMR ile eşleşti. Konum dosyasının NASA MD5
değeri doğrulandı; yangın dosyasının CMR kaydında sağlama değeri yok, yerel SHA256
kaydedildi. Bu bütünlük denetimi antivirüs taraması değildir; yerel antivirüs taramasında tehdit bulunmadığı ayrıca manuel olarak bildirildi.

Yangın ürünü indirilen konum dosyasını doğrudan üretim girdisi olarak gösteriyor.
Ürünler 14 Ocak 2019 10:18–10:24 UTC ve 6.496 × 6.400 pikselde eşleşiyor.
Her dizi HDF5 sürücüsüyle aynı doğal satır/sütun düzeninde okundu; 54 seyrek
yangın kaydının sınıfı ve koordinatı tam dizilerle tek tek doğrulandı. Bütün
geçişteki 54 tespit, Türkiye veya pilot yangın sayısı değildir.

Pilotun sınırlayıcı kutusunda **13.128 piksel merkezi** var; dört ilin gerçek
poligonu içinde **0 merkez** var. İlk örnek katalog kutusu eşleşmesine göre
seçilmişti ve bölgesel QA incelemesi için yeterli çıkmadı. Bu bulgu bulutlu gözlem,
yangın yokluğu veya tüm gün kesintisi kararı değildir. Piksel ayak izleri
hesaplanmadığından sıfır merkez, sıfır alan kesişimi hükmü de değildir.

2.899 hücrenin tümü raporda korunuyor; günlük gözlem durumu `unknown`, negatif
izin bayrağı `False`. Sınıf sayımları alan oranına çevrilmedi. QA dizisinin
boyutu/türü doğrulandı; pilotta merkez olmadığı için bu çift pilot QA koşullarını
açıklamıyor. QA yardımcı kodu girdi kalitesi bitlerini 0–6, konum kalitesini 5,
artık bowtie durumunu 22 olarak ayırır; yangın testi bitleri kalite hatası sayılmaz.

İkinci manuel örnek **2019-01-14 10:24 UTC S-NPP** çifti:

- `VNP14IMG.A2019014.1024.002.2024086175850.nc` — yaklaşık 1,3 MiB.
- `VNP03IMG.A2019014.1024.002.2021102060739.nc` — yaklaşık 175,1 MiB.

İki CMR katalog poligonu da gerçek pilot poligonunu kapsıyor. Bu bir ön seçim
kontrolüdür; indirilen çiftin gerçek piksel/QA sonucu aşağıdadır.
Adresler `next_l2_sample_downloads.csv`, seçim kaydı `next_l2_sample_selection.json`
altında. Hedef klasör `data/raw/firms_observation/sample_2019014_1024/`.
Tek geçiş incelemesi bittikten sonra aynı günün diğer geçişleri ve kontrol günü
karşılaştırılacak; günlük negatif etiket için henüz karar verilmedi.

## İkinci çiftin piksel ve QA sonucu

İndirdiğim 10:24–10:30 UTC çiftinin boyut, zaman ve gerçek konum
girdisi eşleşmesi doğrulandı. Konum dosyası NASA MD5 kaydıyla aynı; yangın
dosyasında resmî CMR sağlama değeri yok, yerel SHA256 kaydedildi. 6.464 × 6.400
boyutundaki dizilerde bütün geçişin 7 yangın kaydıyla doğal satır/sütun ve koordinat
eşleşmesi doğrulandı. Pilot içindeki sayımlar:

| Maske sınıfı | Piksel merkezi sayısı |
|---|---:|
| Bulut | 286.357 |
| Kara (yangın olarak sınıflanmamış) | 18.226 |
| Bowtie silinmiş | 44.542 |
| Su | 331 |
| Yangın (7–9) | 0 |
| Toplam | 349.456 |

Kara sınıfındaki 18.226 merkezin tamamında girdi kalitesi nominal ve artık
bowtie bayrağı kapalı. Nominal QA, bulut/su/silinmiş pikselleri gözlenmiş kara
yapmaz. 44.542 nominal olmayan girdi bayrağı bowtie silinmiş sınıfında; konum
kalitesi ve artık bowtie bayrak sayımları pilotta sıfır. QA sınıf çapraz sayımı
rapora eklendi. Bu kalite koşulu tek geçiş tanısıdır; günlük negatif kullanım
eşiği veya uygunluk profili değildir.

2.868 hücrede merkez var; sadece 443 hücrede en az bir nominal girdili, artık
bowtie olmayan kara merkezi var. Bu hücrelerin tamamen bulutsuz olduğu sonucu
çıkarılmaz. 31 hücrede merkez yok. Bütün 2.899 hücre korunur; günlük durum hâlâ
`unknown`, negatif izin `False`. Sayılar merkez adetleridir; alan yüzdesi veya
24 saatlik yangın yokluğu değildir. Bu örnek, katalog/tespit bulunabilirliğinin
bulutsuz gözlem paydasından neden ayrı tutulduğunu gösteriyor.

Aynı günün **00:42 UTC S-NPP** geçişi de indirildi. Dosyalar:

- `VNP14IMG.A2019014.0042.002.2024086175852.nc` — yaklaşık 1 MiB.
- `VNP03IMG.A2019014.0042.002.2021102055658.nc` — yaklaşık 177,7 MiB.

Adresler `night_l2_sample_downloads.csv`, seçim/kaynak kaydı
`night_l2_sample_selection.json`; klasör `data/raw/firms_observation/sample_2019014_0042/`.
Bu çift bütün günün kapsamını tamamlamaz; diğer geçişler ve NOAA-20 ayrı
değerlendirilecek. 2024'ten kural seçilmedi, 2025 açılmadı.

## Gece geçişi ve iki geçişin karşılaştırması

00:42–00:48 UTC çiftinin boyut, NASA konum MD5, zaman ve gerçek geolocation
üretim girdisi kontrolleri geçti. Ürün gece bayrağı taşıyor; gündüz piksel sayısı
0, gece piksel sayısı 41.369.600. Bütün geçişteki 246 seyrek yangın kaydı,
maske sınıfı/koordinatı ve doğal satır düzeniyle eşleşti; bunlar pilot yangın
sayısı değil. Pilot sayımları:

| Piksel merkezi sınıfı | Gece 00:42 UTC | Gündüz 10:24 UTC |
|---|---:|---:|
| Bulut | 129.964 | 286.357 |
| Nominal girdili, artık bowtie olmayan kara | 109.727 | 18.226 |
| Bowtie silinmiş | 73.130 | 44.542 |
| Su | 1.274 | 331 |
| Yangın | 0 | 0 |
| Toplam | 314.095 | 349.456 |

Gece 2.836 hücrede merkez var; 2.031 hücrede en az bir nominal girdili kara
merkezi var. Gündüz bu ikinci sayı 443. İki geçişin birleşiminde 2.182 hücrede
en az bir böyle merkez var; ikisinde birden 292, yalnız gece 1.739, yalnız
gündüz 151 hücre. 717 hücrede bu iki örnekte nominal girdili kara merkezi yok.
Bu merkezler aynı alanın eşit büyüklükte/bağımsız gözlemleri sayılmadı ve geçişler
arasında piksel merkezleri toplanıp alan kapsamına dönüştürülmedi. Bir merkez
bulunması hücrenin tamamının gözlendiği veya günün yangınsız olduğu hükmü değildir.
Tüm hücrelerin günlük durumu `unknown`, negatif izin `False` olarak korunuyor.

Kalıcı `compare_l2_observation_samples.py` yerel raporları kaynak/kod/coğrafya
özetleri ve sınıf toplamlarıyla doğrular; hücre anahtarına göre birleşim üretir.
İlk karşılaştırma eğitimde aynı UTC günündeki S-NPP örnekleriyle yapıldı; tam
günlük kapsam hattı değildir. Dört test, farklı satır sırası/eksik
ve tekrarlı anahtarların yanlış birleşmesini ve günlük negatif iznini önler.

CMR kutu sorgusunda bulunan **12:00 ve 22:42 UTC S-NPP** çiftleri de indirildi
ve denetlendi. Her iki çiftin katalog poligonu pilotla kesişiyor, bütün pilotu kapsamıyor.
`remaining_snpp_l2_sample_downloads.csv` dört dosyanın adreslerini,
`remaining_snpp_l2_sample_selection.json` resmî metadata/poligon ön kontrolünü
tutar. Hedef klasörler `sample_2019014_1200/` ve `sample_2019014_2242/`.
Sonraki aşama aynı günün NOAA-20 geçişleri ve kontrol günü karşılaştırması.

## Kalan iki S-NPP çiftinin sonucu

Her klasöre doğru yangın/geolocation çiftini koydum. Dört dosyanın
kimlik/boyutu CMR ile, iki konum dosyasının MD5 özeti NASA kaydıyla eşleşiyor.
Maskelerin gerçek geolocation üretim girdileri ve zamanları eşleşti. Bütün
geçişteki 12:00 için 37, 22:42 için 410 seyrek yangın kaydının doğal dizi
sınıf/koordinatı doğrulandı; bu kayıtların hiçbiri pilot poligonuna düşmedi.
Yangın dosyalarında CMR sağlama değeri yok; yerel SHA256 kaydedildi.

| Pilot piksel merkezi sınıfı | 12:00 UTC | 22:42 UTC |
|---|---:|---:|
| Bulut | 104.328 | 129.771 |
| Nominal girdili, artık bowtie olmayan kara | 10.291 | 10.140 |
| Bowtie silinmiş | 37.989 | 46.934 |
| İşlenmemiş | 0 | 423 |
| Su | 566 | 103 |
| Yangın | 0 | 0 |
| Toplam | 153.174 | 187.371 |

12:00'da 349, 22:42'de 313 hücrede en az bir nominal girdili kara merkezi var.
Kara sınıfında girdi/konum kalitesi hatası ve artık bowtie bayrağı yok. 22:42
geçişindeki 423 işlenmemiş merkez gözlem sayılmadı; nominal olmayan girdi
toplamı 47.357 (46.934 silinmiş + 423 işlenmemiş).

Beş S-NPP raporu kaynak özetleri ve sınıf toplamlarıyla denetlenerek hücre
anahtarında karşılaştırıldı: 2.327 hücrede en az bir nominal girdili kara merkezi
var; 572 hücrede bu beş örnekte yok. Önceki gece/gündüz ikilisine göre 145
hücrede daha böyle bir merkez bulundu. 10:18 örneği pilotta merkez taşımadığı
için beşinin hepsinde merkez bulunan hücre sayısı sıfırdır; bu tam günlük
kapsamın ölçütü olarak kullanılmadı. Hiçbir piksel veya geçiş sayımı alan oranı,
tam gözlenmiş hücre veya günlük negatif etikete dönüştürülmedi. Tüm hücrelerin
günlük durumu `unknown`. NOAA-20 ile devamındaki karşılaştırma aşağıda.

## NOAA-20 karşılaştırması için hazırlık

14 Ocak 2019 için üç NOAA-20 çifti CMR ile eşleşiyor: **09:30, 11:12, 23:30 UTC**.
Altı dosyanın resmî metadata kopyası kaydedildi; yangın ve konum katalog
poligonlarının tamamı gerçek pilot poligonuyla kesişiyor. Bu ön seçimin ardından
altı dosya manuel olarak indirildi ve aşağıdaki gerçek piksel/QA denetimi
tamamlandı. Konum dosyalarının beklenen MD5 değerleri metadata'da mevcut.
Yangın ürünleri `VJ114IMG.002`, konum ürünleri `VJ103IMG.021` (CMR sürümü 2.1).

Manuel liste `noaa20_l2_sample_downloads.csv`, katalog/kaynak kaydı
`noaa20_l2_sample_selection.json`. Üç klasör hazır:

- `data/raw/firms_observation/sample_N20_2019014_0930/`
- `data/raw/firms_observation/sample_N20_2019014_1112/`
- `data/raw/firms_observation/sample_N20_2019014_2330/`

Yerel denetim artık S-NPP ve NOAA-20 ürün adı/sürümünü ayrı doğrular; aynı
sensör, aynı zaman ve **gerçek konum üretim girdisi** zorunlu. Salt zaman
eşleşmesi kabul edilmez. NOAA-20 raporlarının adında `N20` bulunur; aynı saatli
iki sensör birbirinin raporunu değiştirmez. CMR koleksiyon sürümü de denetlenir.
Yangınsız bütün geçişte boş seyrek diziler geçerli kabul edilir; o durumda
seyrek koordinatla bağımsız yön kontrolünün yapılamadığı açıkça raporlanır.

Karşılaştırmada `N20:2019014.0930` gibi sensör/zaman anahtarları kullanılır.
Sensör başına ve birlikte en az bir nominal girdili kara merkezi bulunan hücre
sayısı raporlanır. Bu işlem de alan oranı, tam günlük gözlem veya negatif etikete
dönüştürülmez. Gerçek NOAA-20 dosya düzeni indirilen üç çiftte sınandı.

Genişletilen kodla beş mevcut S-NPP çifti yeniden denetlendi. Bütün merkez/sınıf/QA
toplamları, ham dosya özetleri ve beş hücre CSV'sinin SHA256 değerleri öncekiyle
birebir aynı. Birleşim hâlâ 2.327/572. Yeni kapsam için 12 test eklendi;
toplam 93 test başarılı. Bu çalışma eğitimde; 2025 açılmadı.

## Üç NOAA-20 çiftinin sonucu ve iki sensörün birleşimi

Altı dosya doğru klasörlerde. CMR kimlik/boyut, üç konum dosyasının resmî MD5,
aynı zaman/sensör ve gerçek geolocation üretim girdisi kontrolleri geçti. Yangın
ürünlerinde CMR sağlama değeri bulunmadığından yerel SHA256 kaydedildi; resmî
checksum doğrulaması yapılmış sayılmadı. Geçişlerdeki 30/21/197 seyrek yangın
kaydının doğal dizi sınıf/koordinatı eşleşti; hiçbiri pilot poligonuna düşmedi.

| Pilot piksel merkezi sınıfı | 09:30 UTC | 11:12 UTC | 23:30 UTC |
|---|---:|---:|---:|
| Bulut | 24.694 | 315.907 | 325.196 |
| Nominal girdili, artık bowtie olmayan kara | 1.846 | 35.548 | 38.575 |
| Bowtie silinmiş | 8.838 | 13.601 | 12.669 |
| İşlenmemiş | 0 | 0 | 160 |
| Su | 16 | 1.156 | 98 |
| Yangın | 0 | 0 | 0 |
| Toplam | 35.394 | 366.212 | 376.698 |
| En az bir nominal kara merkezi bulunan hücre | 76 | 594 | 570 |

Pilot kara merkezlerinin girdi/konum kalite bayrakları nominal; artık bowtie
bayrağı yok. 23:30'daki 160 işlenmemiş merkez gözlem kabul edilmedi.

Beş S-NPP ve üç NOAA-20 örneği hücre anahtarıyla birleştirildi. Geri okunan
rapor/CSV toplamları ve kaynak özetleri denetlendi:

| En az bir nominal girdili kara merkezi bulunan örnekler | Hücre sayısı |
|---|---:|
| S-NPP | 2.327 |
| NOAA-20 | 1.141 |
| Her iki sensör | 1.049 |
| Yalnız S-NPP | 1.278 |
| Yalnız NOAA-20 | 92 |
| En az bir sensör | 2.419 |
| İkisinde de böyle bir merkez yok | 480 |

NOAA-20, S-NPP'ye ek 92 hücrede böyle bir merkez sağladı. Bu merkez sayımları
tam hücre/alan/gün kapsamı değildir; tüm 2.899 hücre hâlâ `unknown`, negatif
etiket izni `False`. İncelenen sekiz geçişte pilot yangın sınıfı yok. Buna
rağmen ürünlerde pilot dışında yangın kayıtları ve pilot içinde nominal kara
merkezleri var; CSV'de sıfır tespit tek başına tam gün cihaz kesintisi göstermez.
Sıfır tespitin kesin nedeni veya günlük yangın yokluğu doğrulanmış değildir.

## Tespit bulunan kontrol örneği için hazırlık

Sonraki kontrol 13 Ocak 2019 **01:00–01:06 UTC S-NPP** geçişi. Mevcut FIRMS
aday tablosundaki `SNPP_815579_37380` kaydı 01:02 UTC, 38.78991/26.92164
konumunda; `E6933_5K_V1_C519_R917` hücresinde. Bu bir termal tespit adayıdır;
doğrulanmış orman yangını veya nihai pozitif etiket kabul edilmez.

`G2923099810-LPCLOUD` yangın ve `G2126421215-LAADS` konum metadata'sı alındı.
Her iki katalog poligonu aday konumunu kapsıyor; aday zamanı ürün aralığında.
Konum dosyasının beklenen MD5 değeri `0ac8235a81a170a839c675a5c3f64d06`.
İki dosya manuel olarak `data/raw/firms_observation/sample_2019013_0100/`
klasörüne indirildi. Kontrol seçimi kaynak aday/metadata özetleriyle kaydedildi.
Gerçek piksel/QA ve FIRMS eşleşmesi aşağıda. NASA Type alanı hakkındaki teknik
yanıt hâlâ bekleniyor.

## Tespitli kontrolün gerçek piksel ve FIRMS eşleşmesi

Dosyaların CMR kimlik/boyutu, konum dosyasının resmî MD5 değeri ve gerçek konum
üretim girdisi doğrulandı. Bütün geçişteki 174 seyrek yangın kaydının doğal
satır/sütun, sınıf ve koordinatı eşleşti. Pilot içinde 127.668 merkez var:
63.131 bulut, 31.793 nominal girdili kara, 32.015 bowtie silinmiş, 73 işlenmemiş,
653 su ve 3 nominal güvenli yangın merkezi. 618 hücrede en az bir nominal kara
merkezi bulundu. Bu tek geçişten tam alan veya günlük kapsam çıkarılmadı.

`check_l2_firms_control.py` mevcut kaynak/metadata/denetim özetlerini doğrulayıp
aynı sensörün pilot arşivindeki `[01:00,01:06)` kayıtlarını okur. Eşleşme,
arşiv koordinatlarının beş ondalık basamak yuvarlama aralığı içindeki tek seyrek
pikseli gerektirir; en yakın piksele geniş toleransla atama yapılmaz. Tekrarlı,
belirsiz veya eksik eşleşme, güven sınıfı ve hücre uyuşmazlığı işlemi durdurur.
Pikselin maskesi/QA ve tam konum dizileri doğal indeksten geri okunur.

| FIRMS kimliği | Arşiv Type (teyit bekliyor) | Maske sınıfı | Doğal satır/sütun (0 tabanlı) | Konum farkı | Artık bowtie |
|---|---:|---:|---|---:|---|
| SNPP_815579_37380 | 0 | 8 | 2547 / 5855 | 0,406 m | Hayır |
| SNPP_815579_37382 | 2 | 8 | 2554 / 5863 | 0,409 m | Evet |
| SNPP_815579_37383 | 2 | 8 | 2569 / 5864 | 0,368 m | Hayır |

Üç kaydın arşiv güveni `n`, maske sınıfı 8 ve konum/girdi kalite bayrakları
nominal. Bir kaydın artık bowtie bayrağı ayrıca korunuyor; yeni bir eleme
kuralı seçilmedi. İlk kayıt `E6933_5K_V1_C519_R917`, diğer ikisi C519/R916
hücresinde. Pilot içindeki üç seyrek yangın merkezi de eşleşti; eşleşmeyen yok.
Pilot dışında kalan komşu seyrek merkez, pilot arşivine eksik kayıt sayılmadı.

Bu sonuç termal tespit/koordinat hattını sınar; Type 0/2 doğruluğunu veya
bitki örtüsü yangını olduğunu doğrulamaz. Arşiv dakikası granül aralığındadır;
kesin piksel alım saniyesi denetlenmedi. Yeni etiket atanmadı, günlük negatif
izin hâlâ `False`, 2025 açılmadı. Sekiz yeni regresyon testiyle toplam 101 test
başarılı; kod ve biçim kontrolleri geçti. Yerel JSON/CSV sınıf toplamları geri
okunarak doğrulandı.

Sonraki aşama merkez sayımından ayrı, piksel alanı ve geçiş zamanını gözeten
hücre gözlem hesabını tasarlamak. Bulut/silinmiş/işlenmemiş alanlar ve çok
sensörlü örtüşme ayrılmalı; aynı alan/geçiş tekrar sayılmamalı. Alan/geçiş
başarısı tek başına 24 saatte yangın olmadığını kanıtlamaz. Tam dönem veri
edinme hacmi ve günlük kullanım kuralı eğitim döneminde incelenmeden toplu
etiket üretimine geçilmeyecek.

Bu aşamanın devamında dokuz örneğin tarama içi yaklaşık geometri/alan hesabı
çalıştırıldı; sekiz örnek iki sensörlü geometrik birleşimle karşılaştırıldı.
Gerçek tarama saatleri/mod/kalite ve nominal dosya sınırını geçen taramalar
kaydedildi. Yaklaşık nominal yangınsız kara birleşimi 36.011,819 km²; %59,30
tek başına günlük gözlem veya negatif etiketi değildir. Üç kontrol pikselinin
boyut karşılaştırması fiziksel doğruluğu kesinleştirmedi; yaklaşık geometri
üretim etiketlerine taşınmadı. 22 yeni testle toplam 123 test başarılı.
Yöntem, sınırlar, yeniden üretim ve açık doğrulama işleri:
[gözlem alanı yöntemi](OBSERVATION_AREA_METHOD.md).

## Yerel kayıtlar ve yeniden üretim

`outputs/reports/observation_coverage/` altında:

- `sources/manifest.json`: resmî HTML kopyaları, URL/alım zamanı/dosya özetleri.
- `training_sensor_daily.csv`: iki sensörün günlük sayıları ve tanı bayrakları.
- `training_outage_intervals.json`: yalnızca eğitim dönemindeki tablo aralıkları.
- `training_review.json`: kaynak, toplamlar ve açık kapsam sınırları.
- `l2_training_sample_inventory.json`: üç günün CMR sorguları ve granül eşleşmeleri.
- `first_l2_sample_downloads.csv`: ilk eşleşen iki dosyanın indirme listesi.
- `G*_metadata.json`: dosya kimliği/boyutu ve varsa NASA sağlama değeri.
- `l2_sample_2019014.1018_audit.json`: eşleşme, bütünlük ve doğal dizi düzeni denetimi.
- `l2_sample_2019014.1018_grid_centers.csv`: tüm hücreler için merkez sayımları.
- `l2_sample_2019014.1024_audit.json`, `l2_sample_2019014.1024_grid_centers.csv`: ikinci çift.
- `next_l2_sample_downloads.csv`, `next_l2_sample_selection.json`: sonraki çiftin ön seçimi.
- `night_l2_sample_downloads.csv`, `night_l2_sample_selection.json`: aynı gün gece karşılaştırması.
- `l2_sample_2019014.0042_audit.json`, `l2_sample_2019014.0042_grid_centers.csv`: gece denetimi.
- `l2_comparison_2019-01-14_SNPP_2samples.json/.csv`: iki geçişte hücre bazında merkez bulunabilirliği.
- `remaining_snpp_l2_sample_downloads.csv`, `remaining_snpp_l2_sample_selection.json`: kalan iki çift.
- `l2_sample_2019014.1200_audit.json`, `l2_sample_2019014.1200_grid_centers.csv`: 12:00 denetimi.
- `l2_sample_2019014.2242_audit.json`, `l2_sample_2019014.2242_grid_centers.csv`: 22:42 denetimi.
- `l2_comparison_2019-01-14_SNPP_5samples.json/.csv`: beş S-NPP örneğinin hücre karşılaştırması.
- `noaa20_l2_sample_downloads.csv`, `noaa20_l2_sample_selection.json`: üç NOAA-20 çifti için hazırlık.
- `snpp_baseline_before_noaa20_support.json`: genişletme öncesi S-NPP kaynak/sayım/CSV özetleri.
- `l2_sample_N20_2019014.0930_audit.json`, `l2_sample_N20_2019014.0930_grid_centers.csv`: NOAA-20 09:30.
- `l2_sample_N20_2019014.1112_audit.json`, `l2_sample_N20_2019014.1112_grid_centers.csv`: NOAA-20 11:12.
- `l2_sample_N20_2019014.2330_audit.json`, `l2_sample_N20_2019014.2330_grid_centers.csv`: NOAA-20 23:30.
- `l2_comparison_2019-01-14_N20_3samples.json/.csv`: üç NOAA-20 örneğinin birleşimi.
- `l2_comparison_2019-01-14_SNPP_N20_8samples.json/.csv`: sekiz örneğin iki sensörlü karşılaştırması.
- `control_l2_sample_downloads.csv`, `control_l2_sample_selection.json`: 13 Ocak tespitli kontrolün ön seçimi.
- `l2_saved_outputs_8samples_verification.json`: sekiz raporun kaynak/toplam/QA ve bağımsız sensör birleşimi kontrol sonucu.
- `l2_sample_2019013.0100_audit.json`, `l2_sample_2019013.0100_grid_centers.csv`: tespitli kontrol çiftinin piksel/QA denetimi.
- `l2_sample_2019013.0100_firms_control.json`: üç pilot FIRMS kaydının piksel, güven, hücre ve QA eşleşmesi.

Sayımlar ve kesinti eşleştirmesi kalıcı betikle yeniden üretilebilir. Yerel örnek
denetimi `inspect_l2_observation_sample.py` ile yeniden üretilebilir. L2 metadata
envanteri bu oturumdaki salt okunur sorguyla üretildi; henüz toplu indirme/günlük
kapsam hattı değildir. 123 test, kod ve biçim kontrolleri başarılı.
İl sınırları basitleştirilmedi; kesin geometriye hazırlanan mekânsal indeksle
piksel eşleştirmesi hızlandırıldı. Çıktı sınıf/QA toplamları geri okunarak uzlaştırıldı.

Kaynaklar: [S-NPP kesinti tablosu](https://modaps.modaps.eosdis.nasa.gov/services/production/outages_suomi_npp.html),
[NOAA-20 kesinti tablosu](https://modaps.modaps.eosdis.nasa.gov/services/production/outages_noaa_20.html),
[NASA: bulut/eksik veride kaçırılan tespitler](https://forum.earthdata.nasa.gov/viewtopic.php?t=5177).
