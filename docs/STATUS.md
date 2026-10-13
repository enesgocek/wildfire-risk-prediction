# Proje durum raporu — 14 Ekim 2026

Bu rapor, en son paylaşılan çalışma çıktısını ve kayıtlı yerel denetimleri
ayrı belirtir. Canlı VM/API sorgusu yerine geçmez.

## Güncel aşama

[V7 uzak ilerlemesi: 67 tam ay](GCP_V7_PROGRESS_2026-10-14.md#sonraki-uzak-bildirim-67-tam-ay):
kullanıcı running/remaining_months, aynı V7 kimliği/süre sınırı, None
hata alanları ve 529 çift bildiriyor. Mart 2018 üretimde; görünür gün
kapanışları 7, 11, 12, 13 Mart. Önceki snapshot'a göre bir ay/165 çift
artışı; 67/72 nominal ay (%93,1), işlenebilir 70 tam ay hedefine üç ay
kalır. İki ertelenen ay ve yerel bilimsel ürün/final kabulü ayrı kalır.
Gözlem saati olmadığı için hız/bitiş hesabı yapılmadı.

[V7 uzak ilerlemesi: 66 tam ay](GCP_V7_PROGRESS_2026-10-14.md):
kullanıcı running/remaining_months, doğru V7 kimliği, boş hata alanları
ve 364 işlenmiş çift bildiriyor. Nisan 2018 üretimde; 5 ve 6 Nisan
gün kapanışları görünüyor. Önceki 65 aylık uzak kapsamdan bir ay artış
var; eklenen ay kimliği seçilmiş çıktıda yok. 66/72 nominal ay (%91,7),
70 tam aylık işlenebilir hedefe dört ay kalır; iki ertelenen ay ayrı.
STOP sınırı bugün 16:35 Türkiye. Bu kullanıcı uzak çıktısıdır; yeni
yerel bilimsel ürün kabulü veya tam eğitim tamamlanması değildir.

[OAuth kurtarma sonrası V7 uzak başlangıç kontrolü geçti](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#oauth-kurtarma-sonrası-uzak-üretim-ilerlemesi):
kullanıcı progress running/june_safe_days, doğru V7 hash'i ve güncel
14 Ekim 13:35:01.727602 UTC sınırı bildirdi. Hata alanları None; bu çağrıda
16 çift kaydedilip doğrulanmış. Aralık aşamasından Haziran uygun günlerine
geçilmiş. Beş tam ay bu çağrının geri okuma sayacıdır; önceki 65 aylık
kabul silinmedi, yeni tam ay kabulü yok. Bu uzak kullanıcı çıktısıdır;
yerel bilimsel ürün kabulü veya tam eğitim tamamlanması değildir.

[OAuth kurtarma sonrası V7 devam sınırı doğrulandı](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#oauth-kurtarma-sonrası-güncel-oturum-sınırı):
kullanıcı Cloud Shell çıktısı RUNNING, 64800 saniye, STOP ve
automaticRestart=false gösteriyor. Yeni sınır 14 Ekim 13:35:01.727602 UTC
/ 16:35 Türkiye. V7 ve registry yerel hash'leri aynı. Bu kullanıcı
ayar bildirimi ve başlatma hazırlığıdır; üretimin gerçekten başladığı
henüz doğrulanmadı, 65 aylık önceki kabul kapsamı değişmedi.

[VM özel Drive bağlantısı kurulum çıktısı geçti](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#vm-kurulum-çıktısının-geri-okuması):
kullanıcı pinned installer için SHA-256 OK ve üç PASS bildirdi: aynı
client/scope/folder, yeni token ile folder erişimi ve private config kurulumu.
Bu uzak SSH çıktısıdır; bağımsız VM sorgusu yapılmadı. Üretim henüz
başlatılmadı; mevcut Start'ın 18 saat/STOP/automaticRestart=false ve yeni
terminationTimestamp bilgisi bekleniyor. Yerel V7/registry/installer hash'leri
aynı; bilimsel kabul 65 tam aylık önceki kapsamda kaldı.

[Yerel Drive bağlantısı doğrulandı](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md#terminal-kapanması-sonrası-yerel-canlı-doğrulama):
kullanıcı Google callback mesajından sonra terminali kapattığını bildirdi.
Özel dosya 13 Ekim 14:17:33 UTC'de değişmiş; yeni bağlantıyla canlı OAuth
refresh, mevcut folder erişimi/yazabilme yetkisi ve kontrol sırasında dosya
bütünlüğü geçti. Credential değerleri kayda alınmadı; Drive nesnesi yazılmadı.
VM'deki eski istemci/klasör ile eşitlik ve özel config kurulumu sonraki
installer adımında doğrulanacak. VM Stop kullanıcı teyitli; üretim henüz
yeniden başlamadı ve 65 aylık önceki kabul kapsamı değişmedi.

[V7 OAuth hatası ve özel bağlantı kurtarma hazırlığı](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md):
kullanıcı launcher'ı OAUTH 400 / parent GOOGLE_HTTP_400 / poweroff gösteriyor;
18 çocuk ve 22 ZIP arşiv geçişi geçmiş, yeni state yazılmadan durmuş.
Progress eski V6 Haziran hatasıdır; Python süreci yok ve VM Stop teyitli.
Kesin OAuth alt nedeni UNCLASSIFIED; Testing 7 günlük token koşulu olası,
canlı consent/issue zamanı kanıtı değil. Yerel yenileme ilk tarayıcı
denemesinde başarısız; özel dosya hâlâ 6 Ekim mtime'ında. Aynı istemci/
scope/folder ve token/folder erişimi doğrulanmadan değiştirmeyen renewal
ve VM private installer hazır; 61 test/lint/format geçti. 22 donmuş dosya
ve V7 aynı hash'te. Google insan izin adımı, başarılı aktarım ve üretim
devamı bekleniyor; yeni ay/ürün kabulü yok, önceki 65 ay korunur.

[V7 giriş sonrası poweroff bildirimi](GCP_SOURCE_RESUME_V7_2026-10-13.md#giriş-sonrası-erken-poweroff-bildirimi--13-ekim):
kullanıcı 13 Ekim 16:49:33 Türkiye SSH kapanma isteği bildirdi; gizli
Earthdata istemlerinden sonra gelmiş. Kesin neden, gerçek VM duruşu ve
wrapper/progress kimliği için launcher bekleniyor. Kodda supervisor
hata yolunda da poweroff ister; parola veya tamamlanma sonucu çıkarılmadı.
65 aylık önceki günlük/katalog kabulü aynı. Yeni üretim tekrarı verilmedi;
kısa Start sonrası salt okunur günlük/progress/süreç kontrolü istendi.
Aşağıdaki V7 hazırlık kaydı bu kullanıcı bildiriminin öncesindedir.

[V6 ikinci tanı kabulü ve V7 devam hazırlığı](GCP_SOURCE_RESUME_V7_2026-10-13.md):
15.843 baytlık public snapshot katalogla eşleşti: altı kaynak hatası,
12 iptal, tek parent ve 22 hazır ZIP / 65.888.711 bayt. 65 tam aylık
günlük/katalog kabulü korunur; ZIP baytları yerelde/native kabul edilmedi.
Ayrı V7, 13 Haziran 2018 ve 31 Aralık 2023 günlerini eksik tutar; üç
aşamayla diğer gün/aylara devam eder. Exact tanı/final/22 ZIP hash geçişi,
27 kanıt dosyasının korunması, bilinmeyen hata reddi ve 18 saat/poweroff
aynı; kaynak eşleşme ve negatif etiket kapıları korunur. 156 birleşik
test/lint/format geçti; 22 donmuş dosya aynı hash'te. Yeni paket hazır,
VM Stop kullanıcı teyitli; V7 henüz çalıştırılmadı. İşlenebilir sonuç
70 tam ay ve iki kısmi ayın 59 uygun günüdür; eğitim tamamlandı sayılmaz.

[V6 kaynak adları ve NASA metadata kontrolü](GCP_V6_FAILURE_2026-10-13.md#kaynak-tanısının-yerel-geri-okuması):
altı NOAA-20 çiftinde bildirilen geolocation 2021, seçilen sürüm 2024
üretimli; granül/021 alanları aynı. Exact public snapshot geri okuması
geçti; raw boyutlar planla eşleşiyor, checksum eşdeğerliği kanıtlanmadı.
Anonim CMR'de altı eski ad sıfır, altı yeni ad bir hit; eski metadata
revizyonları 404. Bu tüm NASA arşivlerinden yokluk kanıtı değil.
13 Haziran'ı eksik tutup diğer günleri ilerletme hazırlığı için 12 iptal
tanısı ve hazır ZIP hash envanteri toplayan yeni betik hazır; 14 birleşik
test/lint geçti. Yeni erteleme ve devam henüz uygulanmadı; kaynak/negatif
kontrolü korunur, 65 aylık kabul kapsamı değişmedi. VM Stop kullanıcı teyidi var.

[V6 Haziran 2018 kaynak eşleşme hatası](GCP_V6_FAILURE_2026-10-13.md):
yerel arşiv denetimi üç eşit failed final, 65 tam ay ve yedi yeni ay
kapanışı gösterdi. 13 Haziran'ın altı NOAA-20 çiftinde actual geolocation
girdi kontrolü başarısız; hata sonrası poweroff istenmiş. Haziran 1–9
kapalı; Ocak–Haziran 2018 ve Aralık 2023 toplam yedi ay tam kapanmamış.
Kaynak örneklerinde RAM/disk rezerv ihlali yok. Exact final bağlı salt
okunur tanı betiği hazır, sekiz test/lint geçti; VM'de henüz çalıştırılmadı.
Sonraki adım altı görevin bildirilen/seçilen dosya adlarını almaktır.
Kullanıcı indirme sonrası VM Stop teyidi verdi. Yeni üretim/etiket veya
bilimsel ürün bayt kabulü yok; aşağıdaki erken duruş belirsizliği tarihlidir.

[V6 yeni oturum VM duruşu](GCP_DRIVE_RESUME_V6_2026-10-12.md#yeni-oturumun-vm-duruş-bildirimi--13-ekim):
kullanıcı TERMINATED/18 saat/STOP ve otomatik yeniden başlatma kapalı
bildirdi. 13 Ekim 06:00:30 Türkiye duruşu; oturum 8:24:20 sürdü,
18 saatlik sınıra ulaşmadı. Kesin kapanış nedeni ve yeni tam-ay sayısı
bilinmiyor; final arşiv bekleniyor. Aşağıdaki 61 aylık snapshot önceki
ilerlemedir, yeni kapanış sonucu olarak genişletilmedi.

[V6 uzak ilerleme: 61 ay](GCP_DRIVE_RESUME_V6_2026-10-12.md#61-aylık-uzak-ilerleme-bildirimi--13-ekim):
kullanıcı running/remaining_months ve boş hata alanları bildiriyor.
61/72 ay (%84,7); 715 işlenmiş çift, Ekim 2018 son kapanış 1 Ekim.
Önceki snapshot'a göre iki ay/413 çift artış; gözlem zamanları olmadığından
hız hesabı yok. 11 ay tam kapanmamış; yeni yerel ürün kabulü yapılmadı.
Aşağıdaki 59 aylık kayıt önceki bildirimi korur.

[V6 uzak ilerleme: 59 ay](GCP_DRIVE_RESUME_V6_2026-10-12.md#59-aylık-uzak-ilerleme-bildirimi--13-ekim):
kullanıcı SSH running/remaining_months ve boş hata alanları bildiriyor.
59/72 ay (%81,9); 302 yeni çift, Aralık 2018 son kapanış 17 Aralık.
Ay isim listesi/süreç/hash yok; yeni ürün bayt kabulü yapılmadı.
13 ay tam kapanmamış; üst sınır 13 Ekim 15:36:04 Türkiye.
Aşağıdaki 12 Ekim kayıtları önceki snapshot'lardır.

[V6 yeni oturum başlangıcı](GCP_DRIVE_RESUME_V6_2026-10-12.md#yeni-oturum-başlangıç-bildirimi--12-ekim):
kullanıcı SSH çıktısında running/december_safe_days, yeni deadline ve boş
hata alanları var. Dört ay bu çağrıda geri okunmuş; yeni çift sıfır.
Önceki 58 aylık yerel kabul korunur. Eski poweroff satırı yeni phase
satırından öncedir. Süreç/hash snapshot'ı yok; canlı API sorgusu yapılmadı.

[V6 yeni oturum ayarı](GCP_DRIVE_RESUME_V6_2026-10-12.md#sonraki-18-saatlik-oturum-için-scheduling-bildirimi--12-ekim):
kullanıcı RUNNING/18 saat/STOP/automaticRestart=false bildirdi. Yeni üst
sınır 13 Ekim 15:36:04 Türkiye. Aynı V6 devam komutu hazır; üretim başlangıcı
henüz doğrulanmadı. Aşağıdaki kayıt önceki oturumun yerel kapanış denetimidir.

[V6 kapanış arşivinin yerel denetimi](GCP_DRIVE_RESUME_V6_2026-10-12.md#kapanış-arşivinin-yerel-denetimi--12-ekim):
beş dosya sınırı, üç eşit final, donmuş paket/katalog, 4.829 çift satırı
ve 58 tam-ay listesi geçti. Bu oturum 18 yeni ay kapatmış; 541 günlük
kapanış satırı, 588 progress günü içinde 47 önceki günle birlikte tutuluyor.
Ocak 2019 1–11 günleri kapanmış; 12–15 günlerinde 33 çift hazır, günlük
kapanış bekliyor. Aynı V6 ile devam kimliği uygun; yeni dosya yüklemesi
gerekmiyor. 29.146 kaynak örneğinde disk/RAM rezerv ihlali yok; tek negatif
iowait örneği CPU özetinden dışlanıp açık kaydedildi. Yerel kabul günlük/
katalog kapsamındadır; bilimsel ürün baytları ve canlı Drive denetlenmedi.
Kullanıcı indirme sonrası VM Stop teyidi verdi. Yeni 18 saatlik devam
için Start sonrası gerçek deadline/STOP ayarı kontrolü bekleniyor.

[V6 kontrollü oturum kapanışı: 58 ay](GCP_DRIVE_RESUME_V6_2026-10-12.md#kontrollü-oturum-kapanışı-58-ay--12-ekim):
kullanıcı SSH çıktısı paused_at_runtime_reserve, doğru V6 hash'i ve
Guest poweroff requested=True gösteriyor; hata/failed alanları None.
Üretici 2019-02–2023-11 arasında 58 tam ay bildiriyor: 72 eğitim ayının
%80,6'sı. Bu çağrıda 4.829 işlenmiş/beş yeniden kullanılan çift var.
Tam kapanmamış 14 ay: 2018'in 12 ayı, kısmi Ocak 2019 ve 31 Aralık
ertelenmiş Aralık 2023. Son görünen günlük kapanış 11 Ocak 2019;
sonraki günlere ait kaydedilmiş çiftler günlük kapanış sayılmaz.
Kapanış arşivinin yerel denetimi bekleniyor; yeni ürün bayt kabulü veya
üretim başlatması yapılmadı. Önceki duruş/ilerleme kayıtları tarihlidir.

[Literatür kaynaklarının ikinci kontrolü](research/LITERATURE_IDENTITY_AUDIT_2026-10-12.md):
34 kaydın tamamında gerçek yayın/ön baskı/veri/kurum kaydı ve yazar atfı
bulundu; 30 kayıt DOI siciliyle de eşleşti. Uydurma başlık/yazar uyuşmazlığı
saptanmadı. R18/R32'nin önceden doğrulanmamış hakemli yayın durumları
güncellendi; üç DOI tamamlandı, R30 kabul beyanının kanıt düzeyi ayrıldı.
Bu yayın kimliği denetimidir; bağımsız deney, bütün başarı iddiaları veya
özgünlük doğrulaması değildir. Önceki inceleme tarihli düzeltme notuyla korunur.

[Literatür incelemesi ve önerilen makale yönü](research/LITERATURE_REVIEW_2026-10-12.md):
12 Ekim'de 34 seçilmiş kaynak/ürün kaydı, erişim düzeyleri, arama sınırları,
danışman özeti ve hipotez/deney protokolü hazırlandı. Türkiye'de ve Akdeniz'de
yakın 24 saatlik çalışmalar mevcut; genel fikrin ilk kullanımını iddia
etmiyoruz. Olay/gözlem politikasının başarı, kapsam ve uyarı yüküne etkisi
olası araştırma katkısıdır; henüz deney sonucu veya özgünlük ispatı değildir.
Etiket/bağımsız referans kapısı açık, 2025 kapalı; canlı kod/paket/kuyruklar
bu çalışma nedeniyle değiştirilmedi. Aşağıdaki ilerlemeler kendi tarihli
yerel/uzak kanıt kapsamlarını korur.

[V6 uzak ilerleme: 50 ay](GCP_DRIVE_RESUME_V6_2026-10-12.md#50-aylık-uzak-ilerleme-bildirimi--12-ekim):
kullanıcı SSH çıktısında running/doğru hash ve None hata alanları var.
Tam ay sayacı 50/72, yaklaşık %69,4; Eylül 2019 işleniyor, görünen son
kapanış 18 Eylül. Önceki bildirime göre iki tam ay/612 çift ilerleme;
bu çağrıda 2.727 işlenmiş/beş yeniden kullanılan çift. Süreçler aktif,
üst sınır yine 21:13:37 Türkiye. Uzak günlük/katalog kanıtı; yeni yerel
ürün kabulü değil. Aşağıdaki 48 aylık bildirim önceki snapshot'tır.

[V6 uzak ilerleme: 48 ay](GCP_DRIVE_RESUME_V6_2026-10-12.md#48-aylık-uzak-ilerleme-bildirimi--12-ekim):
kullanıcının SSH çıktısında running/doğru V6 hash'i ve hata alanları None.
Tam ay sayacı 48/72; Kasım 2019 işleniyor, görünen son kapanış 11 Kasım.
Bu çağrıda 2.115 yeni/beş yeniden kullanılan çift, aktif supervisor ve
çocuklar var. Üst sınır 12 Ekim 21:13:37 Türkiye; Aralık 31 ertelemesi
korunur. Uzak günlük/katalog kanıtıdır; yeni yerel ürün bayt kabulü değil.

[Eğitim bitki örtüsü kuyruğu tamamlandı](VEGETATION_TRAINING_COMPLETE_2026-10-12.md):
12 Ekim 09:49:26 Türkiye'de selected_training_range_verified; 2018–2023
72 ayın tamamı hazır. Son çağrıda 62 eski ay geri okundu, kalan 10 ay
hazırlandı. Final kayıtlara göre 229 dosya hash'i aynı; gerçek süreçler ve
iki kilit yok, hata/stderr yok. 2.191 gün/2.899 hücre/iki pencere için
12.703.418 aday hücre-gün-pencere satırı. Bu bitki örtüsü kabulüdür;
2024, uydu kuyruğu ve nihai etiket/model kabulü ayrı ve açık kalır.
Aşağıdaki başlangıç ve duruş kayıtları tamamlanmadan önceki durumlardır.

[VPN molası sonrası yerel devam](VEGETATION_VPN_RESUME_2026-10-12.md):
12 Ekim 06:03:08 Türkiye'de yeni iş running; gerçek launcher/supervisor
ve çocuk süreçler canlı, stderr boş. Önceki 62 ay/199 dosya ile Mart'ın
169 kısmi JSON'u aynı hash'lerde; ISO proof/paket ve scalar bağlantı geçti.
Eski aylar yeniden doğrulanıyor; yeni tam ay veya model kabulü yok.
13 Ekim 17:53:22 son sınırı/beş dakika rezerv korunur. VM değiştirilmedi.

[VPN için yerel bitki örtüsü duruşu](VEGETATION_VPN_PAUSE_2026-10-12.md):
12 Ekim 05:30:39 Türkiye'de interrupted_checkpoints_retained; gerçek süreç
ağacı kapandı ve iki kilit temizlendi. 62 ay (Ocak 2018–Şubat 2023) için
199 veri/runtime dosyası hash'i aynı. Mart'ın 169 ham JSON kaydı kısmi;
tam ay kabulü değil. Ctrl+C ardından kapanmayan tek istek alt süreci
kimliği doğrulanarak sonlandırıldı. Kullanıcı istemeden yeniden başlatılmaz;
VM değiştirilmedi. Aşağıdaki 61 referanslı hazırlık snapshot'ı tarihsel olarak korunur.

[Veri setine geçiş hazırlığı](DATASET_PREPARATION_RUNBOOK_2026-10-12.md):
veri sözlüğü, 72 aylık kaynak/teslim envanteri, hash bağlı toplu yeniden
kullanım, nullable hedef eşleştirme ve son aday denetimi hazır. Snapshot'ta
61 bitki örtüsü kaynak referansı, iki aday ay ve son kayıtlı 40 uydu
günlük/katalog ayı ayrı tutuluyor; canlı V6 ilerlemesi değildir. İki gerçek
ay/179.738 hücre-gün yeniden üretilmeden geri okundu; 107 test ve 165
değişmeyen kaynak/yöntem hash'i geçti. Tüm dönem batch'i başlatılmadı.
Bilimsel etiket kapıları, 2024 hazırlığı ve model_ready false korunur.

[Tam aylık aday özellik geri okuması](FEATURE_MONTH_READBACK_2026-10-12.md):
hazır Ocak/Ağustos 2018 kaynaklarıyla 62 gün, 179.738 hücre-gün ve 27 aday
özellik ayrı günlük parçalar halinde doğrulandı. 165 kaynak/yöntem hash'i
aynı; 66 test, lint/format geçti. Eksikler korunuyor, etiket/nihai model
kabulü yok. Yeni ağ/bulut işi açılmadı; çalışan kuyruklar değiştirilmedi.
Bu çalışma tam dönem birleştirmesine hazırlıktır; nihai bilimsel kapılar açık.

[Sonraki V6 süreç/progress bildirimi](GCP_DRIVE_RESUME_V6_2026-10-12.md#sonraki-süreç-ve-progress-bildirimi--12-ekim):
kullanıcının SSH çıktısında doğru V6 hash'i, running ve 53:52 süredir aktif
PID 1683 var; 26 eski ay geri okunmuş, yeni çift sıfır ve hata alanları None.
Progress son sınırı 12 Ekim 21:13:37 Türkiye. Önceki 40 aylık günlük/katalog
kabulü korunur; bağımsız canlı API/Drive veya yeni ürün kabulü yapılmadı.
Aşağıdaki ilk başlangıç kaydı bu yeni bildirimin öncesindedir.

[İlk V6 uzak başlangıç bildirimi](GCP_DRIVE_RESUME_V6_2026-10-12.md#ilk-uzak-başlangıç-bildirimi--12-ekim):
kullanıcı launcher çıktısında V5 kanıtları/31 retained pair korunmuş ve eski
altı ay verified/reused. Son phase remaining_months, görünen hata veya yeni
pair/day satırı yok. Önceki 40 aylık kabul korunur; yeni ürün/ay kabulü yok.
Canlı süreç, uzak progress kod hash'i ve yeni deadline bu çıktıyla doğrulanmadı;
sıradaki adım salt okunur progress/süreç kontrolü. Aşağıdaki V6 hazırlık kaydı
bu uzak başlangıç bildiriminden önceki durumu anlatır.

[Drive tanı geri okuması ve V6 devam hazırlığı](GCP_DRIVE_RESUME_V6_2026-10-12.md):
tanıda OAuth/klasör/listing başarılı, 361,60 GB boş hesap alanı ve protected
hash'ler aynı. 31 hazır ZIP: 30 yayımlanmamış / bir payload completion olmadan
mevcut; Temmuz 18–21. Çocuk hatası yok. Tarihsel 404'ün kesin dosya/nedeni
açık; yeni bilimsel ürün kabulü yok. V6 exact final/tanı/31 ZIP'i kontrol
ederek geçiş yapar, yalnız aynı metadata GET 404'e en çok üç ek deneme ekler;
upload/create tekrarı yok. 97 test ve 25 donmuş dosya hash'i geçti. VM Stop
teyitli; yeni V6 uzak üretimi başlatılmadı. 18 saat/rezerv/poweroff, önceki
40 ay ve Aralık 31 ertelemesi korunur. Aşağıdaki tanı hazırlığı bu yeni
geri okumadan önceydi.

[V5 gerçek arşiv kabulü ve Drive tanısı hazırlığı](GCP_V5_EARLY_STOP_2026-10-12.md#gerçek-arşiv-kontrolü-ve-salt-okunur-tanı-hazırlığı):
beş üyeli arşiv/üç aynı final/V5 ve donmuş paket kimlikleri doğrulandı.
40 tam ay, Temmuz 1–17 kapanışı, 156 yeni çift ve 18 Temmuz'da 5/8 çift
günlük/katalog düzeyinde tutarlı. 2.696 kaynak örneğinde RAM/disk rezerv
ihlali yok. Ürün/Drive baytları arşivde yok; etkilenen dosya ve 404 nedeni açık.
Salt okunur, sınırlandırılmış tanı hazır; 25 yeni + 36 Drive + 51 ilgili
manifest/controller testi geçti (tam eski ay bilimsel testi seçilmedi).
Kullanıcı VM Stop teyidi verdi. Yeni uzak üretim başlatılmadı, bilimsel kod ve
etiket koşulları değiştirilmedi. Aşağıdaki SSH yorumu gerçek arşivden önceydi.

[V5 kapanışının sonraki SSH bildirimi](GCP_V5_EARLY_STOP_2026-10-12.md#sonraki-ssh-bildirimi--drive-metadata-hatası):
Temmuz 2020 pair_publication sırasında Drive FILE_METADATA 404 notFound;
parent hata ve poweroff isteği var. Süre sınırı kaynaklı duruş değil.
156 yeni çift ve son görünen 17 Temmuz gün commit'i uzak günlük bildirimi;
40 tam ay korunur, Temmuz tam değil. Yerel ürün kabulü yapılmadı.
Hangi dosya/erişim yolunun etkilendiği henüz bilinmiyor; sıradaki adım
tam oturum günlüğü/özet arşivi, VM Stop ve salt okunur tanı. Kod/paket
ve bulut ayarları değiştirilmedi. Aşağıdaki ön inceleme bu yeni günlükten önceydi.

[V5 erken kapanış ön incelemesi](GCP_V5_EARLY_STOP_2026-10-12.md):
kullanıcı Cloud Shell çıktısında TERMINATED ve 64800 saniye/18 saat doğru.
Gerçekleşen çalışma 1:56:55,696; duruş 12 Ekim 00:52:49 Türkiye, kayıtlı
16:55:48 sınırından yaklaşık 16 saat önce. Normal süre rezervi değil;
kapanış nedeni günlük alınmadan bilinmiyor. Önceki 40 aylık günlük/katalog
kabulü korunur; yeni üretim/ürün kabulü yok. Sıradaki adım kısa günlük
toplama, ardından VM Stop; üretim yeniden başlatılmadı. Aşağıdaki V5
running bildirimleri bu duruştan önceki tarihsel durumlardır.

[V5 uzak başlangıç bildirimi](GCP_EIGHTEEN_HOUR_CONTINUATION_2026-10-11.md#ilk-v5-uzak-başlangıç-geri-bildirimi):
kullanıcı SSH çıktısında doğru V5 hash'i, running/remaining_months, PID 1681
ve hata None. 24 eski tanı korunmuş; ilk dört ay yeniden kullanılmış.
Ay sayısı beş, bu çağrının geri okunan listesi; önceki 40 ayın kaybı değildir.
Yeni çift sıfır; önceki yerel günlük/katalog kabulü 40 ay olarak korunur.
Kaydedilmiş son sınır 12 Ekim 16:55:48 Türkiye; bağımsız canlı API/Drive
veya yeni bilimsel ürün kabulü yapılmadı. Aşağıdaki V5 hazırlığı bu uzak
başlangıçtan önceki durumu anlatır.

[Bakım sonrası bitki örtüsü devamı](VEGETATION_MAINTENANCE_RESUME_2026-10-11.md)
kullanıcının açık başlat isteğiyle 22:56:57 Türkiye'de başladı. Eski süreç/
kilit yok; 148 kabul edilmiş dosya, 276 Ekim ham kaydı ve ISO proof aynı.
115,45 GiB boş disk/küçük EE bağlantısı geçti; kota kısıt uyarısı yok.
Yeni job `training_iso_v2_maintenance_resume_20261011_bd22517d`, PID 7036
ve çocukları canlı, running/hata yok. İlk iki eski ay geri okunmuş;
45 eski ay korunur, yeni tam ay kabulü henüz yok. Önceki 13 Ekim 17:53
son sınırı korunarak beş dakika rezervli yaklaşık 42,86 saatlik devam açıldı.
Aşağıdaki bakım duruşu kaydı bu yeni çağrıdan önceki durumu anlatır.

[Bilgisayar bakımı için bitki örtüsü duruşu](VEGETATION_MAINTENANCE_PAUSE_2026-10-11.md):
kullanıcı isteğiyle 21:26:43 Türkiye'de kontrollü durdu; üst/çocuk süreçler ve
iki yazıcı kilidi yok. Final `interrupted_checkpoints_retained`, hata yok;
45 ay (Ocak 2018–Eylül 2021) ve 13 runtime pin'i, toplam 148 dosya aynı.
Ekim 2021 kısmi kayıtları korundu. Otomatik devam yok; kullanıcının açık
"başlat" isteği beklenir. Aşağıdaki yerel running kayıtları bu duruştan öncedir.

[V4 hata denetimi ve 18 saatlik V5 hazırlığı](GCP_EIGHTEEN_HOUR_CONTINUATION_2026-10-11.md)
tamamlandı. Gerçek tanı arşivi/katalog geri okumasında 40 tam ay
(Ağustos 2020–Kasım 2023), 3.020 yeni/45 yeniden kullanılan çift tutarlı.
Temmuz 2020 başlangıcında 5 ReadTimeout ve ardından 19 iptal çıkışı var;
örneklenmiş RAM/disk rezerv ihlali yok. V5 yalnız bu zaman aşımını en fazla
iki ek denemeyle karşılar ve 18 saat/STOP için hazırdır. 32 V5/20 V4 + 73
eski regresyon testi, lint/format geçti. Yeni uzak oturum başlatılmadı;
kullanıcı VM Stop teyidi verdi. Ürün ZIP/Drive baytları bu arşivde yeniden
kabul edilmedi. 31 Aralık ertelemesi/unknown/negatif false korunur.
Aşağıdaki V4 başlangıç kayıtları tarihsel durumu anlatır.

[Kesinti sonrası bitki örtüsü devamı](VEGETATION_POWER_RESUME_2026-10-11.md)
yeni kullanıcı isteğiyle 17:53 Türkiye'de başladı. Eski süreç/kilit yok;
121 korunan dosya, ISO proof ve Ocak 2021'in 368 ham grubu kontrol edildi.
116 GiB civarı boş disk; küçük EE isteği geçti, kısıtlı kota uyarısı yok.
Yeni job `training_iso_v2_power_resume_20261011_bb85a275`, PID 33832;
başlangıçta üst/çocuklar canlı, `running`, hata dosyası boş. Son snapshot
16 eski ayı yeniden doğruluyor; kabul edilmiş 36 ay korunur. Aynı V2/iki
istek/10 GiB rezerv, 48 saatlik güvenlik sınırı ve seçilmiş aylar tamamlanınca
duruş kullanılır. Önceki 14:45 sınırı doldu; kullanıcı yeni devamı yetkilendirdi.
Aşağıdaki VPN molası kaydı bu yeni çağrıdan önceki durumu anlatır.
15:09:55 UTC sonraki progress geri okumasında 37 ay doğrulanmış ve
Şubat 2021'de running/hata yok; Ocak 2021 bu yeni devamda kapanmıştır.
15:23:41 UTC kaynak zamanlı sonraki snapshot 38 ay/Mart 2021; 18:26 Türkiye
gerçek Windows sorgusunda üst/çocuklar canlı, stderr boş. Ocak/Şubat
manifest, tablo ve aylık readback hash'leri aynı bulundu.

[VPN molası için yerel kuyruk duruşu](VEGETATION_VPN_PAUSE_2026-10-11.md):
kullanıcı isteğiyle 03:22 Türkiye'de kontrollü Ctrl+C;
`interrupted_checkpoints_retained`, eski süreçler ve iki yazıcı kilidi yok.
36 ay (2018–2020) ve runtime pinleri toplam 121 dosya hash'iyle aynı bulundu.
Ocak 2021 kısmi; kullanıcı VPN kapalı bildirimi sonrası kontrollü devam
bekleniyor. Otomatik yeniden başlatma yok; eski 11 Ekim 14:45 Türkiye
süre sınırı korunur. Uydu VM işi bu yerel duruştan etkilenmedi.
Aşağıdaki yerel `running` kayıtları bu kontrollü duruştan önceki durumlardır.

[V4 uzak başlangıç geri bildirimi](GCP_THIRTEEN_HOUR_CONTINUATION_2026-10-10.md#ilk-uzak-çalışma-geri-bildirimi):
kullanıcının 20:39:26 UTC SSH çıktısında doğru V4 hash'iyle `running`,
`remaining_months`, canlı PID 1733 ve hata alanı `None`. Eski aylar geri
okunarak kullanılıyor; yeni çift sıfır ve son kabul edilmiş toplam 28 ay
değişmedi. Yeni son zaman 11 Ekim 12:16:26 Türkiye olarak kaydedilmiş;
normal rezerv kapanışı yaklaşık 11:51–11:56 beklenir. Önceki Cloud Shell
geri okumasında 46.800 saniye/STOP/automaticRestart false doğruydu.
Kaynak kullanıcı çıktısıdır; bağımsız canlı VM/API veya ürün kabulü yapılmadı.
Aşağıdaki hazırlık kaydı bu yeni uzak başlangıçtan önceki durumu anlatır.

[13 saatlik V4 devam hazırlığı](GCP_THIRTEEN_HOUR_CONTINUATION_2026-10-10.md)
kullanıcı isteğiyle tamamlandı. V3/controller'ın sekiz saatlik deadline kapısı
ayrı V4 girişinde 13 saatle sınırlandı; 5 dakika supervisor/20 dakika pipeline
rezervi korunur. İlk geçiş yalnız kabul edilmiş üç V3 finalinin tam hash'ine
izin verir. 20 V4 ve 46 eski regresyon testi, lint/format geçti; V3, 19 donmuş
paket üyesi ve canlı bitki örtüsü kod kimlikleri aynı. VM ayarı değiştirilmedi
ve VM başlatılmadı. Sonuç sayımı hâlâ 28 tam ay; 13 saatlik uzak sonuç yok.

[İkinci V3 oturum arşivi](GCP_SOURCE_AWARE_V3_2026-10-10.md#ikinci-oturumun-kapanışı-ve-gerçek-arşiv-kontrolü)
gerçek baytlarla ağ kapalı kabul edildi: normal süre rezervi duruşu,
başarılı poweroff kaydı; hata alanı yok. Tam ay listesi 21'den 28'e
çıktı (Ağustos 2021–Kasım 2023); Temmuz 2021 1–20 ve Aralık 2023 1–30
kısmi. 1.863 yeni/18 yeniden kullanılan çift, 206 commit ve 262 gün
katalogla tutarlı. Temmuz 21–25'in 45 nominal çift logu günlük kapanış
sayılmadı. Kaydedilmiş disk/RAM rezerv ihlali yok. Kullanıcı indirme
sonrası VM'yi tekrar Stop yaptığını teyit etti. Bu günlük/katalog kabulü;
yeni bilimsel ürün ZIP'leri/Drive baytları ayrıca geri okunmadı. Gözlem
unknown/negatif false ve 31 Aralık ertelemesi korunur; yeni VM işi yok.

Kullanıcının Contributor güncellemesi sonrası [yerel bitki örtüsü devamı](VEGETATION_QUOTA_CHECK_2026-10-10.md#contributor-güncellemesi-sonrası-devam)
başladı: `training_iso_v2_contributor_resume_20261010_5c811bc3`;
19:02:11 UTC üst kayıt `running`, PID 22500 ve geri okuma çocukları canlı.
19:00 prelaunch'ta 265 dosya aynı, küçük EE isteğinde kısıtlı mod uyarısı yok.
İlk ay yeniden doğrulanmış; eski 22 ay korunur. Aynı V2/2018–2023 kapsamı,
iki EE isteği ve 10 GiB rezervle, önceki 24 saat sınırı uzatılmadan
16,631552 saatlik çağrı açıldı; hedef bitiş yaklaşık 11 Ekim 14:40 Türkiye.
Kalan bütün ayların Contributor kotasına sığacağı henüz ölçülmedi.
Aşağıdaki duruş kaydı bu yeni çağrıdan önceki durumdur.

[Bitki örtüsü kota kontrolü](VEGETATION_QUOTA_CHECK_2026-10-10.md): önceki
yerel V2 iş 15:06:30 UTC'de Kasım 2019 hazırlanırken `EEException` ile
durmuş; eski üst/çocuk süreçler yok. 22 tam ay ve son kesimin 91/92 grubu
korunmuş; 265 dosya ve checkpoint sözleşmeleri kontrol boyunca aynı.
Kimlikle küçük hizmet isteği geçti, fakat SDK güncel noncommercial kota
aşımı/kısıtlı mod bildiriyor. Önceki hatanın kesin nedeni bilinmiyor;
internet kesintisi kanıtlanmadı. Tier bilinmiyor; kuyruk yeniden başlamadı,
billing/commercial kayıt değişmedi. Önceki `running` kayıtları tarihseldir.

[Parçalı özellik kaydı ve okuyucu](FEATURE_PARTITION_PILOT_2026-10-10.md)
dört kabul edilmiş eğitim gününde 11.596 hücre-günü aynen geri okudu.
Günlük feature/kalite parçaları ayrı, hash ve anahtar envanteri kayıtlı;
okuyucu bir gün alıyor ve yanlış dönem/bozulmuş dosyayı reddediyor.
47 ilgili test ve ağ kapalı gerçek deneme geçti. 44 girdi değişmedi;
etiket/imputasyon/model veya bütün ay kabulü yok. Bitki örtüsü son yerel
progress kaydı 13:47:37 UTC'de 20 doğrulanmış ay ve Eylül 2019'da
`running` gösteriyor; 136 eski baseline ve iki canlı kod hash'i aynı.

[Habitat–meteoroloji destek ve zor vaka paketi](DECISION_REVIEW_2026-10-10.md)
tamamlandı: 189 desteksiz, 310 kısmi ve 2.400 tam meteoroloji destekli
hücre; 33 habitat/53 olay-senaryo örneği kaynaklarına bağlandı. Uzman
inceleme formu boş, olay/habitat kararı verilmedi. Ağ engellenmiş gerçek
geri okuma ve 39 ilgili test geçti. [Veri seti kabul taslağı](DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md)
eksik değer, dönem kenarı, etiket kanıtı ve son freeze koşullarını ayırır.
12:35:46 UTC yerel progress kaydı 17 doğrulanmış ay ve Haziran 2019
hazırlığında `running` gösteriyor; eski 136 baseline dosyası değişmedi.

[Gün geçişleri ve hedef kabul hazırlığı](TARGET_ADMISSION_REVIEW_2026-10-10.md)
yerelde geçti. Birleştirme artık dört eğitim gününde 11.596 hücre-günü
kapsıyor; kesim/taşıma yaşları ve ayrı pencere eksikleri korundu. Dokuz
eski keşif kataloğunun hedef pencereleri/boş hedefleri geri okundu; 0/1
etiket üretilmedi. 54 ilgili test geçti. Mevcut etiket kabul kapısı kapalı;
olay, ilk hücre, habitat ve negatif gözlem kararları açık.

Veri hazırlıkları sürerken [özellik birleştirme denemesi](FEATURE_JOIN_PILOT_2026-10-10.md)
tamamlandı: 1 Ağustos 2018'in 2.899 hücresinde 27 aday özellik; kaynak
değerleri ve eksikler CSV geri okumasında korundu. Kalite/provenance ayrı,
etiket veya model yok. Ağ engellenmiş gerçek kabul ve 42 ilgili test geçti.
Son yerel bitki örtüsü progress kaydı (10 Ekim 11:53:32 UTC), Mart 2019
dahil 15 ayın doğrulandığını ve Nisan 2019 hazırlığının `running` olduğunu
gösteriyor. 136 eski baseline dosyası ve iki canlı kod hash'i değişmedi.

Kullanıcının yeni VM ps/log/progress çıktısında V3 `running`; PID 1669,
çalışma 9 dakika 20 saniye. Wrapper kimliği doğru, mevcut Ağustos–Ekim
2023 aylarını yeniden kullanma satırları var. Yeni Google sınırı
10 Ekim 19:28:19,420127 UTC (**22:28:19 Türkiye**). İlk kontrol eski
progress/deadline'ı göstermişti; başlangıç geri okumasından sonra yenisi
yazıldı. Bu yeni uzak çalışma kaydıdır; ikinci oturum bitiş kabulü değil.

Yerel bitki örtüsü duruşunun nedeni gerçek dosyalarla yeniden üretildi:
22 Mart 2019'un 20 ham grubunda karışık saniye hassasiyeti varsayılan Pandas
parser'ında hata veriyor. Açık ISO dönüşümü 868 zamanı scalar ile eşleştirdi;
aynı 5.798 satır özgün bilimsel denetimden geçti. 94 girdi ve 11 kaynak
pinleri değişmedi. [Sınırlı düzeltme ve V2 devam](VEGETATION_ISO_RESUME_2026-10-10.md)
hazırlandı; 105 ilgili test ve gerçek eski Ağustos ayı ağ kapalı geri okuması
geçti. Yeni manifest/raporlarda runtime parser kimliği açık tutuluyor.

Yerel V2 iş `training_iso_v2_2018_2023_20261010_50d439a4`, 10 Ekim yaklaşık
14:45 Türkiye saatinde başlatıldı. Gerçek süreç sorgusunda PID 22892 ve
readback çocukları canlı. Son yerel kontrolde üst kayıt `running`, eski
14 ay yeniden doğrulanmış ve Mart 2019'un eksik kesimine geçilmiştir.
Eski 14 ay korunmuş, 136 baseline dosyasının hash'i başlangıç sonrasında aynı.
Yeni çağrı 24 saatle sınırlı; 11 Ekim yaklaşık 14:45'te bütün aylar bitmeden
durabilir. Bilgisayar açık ve uyanık kalmalıdır. Eski süreç veya kilit silinmedi.

Önceki kapanış ve teşhis kayıtları:

İndirilen V3 günlük arşivinin yerel sınır/hash, üç final durumun eşitliği,
dondurulmuş paket kimliği ve katalog/sayaç denetimi geçti. 496.892 bayt,
SHA-256 `19b177afebe1724770307f9e911e103b538ee7a347a283cd294f000cdb5482c7`.
21 tam ay bildirimi ve 2.032 tekil yeni çift satırı katalogla tutarlı.
235 günlük commit satırı var; final listede ayrıca 35 yeniden kullanıldığı
anlaşılan gün bulunuyor. Şubat 2022 27 ve 28 günlerinin her birinde 9/9
yeni çift satırı mevcut, fakat günlük kapanış yok. Ölçümlerde en az 12,46
GiB boş disk/111,47 GiB kullanılabilir RAM; rezerv ihlali kaydı yok.
[Geri okuma ve devam](GCP_SOURCE_AWARE_V3_2026-10-10.md). Bu yalnız
günlük/katalog tutarlılığıdır; bilimsel ürün ZIP'leri ve canlı Drive bu
arşivde ayrıca denetlenmedi. Kullanıcı indirme sonrasında VM'yi tekrar
Stop yaptığını teyit etti. Aynı V3'nin normal rezervden devam koşulu sağlanır;
yeni başlangıç için yeni Google deadline'ı gerekir.

Teşhis öncesindeki bağımsız yerel bitki örtüsü üst raporu `failed_checkpoints_retained`:
14 ay doğrulanmış, Mart 2019 hazırlığı durmuştur. Alt kuyruk RuntimeError,
aylık çocuk logunun güvenli son satırı ValueError bildirir; kök neden henüz
belirlenmedi. Son üst rapor zamanı 10 Ekim 03:14:45,502942 UTC. 11 kaynak
hash'i ilk başlatılan sürümle aynı; bu bulut denetiminde değişmedi. Yeni
yerel kuyruk başlatılmadı, eski kayıtlar silinmedi. Önceki canlı durumlar
aşağıda ölçüm anlarıyla korunur.

İlk uzak kapanış bildirimi:

Son paylaşılan V3 kapanış kaydı `paused_at_runtime_reserve` ve
`Guest poweroff requested: True` bildiriyor. Kullanıcının Cloud Shell
çıktısında VM `TERMINATED`; 10 Ekim 01:58:42,563–09:36:35,528 UTC arasında
7 saat 37 dakika 52,965 saniye çalışmış. Google sınırından 22 dakika önceki
duruş, süre rezervi ve kalan işlerin kapanmasıyla uyumlu. Bu oturum hata
durumu bildirmiyor; bütün eğitim dönemi bitmiş değil.

Uzak listede Mart 2022–Kasım 2023 arasında **21 tam ay** var; önceki 14 aya
Mart–Eylül 2022 yedi ay eklenmiş. Şubat 2022'nin 1–26 günleri ve Aralık
2023'ün 1–30 günleri doğrulanan gün listesinde. Oturum sayacı 2.032 yeni/9
yeniden kullanılan çift; 270 doğrulanan gün yeniden kullanım da içerir.
Şubat'ın kalan günlerindeki çift logları günlük/aylık tamamlanma sayılmaz.
V3/adapter/proof kimlikleri beklenenlerle eşleşiyor. Gözlem unknown, negatif
izin false ve 31 Aralık ertelemesi korunuyor. Bu kullanıcı tarafından
paylaşılan uzak kayıttır; yeni sonuç arşivi henüz indirilip yerelde kabul
edilmedi. [Kapanış kaydı ve günlük toplama](GCP_SOURCE_AWARE_V3_2026-10-10.md).

Önceki başlangıç kaydı:

Kullanıcının son VM ps/log/progress çıktısında V3 üst süreci canlı
(PID 1677, çalışma 2 dakika 14 saniye), durum `running`. Wrapper
`792d774f53c2a7249a10f4111f2f785e08d5bd2a8153e1151c73efe493b5942e`
ve adapter kimliği hazırlanmış sürümle eşleşiyor. Günlük 15 V2 tanısının
korunduğunu ve `december_safe_days` aşamasına girildiğini bildiriyor.
Uygulamanın yeni durma kaydı 10 Ekim 09:58:35,730711 UTC
(12:58:35 Türkiye). Bu kullanıcı tarafından paylaşılan uzak başlangıç
kaydıdır; canlı API sorgusu, yeni raw kaynak başarısı veya oturum sonu
kabulü değildir. İlk kontrol, önceki V2 progress dosyasını göstermişti;
Drive başlangıç kontrollerinden sonra V3 durumu yazılmıştır.

Başlangıçtan önceki hazırlık:

Son indirilen 3.233 bayt gerçek kaynak adapter kontrolü kabul edildi:
203 tarama/1.889 scan–grid satırı, native hücre sayımları ve üç UTC sütununun
nanosaniyeleri eşleşti; girdi hash'leri aynı ve isim alanı geri yüklendi.
[V3 devam sürümü](GCP_SOURCE_AWARE_V3_2026-10-10.md) hazır. Yeni ürünlerin
yöntem/progress kaydında adapter kimliği açık tutuluyor; eski 15 V2 tanısı
baytları korunarak merkezi arşive taşınacak. Eski başarılı checkpoint'ler
yeniden hesaplanmadan doğrulanıyor. 94 ilgili test, gerçek eski checkpoint'in
ağ kapalı V3 tekrar kullanımı ve ayrı fixture provenance biçim kontrolü geçti.
Yeni uzun oturum henüz başlamadı. Kullanıcı son indirme sonrası VM'nin
Stopped olduğunu teyit etti. Negatif etiket yasağı, 31 Aralık 2023 ertelemesi
ve 2025 kapalı test sınırı korunuyor.

Önceki teşhis aşamaları:

Son paylaşılan Cloud Shell sorgusunda VM `TERMINATED`; 9 Ekim
20:43:22–23:10:27 UTC arasında yaklaşık 2 saat 27 dakika çalışmış.
Planlı 10 Ekim 04:43 UTC sınırından önce durmuş. V2 günlükte ilk hata
`SNPP:2022252.2230 ValueError CLASS_ONLY`, ardından çocuk `-9` kodları ve
otomatik poweroff isteği var. Uzak progress Ekim 2022–Kasım 2023 için 14
tam ay, Eylül 1–5 günlerini; 510 yeni/15 yeniden kullanılan çift bildiriyor.
Yeni tam aylık sonuçların yerel kabulü yapılmadı. İlk kaynak hatası için
[ayrı V2 teşhis aracı ve toplama rehberi](GCP_V2_FAILURE_2026-10-10.md) kullanıldı.
Kullanıcı son log alımından sonra VM'yi tekrar Stop yaptığını teyit etti.
İndirilen 8.794 bayt snapshot'ın V2/plan kimlik geri okuması geçti. 3.511
ölçümde en düşük boş disk 13,05 GiB, kullanılabilir RAM 112,08 GiB; ölçümlerde
rezerv tükenmesi görünmüyor. İki kaynak dosyasının boyutu eşleşiyor; alan
çıktıları mevcut, scan çıktıları eksik. Karışık saniye hassasiyetinin Pandas
çözümlemesinde hata üretebilmesi sentetik olarak gösterildi; gerçek kaynağın
kök nedeni bu ilk snapshot aşamasında henüz kanıtlanmadı. Ağ kapalı, tek
kaynakta özgün scan fonksiyonunu
yeniden çalıştıran ayrı araç hazır; 60 ilgili test ve gerçek paket import
kontrolü geçti. Üretim kodu değiştirilmedi, kuyruk yeniden başlatılmadı.
Snapshot indirildikten sonra da VM'nin Stopped olduğu kullanıcıca teyit edildi.

Sonraki 2.824 bayt gerçek kaynak replay JSON'u 184. satırdaki tarih
çözümleme ValueError'ını yeniden üretti. 203 başlangıç zamanından 202'si
kesirli, biri tam saniye; açık ISO çözümleme üç zaman sütununda özgün ham
TAI93 dönüşümüyle nanosaniyesine kadar eşleşti. Girdi hash'leri değişmedi.
[Dar parser düzeltmesi ve son kısa kabul kontrolü](GCP_SCAN_TIME_FIX_2026-10-10.md)
hazır: çalışma anında yalnız özgün scan modülündeki üç UTC çağrısı sarılıyor;
ham zaman ve hücre eşitlik guard'ları korunuyor. 76 ilgili yerel test geçti.
Gerçek kaynakta adapter altında bütün hücre sayımı henüz denenmedi; üretim
başlatılmadı. Kullanıcı son JSON alımından sonra VM'yi Stop yaptığını teyit etti.

Önceki uzak ilerleme kaydı aşağıda zamanıyla korunmuştur:

10 Ekim'de paylaşılan uzak log/progress, V2 devam oturumunun `running` ve
`remaining_months` aşamasında olduğunu gösteriyor. Bu oturumda Mayıs–Kasım
2023 yedi ay doğrulanmış/yeniden kullanılmış; Aralık 2023 1–30 günleri
doğrulanmış gün listesinde. Yeni çift sayacı bu çıktı anında sıfır; önceki
kayıtlar yeniden hesaplanmadan kontrol ediliyor. Liste doğrulama ilerledikçe
genişliyor; önceki ayların silindiği veya bütün sonuçların yerel kabul aldığı
anlamına gelmez. Durma sınırı 10 Ekim 2026 04:43:15 UTC (07:43:15 Türkiye).
Bu bilgi kullanıcı tarafından paylaşılan uzak çıktıdır; canlı API sorgusu değildir.

VM çalışırken bağımsız yerel özellik hazırlığı sürüyor. [Veri setine geçiş
planı](DATASET_READINESS_2026-10-10.md), hazır parçaları, bitki örtüsü ölçeklemesini
ve olay/etiket/birleştirme kabul adımlarını ayırır. Son yerel kabul kaydında
Ocak–Nisan ve Ağustos 2018 beş ay, toplam 875.498 günlük aday satır mevcut.
2.899 hücrede ayrı 30/60 günlük pencereler kullanılıyor. [Kış–yaz incelemesi](VEGETATION_TRAINING_SUPPORT_2026-10-10.md)
Şubat kısa penceresinde %13,845 destek eksikliği gösterdi; eksikler korundu.
72 eğitim ayının beşi hazırdır. [Sınırlı kuyruk](VEGETATION_PERIOD_QUEUE_2026-10-10.md)
doğrulanmış yeniden kullanım, süre ve disk denetimleriyle hazır. Sonrasında
[otomatik toplu hazırlık](VEGETATION_TRAINING_AUTORUN_2026-10-10.md) başladı:
2018–2023 seçili, dört saatlik alt kuyruklar, toplam 24 saat sınırı ve
10 GiB disk rezervi. 10 Ekim 02:45 Türkiye saati civarındaki yerel süreç/log
ve kabul kontrolünde `running`, Mayıs 2018 hazırlanıyor. Yeni çağrıda Ocak–Nisan
doğrulanmış; Şubat yeniden kullanılmış, önceki Ağustos kabulü korunuyor.
Kalan 67 ay dahil aktif ay için iki yeni ay ölçümünden yaklaşık 24–28 saat
ek süre öngörülüyor; kaynak değişimi ve tekrar geri okuma nedeniyle garanti değil.
24 saatlik çağrı sınırı 11 Ekim 01:38 civarı; bütün aylar bitmeden durabilir.
Bütün dönem seri ve tarihsel erişim doğrulaması tamamlanmadı.

Bitki örtüsü kuyruğu sürerken [habitat kapsamı ön incelemesi](HABITAT_REVIEW_2026-10-10.md)
tamamlandı. Statik 2.899 hücrenin tamamı korundu; 15 keşif eşiği karşılaştırıldı.
2017 haritasında 10 tamamen su sınıfı hücre ve önceki 17 küçük arazi destek
işareti görüldü. 28 ilgili test ve ayrı sınıf-formülü geri okuması geçti.
Habitat uygunluğu seçilmedi, etiket üretilmedi. 02:52 Türkiye saati sorgusunda
arka plan üst süreci canlı, Mayıs hazırlanıyor; üretim kaynak hash'leri değişmedi.

[Olay gruplaması geri okuması](EVENT_GROUPING_REVIEW_2026-10-10.md) eğitimdeki
30.295 adayın dokuz eski gruplama senaryosunu ayrı kodla eşleştirdi. Uzun
zincirler, ilk anda çok hücreli gruplar ve dönem kenarları inceleme işaretleriyle
korundu; nihai olay veya etiket ilan edilmedi. 56 ilgili test geçti.
03:14 Türkiye saati süreç sorgusunda bitki örtüsü işi canlı, Mayıs kabul edilmiş
ve Haziran hazırlanıyor; önceki Ağustos dahil altı ay/1.055.236 aday satır kayıtlı.
Kalan 66 eğitim ayı aktif Haziran'ı içerir; tüm dönem tamamlanmış değildir.

## Önceki oturumun kapanış incelemesi — 9 Ekim

Kaynak uyuşmazlığına duyarlı devam oturumu kapandı. Paylaşılan Cloud Shell
instance sorgusunda VM `TERMINATED`; 9 Ekim 2026 10:39:32–18:13:05 UTC arasında
yaklaşık 7 saat 33 dakika çalışmış. Son launcher/progress normal rezerv
duruşu yerine `failed_checkpoints_retained`, `RuntimeError` bildiriyor;
başarısız ay Kasım 2022, kaydedilen son aşama `pair_publication`.
Kapatma isteği başarılı görünmüş; temel hata nedeni henüz doğrulanmadı.
İndirilen teşhis arşivinde Kasım planı ve kalan 19 tam çift ZIP'in bilimsel
geri okuması geçti; 10 görev tamamlanmamış. Kaydedilmiş disk/RAM rezerv
ihlali yok. Arşivde çocuk hata ayrıntısı bulunmadı. İndirilen salt okunur Drive
teşhisi geçti: Kasım manifesti eşleşiyor, kota yeterli; 19 yerel çift henüz
uzak payload/completion olarak yayımlanmamış. Teşhis bytes/hash'leri yerel
arşivle eşleştirildi. Geçmiş hata nedeni açık; tekrar hatada güvenli tanı
kaydeden ayrı V2 devam sürümü hazırlandı. 9 Ekim'deki yerel hazırlık sırasında
gerçek yeni oturum henüz başlamamıştı; sonraki uzak durum yukarıda ayrı kaydedildi.
Son uzak progress Aralık 2022–Kasım 2023 on iki tam ay listeliyor;
Kasım 2022 1–8 ve Aralık 2023 1–30 günleri de kayıtlı. Bu yeni oturumun
tam aylık çıktıları henüz yerelde ayrıca kabul edilmedi.

Son paylaşılan oturum sayacı 1.989 yeni çift ve 10 yeniden kullanılan çift;
250 gün bu oturumun doğrulanan gün listesinde. Önceki tam aylara ait günler
bu oturum sayacında ayrıca yer almıyor.
Uzak ilerleme kaydındaki durma zamanı 9 Ekim 2026 18:39:24 UTC
(21:39:24 Türkiye saati). Sekiz saatlik sınır, bütün veri setinin bitiş tahmini değildir.
[Çalışma ve kaynak erteleme rehberi](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md).
[Kapanma incelemesi ve dosya toplama adımları](GCP_CONTINUATION_FAILURE_2026-10-09.md).
[V2 devam adımları ve karar sınırı](GCP_SOURCE_AWARE_V2_2026-10-09.md).

31 Aralık 2023'te `SNPP:2023365.0106` ve `SNPP:2023365.1048` için gerçek
geolocation işleme sürümü uyuşmazlığı açık. Gün ertelendi; Aralık tam ay
sayılmıyor ve `full_training_complete=false` korunuyor. NASA FIRMS Type
yazışması ayrı bir konudur; inceleme bildirimi teknik teyit değildir.

## Tamamlanmış altyapı ve kanıtlar

| Alan | Durum | Sınır |
|---|---|---|
| Coğrafi altyapı | Dört il ve 2.899 hücre hazır | Model için bitki örtüsü uygunluk seçimi açık |
| Meteoroloji | 2018–2024; 2.557 gün, 7.412.743 hücre-gün denetlendi | Eğitim 6.351.709; doğrulama 1.061.034; gerçek zaman erişimi doğrulanmadı |
| Örtü ve arazi | 2.899 statik hücre; mevsim/tam grid denemeleri ve altı eğitim ayının 1.055.236 günlük bitki örtüsü adayı kabul kaydında | Kalan 66 eğitim ayı ve habitat kararı tamamlanmadı; tarihsel erişim zamanı bilinmiyor |
| FIRMS | İki sensörden 33.255 aday tespit | Bağımsız yangın sayısı veya nihai etiket değil |
| Olay ön incelemesi | 30.295 eğitim adayının dokuz gruplama grafiği geri okundu; ilk zaman/hücre/pencere ayrı denetlendi | Zincirleme ve kaynak belirsizlikleri açık; nihai olay kimliği ve etiket yok |
| Gözlem alanı | Kaynak/alan/tarama tanıları ve bulut üretim hattı mevcut | Yaklaşık geometri; negatif etiket izni yok |
| Hızlandırma | Aynı VM baz ortalamasına karşı 1,4655 kat throughput | Üç günlük deney; tüm dönem veya donanım etkisi garantisi değil |
| Model | Henüz eğitilmedi | Başarı yüzdesi veya operasyonel kullanım iddiası yok |

Birincil rapor bağlantıları [kanıt dizininde](research/EVIDENCE_REGISTER.md).
[Arazi hazırlığı ve bitki örtüsü örneği](LANDSCAPE_PREPARATION_2026-10-09.md)
yerelde tamamlandı; VM'deki yangın gözlem üretiminden bağımsızdır.
[Mevsim ve görüntü yaşı karşılaştırması](VEGETATION_WINDOW_REVIEW_2026-10-09.md)
da yerelde denetlendi. 30 ve 60 günlük ayrı aday özelliklerin iki eğitim
ayındaki günlük eşleştirme ve destek/yaş incelemesi 10 Ekim'de geçti. Bu çalışma bütün dönem
veri hazırlığı veya operasyonel kullanım onayı olarak sayılmadı.
Üretim boyunca `daily_observation_status=unknown` ve
`negative_label_permitted=false` geçerli. 2025 final testi kapalıdır.

## Sonraki aşamalar

1. Oturum sonu raporlarını ve sonuçları bağımsız geri okumayla kontrol etmek.
2. Eksik kaynakları ayrı izleyerek kalan eğitim aylarını tamamlamak.
3. Olay gruplaması, gözlem belirsizliği ve negatif etiket kuralını gerekçelendirmek.
4. Etiket/özellik/split manifestlerini ve sızıntı kontrollerini tamamlamak.
5. Temel model karşılaştırmalarına, kalibrasyona ve hata analizine geçmek.

## Başvuru ve kaynak yönetimi

2209-A başvurusunun bitirme danışmanıyla hazırlanması; başvuru metnine yaklaşık
1–2 hafta sonra başlanması planlanıyor. Şu anda başvuru yapılmış veya danışman
onayı alınmış değil. [Hazırlık planı](research/2209A_PREPARATION.md).

Free Trial dışına çıkılmaması ve kişisel ödeme oluşmaması sınırı korunuyor.
VM Stop, disk ve diğer kaynakların silindiği anlamına gelmez. Kalıcı sonuçlar
doğrulandıktan sonra [tam kaynak temizliği](GCP_FINAL_CLEANUP.md) uygulanacak.

## Önceki kayıtlar

Güncel rapor sadeleştirilirken önceki ayrıntılı kayıtlar
[tarihsel durum dosyasında](STATUS_HISTORY_2026-10-09.md) korunmuştur.
Günlük çalışma ayrıntıları [araştırma günlüğündedir](../Diary/README.md).
