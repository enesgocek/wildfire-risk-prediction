# Marmaris/Bördübet kaynak işareti — 19 Kasım 2026

## Amaç ve sonuç

Salur dışındaki fit-dönemi vakalarında, hata içerebilen L adaylığı için
kaynak kökeni açık konum kanıtı araştırıldı. Marmaris'in 21 Haziran 2022
yangını için yayımlanmış başlangıç sembolü bulunup yaklaşık konumu
hesaplandı. **Yeni L üyeliği veya hedef etiketi oluşturulmadı.** Tek Salur
hücresi için önceki olası L önerisi aynı durumda; bilimsel birinci aşama açık.

Önceki sicilin 27 bağlam satırı yalnız tarih/rol bilgisiyle ayrıldı:
20 satır 2018–2022 fit-rolü, yedi satır 2023 kalibrasyon bağlamında.
Bunlar bağımsız yangın veya L örneği sayıları değil. 2023 örnekleri fit
pilotuna taşınmadı; 2023/2024/2025 bilimsel veri değerleri kullanılmadı.

## Gerçek kaynaklar ve uyuşmazlık

- Delfin Günay Ercan ve Mehmet Uygunol, **2022**, *Yanmış Alanların
  Uzaktan Algılama ile Tespiti ve Arazi Örtüsü Sınıfları ile
  Karşılaştırılması, Muğla/Marmaris Örneği*, UZAL-CBS 2022.
  PDF sayfa 6, Şekil 9'da tek sarı başlangıç sembolü; sayfa 7'de
  batıdan doğuya ilerleme anlatımı var. Başlangıç koordinat tablosu,
  sembol hata sınırı ve her başlangıcın ayrı kimliği sunulmuyor.
  [Birincil bildiri](https://uzalcbs.org/wp-content/uploads/bildiriler/2022/2022_12754.pdf).
- Belediyenin **25 Haziran 2022** açıklaması üç başlangıç noktası
  anlatıyor. Önceden korunan HTML yeniden doğrulandı.
  [Belediye açıklaması](https://www.mugla.bel.tr/haber/buyuksehirden-marmaris-yangini-raporu).
- Ege Orman Vakfının yayımladığı, **3–4 Eylül 2022** saha incelemesini
  anlatan raporun PDF sayfa 20'si yaklaşık 2 km boyunca dört başlangıç
  bildiriyor. Sayfa görsel olarak da okundu. Noktaların koordinatları
  çıkarılamadı; üç/dört uyuşmazlığı çözülmedi.
  [Birincil saha raporu](https://www.egeorman.org.tr/images/orman-yanginlari-sonrasi-inceleme-ve-degerlendirme-raporu.pdf).

Bildiri belediyenin CBS çalışmasını derliyor; bunlar tamamen bağımsız
ölçümler sayılmadı. Saha raporundaki başlangıç sayısının asıl ölçüm kökeni
de doğrulanmadı. Başlangıç sayılarından gerçek bağımsız yangın sayısı
üretilmedi; yanmış alan merkezi başlangıç koordinatı olarak kullanılmadı.

## Teknik işlem ve bulgu

Haritanın yedi görüntü bölgesi, bilinen EPSG:3857 sınırlarıyla alınan tek
Esri referans görüntüsünde normalize çapraz korelasyonla eşleştirildi.
Yollar/arazi şekilleri karşılaştırıldı; yangın tespitlerine uydurma yok.
Eşleşme çiftleri asistan tarafından görsel kontrol edildi; araştırmacının
yeni manuel incelemesi sayılmadı. Referansın tarihi bilinmediğinden
geçmiş örtü kanıtı veya model girdisi olarak kullanılmadı.

UTM 35N'de afin dönüşüm ve kontrol çıkarma hesabı yapıldı. Aynı referanstaki
dört renklendirilmemiş bölgeyle duyarlılık hesabı bağımsız görüntü doğrulaması değil.

| Ölçüm | Yedi bölge | Dört bölge alt kümesi |
|---|---:|---:|
| En büyük kontrol çıkarma konum farkı | 8,53 m | 11,99 m |
| Sembol merkezinin kontrol çıkarma ile en büyük kayması | 5,97 m | 14,69 m |
| Merkezin kırpılmış AOI'ye uzaklığı, EPSG:6933 | 30,55 m | 36,88 m |
| Merkezi kapsayan kırpılmış AOI hücresi | Yok | Yok |
| Görünür sembol alanıyla kesişen hücre | C541/R878 | C541/R878 |

Yaklaşık sembol merkezi 28,0574° D / 36,8696° K; iki tahmin 8,42 m
ayrılıyor. **Uyum gerçek başlangıç konumunun doğruluğu değil.** İşaret
kontrol bölgelerinin dışbükey zarfının dışında; ekstrapolasyon var.
Görünür sarı sembolün 11 piksel yarıçapı yalnız baskıdaki işaret alanı;
yer hatası/yangın sınırı sayılmadı. Merkez en yakın kara hücresine taşınmadı.

Yalnız 20–22 Haziran 2022 katalog satırları bilimsel işleme alındı.
İşaretin 3 km çevresinde bu üç günden 34 kayıt var; hedefleri boş.
21 Haziran UTC hedef penceresinde, önceden kayıtlı 17:02 UTC kurum
saatinden sonra 1 km içinde kayıt yok; bu negatif kanıt değil.
2 km içinde beş, 3 km içinde on kayıt var. İlk dakika 23:22 UTC;
ilk kayıtların hücresi `E6933_5K_V1_C541_R878`. En yakın kayıt yaklaşık
1.217 m uzakta. Saat farkı tutuşma gecikmesi, mekânsal fark yayılma hızı sayılmadı.

## Tek ham çift ve devam sınırı

2 km içindeki beş ilk katalog merkezi aynı NOAA-20 geçişinde. Kabul
edilmiş günlük raporda bunları kapsayan granül **N20:2022172.2318**,
23:18–23:24 UTC. 23:22 katalog dakikası dosyanın 23:18 adıyla çelişmiyor.
Güncel CMR'de iki dosyanın tam kimliği/boyutu doğrulandı. Yerelde çift
bulunmadı. Plan **175.759.551 bayt**, tek çift/işçi, 900 saniye,
2 GB önbellek sınırı ve 20 GB boş alan koşulu taşıyor.
Ham dosya indirilmedi; araştırmacının kendi terminalinde özel Earthdata girişi gerekiyor.

İndirme sonrası beş merkezin ham maske/koordinat ve kalite eşleşmesi
kontrol edilecek. Bu işlem üç/dört başlangıç uyuşmazlığını, sembolün
fiziksel konum hatasını veya PU seçilme varsayımlarını tek başına çözmeyecek.
Olası L üyeliği ayrıca değerlendirilecek; Salur kararı genellenmedi.
Kaynak bulunabilirliğine göre derlenen örnekler için örnekleme tasarımı,
sınıf koşullu seçilme ve pozitif zenginleşme desteği henüz yok.

## Yeniden üretim ve kontrol

Komutlar: `scripts/quality/review_marmaris_published_marker.py` ve
`scripts/quality/prepare_marmaris_native_pair.py`.

- Kaynak klasörü: `outputs/reports/dataset/L_expansion_sources_v1/20261119T122526Z_9d545fe4/`.
  Bildiri SHA-256 `82d1ddb27577c8da4aedbe9aafe7c3a519f5d3415d8f7e03f983d51edcb63537`;
  saha raporu `0b41f3af4a794a8454ec559b1844364f916cab4645c42dedce34a97355c4865c`.
- Son kayıt: `outputs/reports/dataset/marmaris_published_marker_v1/20261119T124316Z_6993b935/readback.json`.
  SHA-256 `6672e96bb52dbc65d385b9debd00675528f868086b6eb0df2992feb6a438301b`.
- Plan: `outputs/reports/dataset/observation_core_transfer_v1/20261119T124453Z_f5b8c745/native_plan.json`.
  SHA-256 `04b40b06a7137b0fbea2618a141867ad2fef13052e265ed070c13f34b358a864`.
- Geri okuma: `outputs/reports/dataset/marmaris_marker_closure_v1/20261119T124544Z_2ab242a0/readback.json`.
  SHA-256 `5696e6de795f41a7c3ecf9258e6aab26902dce641de2cd3dc78c4537030d0b0b`.

Kaynak/çıktı/kod hash'leri ve tek-çift plan sınırları geri okundu.
Bu oturumda kayıt eşleme, hedef kabulü ve aktarımla ilgili **99 davranış
testi geçti**; yeni komutların Ruff/biçim kontrolü geçti.
Eski deneme çıktıları korundu; son sürüm yukarıdaki kimlikle ayrıldı.
Bunlar gerçek yangın/etiket doğruluğu testleri değil. Gözlem `unknown`;
etiket izinleri, eğitim ve nihai birleştirme kapalı. Birinci aşama açık;
bulut işi veya yeni yazışma başlatılmadı.

## Aynı gün: indirme sonrası ham, örtü ve zaman sonucu

Araştırmacının yerel indirmesi tamamlandı. İki dosyada 175.759.551 bayt,
beklenen SHA-256 değerleri, 6.464×6.400 boyut ve gerçek geolocation
girdi işaretçisi doğrulandı. Yukarıdaki indirme bekleme kaydı hazırlık
anının durumudur; aşağıdaki bulgular tamamlanan indirmeye aittir.

Beş planlı katalog merkezi ham seyrek dizide tek eşleşme verdi; merkez
farkı en çok 0,482 m. Bu yuvarlama uyumu, sensörün gerçek arazi konum
doğruluğu değil. Hepsi maske 8, nominal güven düzeyinde. QA=384 üç,
QA=29952 iki kayıtta; alt yedi giriş kalite biti sıfır. Üst yangın testi
bitleri giriş arızası sayılmadı. Gerçek yangın/yanlış tespit kabulü yapılmadı.
[NASA kılavuzu, basılı s.5 Tablo 2 ve s.6 Tablo 3](https://www.earthdata.nasa.gov/s3fs-public/2025-06/VIIRS_C2_AF-375m_User_Guide_1.2.pdf).
Kılavuzun önceden doğrulanmış yerel kopyası yeniden okundu; web aracı
bu oturumda 403 verdi. Yeni kılavuz sürümü iddiası yok.

| Kod | Katalog son eki | Ham satır/sütun | Yaklaşık alan, km² | Araştırmacının örtü ön notu |
|---|---|---|---:|---|
| M1 | 172025 | 5009/1412 | 0,309 | Ormanlık, yol; gözle yaklaşık %90 |
| M2 | 172075 | 5006/1412 | 0,319 | Dağlık görünüm; orman doğrulanamıyor |
| M3 | 172076 | 5006/1413 | 0,318 | Yükseltili, ağaçlık alan |
| M4 | 172083 | 5007/1412 | 0,317 | Ormanlık, ince yol; gözle %90–95 |
| M5 | 172084 | 5007/1413 | 0,318 | M3 ile aynı ön yorum |

Tam kimlik öneki `N20_815590_`. Yüzdeler araştırmacının görsel tahmini;
ölçülmüş alan, kapalılık oranı veya kabul eşiği değil. M2 belirsiz kaldı.
Dağlık/yükseltili olması ağaçlık bulunmadığı anlamında kodlanmadı.
Yaklaşık sınırlar aynı tarama içindeki 3×3 komşu merkezlerden hesaplandı;
resmî piksel köşeleri veya pikselin yanan alt bölümü bilinmiyor.

İlk beşi 2 km çemberinde kesip bağlantı grubu gibi sunmamak için, kayıtlı
aday kataloğun aynı NOAA-20 dakikasındaki **40 AOI kaydı** birlikte
incelendi. 1 km ayarında bu beşin bağlı olduğu iki grafik grubu 14 ve
bir üyeli; toplam 15 merkez iki hücreye taşıyor. İkinci hücredeki kayıtlar
atılmadı. Bütün 15 merkez aynı önbellek çiftinde tek eşleşti; tarama 156,
23:22:38,865–23:22:39,429 UTC. Üç kayıtta M13 giriş uyarısı var, geolocation
ve artık bowtie uyarısı yok. Giriş alt yedi biti temiz 12/15; bu kesim
uygulanmadı. Grafik, ayrı bütün ikili uzaklık/kapanış hesabıyla kontrol edildi.
Proje AOI'si dışındaki kayıtların kapsandığı iddia edilmedi.

Mesafe ayarı 500 m iken beş tekil bağlantı grubu, 1 km iken 14+1,
2 km iken 39 üyeli bir grup seçiliyor. Bu sayılar bağımsız gerçek yangın
sayısı değil. 2 km ayarındaki diğer 24 kaydın ham incelemesi yapılmış
sayılmadı. Ayara göre ilk hücre listesine üçüncü bir hücre de giriyor.

CGLS 2017'de beş alanın orman/çalı **harita sınıfı payı** %100; CORINE
2018'de M1 çayırlık, M2/M3/M5 ağırlıkla seyrek bitki, M4 çayırlık ve
sklerofil karışımı. Sınıf payları ağaçların gerçek alan yüzdesi değil;
haritaların sınıf/tarih farkı doğruluk veya gerçek örtü değişimi sayılmadı.
15 CORINE kesişimi exactextract ile ayrıca kontrol edildi; en büyük
sınıf payı farkı `1,89e-9` altında.

16 ve 18 Haziran 2022 Sentinel-2 L2A görüntülerinden iki küçük bölgede
RGB/SCL kesitleri okundu. Tahmin kesimi 21 Haziran 00:00 UTC; görüntüler
bundan önce. 19 uygun metadata kaydındaki aynı gün işlenmiş kopyalar
ayrı gözlem sayılmadı. Kaynak değişmezliği ve yerel raster geri okuması
kontrol edildi. Beş alan × iki tarihte SCL sınıfları yalnız 4/5; bulut,
gölge, kar, su, kusurlu/eksik ve sınıflandırılamayan sınıf sayıları sıfır.
Bu sayımlar bağımsız olarak yeniden hesaplandı. SCL bitki sınıfı orman
etiketi, bitkisiz sınıfı kesin orman yokluğu sayılmadı. Ürün üretim zamanı
kesimden önce olsa bile tarihsel erişilebilirlik doğrulanmış sayılmadı.
Araştırmacı bu görüntüleri görerek yukarıdaki beş ön notu verdi.

**Zaman devamı:** 1–23 Haziran 2022'nin 614 kayıtlı AOI adayında,
500/1.000/2.000 m × 24/48/72 saat olmak üzere dokuz ayar incelendi.
İlk yerel dakika ve hedef pencere sonu için toplam 18 geçmiş karşılaştırması
yapıldı. Beş ana kaydın ilgili ataları bütün ayarlarda 21 Haziran
23:22 UTC'de doğuyor; bu sınırlı katalogda tahmin anından önceye bağlanan
ata yok. Sonraki veriler bu geçmişi değiştirmedi. Bu bulgu gerçek tutuşma
zamanı, eksiksiz gözlem veya 1 Haziran öncesi sansür çözümü değil.

## Marmaris için somut üyelik seçeneği

Son tablo üç hücreyi de koruyor. `C541_R878` dokuz ayarda kaynakla ilişkili
ilk hücreler arasında; `C542_R878` altı, `C542_R877` üç ayarda. Bunlar
aynı veride bağımlı duyarlılık hesapları, dokuz bağımsız kanıt değil.
İki harita uyumunda sembol alanı yalnız C541/R878'e değiyor; sembol merkezi
AOI dışında kalmaya devam ediyor. Noktayı en yakın hücreye taşıma yapılmadı.

- **A yönü:** yalnız C541/R878, 21 Haziran hücre-günü için hata içerebilen
  L üyeliği önerisi hazırlamak; diğer iki hücreyi atamasız korumak.
  Bu, kesin nokta yerine yayımlanmış sembol alanına dayanan tek-vaka
  hazırlık kararı olur; yeni genel kural veya Y=1 kabulü olmaz.
- **B yönü:** daha açık başlangıç geometrisi bulunana kadar üç hücreyi
  de L'ye atamadan korumak. Daha temkinli, fakat kaynaklı L örneklemi genişlemez.

Araştırmacının Salur kararı Marmaris'e otomatik aktarılmadı. Her iki seçenek
için mevcut üyelikler ve hedefler atamasız. A yönü için gerekçeli öneri,
üç/dört kaynak uyuşmazlığını ve sembol konum belirsizliğini kapatmak değil;
onları koruyarak ikinci vaka üzerinde hata içerebilen L hazırlığını sınamak.
İki vaka da oran/karışım tahmini veya dört ilde değerlendirme için yeterlilik
kanıtı değil. Birinci aşamanın bilimsel kabulü açık.

Yeni çıktılar ve SHA-256:

- Ham kontrol: `outputs/reports/dataset/marmaris_native_support_v1/20261119T130257Z_bf16c6bd/readback.json`;
  `09baaccbd41d5e8a175b2bd988d46acf25c782fd5ac0b20ab21679bea6024ff4`.
- İki tarih: `outputs/reports/dataset/marmaris_cover_review_v1/20261119T130607Z_f0819694/readback.json`;
  `6bd38dabb3f24a6774a3a1a7586050eeae26f62c814aa8c7603d063340b38a61`.
- İnsan notu: `outputs/reports/dataset/marmaris_researcher_cover_v1/20261119T131258Z_0c3894ed/readback.json`;
  `ea5b8a0dffe0660ad140031e76d34a7890d88d4426f8dbbb28bb58ca1c07ed61`.
  Açık kayıt: `configs/marmaris_cover_notes_v1.json`.
- Zaman: `outputs/reports/dataset/marmaris_temporal_context_v1/20261119T131219Z_97f55f00/readback.json`;
  `e8e0086ffb0caa73fcceb362e5a33bdb061978c4b33be566c99316f5d8264be0`.
- Seçenek tablosu/şema: `outputs/reports/dataset/marmaris_L_direction_v1/20261119T131723Z_8bba0c84/readback.json`;
  `c6b5206886af35fa34f7cc195fb662904ea20196e30c1dc1c89c82fd3e3021e4`.

Bu devamda **114 ilgili davranış testi** geçti; ham/alan/katalog ve 18
zaman karşılaştırması ayrıca çalıştırıldı. Yeni komutlar Ruff/biçim
kontrolünü geçti. Seçenek tablosunun ilk geri okumasında Windows varsayılan
metin kodlaması Türkçe notları eşleştiremedi; açık UTF-8 ile yeni sürüm
üretildi, girdiler ve eski çıktılar korundu. Bu hata etikete dönüşmedi.

Yeni komutlar: `audit_marmaris_native_support.py`,
`prepare_marmaris_cover_review.py`, `review_marmaris_temporal_context.py`
ve `prepare_marmaris_L_direction.py` (`scripts/quality/` altında).
Son kapanışta beş vaka raporu, güncel kod/girdi/çıktı hash'leri, beş insan
ön notu, 18 zaman karşılaştırması ve üç atamasız hücre seçeneği geri okundu:
`outputs/reports/dataset/marmaris_case_review_closure_v1/20261119T132001Z_521890ee/readback.json`.
SHA-256 `c4c28c7a42d4f427869c6981ac8a5ba5ce804e2c718a9bdadbbbca8ecfdae287`.
