> Tarihsel kayıt: 9 Ekim 2026 belge düzenlemesinden önce birikmiş durum notları.
> Bazı aşamalar daha sonra tamamlanmıştır; güncel durum [STATUS.md](STATUS.md) içindedir.
> Dil düzenlemesi deney tarihlerini veya kanıt düzeyini değiştirmez.

# Kısa proje durum raporu — 9 Ekim 2026

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

Hızlandırılmış üretim Aralık 2023 içinde `ValueError` ile durdu;
uygulama VM için kapatma istedi. Paylaştığım Compute Engine çıktısına göre
8 Ekim 21:50:46–9 Ekim 00:20:16 Türkiye saati arasında 2 saat 29 dakika
çalışmış; Google'ın sekiz saatlik sınırı 9 Ekim 05:50:39 idi. Erken duruş
zaman sınırından kaynaklanmadı. VM günlüklerindeki iki durum dosyası aynı:
Temmuz–Kasım 2023 beş tam ay, Aralık 1–26 günlük kapanışları;
bu oturumda 648 yeni çift / 10 yeniden kullanılan çift var.
Yeni Ekim/Kasım/Aralık çıktıları henüz yerelde bağımsız geri okunmadı.
`failed_phase=pair_publication` son ana süreç aşaması; arka plan çocuk
hatasının kesin kaynağını belirtmeyebilir. Bilimsel kontrol/Drive/ağ
arasında kesin neden bu günlüklerden seçilemiyor. VM'nin
yeniden Stopped olduğunu teyit ettim. Kalan dosyalar salt okunur teşhis
arşiviyle alındı ve CRC/hash/Aralık kaynak metadata kontrolü geçti.
20 tam çift ZIP'i bağımsız native CSV/geometri/tarama/checkpoint
kontrollerinden geçti, 14 yarım görev kaldı. Tüm 68 ham dosyanın boyutu
beklendiği gibi; 3.862 örnekte RAM/disk rezerv ihlali yok.
Yerel ham dosya yeniden denemesi ve başlık raporu kesin eşleşme sorununu
gösterdi: 34 kalan çiftin 32'si başlık eşleşmesini geçti; 31 Aralık'taki
SNPP:2023365.0106 ve SNPP:2023365.1048 yangın dosyaları farklı geolocation
işleme sürümlerini istiyor. Raporun CRC/hash ve plan kimlikleri eşleşti.
İstenen eski dosya adları güncel CMR/LAADS kayıtlarında bulunamadı;
mevcut dosya için pozitif sorgu kontrolü geçti. Eşleşme kontrolü korunuyor.

31 Aralık'ı eksik bırakıp diğer aylara devam etmeyi onayladım.
Yeni bağımsız devam aracı Aralık 1–30'u tamamlayıp Haziran 2023'ten
başlayarak kalan 66 aya geçecek. Orijinal paket, bilimsel işçi, kaynak
CSV'leri ve checkpoint kimliği değişmedi. Aralık tam ay sayılmayacak;
full_training_complete=false kalacak. Güvenli çocuk hata kayıtları eklendi.
10 yeni devam testi ve mevcut kapatma/bütçe/paket/gate/ay doğrulamasından
8 seçili test geçti; Ruff geçti. Gerçek VM devam işi henüz başlatılmadı.
[Hazır dosyalar ve yeni başlatma adımları](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md).

9 Ekim'de NASA FIRMS ekibinden yaklaşık altı gün sonra incelemeye başlandığı yanıtının alındığı bildirildi. Bu, 815579/815590
teslimlerindeki Type sürümü sorusudur; teknik teyit hâlâ bekleniyor.
31 Aralık L2 kaynak eşleşmesi ayrı açık sorun olarak kalıyor.

Hata öncesinde doğrulanan hızlandırma deneyi:

