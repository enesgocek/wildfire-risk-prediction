# Kısa proje durum raporu — 6 Ekim 2026

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

5 Ekim'de kullanıcı ayrıntılı yangın çıkış nedeni zenginleştirmesini erteleyip
mevcut hedefle devam etmeyi seçti. Bilinmeyen neden doğal yangın sayılmayacak;
neden eksikliği raporun sınırlaması olarak tutulacak. Veri hazırlama hedefi aynı.
Yaz kontrolü envanteri hazır: Colab için 0,35 / 1,10 / 4,02 GB alternatifler;
Kullanıcı tek eğitim günü ve iki sensör/gündüz-gece içeren 1,10 GB B seçeneğini
seçti ve Colab işi tamamlandı. Altı çift / 17.394 hücre-çift satırı yerel
sonuç denetiminden geçti. 1,10 GB ham kaynak Colab'a, 21,34 MB sonuç yerel
bilgisayara geldi. FIRMS n/h kayıtları doğal sınıflarla güven/hücre bazında
tam eşleşti; 46 termal tespit bağımsız yangın sayısı değil. Günlük geometrik
birleşim ve küçük sonuç formatı bağımsız kontrolden geçti. Kullanıcı Temmuz
2023 aylık grubunu seçti ve tamamladı: 264 yeni çift ve hazır altı çift,
31 gün, 89.869 hücre-gün kaydı yerel tablo/kaynak/zaman denetiminden geçti.
48,30 GB yeni çift kaynak boyutu Colab kapsamı; gelen küçük ZIP 16,89 MB.
25 günde bulut sınıfı merkezi de görüldü. NOAA-20'nin 19–22 Temmuz 2023
günlerindeki 10 geçişte, doğal ürünün 61 termal kaydı FIRMS arşivinde yok;
NASA'nın resmî eksik veri tablosu aynı dört günü listeliyor. Arşiv boşluğu
kalite bulgusu olarak tutuldu, kaynaklara kayıt eklenmedi. Günlük durum
unknown/negatif izin false; nihai yangın etiketi henüz üretilmedi.
[Aylık sonuç ve arşiv boşluğu](COLAB_MONTH_RESULTS_2023_07.md).
[Aylık işin çalıştırılması ve sınırlar](COLAB_MONTH_2023_07.md).
Kullanıcı mevcut Google Cloud deneme kredisini paralel CPU işlerine ayırmayı
önerdi. 6 Ekim ekranında 13.650 TL kalan kredi, 26 Ekim bitişi ve Free trial
account görünüyor. Kullanıcı hesabı yeniden açtı; yeni Overview ekranında
Free trial ve kredi korundu, kapalı uyarısı yok. Terminalde global CPU limiti
32, us-central1 E2 limiti 24 vCPU ve her iki kullanım 0 doğrulandı. Kullanıcı
Compute Engine API'sini etkinleştirdi. VM/disk envanteri terminal ve web
ekranlarında boş doğrulandı. Sıradaki kontrol makine yapılandırması ve fiyat;
önerilen 8 vCPU denemesi kota içinde, henüz başlatılmadı.
Bulut kaynağı, harcama veya ücretli hesap
yükseltme başlatılmadı. Kullanıcı cebinden ödeme çıkmamasını kesin sınır
olarak belirtti; ücretli yükseltme/kredi dışı kullanım yapılmayacak.
[Krediyle hızlandırma seçenekleri](CLOUD_CREDIT_OPTIONS_2026-10-05.md).
[GCP ayarları ve gün sonu kontrolü](GCP_CPU_PREFLIGHT.md): kullanıcı Frankfurt
europe-west3, e2-standard-8 ve Standard modelini seçti; formda 2 saat/Stop
doğrulandı. Son fiyat tahmini mevcut 10 GB diskle yaklaşık 0,35 USD/saat.
Ubuntu 24.04 / 30 GB disk, otomatik restart Off, snapshot/Ops Agent ve
Frankfurt kotası henüz doğrulanmadı. GCP işçisi ve kalıcı çıktı aktarımı
hazırlanacak. Kullanıcı oluşturmayı sabah oturumuna bıraktı; gece işi veya
zamanlayıcı kurulmadı, VM oluşturulmadı.
[Gerçek sonuç ve seçenekler](COLAB_SUMMER_RESULTS_2026-10-05.md).
[Yeni notebook ve otomatik kayıt](COLAB_SUMMER_CONTROL.md).
[Seçenekler, açık eşleşmeler ve sonraki iş](SUMMER_CONTROL_OPTIONS_2026-10-05.md).

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

