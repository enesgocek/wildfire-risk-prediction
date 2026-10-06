# Uzun GCP üretimine geçiş — 6 Ekim 2026

**Güncel karar:** Kullanıcı örneklem yerine bütün eğitim aylarının üretimine
geçmemizi istedi. Kalan 71 ay / 18.441 nominal çift için yeni üretim paketi,
Drive kayıtları, günlük geometrik birleşim ve kesintiden devam mekanizması
hazırlandı. Başlatma için [güncel rehber](GCP_PRODUCTION_RUN.md) kullanılır.
İlk uzun çalışma 8 saat / Stop; dört işçi hızlanması ve gerçek Stop/Start
devamı henüz VM'de ölçülmedi. Kullanıcı Free Trial / TRY13,623 bildirdi.
Yeni VM üretimi bu notun yazıldığı sırada başlamadı.

**Aşağıdaki bölümler önceki hazırlık aşamalarının tarihsel kaydıdır.**
Eski “seçilmedi”, “adapter açık” ve test sayısı ifadeleri o aşamaya aittir;
güncel çalıştırma adımlarının yerine kullanılmaz.

Güncel kapı sonucu: V2 gerçek Drive yazma/geri okuma ve ayrı süreç restore
kontrolünü geçtiğini bildirdi; alınan JSON ve hazırlanmış ZIP/manifest/ürün
yerelde doğrulandı. 3,98 MB ürün, 5+1 bilimsel geri okuma, PID 1327/1336,
kesinti true. Kullanıcı sonuçtan sonra VM Stop bildirdi. Yerel bağımsız
remote payload indirmesi, VM Stop/Start resume ve SSH kopması sınanmadı.
Yeni üretim ayı/ham veri yok. Önceki hazırlık notları tarihsel aşamaları
anlatır; sarmalayıcı sonradan hazırlandı. Güncel kalan büyük iş canlı üretim
başlatma, ilk kalıcı kaydı doğrulama ve gerçek hız/tüketim ölçümüdür.
[Gerçek sonuç ve sınırlar](GCP_DRIVE_PROOF_RESULTS.md).

Mevcut iki saat, VM için seçilmiş max-run-duration/Stop sınırıdır. İki saat
dolduğunda VM durur. Bu, bütün proje veya tarayıcı oturumu için zorunlu bir
üst sınır değildir. Süre değiştirilebilir; duration sonraki Start anında
yeniden hesaplanır, reboot/reset süreyi sıfırlamaz. Üretim işçisi Google'ın
gerçek terminationTimestamp alanını kullanmalı; boot yaşından son zamanı
tahmin etmeyi üretim yöntemi saymıyoruz.
[Google süre rehberi](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime).

## Denetimde görülen açık işler

1. GCP benchmark dolu çalışma dizinini ve sonuç yeniden kullanımını reddeder;
   doğrudan üretim kuyruğu olarak kullanılamaz. Donmuş paketi değiştirmedik.
2. Mevcut aylık Colab kodu Temmuz 2023 ve /content/Drive yollarına bağlıdır;
   GCP'ye olduğu gibi taşınmış sayılmaz. Günlük spatial union ve belirsiz
   gözlem politikasını koruyan yeni sarmalayıcı gerekir.
3. Benchmark checkpoint'i yalnızca boot diskindedir. VM dışı kayıt adapter'ı,
   yazma yetkisi ve başka çalışma dizininde gerçek geri yükleme açık.
4. Mevcut foreground SSH işi bağlantıdan bağımsız çalıştırma kanıtı değildir.
   Yeni launcher gizli giriş sonrası ayrılmış süreç/log üzerinden çalışmalı;
   parola/token komut satırı veya günlük dosyasına kaydedilmemeli.
5. Sadece denetimden geçmiş bütün günün beklenen çiftleriyle günlük birleşim
   yapılmalı. Tamamlanmamış gün final/negatif etiket olarak dışa verilmez.

## Hazırlanan çekirdek ve ikinci denetim