Yeni 32 vCPU hızlandırma deneyi tamamlandı ve bağımsız geri okumadan geçti.
112 cold çift kaydı / 12 günlük ürün, kaynak/native CSV/CMR ve günlük
tablolar eşleşti. VM indirme sonrası manuel durum bildirimiyle Stopped.
İlk/son baz 637,308 / 643,416 sn; pipeline8 532,233 sn,
pipeline24/day4 436,957 sn. Baz tekrarı 1,00958, seçilen 24/4 ayarı
aynı makinedeki baz ortalamasına karşı 1,4655 kat throughput (%46,55 artış)
ve %31,76 kısa süre sağladı. 2–3 kat hedefi henüz kanıtlanmadı.
CPU ortalama %15,73/tepe %75,25; süreç RSS tepe 10,83 GiB,
en az 111,21 GiB kullanılabilir RAM / 18,82 GiB boş disk; rezervler korundu.
Seri yayın/doğrulama/bekleme aşamalarında kayda değer süre kaldı;
saf donanım büyütmesinin büyük kazancı gösterilmiş değil.
Hash bağlı production_readiness.json üretildi; yeni ZIP gerekmiyor.
Mevcut controller ile eski kayıtları kullanarak sekiz saatlik üretim
başlatıldı; erken hata teşhis edildi ve yukarıdaki devam aracı hazırlandı.
Deneyin kendisi yeni ay eklememişti.
[Sonuç raporu](GCP_ACCELERATION_RESULTS_2026-10-08.md),
[güncel üretim devam adımları](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md).

Daha güçlü VM ve yazılım iyileştirmesiyle 2–3 kat hız hedefini
onayladım. Son Free Trial ekranı 149 TL ay içi kullanım / aynı indirim /
net 0 TL; kalan kredi 13.484 TL / 18 gün. Doğru kota çıktısında global CPU
32, Frankfurt N2_CPU 200, kullanım 0: mevcut durmuş VM için N2/32 vCPU
adayı kota içine sığıyor. Ücretli hesaba geçiş veya bulut müdahalesi yapılmadı.

Yeni dış controller hazır: çiftler ve farklı günlerin günlük birleşimleri
örtüşüyor; sırayla çalışan ana bilimsel doğrulama ve taze Drive geri okuması
korunurken tekrarlanan aynı kontrol/listeler azaltılıyor. Üretim kapsamı,
donmuş bilimsel çocuk kodu ve eski checkpoint kimlikleri korunuyor.
26 ayrı yerel kontrol geçti; gerçek native ürünlerden ayrı günlük çocuk,
eski okuyucuyla yeni kayıt geri yükleme, tamamlanmış günün ham indirme
olmadan kullanılması ve 12 gerçek günlük üründen hazır-kaydı okuma provası
dahil. Eski Ağustos'un 31 günlük aylık arşivi yeni kontrolle kabul edildi;
bozuk nested worker kaydı reddedildi. Rehberdeki kurulum/overwrite ve paket
üye SHA değişimi reddi de geçti. Prova benchmark saatleri yapay; yeni VM hız kanıtı yok.
İlk adım N2/32 üzerinde iki saatlik 8 baz → pipeline8 → pipeline24 → tekrar8
deneyi. Tam ve istikrarlı karşılaştırma + bağımsız geri okuma sonrası hash
bağlı hazır-kaydıyla bütün kalan ayların 8 saatlik devam kuyruğuna geçilecek.
VM manuel durum bildirimiyle kapalı. [Yeni paket ve manuel adımlar](GCP_ACCELERATION_2026-10-08.md).