## Son kapanış denetimi — 6 Ekim

345 test yeniden geçti; Ruff kod kontrolü ve 118 Python dosyasının biçimi
başarılı. Ortamın 119 paketi uyumlu. Temmuz 2023 gelen ZIP'i güncel
doğrulayıcıyla yeniden okundu: 31/31 gün, kaynak/kod kimlikleri ve kompakt
sayısal/zaman kontrolleri başarılı, ZIP SHA değişmedi. Ham kaynaklar yeniden
işlenmedi; uzak Drive veya tam geometri yeniden hesaplaması iddia edilmedi.
Git aday dosyalarında tanımlı kimlik bilgisi örüntüsü veya büyük/ham artefakt
bulunmadı; yerel doküman bağlantıları ve Git fark biçimi kontrol edildi.

## Önceki kontrol kayıtları

Mevcut coğrafya, FIRMS kaynak eşleşmeleri, gruplama kayıt bütünlüğü, örtü oranları,
MODIS çalışma kopyaları ve 2018–2024 meteoroloji hesapları kontrolleri geçti.
Yaz paketi hazırlığı aşamasındaki tam kümede 308 test ve kod/biçim kontrolleri başarılı. Önceki ortam/kilit incelemesi de
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

Devam oturumunda dört ürünün tam eğitim metadata'sı denetlendi: 37.705 kayıt,
18.711 nominal çift ve 283 eşsiz kayıt. Katalog boyutları toplamı yaklaşık
3,17 TiB / 3,49 TB; nihai eğitim tablosunun boyutu değildir. Yeni ham dosya
indirilmedi. Metadata/çıktı özetleri, sayımlar ve hacim geri okuma kontrolünden
geçti; 20 yeni katalog testiyle toplam 168 test başarılı.

Kullanıcının ek disk sınırı 27 GB; en az 40 GB boş alan korunacak. Kapsam,
yöntem ve maliyet kararlarından önce seçenek sunulacak. Dört koleksiyonda
Harmony kırpma desteği bulunmadı; girişli OPeNDAP testi açık. Bulut ve partili
yerel işleme seçenekleri [karar belgesinde](L2_STORAGE_OPTIONS_2026-10-04.md).
Kullanıcı henüz yol seçmedi; büyük indirme veya bulut işi başlatılmadı.

Platform karşılaştırması sonrası ücretsiz Colab için tek geçiş pilot paketi
hazırlandı. Yerel paket denemesi özgün sayımlar ve bütün grid CSV'siyle tam
eşleşti; 7 ek testle toplam 175 test başarılı. Hesap girişli Colab denemesi
henüz yapılmadı; tam dönem platform/maliyet kararı pilot sonrasına bırakılıyor.
[Çalıştırma ve sınırlamalar](COLAB_PILOT.md).

İlk Colab sistem kurulumu bağımlılık çakışması verdi. Pilot artık ayrı venv
ve alt süreçte çalışıyor; 47 Linux/Python 3.12 bağımlılığı sabitlendi. Kurulum
kontrolü ve güvenli alt süreç giriş testleri eklendi; toplam 182 test geçti.
Temiz Colab çalışma zamanı için yeni isolated dosyalar hazırlandı.
Sistem ortamının uyumluluğu bir model/veri doğruluğu kanıtı değildir.

4 Ekim'de kullanıcı isolated Colab pilotunun bütün hücrelerini çalıştırdı.
Gerçek sonuç ZIP'i bağımsız denetimden geçti: 2.899 hücrenin bütün sütunları,
tam QA raporu ve kaynak/kod özetleri yerel referansla eşleşti. Yaklaşık 195 MB
ham kaynak Colab'a, 24,5 KB sonuç yerel bilgisayara geldi. İndirme ve denetim
35,1 saniye; ortam kurulumu hariç. Python 3.12.13 ve raporlanan paketler doğru.
10 sonuç denetimi testi eklendi. Günlük gözlem unknown, negatif etiket izni
false; NASA Type teyidi ve fiziksel ayak izi yöntemi açık. Tam dönem indirme
başlatılmadı; sıradaki öneri iki sensörlü bir eğitim günüyle kapasite ve
kesintiden devam denemesi. [Sonuç ve sınırlamalar](COLAB_PILOT.md).
Güncel tam test kümesi 192 başarılı; kod, biçim ve Git fark kontrolleri geçti.

