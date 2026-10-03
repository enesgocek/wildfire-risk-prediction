# Kısa proje durum raporu — 4 Ekim 2026

## Amacımız

Antalya, Muğla, İzmir ve Mersin'de, geçmiş yangın tespitleri, hava koşulları,
bitki örtüsü ve arazi bilgilerini kullanarak sonraki 24 saat için yangın riski
üreten bir model ve risk haritası geliştirmek. Model kesin yangın tahmini
yapmayacak; hedefimiz ölçülmüş ve doğrulanmış bir risk olasılığı sunmak.

## Bugüne kadar yaptıklarımız

- Python ortamını, deney takibini ve Earth Engine erişimini kurduk.
- Dört ili 2.899 coğrafi hücreye ayırdık; sınırları ve alan hesaplarını doğruladık.
- NASA FIRMS'ın iki uydu arşivini aldık; 2018–2024 için 33.255 aday tespiti
  kaynak kayıtlarıyla eşleştirdik. Bu sayı bağımsız yangın sayısı değildir.
- Aynı yangının tekrarlarını birleştirmek için dokuz gruplama ayarını inceledik.
  Sanayi kaynaklarıyla karışabilecek altı örneği tarihsel görüntülerle araştırdık.
- 2017 arazi örtüsü oranlarını hesapladık; modelde kullanım kararı henüz verilmedi.
- Meteoroloji hazırlama hattını kurduk. 2018–2024 döneminin 2.557 günü ve
  7.412.743 hücre-gün kaydı doğrulandı. 13 hava özelliği hazır; 6.351.709 kayıt
  eğitim, 1.061.034 kayıt doğrulama döneminde. 2025 final testi kapalı tutuluyor.
- İlk meteoroloji kullanım kuralını hazırladık: tam alan ana deney, %90 alan ayrı
  duyarlılık deneyi. Küçük negatif yağış yeni sütunda işleniyor; ham veri korunuyor.
  Eğitim incelemesi ve tam dönem uygulaması tamamlandı; bütün günlük kaynak ve
  çıktı dosyaları bağımsız kapanış kontrolünden geçti. Hiçbir kayıt silinmedi.

## Şu anki aşama

Veri toplama ve kalite kontrolündeyiz. Nihai yangın olay kataloğu, günlük yangın
etiketleri ve eğitim tablosu henüz hazır değil; model eğitimine başlamadık.
NASA'nın FIRMS tür alanına ilişkin açıklaması açık konu. Kullanıcının paylaştığı
Earthdata otomatik alındı bildirimi, talebin destek kaydına ulaştığını doğruluyor:
**#115134**, 2 Ekim 2026. Teknik yanıt bekleniyor; teslim belirsizliği artık yok.

## Bundan sonra

1. FIRMS tür alanının üretim geçmişini ve olay gruplama kurallarını kesinleştirip
   yangın tespitlerini olaylara dönüştürerek günlük etiketleri hazırlayacağız.
   Gözlem eksikken “yangın tespit edilmedi” kaydını otomatik negatif saymayacağız.
2. Geçmişe uygun bitki örtüsü, yükseklik ve eğim özelliklerini ekleyeceğiz.
   Veri kaynaklarının gözlem ve yayımlanma zamanlarını kontrol edeceğiz.
3. Veri setini sürümleyip zaman/mekân ayrımlarını ve bilgi sızıntısını test edeceğiz.
   Önce basit modelleri karşılaştıracak, olasılıkları kalibre edeceğiz.
4. Model kararları sabitlendikten sonra 2025 final testini açacak; sonuçları
   API, harita ve bitirme raporuyla sunacağız. Daha karmaşık modeller katkısı
   gösterilirse eklenecek.

## Bugünkü denetimin sonucu

Mevcut coğrafya, FIRMS kaynak eşleşmeleri, gruplama kayıt bütünlüğü, örtü oranları,
MODIS çalışma kopyaları ve 2018–2024 meteoroloji hesapları kontrolleri geçti.
148 otomatik test ve kod kontrolleri başarılı. Önceki ortam/kilit incelemesi de
geçmişti. Yanlış tarih/sürüm/özellik sırası taşıyan dosyalar reddediliyor;
sıcaklık, rüzgâr ve toprak nemi tutarlılığı yıllık denetime eklendi.
Ayrıntılı kapsam: [kalite incelemesi](QUALITY_REVIEW_2026-10-02.md).

Tüm dönemde günlük 189 hücrede veri eksik; sıcaklık kapsamı 310 hücrede kısmi.
Toplam 483.273 kayıtta eksik hava özelliği var; 6.929.470 kayıtta 13 özellik
dolu. Bu sayılar ara meteoroloji tablosunundur; nihai model uygunluğu değildir.
Çok küçük negatif yağış değerleri korunup raporlandı: 24 saat toplamlarında
28.728, 72 saat toplamlarında 1.296 negatif hücre-gün kaydı var.
Mevcut kontrollerin geçmesi, henüz tamamlanmamış veri setinin kusursuz olduğu
anlamına gelmez. Açık kalite konuları çözülmeden eğitim verisini kesinleştirmeyeceğiz.

Kullanıcının devrettiği 2021–2024 toplu çalışma tamamlandı. Yıllık raporlar ve
tüm dönem özeti yerelde outputs/reports/quality altında; ham/ara veriler Git
kapsamı dışında. Sonraki işlemlerde yeniden kullanıcıyla manuel adımlarla
ilerleyeceğiz. Meteoroloji sütunları tam döneme uygulandı ve kontrol edildi.
Ana profil 5.258.400 eğitim, 878.400 doğrulama hücre-günü kapsıyor; %90 profil
5.403.006 eğitim ve 902.556 doğrulama kaydı kapsıyor. Ana profilde kapsam dışındaki
5.291 eğitim adayı tutuluyor; bu sınırlama model değerlendirmesinde açıklanacak.
Kapanış raporu outputs/reports/quality/model_weather_2018_2024_audit.json altında.
Sırada olay/etiket hazırlığı var. Nihai eğitim tablosu hâlâ hazırlanıyor.

