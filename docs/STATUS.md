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
- Meteoroloji hazırlama hattını kurduk. 2018 ve 2019 yıllarının toplam 730 günü ve
  2.116.270 hücre-gün kaydı doğrulandı. Sonraki oturumda 2020’den devam edeceğiz.

## Şu anki aşama

Veri toplama ve kalite kontrolündeyiz. Nihai yangın olay kataloğu, günlük yangın
etiketleri ve eğitim tablosu henüz hazır değil; model eğitimine başlamadık.
NASA'nın FIRMS tür alanına ilişkin açıklaması açık konu. İlk e-postanın teslim
sorunu vardı; alternatif adrese yeniden gönderildiği bu sohbette doğrulanmadı.

## Bundan sonra

1. Meteorolojiyi kalan 2020–2023 eğitim ve 2024 doğrulama dönemi için
   tamamlayıp denetleyeceğiz. Eksik/kısmi kapsam ve küçük negatif yağış değerleri
   için açık, test edilebilir kurallar belirleyeceğiz.
2. Yangın tespitlerini olaylara dönüştürüp günlük etiketleri hazırlayacağız.
   Gözlem eksikken “yangın tespit edilmedi” kaydını otomatik negatif saymayacağız.
3. Geçmişe uygun bitki örtüsü, yükseklik ve eğim özelliklerini ekleyeceğiz.
   Veri kaynaklarının gözlem ve yayımlanma zamanlarını kontrol edeceğiz.
4. Veri setini sürümleyip zaman/mekân ayrımlarını ve bilgi sızıntısını test edeceğiz.
   Önce basit modelleri karşılaştıracak, olasılıkları kalibre edeceğiz.
5. Model kararları sabitlendikten sonra 2025 final testini açacak; sonuçları
   API, harita ve bitirme raporuyla sunacağız. Daha karmaşık modeller katkısı
   gösterilirse eklenecek.

## Bugünkü denetimin sonucu

Mevcut coğrafya, FIRMS kaynak eşleşmeleri, gruplama kayıt bütünlüğü, örtü oranları,
MODIS çalışma kopyaları ve 2018–2019 meteoroloji hesapları kontrolleri geçti.
35 otomatik test, kod biçimi ve bağımlılık kontrolleri başarılı. Meteorolojide
yanlış tarih/sürüm/özellik sırası taşıyan dosyaların kabul edilmesini önleyen
ek kontrol eklendi. Ayrıntılı kapsam: [kalite incelemesi](QUALITY_REVIEW_2026-10-02.md).

Her iki yılda da günlük 189 hücrede veri eksik; sıcaklık kapsamı 310 hücrede
kısmi. Çok küçük negatif yağış değerleri korunup raporlandı. 2019’da 24 saat
toplamlarında 10.221, 72 saat toplamlarında 909 negatif kayıt var.
Mevcut kontrollerin geçmesi, henüz tamamlanmamış veri setinin kusursuz olduğu
anlamına gelmez. Açık kalite konuları çözülmeden eğitim verisini kesinleştirmeyeceğiz.

3 Ekim kapanışı: kontroller tamamlandı; kullanıcı talimatıyla GitHub push
yapılıp bugünlük mola verilecek. Sonraki meteoroloji dönemi 2020.