Gerçek paralellik deneyi tamamlandı; dört profil yaklaşık 47 dk 20 sn sürdü.
İndirilen ZIP bağımsız bilimsel kontrolden geçti: 112 cold çift kaydı,
12 günlük payload ve aynı kaynak/native CSV hash'leri tutarlı. VM indirme
sonrası Stopped manuel durum bildirimiyle doğrulanmış. 8 işçi 10 dk 44 sn ile aday; 4 işçi
ortalamasına karşı throughput %18,34 arttı, süre %15,49 kısaldı.
12 işçi 11 dk 11 sn ile 8'den %4,18 yavaş. RAM/disk rezerv ihlali yok.
Orijinal üretim paketi/ilerlemesi değişmedi; deney yeni ay eklemedi.
Bu sonuç yeni hızlandırma hazırlığının önceki gerçek baz kanıtıdır.
[Gerçek ölçüm ve sınırları](GCP_PARALLEL_TUNING_RESULTS_2026-10-08.md).

Mevcut VM'de iki saatlik 4/8/12/4 paralellik deneyi hazır. Üç tam günün aynı
28 çiftini donmuş bilimsel kodla yeniden işleyecek; ölçüm yayın/geri okuma ve
günlük union dahil. Toplam nominal ham indirme 20,56 GB; test yeni üretim
ayı eklemez. Ayrı test namespace'i, RAM/disk/süre rezervleri ve sonunda
poweroff var. Bu hazırlık kaydı deney öncesine ait; güncel ölçüm üstte.
8 Ekim konsol ekranında Free Trial, ay içi 80,11 TL kullanım / aynı
tutarda indirim / net 0 TL, kalan kredi 13.519 TL ve 18 gün görünüyor.
Ücretli yükseltme yok. Paket ve yerel gerçek ürün provası hazır;
sonuç doğrulanınca yeni üretim sürücüsü/continue uyumu ve 8 saatlik oturum
ayrıca ele alınacak. [Başlatma ve indirme rehberi](GCP_PARALLEL_TUNING_2026-10-08.md).

8 Ekim oturum sonu günlük arşivi yerelde katalogla karşılaştırıldı ve geçti:
durum paused_at_runtime_reserve, son queue exit 0, poweroff True; yeni
çalışmada hata yok. Ağustos ve Eylül tamamen kapanmış; Ekim 1–14 tamam.
Toplam 75 tam gün / 673 kaydedilen çift; 663 tam gün çiftine ek 15 Ekim'in
10/10 çifti kaydedilmiş, günlük birleşim hâlâ bekliyor. Kalan 69 ay / 17.768
işlenmemiş nominal çift. Günlükleri indirdikten sonra VM tekrar Stop yapıldı;
bu durum manuel bildirimle teyit edildi. Yeni üretim veya kapasite değişimi yapılmadı.
Bilimsel sonuç arşivinin bağımsız yerel geri okuması da geçti: 120 dosya,
3 metadata manifesti, 75 günlük tablo/zaman/kaynak kontrolleri, 2 aylık
receipt/nested SHA ve 15 Ekim'in 10 çiftinin checkpoint/geometrileri tutarlı.
Ham veri yeniden indirilmedi. 7 yeni arşiv/bozuk completion testi ve Ruff
geçti. Günlüklerin ve gerçek ürünlerin bağımsız kontrolleri ayrı raporlandı.
75 günün full union geometrileri yeniden hesaplanmadı; yeni Drive API
readback'i yapılmadı. Mevcut donmuş üretim paketi değiştirilmedi.
[İlk oturum denetimi ve sıradaki sonuç arşivi](GCP_FIRST_SESSION_RESULTS.md).
Cloud Shell describe ile TERMINATED durumunu doğruladım:
başlangıç 7 Ekim 23:55:37,862, duruş 8 Ekim 07:11:27,486 Türkiye saati.
Gerçek çalışma 7 saat 15 dakika 49,624 saniye; bildirilen Google son
zamanından yaklaşık 44 dakika önce. Günlükler normal rezerv duruşunu doğruladı.

