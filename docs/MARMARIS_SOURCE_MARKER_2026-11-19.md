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
