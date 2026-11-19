# Salur'da kaynak ve ilk tespit örtüsü — 19 Kasım 2026

Amaç, hücrede orman bulunması ile olay adayının yerel örtüsünü ayrı
inceleme yönünü somutlaştırmak. Tek vaka, 28 Temmuz 2021 Salur.
Kullanıcı, yüzdeyle ek eleme yapmadan 2.889 hücreyi koruma kararını
vermişti. Bu çalışma bu nüfusu veya kapalı etiket protokolünü değiştirmez.

## İncelenen konumlar

Kaynak haritasının iki bağımsız görüntü uyumundan elde edilen alternatif
işaret konumu ve ilk yerel katalog tespit merkezi ayrı tutuldu.
İki uyum iki ayrı olay değildir. İlk yerel kayıt
`N20_815590_134793`, 28 Temmuz 10.12 UTC; kaynak işaretinin bir
çözümünden yaklaşık 691 m uzakta. Kaynak eşleşmesi ve gerçek tutuşma
konumu bu yakınlıktan otomatik kabul edilmedi.

Her konum için 100, 250 ve 500 m çevreler ölçüldü: dokuz geometri.
Bunlar duyarlılık çevreleri; gerçek piksel sınırı, tutuşma alanı veya
ölçülmüş konum hatası aralığı değil. Oranların paydası bütün çevre alanı.
Çemberler EPSG:6933 koordinatlarında tanımlı projeksiyon çevreleridir;
elipsoit üzerinde sabit jeodezik uzaklık veya UTM tamponu değildir.

## Eski harita ölçümü ve güncel görüntü

| Konumun 250 m çevresi | CGLS 2017 orman/çalı sınıf payı | CORINE 2018 sınıf alanı |
|---|---:|---|
| Kaynak işareti, görüntü uyumu | %99,97 | %70,05 iğne yapraklı orman; %29,95 geçiş ağaçlık/çalı |
| Kaynak işareti, Sentinel uyumu | yaklaşık %100 | %72,24 iğne yapraklı orman; %27,76 geçiş ağaçlık/çalı |
| İlk yerel tespit merkezi | yaklaşık %100 | %9,95 iğne yapraklı orman; %90,05 geçiş ağaçlık/çalı |

Bu paylar haritaların sınıf alanıdır; olay günündeki doğal örtü yüzdesi
veya doğruluk oranı değildir. Özellikle CORINE geçiş sınıfı kapalılık,
doğallık veya gerçek tutuşma yeri doğrulaması sağlamaz.

20 Temmuz 2021 Sentinel-2B 10 m RGB görüntüsü, olaydan sekiz gün önceki
görsel bağlamı sağlıyor. A kaynak işareti, B ilk yerel tespit merkezidir.
Asistanın ön yorumu A'da ağırlıkla ağaçlık ve yol/açıklıklar; B'de
ağaçlık ile belirgin çıplak/açık alan karışımı. **Araştırmacı bu ön
yorumlara katıldı.** Bu karar yangın etiketi, uzman saha doğrulaması,
doğal örtü yüzdesi veya örnek silme onayı olarak kullanılmadı.

[Araştırmacının incelediği görsel](../outputs/reports/dataset/salur_local_cover_v1/20261119T112923Z_2623c49d/salur_cover_review.png).
RGB görsel incelendi; piksel bazında SCL/bulut/gölge temizliği kabulü yok.
Açıklığın tarım, kesim, maden veya başka kullanım olduğu kararlaştırılmadı.

## Kontrol ve katkı

CGLS kesişimleri EPSG:6933 alanlarında, CORINE kesişimleri özgün raster
CRS'sinde hesaplandı. Dokuz CORINE geometri ölçümü ayrıca exactextract
ile kontrol edildi. En büyük sınıf payı farkı yaklaşık `6,02e-9`, göreli
alan farkı `1,39e-8`. Bu hesap uyumu haritanın arazi doğruluğu değildir.
Üç konumun merkez sınıfları da alan paylarından ayrı kaydedildi.

`python scripts/quality/review_salur_local_cover.py` sekiz sabit kaynağın
hash'ini, yerel 11 katalog merkezinin gün/kimliğini, harita dönüşümlerini,
alan toplamlarını ve JSON geri okumasını denetler. Son görselde panel
dışına taşan A/B yazıları kırpıldı; önceki sürüm korunur, ölçümler aynı.
Yeni rapor:
`outputs/reports/dataset/salur_local_cover_v1/20261119T112923Z_2623c49d/readback.json`.
SHA-256 `846e53f969003cda5bf5aa2dca361f20a04e5d9abafd357b36c04f2cd822f91e`.
Görsel SHA-256 `e1be0c0965e5ecfa7b90f2258dcbdaa4202dc473d0dd776ad9426441652e6aa7`.