8 Ekim yeni üretim çalışması SSH çıktısıyla doğrulandı:
oturum içindeki günlükte running; Ağustos'un 31 günü ve aylık küçük arşivi Drive'a
kaydedilip bağımsız geri okumadan geçti. existing_months artık 2023-07 ve
2023-08. Kuyruk otomatik Eylül'e geçti; 1–4 Eylül tamam, 5 Eylül'ün 10
çiftinden 2'si kaydedilmişti. Sonraki çıktı Eylül 1–11 tamam, 12 Eylül'ün
9 çiftinden 7'si kaydedilmiş; toplam 42 gün ve 382 çift, reused 0 gösterdi.
Bu 382 çift örneği oturum içi tarihsel kayıttır; yukarıdaki 673 çift son
oturum kapsamıdır.
İkinci günden itibaren dört işçi aktif.
Dört işçinin karşılaştırmalı hızlanması henüz ölçülmedi.
Yeni süreç örneğinde dört çocuk aynı ebeveyne bağlı ve yaklaşık 30 saniyedir
çalışıyor; toplam RSS yaklaşık 1,23 GiB. Bu çocukların ömür ortalamalı CPU
toplamı yaklaşık 1,89 çekirdek eşdeğeri; tüm VM'nin anlık kullanım ölçümü değil.
Önceki 153 çift örneğinde kuyruk/supervisor süresi 1:35:43:
ilk canlı oran yaklaşık 95,91 çift/saat,
Ağustos için doğrusal 2,90 saat senaryosu; aylık son işlem ve değişken veri
boyutları nedeniyle kesin bitiş zamanı verilmedi. İlk kaynak örneğinde
CPU/bellek/disk kapasitesi baskısı görülmedi; daha büyük VM kararı henüz yok.
Günlükteki eski RuntimeError yeni çalışmadan önceki başarısız denemeye ait.
Yeni progress son zamanı 2026-10-08T04:55:30.424102Z, Türkiye saatiyle
8 Ekim 07:55:30. Bu, bildirilen uygulama son zamanıdır; bu aşamada canlı
Console ayarı ayrıca araçla okunmadı. İlk tam gün doğrulaması geçti;
oturum sonunda ve iki kontrol indirmesinden sonra VM Stopped durumu manuel
bildirimle teyit edildi. Unknown/negative false politikası korunuyor.
[Canlı çalışma kaydı](../Diary/08-10-2026.md).

Önceki denemenin teşhisi:

7 Ekim ilk canlı üretim güncellemesi: 8 saat sınırı manuel olarak kaydedildi ve
VM başlatıldı. `Preparing verified metadata: 2023-08 sources: 556` çıktısı
alındı. Sonra SSH IAP 4003 bağlantı hatası görüldü. Cloud Shell describe
çıktısı VM'nin TERMINATED olduğunu, süre ayarının 28.800 saniye / STOP
olduğunu doğruladı. Başlangıç 7 Ekim 22:44:38, son duruş 22:52:32 Türkiye
saati: yaklaşık 7 dakika 54 saniye, sekiz saatlik sınıra ulaşılmadı.
Sonraki günlükler kuyruk hata çıkışı ve programın VM'yi kapatma isteğini
doğruladı. Üretim başarılı veya yalnızca SSH kopmuş sayılmıyor. Aşağıdaki
kapanış kaydı bu canlı denemeden önceki durumu anlatır.

