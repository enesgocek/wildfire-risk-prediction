# WF1538 gündüz ham adayı ve olay öncesi örtü — 19 Kasım 2026

Araştırmacının indirdiği NOAA-20 `2022147.1030` çifti yerelde doğrulandı.
İndirme 186.934.166 bayt, 6.432×6.400 boyut ve N20:23461 yörüngesiyle
tamamlandı. Bu, katalog sonucuna göre seçilmiş takip incelemesidir;
sonuçtan bağımsız ilk sekiz geçişin yerine konmadı. Dondurulmuş 10 kaynak
satırı ve önceki sekiz sonuç korundu.
[İlk-geçiş örnekleminin sonucu](SOURCE_SAMPLE_NATIVE_2026-11-19.md).

## Kaynak noktası ile uydu merkezi aynı şey değil

| Kontrol | Ölçülen bulgu | Anlam sınırı |
|---|---|---|
| Katalog kimliği | `N20_815590_170090`, tek ham eşleşme | Bağımsız yangın kimliği değil |
| Ham konum | Satır 807, sütun 4012; tarama 25 | Aynı taramadaki 3×3 komşuluk kontrol edildi |
| Katalog/sparse/ham maske | Nominal güven `n` / 8 / 8 uyumlu | Gerçek pozitif veya orman yangını doğrulaması değil |
| Gerçek tarama | 27 Mayıs 2022, 10:30:46,367 UTC başlangıcı | 10:30 katalog dakikasıyla uyumlu; tutuşma zamanı değil |
| Kalite | QA 64768, alt yedi giriş biti 0; jeokonum bit 5, M13 bit 6 ve artık bowtie bit 22 kapalı | Yangın testi bitleri giriş hatası sayılmadı; kalite gerçek yangını kanıtlamıyor |
| Yaklaşık piksel alanı | 185.881,98 m², yaklaşık 0,186 km² | Resmî köşe veya yanmış alan değil |
| Kaynak–ham merkez | 367,09 m projeksiyon uzaklığı | Katalogdaki yuvarlanmış merkezle önceki 367,60 m ölçümünden farklı |
| Kaynak noktasının piksele ilişkisi | Yaklaşık yangın alanının dışında, sınıra 126,00 m | Konum hata yarıçapı bilinmiyor; aynı olay veya farklı olay kararı çıkarılmadı |

Kaynak noktasının tam ham konumu ayrıca 201 taramanın tamamında arandı:
aynı tarama 25 içinde noktayı kapsayan destek **maske 5, nominal kara**.
En yakın merkez satır 808/sütun 4012; hemen komşu satırdaki aday maske 8.
250 m çevrenin yaklaşık %12,93'ü, 1 km çevrenin %5,93'ü bu geçişte
yangın maskesi alanıyla kesişiyor. Bunlar yaklaşık alan payları;
yanmış alan yüzdesi, hata oranı veya noktanın yandığının kanıtı değil.

Kaynağın UTC yorumu 12:47, Türkiye yorumu 09:47 UTC. Ham tarama
birinciden yaklaşık **136,23 dakika önce**, ikinciden **43,77 dakika sonra**.
Saat standardı uyuma bakılarak seçilmedi. Kaynak koordinatının başlangıç,
yayılma veya başka bir konum rolü olduğu henüz doğrulanmadı.

## Eski haritalar ve gerçek görüntü ayrı tutuldu

Yaklaşık yangın pikselinde CGLS 2017 eşlemesi orman/çalı alanı veriyor.
CORINE 2018'de yaklaşık %68,39 ibreli orman (312), %31,60 geçiş
orman/çalılık (324), %0,0125 karma tarım (242) alanı var. CORINE
kesişimleri ayrı `exactextract` sınıf paylarıyla doğrulandı. Bu, eski
harita sınıflarının karşılaştırması; 2022 örtüsü veya bitkinin yandığı
alan değil. Asgari oran eşiğiyle örnek silinmedi.

Açık Sentinel-2 kataloğundan T=27 Mayıs 2022 00:00 UTC öncesindeki
30 gün tarandı; iki ayrı edinim tarihi **23 Mayıs ve 18 Mayıs 2022**.
RGB/SCL'nin küçük yerel kesitleri alınarak kaynak ETag/boyut bilgisi,
yerel dönüşüm, maske, hash ve kayıpsız geri okuma kontrol edildi.
Geçici erişim bilgileri kaydedilmedi. Bu geriye dönük görüntülerin
tahmin anında aynı ürün sürümüyle erişilebilir olduğu doğrulanmadı;
burada eğitim girdisi yapılmadı.

- **18 Mayıs:** mor yaklaşık piksel alanındaki 465 SCL merkezi içinde
  bulut/gölge/nodata sınıfı yok; bitki sınıfı 142, bitkisiz sınıf 323.