İki sensörün eğitim dönemi [gözlem kapsamı ön incelemesi](FIRMS_OBSERVATION_COVERAGE.md)
tamamlandı: S-NPP 26, NOAA-20 12 Türkiye sıfır tespit günü; ikisinin de sıfır
olduğu gün 2019-01-14. NOAA-20 talep dışındaki ilk 90 gün sıfır sayılmadı.
Bu gün için L2 yangın maskesi ve geolocation metadata'sı bulundu. İndirilen
10:18 UTC çifti bütünlük, kaynak eşleşmesi ve 54 seyrek yangın koordinatı
kontrollerini geçti; pilot il poligonlarında piksel merkezi bulunmadı. Bu yüzden
bölgesel QA incelemesi için 10:24 UTC çifti indirildi ve denetlendi. Pilot içindeki
349.456 merkezden 286.357'si bulut, 18.226'sı nominal girdili kara; yangın sınıfı
yok. 2.868 hücrede merkez var, 443 hücrede en az bir nominal girdili kara merkezi
var; bunlar alan/gün kapsamı değil. 00:42 UTC gece geçişi de denetlendi: 109.727
nominal girdili kara ve 129.964 bulut merkezi, pilot yangın sınıfı sıfır. Gece ve
gündüz birleşiminde 2.182 hücrede en az bir nominal girdili kara merkezi var;
717 hücrede yok. 12:00 ve 22:42 UTC çiftleri de bütünlük/konum/QA denetimini
geçti; nominal girdili kara merkezleri sırasıyla 10.291/10.140 ve pilot yangın
sınıfı sıfır. Beş S-NPP örneğinin birleşiminde 2.327 hücrede en az bir nominal
girdili kara merkezi var, 572 hücrede yok. Bu, tam hücre/gün gözlemi değil.
NOAA-20'nin 09:30/11:12/23:30 UTC çiftleri indirildi; kimlik/boyut, resmî konum
MD5, gerçek geolocation girdisi ve piksel/QA denetimleri geçti. Üç örnekte
1.141 hücrede en az bir nominal girdili kara merkezi var; pilot yangın sınıfı
sıfır. Sekiz örneğin iki sensörlü birleşimi 2.419 hücre; 480 hücrede böyle bir
merkez yok. NOAA-20 ek 92 hücre sağlıyor; bu tam hücre/gün kapsamı değildir.
Genişletmeyle mevcut beş S-NPP CSV'si ve tüm sayımları değişmedi. Güvenilir
günlük gözlem paydası henüz yok.
Sıfır tespitler negatif etikete çevrilmedi.
13 Ocak 2019 01:00 UTC S-NPP kontrol çifti de indirildi ve denetlendi. 174
seyrek yangın kaydı doğal dizilerle eşleşti. Pilot içindeki üç nominal güvenli
yangın pikseli, aynı geçişin üç FIRMS kaydıyla konum/güven/hücre bakımından
eşleşiyor. Seçilen adayın konum farkı 0,406 m ve girdi/konum QA bayrakları
nominal; artık bowtie bayrağı yok. Diğer iki kayıttan birinde artık bowtie
bayrağı var; korunup raporlandı, yeni eleme kuralı seçilmedi. Tek geçişte
618 hücrede en az bir nominal kara merkezi var; bu günlük alan kapsamı değil.
Kalıcı kontrol betiği ve sekiz yeni test eklendi. NASA Type teyidi bekleniyor;
termal eşleşme doğrulanmış orman yangını etiketi sayılmıyor.

Dokuz örnekte [yaklaşık gözlem alanı yöntemi](OBSERVATION_AREA_METHOD.md) sınandı:
tarama sınırları ayrı, aynı alanın tekrar sayımı geometrik birleşimle önleniyor,
gerçek tarama zamanları kaydediliyor. Sekiz geçişin yaklaşık nominal yangınsız
kara birleşimi 36.011,819 km² (%59,30); bu tam gün gözlem veya negatif kriteri
değil. Merkezlerden çıkarılan geometri resmî ayak izi değildir. Üç kontrolün
scan boyutları arşiv değerlerinden yaklaşık %1–9 farklı; yöntem fiziksel doğruluk
onayı almış sayılmadı. Hesap doğruluğu ve fiziksel yöntem doğruluğu ayrı tutuluyor.
3 Ekim'de 22 yeni testle 123 test geçti. 4 Ekim'de geometri tanısı dokuz dosyadaki
1.176 termal tespite genişletildi: 1.145 yerel ölçüm, 31 ölçümsüz kenar kaydı.
Fiziksel boyut referansı hâlâ üç arşiv kaydı; yuvarlama farkları tek başına
açıklamıyor, düzeltme seçilmedi. Dört eğitim katalog sorgusunda 37.705 kayıt
bulundu; yerel örnek ortalamalarıyla hacim senaryosu 3,16 TiB. Gerçek ürün eşleri
ve eksikler ayrıca incelenecek. 25 ek testle güncel toplam 148 test başarılı.
Sırada dosya eşleme ve veri erişim/işleme planı var; gözlem kuralı ve etiketler
açık. [4 Ekim incelemesi](GEOMETRY_DIAGNOSIS_2026-10-04.md).
