# Kısa proje durum raporu — 3 Ekim 2026

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
NASA'nın FIRMS tür alanına ilişkin açıklaması açık konu. İlk e-postanın teslim
sorunu vardı; alternatif adrese yeniden gönderildiği bu sohbette doğrulanmadı.

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
61 otomatik test ve kod kontrolleri başarılı. Önceki ortam/kilit incelemesi de
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