- **23 Mayıs:** aynı alanda 465 merkez; 75 bulut gölgesi, 108 bitki,
  282 bitkisiz sınıf. Bulut gölgesi payı %16,13; bulut/sirüs 0.
- Bitki SCL sınıfı orman sınıfı değildir; bu sayımlar doğal orman,
  ağaçlandırma veya tarım ayrımını çözmedi.

Görsel `outputs/reports/dataset/wf1538_cover_review_v1/20261119T181659Z_55e092be/wf1538_cover_review.png`.
Sarı A yayımlanmış kaynak noktası/250 m çevresi, mor B yaklaşık yangın
pikseli. Asistanın ön notu: A'da düzenli çizgiler/parsel benzeri doku;
B'de açık zemin ve yeşil örtü karışımı. Doğal orman–ağaçlandırma–tarım
ayrımı belirsiz. Bu otomatik/AI ön not, araştırmacının insan incelemesi değil.
**A/B örtü ön yorumu araştırmacıya soruldu; yanıt henüz kayıtlı değil.**

## Katalog geçmişi

1–29 Mayıs 2022'nin kayıtlı proje AOI'sindeki 75 aday, önce yerel
yarıçapla kırpılmadan incelendi. 500/1.000/2.000 m ve 24/48/72 saatlik
dokuz gruplama tanısında adayın katalog başlangıç geçmişi 27 Mayıs
10:30 UTC, C642/R876 olarak kaldı. T öncesi katalog atası bulunmadı;
sonraki kayıtlar önceki başlangıçları değiştirmedi. Bunlar dokuz farklı
yangın değil; aynı adayın yöntem duyarlılık kontrolleri. AOI dışındaki
bağlantılar ve daha eski/eksik gözlemler çözülmedi. Gerçek yeni tutuşma
veya günlük gözlem eksiksizliği çıkarılmadı.

## Kabul durumu ve kontroller

Yeni L/etiket, eğitim ve nihai birleştirme yok. Gözlem `unknown`,
pozitif/negatif izinler kapalı; iki olası L önerisi ve 2.048 U korundu.
Kaynakla aynı fiziksel olay olduğuna dair kanıt, saat/konum anlamı,
örtü ve PU varsayımları açık. İnsan örtü notu bunların hepsini çözmez.

Bu devamda **11 yeni davranış testi dahil 111 ilgili test** geçti.
QA yangın-testi bitlerinin jeokonum hatası sayılmaması, alan payının
doğru paydayla çevrilmesi, yaklaşık geometri/örtü, görüntü zamanı,
etiket kapıları ve olay geçmişi sınandı. Eski Affine işlem biçimi için
10 deprecation uyarısı çıktı; bu çalışmada hash-bağlı ortak kod değiştirilmedi.

İlk alan geri okuma koruması `frac` sonucunun tek raster hücresinin
alanıyla çarpılmasını reddetti; doğru payda poligon alanı olarak
düzeltildi ve küçük bilinen geometriyle test edildi. İlk geçici QA
çıktısındaki kaydırılmış `geolocation_low7` alanı kaldırılıp kılavuz/
ortak inceleyicideki bit 5 anlamıyla yeni sonuç üretildi. Eski geçici
dosya korunuyor; düzeltilmiş sonuç onun hash'ini açıkça üstleniyor.
Geçici QA alanı etiket veya aday reddinde kullanılmadı.

| Yeni sonuç | Yerel readback | SHA-256 |
|---|---|---|
| Kaynak noktasının gündüz tanısı | `outputs/reports/dataset/source_sample_point_v1/20261119T180958Z_50a96e58/readback.json` | `1e215960e548f0eca5b5fa4593c4c6dcaf675269a990bfa8f8186f3dfedc6d55` |
| Düzeltilmiş aday/ham alan | `outputs/reports/dataset/wf1538_native_support_v1/20261119T181411Z_926a75aa/readback.json` | `412c2a3209ea52b67c79f0460eefa31a3ade7c67fbad25ef8c3b5e22b198003a` |
| İki tarihli örtü incelemesi | `outputs/reports/dataset/wf1538_cover_review_v1/20261119T181659Z_55e092be/readback.json` | `55ac06f4bb6e749a6dffae96c4d92c402b11449937481feba1647a26669146c1` |
| Katalog zaman geçmişi | `outputs/reports/dataset/wf1538_temporal_context_v1/20261119T181852Z_4b9b09f1/readback.json` | `0998fc93977f1f35d01e69d8a28fddbf6ca26420d30573aac1ab56d38ec35e11` |

Sıradaki insan işlemi yeni indirme değil, A/B örtüsüne ön yorum.
Sonrasında bu not, kaynak anlamı ve geometrik ayrımla birlikte
değerlendirilecek; L üyelik yönü otomatik kararlaştırılmayacak.