Araştırmacı notları ayrı, yeni makbuzda kaydedildi; otomatik rapor
sonradan değiştirilmedi:
`outputs/reports/dataset/salur_local_cover_review_v1/20261119T113546Z_13619fad/readback.json`.
SHA-256 `cb04cf6dae0ddd1bdc4c319784dfc9f2990a5eefb8eb08c56ddc07f97402a49c`.

## Sonraki somut adım: tek ham çift

Mevcut sıkıştırılmış günlük paket `area/centers/scan_grid/scans` toplamları
ve kaynak denetimini içeriyor. Komşu ham koordinat pikselleri bu pakette
yok. İlk yerel tespitin NOAA-20 çiftinin iki dosyası `data/raw` NetCDF
önbelleğinde bulunmadı. Kamuya açık CMR'de iki tam dosya kimliği, tarih,
ürün sürümü ve boyutları yeniden doğrulandı. Veri uçları indirilmedi.

`python scripts/quality/prepare_salur_native_pair.py` mevcut 15 dakikalık
güvenli aktarıcı için yalnız bu çifti seçti. Plan 186.966.497 bayt
(yaklaşık 187 MB), tek işçi, 2 GB önbellek sınırı ve 20 GB boş alan
rezervini koruyor. Kısmi dosya silme/üzerine yazma ve bulut çalışması yok.
Plan normal aktarıcı girişinden geri yüklendi.

Plan:
`outputs/reports/dataset/observation_core_transfer_v1/20261119T113530Z_92bbba6c/native_plan.json`.
SHA-256 `060a2456898a709a07b1a3e95b3abd05bf6921fa91bb11477a0439c6f4d4c4c8`.

Araştırmacıdan istenen yerel PowerShell işlemi:

```powershell
.\.venv\Scripts\python.exe scripts/firms/run_observation_core_pair.py --plan outputs/reports/dataset/observation_core_transfer_v1/20261119T113530Z_92bbba6c/native_plan.json --run-one --prompt-login
```

Earthdata girişi yalnız araştırmacının etkileşimli terminalinde yapılır.
Parola, token veya terminal dökümü istenmedi; yalnız genel sonuç ve klasör
kimliği beklenecek. İndirme sonrası önce bayt/hash ve girdi kimliği,
sonra tam yerel piksel eşleşmesi, kalite ve komşu koordinatlardan yaklaşık
alan incelenecek. Bu da gerçek tutuşma veya yangın kimliği kanıtı değildir.

İlgili mevcut aktarım/CMR/yerel geometri/kapalı etiket testlerinde 137
kontrol geçti; yeni üç komutta Ruff ve biçim kontrolü geçti. İlk test
çalıştırmasında iki test, varsayılan geçici klasörün depo dışında
olması nedeniyle başarısızdı. Üretim kodu değiştirilmeden yeni, depo içi
geçici klasörle 137 test geçti. Bu testler yeni ham piksel sonucunun
yerine geçmez. Birinci aşama açık; 2024/2025 açılmadı, etiket/eğitim/
nihai birleştirme yapılmadı.

## Aynı oturumda indirme sonrası ham piksel sonucu

Araştırmacı yerel indirme işlemini tamamladı. İki dosyada
186.966.497 ağ baytı, beklenen SHA-256 değerleri ve 6.464×6.400 ham
dizilerin başlıkları doğrulandı. Hazırlık sırasındaki bekleme kaydı
yukarıda korunur; aşağıdaki sonuç tamamlanan indirmeye aittir.

`python scripts/quality/review_salur_native_support.py` ağ bağlantısı
kapalıyken çalıştı. İlk yerel katalog noktası, seyrek aktif tespit
dizisinde beş ondalıklı koordinatla tek eşleşme verdi. Ham satır/sütun
19/5113, tarama 0. Zaman aralığı 10.12.00,000738–10.12.00,564538 UTC.
Katalog ile ham merkez farkı yaklaşık **0,346 m**; bu koordinat yuvarlama
uyumudur, sensörün arazi konum doğruluğu değildir.