Sonraki SSH teşhis görüntüsü `Production stopped: RuntimeError`,
`Queue invocation exit: 1`, `Guest poweroff requested: True` gösterdi.
İlerleme durumu failed_checkpoints_retained; bu oturumda işlenen ve yeniden
kullanılan çiftler 0, doğrulanmış gün listesi boş. Kuyruk hata çıkışından
sonra program VM'yi kapatmış; SSH hatası bu duruş sonrası görülmüş.
Alt hata metni güvenlik filtresinde genelleştirilmiş. VM'de 556
cache, 556 metadata, month.json ve manifest.zip bulunduğunu doğruladım.
Kod sırasına göre hata metadata hazırlığı sonrası Drive manifest kaydı
veya geri okuması sırasında oluşmuş; kesin Google hata nedeni bilinmiyor.
AI Pro planının birkaç saat önce bitip yeniden açıldığı bildirildi;
görselde 31,67 GB / 400 GB kullanım var. Geçici kota aşımı olası neden,
henüz doğrulanmadı. OAuth hesabının gerçek kotasını okuyup yalnızca hazır
metadata ZIP'ini doğrulayarak kaydedebilen ayrı teşhis aracı hazırlandı.
İlgili 121 test ve Ruff geçti. Kaydettiğim gerçek VM çıktısında 736.111
bayt metadata ZIP'i bilimsel kontrolden geçti, Drive'a kaydedilip bağımsız
geri okundu; MANIFEST_READY doğrulandı. Bağlı hesabın API kotasında 34,00 GB
kullanım / 429,50 GB sınır / 395,49 GB boş alan var (ondalık GB).
Önceki hatanın geçici kota aşımı olduğu kesinleşmedi; mevcut kayıt engeli yok.
Teşhis sırasında donmuş üretim paketi değişmedi, yeni ham indirme yapılmadı.
Sonraki uzun çalışma yukarıda bildirilen dört gerçek çift kaydıyla ilerliyor;
ilk gün veya bütün dönem tamamlanmış sayılmıyor.
[Sınırlı teşhis ve metadata kaydı](GCP_MANIFEST_DIAGNOSIS.md).

Küçük gün örneklemini ana plan olarak seçmedim; bütün eğitim
aylarıyla devam etmeyi planladım. 2018–2023'ün 72 ayından Temmuz 2023 hazır,
kalan 71 ay / 18.441 nominal çift otomatik GCP kuyruğunda. İlk ay Ağustos
2023. Gün/ay başına ayrı komut yerine Drive'a doğrulanmış kayıt ve aynı
paketle devam etme uygulanır. İlk uzun çalışma için 8 saat / Stop seçildi;
VM ayarı manuel olarak kaydedildi ve gerçek üretim başladı.
Free Trial ve TRY13,623 kredi manuel kontrol bildirimiyle teyit edildi; canlı
Billing araçla okunamadı, ücretli yükseltme yapılmadı.
[Üretim paketi ve sıralı başlatma](GCP_PRODUCTION_RUN.md).
Önceki 7/14/21 gün incelemesi yalnızca tarihsel alternatif olarak korunur;
model yeterliliği kanıtı değildir.

7 Ekim kapanışı: üretim hâlâ başlatılmadı. 8 saat ilk uzun çalışma için üst
sınırdır; toplam kuyruk bitiş garantisi değildir. Doğrulanmış çift/gün/ay
kayıtları sonraki oturumda atlanır; kesintide henüz kalıcı kaydı doğrulanmamış
son işler yeniden gerekebilir. Başlatıcı terminalden bağımsız çalışır; bildirim
göndermez. İlk kayıt ve oturum sonu VM durum kontrolü gerekir. Sonraki süre
gerçek üretim ölçümüyle seçilecek; otomatik VM Start ve ücretli Upgrade yok.
Sonuçlar bağımsız kopyayla doğrulandıktan sonra VM/disk ve diğer oluşturulmuş
kaynaklar kaldırılacak, proje billing bağlantısı devre dışı bırakılacak ve
ilgili Cloud Billing hesabı kapatılacak.
[İş sonu temizlik planı](GCP_FINAL_CLEANUP.md).
Yarın devam noktası: kapalı VM'de 8 saat / Stop / restart Off ayarını doğrulama,
Start sonrası yeni Google son zamanını alma, hazır üretim ZIP'ini uygulama
ve ilk gerçek kalıcı kaydı denetleme. Canlı kaynak durumu son manuel
bildirime dayanır; bu kapanışta yeni bulut işlemi yapılmadı.
7 Ekim kapanış denetimi: tam kümede 512 test başarılı; Ruff kod denetimi,
158 Python dosyası biçim kontrolü ve donmuş üretim paketi bütünlüğü geçti.