`scripts/cloud/verified_job_store.py`: kaynak/işçi/manifest SHA bağlı kayıt
protokolü. Önce ZIP üye/CRC ve bilimsel denetim, ardından kayıt, kaydedilen
byte'ları yeni dizine indirip tekrar aynı bilimsel denetim; tamamlanma kaydı
en son. Bozuk veya eksik kayıt işi bitmiş saydırmaz. Kimliği değişmiş veya
negatif etikete çevrilmiş kayıt reddedilir. Aynı tamamlanmış görevin üstüne
yazılmaz; yeni görev için en kötü çocuk zamanı ve kaydetme rezervi birlikte
kalan süreye sığmalı. Varsayılan 900+180 saniye rezervi gerçek sağlayıcı
upload/retry ölçümüyle sınanacak; süre tahmini olarak otomatik güvence değildir.

RehearsalFileStore sadece iki yerel dizin arasında prova yapar; VM dışı
kalıcılık veya dağıtılmış kilit sağlamış sayılmaz. Tek ebeveyn yazmaları
koordine eder. Depo byte bütçesi para/fatura sınırı değildir. Hata durumunda
orphan payload korunur ve tamamlanmış sayılmaz; bozuk yayımlanmış kayıt
sessizce silinip yeniden hesaplanmaz, inceleme için durur. GCS adapter'ı
koşullu create/generation, Drive adapter'ı doğrulanmış yeni sürüm ve son
tamamlanma kaydı semantiğini ayrıca sağlamalı.

21 yeni koruyucu test kesinti, bozuk geri okuma, yanlış manifest/işçi/politika,
depo sınırı, zararlı üye/yol ve geçersiz/yetersiz zaman rezervini geçti.
`scripts/cloud/rehearse_gcp_resume.py` ile gerçek alınmış GCP ürününün
SNPP:2023197.0018 çifti (3.982.961 bayt) kullanıldı: tamamlanma öncesi kesinti,
yeni store nesnesi ve yeni geçici dizinler üzerinden altı bilimsel geri okuma
başarılı. Eski GCP ZIP'i değişmedi. Ham yeniden işleme/NASA veya VM/Drive/GCS
erişimi yok. Rapor: `outputs/gcp_resume_rehearsal/report.json`.

Tam küme **407 test**, Ruff kod ve 132 Python dosyasının biçimi başarılı.
Bu testler kusursuzluk/fiziksel ayak izi/tam dönem kapasite garantisi değildir;
gerçek bulut kayıt ve restart kanıtı halen bir sonraki kapıdır.

## Önerilen ilerleme ve seçenekler

| Aşama / süre | Amaç | Uygulandı mı? |
|---|---|---|
| Mevcut 2 saat sınırı | Küçük sonuçla gerçek bulut kayıt/geri yükleme kanıtı; sonra kısa yeni üretim örneği | VM sınırı mevcut; yeni üretim başlamadı |
| 6 saat, önerilen sonraki seçenek | Kayıt ve tam günlük iş ölçümü sonrası daha büyük gruplar | Kullanıcı seçimi bekleniyor, ayar değişmedi |
| 8 saat | Ölçülen grup süresi 6 saate sığmıyorsa daha uzun çalışma | Seçilmedi; otomatik kredi/süre taahhüdü yok |

Sınırda yeni çift başlatmak yerine kayıt rezervi bırakılır. Tamamlananlar
yeniden hesaplanmaz; yarım çift tamamlanmış sayılmaz. Tarayıcıdan ayrılan
işçi ve otomatik VM Stop ayrı korumalardır. Sessiz sonsuz yeniden başlama,
limitsiz retry veya bütün yılları ölçüm olmadan başlatma yok.

İlk bulut kayıt kanıtında mevcut doğrulanmış küçük ürün kullanılarak yeni ham
indirme yapılması gerekmez. Sonraki **öneri**, 1–3 Ağustos 2023: katalogda
26 çift/52 dosya, yaklaşık 4,76 GB yalnızca VM'ye. İki işçili altı-geçiş
hızından saf çift evresi yaklaşık 16,56 dakika çıkar; günlük birleşim,
uzak kayıt, kurulum/retry dahil değil ve çalışma süresi garantisi değil.
Bu yeni kapsam henüz kullanıcıya yürütme için verilmedi/onaylanmış sayılmadı.