Merkez yangın maskesi 9 (yüksek güven), çevredeki 3×3 maskede kara ve
üç güven düzeyindeki ısıl sınıflar var. QA=320, işaretli bitler 6 ve 8.
Collection 2 kullanıcı kılavuzu v1.2, basılı s. 5 Tablo 2'de **bit 6
M13 kanalı non-nominal kaliteyi** bildiriyor. Geolocation bit 5 ve artık
bowtie bit 22 sıfır; tarama kalite değeri sıfır. Bu uyarı tek başına
yanlış yangın, hatalı koordinat veya bulut demek değildir. Nedeninin
ne olduğu ve etiket politikasındaki etkisi kabul edilmedi. Ham kayıtta
FRP yaklaşık 174,43 MW; bu değer yangın kimliği veya kalite sorununun
nedenini doğrulamıyor.
[NASA Collection 2 kılavuzu](https://www.earthdata.nasa.gov/s3fs-public/2025-06/VIIRS_C2_AF-375m_User_Guide_1.2.pdf).

Web okuma aracı kılavuz URL'sinde 403 döndürdü; aynı resmî herkese açık
dosya normal anonim GET ile 200 alındı. 1.602.644 bayt, SHA-256
`fb957afb6e465cb312fb8229a2b6e424c489344bb09e76a7baee80a248d1ccb7`.
Tablo hem metin hem sayfa görüntüsünden kontrol edildi. Kılavuzun eski
aylık ürün sürüm açıklaması güncel FIRMS sürüm kararı yerine kullanılmadı.

Komşu 3×3 geolocation merkezlerinden hesaplanan yaklaşık alan
**314.254 m² (0,314 km²)**. Resmî piksel köşeleri veya gerçekten yanmış
alan değil. Önceki EPSG:6933 250 m çevresi bu alanın yaklaşık %62,38'ini
kapsıyor; %37,62 dışarıda. Bu nedenle önceki çember için alınan insan
notu yeni geometrinin tamamına otomatik aktarılmadı.

Yaklaşık alan CORINE'de %14,81 iğne yapraklı orman ve %85,19 geçiş
ağaçlık/çalı sınıfına denk geliyor. CGLS orman/çalı sınıf payı yaklaşık
%100. Ayrı exactextract hesabının sınıf payı farkı `6,52e-10`.
Bunlar eski harita sınıfları; alt pikselde hangi örtünün yandığı bilinmiyor.
Mor sınırın olay öncesi RGB üzerinde ağaçlık/açıklık karışımı yorumu
araştırmacının yeni görsel ön incelemesine sunuldu.

Ham sonuç:
`outputs/reports/dataset/salur_native_support_v1/20261119T114722Z_fb7ab551/readback.json`.
SHA-256 `26735f235170998749b763847281c109c72a878231af4535e8272f65b596ec89`.
[Mor sınır görseli](../outputs/reports/dataset/salur_native_support_v1/20261119T114722Z_fb7ab551/salur_native_support.png).
Görsel SHA-256 `6435c7f90759f54b0f664796f90f7d31251ae1a9f7678958c565692091dda739`.
İndirme makbuzu:
`outputs/reports/dataset/observation_core_native_v1/20261119T113907Z_b104e81d/native_probe.json`.
SHA-256 `2fb726fb9467091ddcffcbf49590bc26d6e9b97fd025a36a9de4541c357608b8`.

İlk yerel çalıştırmada exactextract'e verilen sözlük tipi desteklenmedi;
CRS'si açık GeoDataFrame ile çalıştırma tamamlandı. Girdi veya bilimsel
kabul kodu değiştirilmedi. Daha önceki geometriler ve raporlar korundu.
Kaynak eşleşmesi, yeni başlangıç/devam ayrımı ve dört ilde PU/değerlendirme
koşulları halen açık. Yüksek güven maskesi ve bu tek vaka birinci aşamayı
tek başına tamamlamıyor. Etiket/eğitim/nihai birleştirme yok.

**Araştırmacının geniş alan ön notu:** mor alanın genelinde karışık
örtü olduğu yorumuna katıldı. Mor sınır ile turkuaz çember arasındaki
bölümü gözle yaklaşık %60 ormanlık olarak değerlendirdi. Bu sayı o
bölüm için görsel tahmin; ölçülmüş alan payı, bütün piksel oranı veya
kabul eşiği değildir. Bölge geometrisi araştırmacı tarafından ayrıca
çizilip ölçülmedi. Not yeni makbuzda saklandı:
`outputs/reports/dataset/salur_native_support_review_v1/20261119T115008Z_4164d1f5/readback.json`.
SHA-256 `8d2e7927d094319ac2e24d4d31d7b900a9e575345e01b7ba17e0af09bbdbbd21`.
Bu örneğin teknik örtü/ham merkez incelemesi tamamlandı; ana veri
setine pozitif kabulü sağlanmadı. Bir sonraki bilimsel iş, kaynakla
eşleştirme ve pozitif seçilme/değerlendirme gerekçesini mevcut kabul
taslağında somutlaştırmak. Yeni örtü/kalite bilgisi bu gerekçenin girdisi;
aynı noktaları tekrar saymak birinci aşamayı kapatmaz.

Son bütünlük kontrolünde yedi raporun ve birbirini tekrar eden
girdiler tekilleştirilerek 151 kaynak/çıktı/kod dosyasının hash'i geri
okundu; yeni iki raporun yerel belge bağlantıları da doğrulandı.
Bu sayı bilimsel örnek veya bağımsız deney sayısı değil.
Kapanış makbuzu:
`outputs/reports/dataset/salur_review_closure_v1/20261119T115155Z_c1514d81/readback.json`.
SHA-256 `8876b7b9e01809bbab1c4f6682d96effd7ab2d61dba5703aeb0637f0966b4ff4`.
Son dört komutun Ruff/biçim kontrolü geçti.