GCP → Drive kalıcılık kontrolünün V2 sonucu yerelde doğrulandı. İlk çalışmada
ZIP MIME etiketi kontrolü düzeltildi; V2 gerçek Drive'a kaydetme, tamamlanma
öncesi kesinti ve ayrı süreçte geri yükleme kontrolünü geçtiğini bildirdi.
Ürün 3,98 MB; 5+1 bilimsel geri okuma, farklı PID 1327/1336, hazırlanmış
paket/manifest/ürün SHA ve ZIP CRC eşleşti. Yeni ham veri/üretim ayı yok.
Yerelde remote payload tekrar indirilmedi; SSH kopması veya VM Stop/Start
sonrası resume sınanmadı. Sonuçtan sonra VM'yi Stop yaptığımı
bildirdim. Süre/disk/ödeme ayarı değişmedi. Uzun ay kuyruğu/günlük birleşim
GCP sarmalayıcısı hazırlandı; yerel kontroller gerçek yeni VM üretimini
başlamış veya kusursuzluğu kanıtlamış saydırmaz.
[Sonuç ve kapsam](GCP_DRIVE_PROOF_RESULTS.md),
[MIME düzeltmesi](GCP_DRIVE_MIME_REPAIR.md).

Veri toplama ve kalite kontrolündeyiz. Nihai yangın olay kataloğu, günlük yangın
etiketleri ve eğitim tablosu henüz hazır değil; model eğitimine başlamadık.
NASA'nın FIRMS tür alanına ilişkin açıklaması açık konu. Paylaştığım
Earthdata otomatik alındı bildirimi, talebin destek kaydına ulaştığını doğruluyor:
**#115134**, 2 Ekim 2026. Teknik yanıt bekleniyor; teslim belirsizliği artık yok.