Kullanıcı onayıyla iki sensörlü 14 Ocak 2019 Colab denemesi hazırlandı: 8 geçiş,
16 dosya, toplam 1,46 GB; en büyük geçici çift 187,35 MB. Sırayla işleme,
doğrulanmış checkpoint/ZIP sonrası geçici kaynak temizliği ve kesinti sonrası
devam mekanizması eklendi. Yerel prova bütün referanslarla eşleşti; süreç
yeniden başlatması ve yeni oturum dizinine ZIP geri yüklemesi geçti. Proje
kaynakları korunuyor. 18 ek testle toplam 210 test başarılı. Gerçek Colab günü
ve Linux bellek/disk ölçümü henüz çalıştırılmadı; tam dönem kararı açık.
[Yeni deneme ve çalıştırma](COLAB_DAY_PILOT.md).

Gerçek iki sensörlü Colab günü de bağımsız denetimden geçti: 8 geçiş × 2.899
hücrenin bütün sütunları ve QA raporları tam eşleşti; bir checkpoint yeniden
kullanılıp kalan yedi geçiş işlendi. 1,46 GB kaynak için en yüksek örneklenen
disk artışı 188 MB, çocuk süreç RSS belleği 544 MB, yerel sonuç ZIP'i 198 KB.
Geçiş indirme/denetim süreleri toplamı 165,94 saniye; kurulum ve bütün checkpoint
işleri dahil değil. Ek satır/QA/transfer geri okuması ve 18 bulut günü testi
geçti. Günlük gözlem/etiket hâlâ açık. Sırada kalıcı küçük çıktı saklama ve
fiziksel gözlem alanı kontrolleri; tam dönem işi başlatılmadı.

5 Ekim'de kullanıcı Google Drive'a otomatik sonuç kaydını seçti. Küçük ZIP'i
içerik özetiyle ayrı sürüm olarak saklama, tamamlanma kaydı, geri okuma ve
depolama hata kapısı hazırlandı. Sekiz geçişli mevcut sonuçla yerel kayıt ve
geri yükleme provası geçti. Yeni notebook Drive'ı eşitleyip yeniden bağladıktan
sonra aynı sonucu tekrar denetleyecek; yeni NASA indirmesi yapmıyor. Gerçek
Drive denemesi henüz yapılmadı. Drive kotası ve tam dönem nihai çıktı boyutu
açık; fiziksel gözlem/etiket kuralları değiştirilmedi.
[Drive denemesi](COLAB_DRIVE_STORAGE.md).
16 ek koruyucu testle güncel toplam 226 test başarılı; kod/biçim, paket ve
notebook denetimleri geçti. Ardından 5 Ekim gerçek Drive sonucu da doğrulandı:
eşitleme ve yeniden bağlama sonrası sekiz geçişin bütün QA/CSV sonuçları
referansla eşleşti (23.192 hücre/geçiş satırı). Kanıt ZIP'i 187.959 bayt,
Drive'da saklanan önceki sonuç 197.607 bayt. İçerik/kod/manifest kimliği ve
tamamlanma kaydı geçti; yeni ham indirme veya ham arşiv yükleme yok.
Rapor: outputs/reports/observation_coverage/drive_storage_received_verification.json.
Uzun dönem kapasitesi ve alan/etiket yöntemi henüz onaylanmış sayılmıyor.

Mevcut eğitim günü geometrisinde sınır ofseti tanısı tamamlandı. Aynı AOI iç
karşılaştırma alanında ±25 koordinat metresi senaryoları yaklaşık kapsamı
%58,69–60,12 aralığına taşıyor; sıfır senaryosu %59,41. Bunlar fiziksel hata
payı değil. 2.899 hücre korundu; 22 hücrede iç karşılaştırma paydası kalmadığı
için oran boş. Global/komşuluk hesaplarının ofsetli sonuçlarındaki küçük
sayısal farklar ayrıca kaydedildi; üretim yöntemi/etiket eşiği seçilmedi.
[Denetim ve sonraki adım](AREA_BOUNDARY_SENSITIVITY_2026-10-05.md).
12 ek testle tam kümede 238 test başarılı. Sırada sabit analiz ızgarasının
çözünürlük ve başlangıç konumu hassasiyeti; ardından gözlem/etiket kuralı var.