Ağustos ayı seçeneği 278 çift, yaklaşık 50,83 GB toplam akış; saf çift evresi
aynı kaba hızla 2,95 saat. Ayın tamamının bu sürede biteceği söylenmiyor.
Günlük birleşim/kalıcı kayıt/yeniden başlatma kanıtından önce 6 saate sığma
veya bütün yılların krediye sığması sonucu çıkarılmayacak.

`scripts/cloud/plan_gcp_production.py` bu iki envanteri çevrimdışı kontrol etti:
72 eğitim ayından tamamlanmış Temmuz 2023 dışındaki 71 ay sırada. 283
katalog eşleşmemiş kaydı korunuyor; hiçbiri negatif sayılmadı. 2024 doğrulama
ve kapalı 2025 final alanına yeni ham sorgu yapılmadı. Rapor:
`outputs/reports/observation_coverage/gcp_production_readiness_plan.json`,
durum offline_design_not_production_ready.

## Kalıcı depo ve kredi

6 Ekim sonraki hazırlık: önceki Drive tercihiyle doğrudan Drive API adapter'ı,
yerel Desktop OAuth bağlantısı ve ayrılmış/bounded launcher hazırlandı.
`outputs/gcp_drive_proof/wildfire_gcp_drive_proof.zip` 6,86 MB; ilk çalışma
eski doğrulanmış 3,98 MB ürünü kaydeder, ham indirme yapmaz. Drive-file izni,
ayrı uygulama klasörü, bozuk/aynı isimli kayıt reddi, aynı generated-ID ile
belirsiz create kontrolü, tamamlanma öncesi kesinti ve ayrı restore süreci
vardır. Dosya/list/get hataları missing sayılmaz; para/dağıtılmış kilit
garantisi değildir. Google OAuth Testing token ömrü 7 gün; yenileme aynı
kalıcı klasörü korur. Yeni bağlanma VM kapalıyken Windows'ta yapılır.
[Hazır paket ve sıralı adımlar](GCP_DRIVE_PROOF.md).

Yerelde iki ayrı süreçte gerçek ürünle altı bilimsel denetim geçti.
Gerçek Drive yazma/okuma ve Linux supervisor/SSH kopması hâlâ yürütülmedi.
Uzun üretim ay kuyruğu/günlük union sarmalayıcısı bu küçük paketin kapsamı
değildir. VM yeniden başlatılmadı; süre/scope/disk ayarı değiştirilmedi.

Önceki Google Drive tercihi kayıtta korunuyor. GCP için Drive ile devam
veya deneme kredisi içinde Cloud Storage kullanma seçeneği kullanıcıya
soruldu; bu turda yanıt gelmedi. Sağlayıcı seçimi gerektirmeyen çekirdek
tamamlandı; bucket/OAuth bağlantısı veya ücretli kaynak oluşturulmadı.
Drive'ın 1,5 TB alanı biliniyor; GCP VM'de Drive mount olmuş sayılmıyor.
Cloud Storage seçilirse mevcut VM service-account scope'ları storage.read_only;
yazma için doğru scope ve yalnızca hedef depo izinleri ayrıca incelenmeli.
Service-account anahtar JSON'u/parola sohbet veya repoya konmaz.

Free Trial statüsü ve Upgrade yasağı korunur. Normal alerts-only bütçe
harcamayı durdurmaz; Google bazı hizmetler için ayrı spend-cap bütçeleri
sunar, bu projede etkin/uygun oldukları doğrulanmadı. Süre, kapsam, retry ve
byte sınırları ayrı kontrollerdir. Deneme statüsünde kullanıcı faturalandırılmaz;
ücretli yükseltme sonrası kredi dışı kullanım ödeme doğurabilir. Statü ve
güncel kredi büyük grup öncesi kontrol edilir. Kredi bitişi 26 Ekim olarak
paylaşıldı; GCP sonuçları erişim kapanmadan Drive/yerel kalıcı kopyaya
doğrulanarak aktarılmalı. Sunucu durmuş olarak bildirildi; boot disk silinmedi.

[Deneme koşulları](https://docs.cloud.google.com/free/docs/free-cloud-features),
[normal bütçe uyarılarının sınırı](https://docs.cloud.google.com/billing/docs/how-to/budgets),
[Storage yükleme/yazma izinleri](https://docs.cloud.google.com/storage/docs/uploading-objects).