5 Ekim'de ayrıntılı yangın çıkış nedeni zenginleştirmesi ertelenerek
mevcut hedefle devam edilmesi seçildi. Bilinmeyen neden doğal yangın sayılmayacak;
neden eksikliği raporun sınırlaması olarak tutulacak. Veri hazırlama hedefi aynı.
Yaz kontrolü envanteri hazır: Colab için 0,35 / 1,10 / 4,02 GB alternatifler;
Tek eğitim günü ve iki sensör/gündüz-gece içeren 1,10 GB B seçeneğini
seçtim ve Colab işi tamamlandı. Altı çift / 17.394 hücre-çift satırı yerel
sonuç denetiminden geçti. 1,10 GB ham kaynak Colab'a, 21,34 MB sonuç yerel
bilgisayara geldi. FIRMS n/h kayıtları doğal sınıflarla güven/hücre bazında
tam eşleşti; 46 termal tespit bağımsız yangın sayısı değil. Günlük geometrik
birleşim ve küçük sonuç formatı bağımsız kontrolden geçti. Temmuz
2023 aylık grubunu seçtim ve tamamladım: 264 yeni çift ve hazır altı çift,
31 gün, 89.869 hücre-gün kaydı yerel tablo/kaynak/zaman denetiminden geçti.
48,30 GB yeni çift kaynak boyutu Colab kapsamı; gelen küçük ZIP 16,89 MB.
25 günde bulut sınıfı merkezi de görüldü. NOAA-20'nin 19–22 Temmuz 2023
günlerindeki 10 geçişte, doğal ürünün 61 termal kaydı FIRMS arşivinde yok;
NASA'nın resmî eksik veri tablosu aynı dört günü listeliyor. Arşiv boşluğu
kalite bulgusu olarak tutuldu, kaynaklara kayıt eklenmedi. Günlük durum
unknown/negatif izin false; nihai yangın etiketi henüz üretilmedi.
[Aylık sonuç ve arşiv boşluğu](COLAB_MONTH_RESULTS_2023_07.md).
[Aylık işin çalıştırılması ve sınırlar](COLAB_MONTH_2023_07.md).
Mevcut Google Cloud deneme kredisini paralel CPU işlerine ayırmayı
planladım. 6 Ekim ekranında 13.650 TL kalan kredi, 26 Ekim bitişi ve Free trial
account görünüyor. Hesabı yeniden açtım; yeni Overview ekranında
Free trial ve kredi korundu, kapalı uyarısı yok. Terminalde global CPU limiti
32, us-central1 E2 limiti 24 vCPU ve her iki kullanım 0 doğrulandı.
Compute Engine API'sini manuel olarak etkinleştirdim. VM/disk envanteri terminal ve web
ekranlarında boş doğrulandı. Sıradaki kontrol makine yapılandırması ve fiyat;
önerilen 8 vCPU denemesi kota içinde, henüz başlatılmadı.
Bulut kaynağı, harcama veya ücretli hesap
yükseltme başlatılmadı. Kişisel ödeme yapılmamasını kesin sınır
olarak belirledim; ücretli yükseltme/kredi dışı kullanım yapılmayacak.
[Krediyle hızlandırma seçenekleri](CLOUD_CREDIT_OPTIONS_2026-10-05.md).
[GCP ayarları](GCP_CPU_PREFLIGHT.md): aynı gece devam edilerek
Frankfurt europe-west3-c / e2-standard-8 / Ubuntu 24.04 / 30 GB VM oluşturdum.
2 saat/Stop, restart Off, No backups ayarları Equivalent code ile doğrulandı;
oluşturma Google'ın kota/kaynak denetimini geçti. Yaklaşık 0,35 USD/saat
form tahmini toplam harcama tavanı değildir; Free trial/Upgrade yasağı sürüyor.
[Tek geçiş GCP sonucu](GCP_PORTABILITY_PILOT.md) bağımsız yerel kontrolden
geçti: 194,70 MB iki kaynak, QA ve 2.899 hücrenin bütün sütunları referansla
tam eşleşti. Son çalıştırmanın kurulum dahil süresi 134,84 saniye; VM'nin
önceki denemeleri/boş bekleme ve toplam faturalama süresi değil.
[Bir/iki işçi denemesi](GCP_PARALLEL_BENCHMARK.md) de tamamlandı ve 42,02 MB
sonuç bağımsız yerel kontrolden geçti. Aynı altı yaz geçişi 432,39 / 229,29
saniye: 1,886 kat hızlanma, %46,97 süre azalması. Kaynak/QA ve sayım/tarama
CSV'leri Colab referansıyla tam eşleşti. İki GCP kolunun alan sütunları ve
kaydedilmiş geometrileri de tam eşit. Colab'a göre çok küçük sayısal alan/
sınır farkları ölçülüp açık toleranslarla ayrı raporlandı; bit eşitliği veya
fiziksel ayak izi doğruluğu iddia edilmedi. Yeni yerel ham indirme veya üretim
ayı yok; bütün yıllara hız/bütçe oranı uygulanmadı. Dosyayı aldıktan
sonra VM'yi Stop yaptığımı bildirdim; uzaktan durum/fatura okunmadı, boot disk
silinmedi. Üretim kuyruğu ve VM dışı kalıcı kayıt sırada. Güncel tam test kümesi
386 başarılı; Ruff kod/128 Python dosyası biçimi geçti.

Uzun üretim için [süre/kayıt tasarımı](GCP_PRODUCTION_READINESS.md) incelendi:
benchmark üretim/resume kodu değildir, Colab ayı sabit dizinlere bağlıdır.
Yeni sağlayıcı bağımsız kayıt çekirdeği ve gerçek alınmış GCP ürünüyle yerel
kesinti/yeniden yükleme provası geçti; tamamlanma kaydı en son yayımlanıyor.
Altı bilimsel geri okuma, 21 yeni koruyucu test, toplam 407 test ve Ruff/132
dosya başarılı. VM dışı depo bağlantısı, gerçek restore, ayrılmış launcher ve
yeni üretim işçisi açık; kusursuzluk/tam dönem kapasite iddiası yok. İlk depo
kanıtında mevcut 2 saat sınırı korunacak; sonrasında 6/8 saat seçenekleri
ölçümle seçilecek. Ayar değişmedi, VM yeniden başlatılmadı. Drive/Cloud Storage
seçimi karara bağlanmak üzere kaydedildi; sağlayıcıya bağlı çalışma henüz uygulanmadı.
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