Hesap ızgarası incelemesi de tamamlandı: mevcut eğitim gününün yaklaşık
poligonu 50/100/200 koordinat metresi ve dört başlangıçla karşılaştırıldı.
Modelin 5 km ızgarası aynı kaldı. Hücrelerin %95'inde başlangıç açıklığı
yaklaşık 0,203/0,580/1,639 yüzde puanı; küçük AOI parçaları daha hassas.
2.899 hücre ve 12 senaryonun tüm sütun/istatistik/kaynak özetleri bağımsız
geri okundu; altı seçilmiş kare-birleşim kontrolü geçti. 19 ek testle toplam
257 test başarılı. CSV yaklaşık 1,45 MB; yeni ham indirme yok. Bu inceleme
doğal VIIRS dizisi veya fiziksel ayak izi doğrulaması değil; üretim çözünürlüğü,
gözlem eşiği ve negatif etiket seçilmedi.
[Sonuç ve kapsam](AREA_GRID_SENSITIVITY_2026-10-05.md).
Sırada eğitim örneklerinde tarama kalitesi ve gözlem zaman boşlukları var.

Tarama kalite/zaman incelemesi tamamlandı: mevcut sekiz granule yedi
sensör/yörüngeye ait; S-NPP 10:18/10:24 bağımsız geçiş sayılmadı. 2.899
hücrenin 480'inde seçilen kayıtlarda uygun kara merkezi yok. Uygun merkez
bulunan hücrelerin en uzun zaman boşluğunun medyanı 22,746 saat. Bu tek kış
gününe ait merkez tanısı, fiziksel alan/eksiksiz günlük gözlem kanıtı değil.
Sekiz parçanın tüm eski sayım/saat/QA alanları ve 29.637 yeni hücre/tarama
satırı bağımsız geri okumadan geçti. 17 ek testle güncel toplam 274 başarılı;
Ruff kod/biçim geçti. Yeni ham indirme yok, üç CSV yaklaşık 7,93 MB.
Günlük gözlem unknown ve negatif izin false. Sırada eğitim döneminden yaz,
yangınlı ve farklı bulut koşullu küçük kontrol envanteri; eşik ve tam dönem
işi seçilmedi. [Sonuç ve sınırlamalar](OBSERVATION_TIMING_2026-10-05.md).

Yaz kontrol envanteri ve bağımsız geri okuması da tamamlandı. Eğitimden 24
tabakalı aday ve üç maliyet alternatifi hazırlandı; kullanıcı kapsamı henüz
seçmedi. NOAA-20'nin 679 erken eğitim tespitinin nominal katalog zamanlarıyla
eşleşmemesi açık sorun olarak kaydedildi; hiçbiri silinmedi/negatif sayılmadı.
Seçilen kontrol günleri bu farkın dışında. 14 ek testle tam kümede 288 test
geçti; Ruff kod/biçim başarılı. Yeni ham indirme ve push yok.
[Kapsam seçenekleri ve sonraki iş](SUMMER_CONTROL_OPTIONS_2026-10-05.md).

Kullanıcı B kapsamını seçti. Altı çiftin otomatik Colab/Drive kayıt ve yeni
oturumda devam paketi hazır. Metadata boyutu toplam 1,10 GB; paket 2,95 MB.
Yerel kış kaynaklarıyla doğal denetim/alan/tarama ve ayrı ZIP geri yükleme
provada geçti; ham kaynaklar değişmedi. Gerçek yaz Colab işi hâlâ bekliyor.
20 yeni koruyucu testle tam kümede 308 başarılı; Ruff kod/biçim ve paket
CRC/SHA/notebook denetimleri geçti. Yeni yerel ham indirme ve push yok.
[Notebook, otomatik gruplar ve sonraki adım](COLAB_SUMMER_CONTROL.md).