Otomatik akışla yürütülen 2021–2024 toplu çalışma tamamlandı. Yıllık raporlar ve
tüm dönem özeti yerelde outputs/reports/quality altında; ham/ara veriler Git
kapsamı dışında. Sonraki işlemlerde yeniden manuel adımlarla
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

Çalışmanın ek disk sınırı 27 GB; en az 40 GB boş alan korunacak. Kapsam,
yöntem ve maliyet kararlarından önce seçenek sunulacak. Dört koleksiyonda
Harmony kırpma desteği bulunmadı; girişli OPeNDAP testi açık. Bulut ve partili
yerel işleme seçenekleri [karar belgesinde](L2_STORAGE_OPTIONS_2026-10-04.md).
Yürütme yöntemi henüz seçilmedi; büyük indirme veya bulut işi başlatılmadı.

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

4 Ekim'de isolated Colab pilotunun bütün hücreleri çalıştırıldı.
Gerçek sonuç ZIP'i bağımsız denetimden geçti: 2.899 hücrenin bütün sütunları,
tam QA raporu ve kaynak/kod özetleri yerel referansla eşleşti. Yaklaşık 195 MB
ham kaynak Colab'a, 24,5 KB sonuç yerel bilgisayara geldi. İndirme ve denetim
35,1 saniye; ortam kurulumu hariç. Python 3.12.13 ve raporlanan paketler doğru.
10 sonuç denetimi testi eklendi. Günlük gözlem unknown, negatif etiket izni
false; NASA Type teyidi ve fiziksel ayak izi yöntemi açık. Tam dönem indirme
başlatılmadı; sıradaki öneri iki sensörlü bir eğitim günüyle kapasite ve
kesintiden devam denemesi. [Sonuç ve sınırlamalar](COLAB_PILOT.md).
Güncel tam test kümesi 192 başarılı; kod, biçim ve Git fark kontrolleri geçti.

Belirlenen kapsam doğrultusunda iki sensörlü 14 Ocak 2019 Colab denemesi hazırlandı: 8 geçiş,
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

5 Ekim'de Google Drive'a otomatik sonuç kaydı seçildi. Küçük ZIP'i
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
tabakalı aday ve üç maliyet alternatifi hazırlandı; kapsam kararı henüz
verilmedi. NOAA-20'nin 679 erken eğitim tespitinin nominal katalog zamanlarıyla
eşleşmemesi açık sorun olarak kaydedildi; hiçbiri silinmedi/negatif sayılmadı.
Seçilen kontrol günleri bu farkın dışında. 14 ek testle tam kümede 288 test
geçti; Ruff kod/biçim başarılı. Yeni ham indirme ve push yok.
[Kapsam seçenekleri ve sonraki iş](SUMMER_CONTROL_OPTIONS_2026-10-05.md).

B kapsamını seçtim. Altı çiftin otomatik Colab/Drive kayıt ve yeni
oturumda devam paketi hazır. Metadata boyutu toplam 1,10 GB; paket 2,95 MB.
Yerel kış kaynaklarıyla doğal denetim/alan/tarama ve ayrı ZIP geri yükleme
provada geçti; ham kaynaklar değişmedi. Gerçek yaz Colab işi hâlâ bekliyor.
20 yeni koruyucu testle tam kümede 308 başarılı; Ruff kod/biçim ve paket
CRC/SHA/notebook denetimleri geçti. Yeni yerel ham indirme ve push yok.
[Notebook, otomatik gruplar ve sonraki adım](COLAB_SUMMER_CONTROL.md).
