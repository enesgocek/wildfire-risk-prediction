# Ücretsiz deneme için CPU kapasite sorgusu

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

6 Ekim sonraki güncelleme: Free Trial / TRY13,623 kredi durumu manuel bildirimle teyit edildi.
Tam 71 kalan ay için üretim paketi hazırlandı; ilk uzun çalışma 8 saat / Stop
olarak [güncel rehberde](GCP_PRODUCTION_RUN.md) anlatılır. VM bu hazırlık
sırasında kapalı; aşağıdaki 2 saat bilgileri önceki prova ayarlarıdır.

Güncel durum: Frankfurt'ta VM oluşturuldu; ilk gerçek GCP kaynak
kontrolü ve yerel bağımsız sonuç denetimi geçti. Mevcut 2 saat/Stop ve Free trial
sınırı korunarak [bir/iki işçi denemesi](GCP_PARALLEL_BENCHMARK.md) de tamamlandı:
aynı altı geçişte 1,886 kat hızlanma ve eş GCP sonuçları doğrulandı. Sonuçları indirdikten sonra VM'yi durdurdum; boot disk silinmedi.
Tam dönem bütçesi veya uzaktaki fatura ölçülmedi. Aşağıdaki kota/form kayıtları tarihsel denetim
izidir; us-central1 değerleri Frankfurt kotası olarak yorumlanmaz.

6 Ekim 2026'da hesabı yeniden açtım. Son Overview ekranı aktif
Free trial, kalan 13.650 TRY ve 26 Ekim bitişini gösteriyor. Kişisel ödeme
yapılmayacak; Upgrade, peşin ödeme ve kredi dışı kullanım yok.

Google Cloud üst çubuğundaki `>_` simgesiyle Cloud Shell açılır. Bunlar
Cloud Shell'in Bash terminaline yazılır, yerel PowerShell'e değil.
[Cloud Shell ücretsizdir](https://cloud.google.com/shell/pricing).

Kota bilgisi okunur; VM, disk veya ücretli kaynak oluşturulmaz:

```bash
gcloud compute project-info describe \
  --project=dogalafetonlemesistemi \
  --flatten=quotas \
  --format="table(quotas.metric,quotas.limit,quotas.usage)"

gcloud compute regions describe us-central1 \
  --project=dogalafetonlemesistemi \
  --flatten=quotas \
  --format="table(quotas.metric,quotas.limit,quotas.usage)"
```

Komut, global kota ve ilk aday bölgenin kotasını verir. Bölge seçimi henüz
kesinleşmedi. Sadece kota alanları istenir; proje metadata'sı ve kimlik
bilgileri çıktıya eklenmez. API etkinleştirme sorusu veya hata çıkarsa çıktı
incelenir; bu komutlara sessiz onay (`--quiet`) veya kaynak oluşturma eklenmez.

Okumamız gereken alanlar CPU limit/usage ve varsa CPUS_ALL_REGIONS. Regional
kota tek başına yeterli değildir; global kalan kapasite de uygun olmalıdır.
Deneme hesabında kota artırma/ücretli yükseltme varsayılmayacak.

## 6 Ekim terminal sonucu

Compute Engine API etkinleştirmesini Cloud Shell'de onayladım;
işlem ve her iki kota sorgusu başarıyla tamamlandı. Paylaşılan terminal
çıktısında önemli alanlar:

| Kapsam / metrik | Limit | Kullanım |
|---|---:|---:|
| Global CPUS_ALL_REGIONS | 32 | 0 |
| Global GPUS_ALL_REGIONS | 0 | 0 |
| us-central1 CPUS | 200 | 0 |
| us-central1 E2_CPUS | 24 | 0 |
| us-central1 N2_CPUS | 200 | 0 |
| us-central1 N2D_CPUS | 16 | 0 |
| us-central1 INSTANCES | 24 | 0 |
| us-central1 DISKS_TOTAL_GB | 4096 | 0 |
| us-central1 SSD_TOTAL_GB | 500 | 0 |
| us-central1 PREEMPTIBLE_CPUS | 0 | 0 |

200 bölgesel CPU limiti global 32 CPU sınırını kaldırmaz. E2 için görünen
kota sınırı bu bölgede 24 vCPU'dur. Önerilen 8 vCPU / 2–4 işçi denemesi
bu görünen sınırlar içinde kalır. Kota, fiziksel kaynak bulunabilirliği
veya deneme hesabının bütün hizmetlere erişimi için garanti değildir.
GPU ve Spot/preemptible seçeneği bu denemeye dahil edilmedi. API açma
işlemi VM veya disk oluşturma olarak yorumlanmadı.

Sıradaki komutlar yalnızca bu projenin bütün bölgelerdeki VM ve disk
envanterini okur; IP, metadata veya kimlik bilgisi istemez:

```bash
gcloud compute instances list \
  --project=dogalafetonlemesistemi \
  --format="table(name,zone.basename(),machineType.basename(),status)"

gcloud compute disks list \
  --project=dogalafetonlemesistemi \
  --format="table(name,zone.basename(),region.basename(),sizeGb,type.basename())"
```

Sıfır CPU kullanımı tek başına durdurulmuş VM bulunmadığı kanıtı sayılmaz.
İki list komutunun çıktısını paylaştım: hata mesajı veya kaynak
satırı olmadan terminal istemine dönüldü. Ardından doğru projedeki VM
instances ve Disks ekranları paylaşıldı: VM listesi boş, disk listesi
"No rows to display" gösteriyor. Bu proje için VM/disk envanterinin boş
olduğu iki yöntemle doğrulandı; başka hizmetlerin veya başka projelerin
envanterine ilişkin sonuç çıkarılmadı. Fiyat ve hız karşılaştırması yapılmadı.

İşlemlerin izlenebilmesi için Google Cloud web arayüzünden manuel ilerleme tercih edildi. Sonraki adımlar tıklama yolu ve amacıyla açıklanacak; terminal
zorunlu tutulmayacak. Doğru proje seçilerek Compute Engine > VM instances
ve Compute Engine > Storage > Disks listeleri kontrol edilir. Ücretli hesap
yükseltme yapılmadan, makine yapılandırması ve maliyet değerlendirmesi
kaynak oluşturma adımından önce tamamlanır.

Sıradaki adım Create instance formunda aday makinenin bölgesel fiyatını
ve ayarlarını incelemek; formu açmak kaynak oluşturma değildir. İlk aday
e2-standard-8 (8 vCPU, 32 GiB RAM); 4 vCPU daha küçük deneme ve 16 vCPU
ölçüm sonrası büyütme seçenekleri olarak açıklanır. Önerilen kapsam:
kısa CPU hız karşılaştırması, 2–4 ayrı işçi,
önceden belirlenmiş azami süre ve bitişte kaynak temizliği. Henüz kaynak veya
yürütme komutu hazırlanıp başlatılmadı. Hız/maliyet ölçülmeden bütün dönemin
krediye sığacağı veya bir ayın bir saate ineceği iddia edilmiyor.

## Frankfurt yapılandırma incelemesi

Formda europe-west3 (Frankfurt), Zone Any, wildfire-cpu-pilot,
e2-standard-8 (8 vCPU / 4 core / 32 GB RAM), Standard model seçtim.
Ekrandaki tahmin 253,30 USD/ay, yaklaşık 0,35 USD/saat; bunun 252,10 USD'si
makine, 1,20 USD'si 10 GB balanced disk için. Bunlar form tahmini, gerçek
harcama veya krediye uygulanmış nihai tutar değildir. Belçika tahmini
paylaşılmadı; fiyat bakımından en ucuz Avrupa bölgesi olduğu iddia edilmedi.

Gönderilen üç görüntü yalnızca machine configuration bölümünü gösteriyor.
Yan menü Debian 13, snapshot schedules ve Install Ops Agent yazıyor;
seçeneklerin ayrıntıları görülmeden kapalı/etkin olduğu kesinleştirilmedi.
Frankfurt bölgesel CPU/disk kotası henüz okunmadı; Iowa kotası taşınmaz.

İlk kısa deneme için önerilen düzeltmeler:

- OS and storage > Change: standart Ubuntu 24.04 LTS x86/64, 30 GB
  Balanced Persistent Disk. Python 3.12 mevcut paket kilidiyle kullanılacak;
  Ubuntu Pro/Marketplace/lisanslı accelerator imajı seçilmeyecek.
- VM provisioning model advanced settings: Set a time limit for the VM,
  By hours = 2, On VM termination = Stop. Bu öneri kurulum ve küçük hız
  denemesi için; bütün eğitim arşivi veya bütün ay için süre iddiası değil.
- Otomatik snapshot schedule ve Ops Agent kurulumu ilk deneme için
  seçilmeyecek. Çıktı günlükleri uygulama tarafından saklanacak.
- Yeni sekmede IAM & Admin > Quotas & System Limits üzerinden Compute
  Engine / europe-west3 / E2 CPU kalan kota >= 8 doğrulanacak; disk ve
  instance limitleri de gözden geçirilecek. Kota artırma istenmeyecek.
- Yeni disk seçimi sonrası fiyat ve süre ayarlarının ekranları görülmeden
  Create adımı tamamlanmış sayılmayacak. Aktif Free trial ve Upgrade
  yasağı korunuyor.

İki saat için 0,70 USD yalnızca görünen yuvarlanmış saatlik tahminin kaba
çarpımıdır; toplam harcama garantisi değildir. IP/ağ, log, saklama ve
otomatik durdurma sonrasında kalan disk maliyeti ayrıca değerlendirilmeli.
Stop diski silmez. Sonuçların kalıcı kopyası doğrulanmadan VM/disk silinmez;
deneme kapanışında disk temizliği ayrıca yapılır.

Mevcut Colab kodu sabit /content ve Drive yolu kontrol ediyor. GCP işçisi
ve kalıcı sonuç aktarımı ayrıca hazırlanmalı; VM oluşturmak bu kodu
otomatik çalıştırmaz. Tamamlanan Temmuz verisini üretim işi olarak yeniden
indirmek yerine küçük, doğrulanmış kaynaklarla karşılaştırma yapılacak.

## 6 Ekim gün sonu: oluşturma ertelendi

Son ekran Set a time limit işaretli, By hours = 2, On VM termination = Stop
ayarlarını doğruluyor. Gracefully shut down işaretli değil; Automatic restart
halen On. Kısa deneme için Off önerildi, uygulanmış sayılmadı. Yan menü
Debian 13 ve fiyat tablosu 10 GB disk göstermeye devam ediyor; Ubuntu/30 GB
değişikliği henüz doğrulanmadı. Snapshot/Ops Agent, Frankfurt kotası ve
nihai fiyat kontrolü açık.

Uyku nedeniyle oluşturmayı sonraki sabah oturumuna bıraktım.
Create'e basılmadı; VM/disk veya bulut işi başlatılmadı. Formdan çıkılırsa
ayarlar yeniden girilebilir; otomatik zamanlayıcı veya gece işi kurulmadı.
Sonraki oturum: açık ayarları tamamlamak, GCP işçisi/kalıcı sonuç yolunu
hazırlamak, Free trial durumunu ve kısa denemenin maliyetini doğrulamak;
ardından oluşturma ve küçük hız karşılaştırması. Tam dönem başlatılmayacak.

Kapanış push'undan sonra aynı gece devam edilmesi kararlaştırıldı. Sabaha
erteleme tercihi geri alındı; form/Frankfurt kota ve GCP yürütme hazırlığı
tamamlanmadığı için son görüntü oluşturma onayı olarak kabul edilmedi.
Create'e henüz basmadığımı, formun açık olduğunu doğruladım.
VM henüz oluşturulmadı. Sıradaki manuel adım OS/disk ayarlarını tamamlamak;
Frankfurt kotası ve GCP iş paketi henüz açık. Diskin Stop sonrasında
kaldığı ve kredi tüketmeye devam edebildiği korunuyor.

Yeni OS and storage ekranında 30 GB Balanced Persistent Disk ve Free
lisans doğrulandı. Ancak Ubuntu 26.04 LTS seçilmiş; mevcut Python
3.12 kilidi için istenen Ubuntu 24.04 LTS henüz seçilmedi. Snapshot schedule
alanında default-schedule-1 bağlı olduğu açıkça görülüyor; formdaki bu
seçim kaldırılmalı. Yeni tahmin 255,70 USD/ay (makine 252,10 + disk 3,60),
yaklaşık 0,35 USD/saat. Snapshot/log/ağ gibi değişken kalemler dahil
nihai harcama garantisi değildir.

Diğer form kontrolleri: Observability > Install Ops Agent kapalı; Networking
HTTP/HTTPS ingress kutuları boş (NASA'ya dışarı HTTPS indirmesi için gelen
web trafiği açılmaz); Machine configuration süre = 2 saat, Stop ve kısa
deneme için Automatic restart = Off. Networking/Security/Advanced
ayrıntıları henüz görülmedi; varsayılanların değiştirilmiş olup olmadığı
kanıtsız kabul edilmez. Frankfurt kotası ve GCP yürütme paketi açık.

Son üç ekran Ubuntu 24.04, 30 GB Balanced disk, No backups / No schedule,
replication kutuları boş, 2 saat/Stop ve Automatic restart Off gösteriyor.
Kaydedilen Equivalent code bu ayarları doğruluyor: europe-west3-c,
Standard, pd-balanced, disk auto-delete=yes (VM silinince), yeniden başlama
kapalı ve 7200s süre. Startup metadata, HTTP/HTTPS tag veya snapshot policy
talimatı yok; Ops Agent kurulum talimatı da yok. Tek default subnet arayüzü,
Premium tier ve mevcut varsayılan service account/scope'lar seçilmiş. Bu
hesap adı parola/token değildir; depoya kimlik bilgisi yazılmadı.

Frankfurt CPU/disk/instance kotası henüz paylaşılmadı. İlk GCP taşınabilirlik
paketi hazırlanıp mevcut yerel kaynaklarla prova edildi; mevcut 195 MB
tek geçişi kullanır, paralel iş veya tam dönem kuyruğu henüz hazır değildir.
[Paket ve kullanım](GCP_PORTABILITY_PILOT.md). VM henüz oluşturulmadı.

GCP ilk paketinin gerçek yerel kaynak provası, bağımsız geri okuması ve
356 test/121 dosya kod-biçim kontrolü tamamlandı. VM oluşturulması kararlaştırıldı. Form ve yürütme ön hazırlığı uygun; Frankfurt kotası ayrı
okunmamış olarak açıkça tutuluyor. Son tercih, bölgesel kota ve kaynak
uygunluğunun oluşturma isteğinde Google tarafından denetlenmesiyle
ilerlemek. Kota/kapasite hatasında yükseltme veya daha büyük kaynak seçimi
yapılmayacak; hata ve VM/disk durumu incelenecek. Create başarıyla
tamamlanmış sayılmadı; Running durumu ve erişim henüz doğrulanmayı bekliyor.
Deneme yalnızca tek geçiştir; 71 aylık üretim kuyruğu henüz hazır değildir.

wildfire-cpu-pilot SSH terminalini paylaştım; VM oluşturuldu ve
erişim sağlandı. Karşılama Ubuntu 24.04.5 LTS / x86_64, yaklaşık 28 GB
dosya sistemi ve düşük başlangıç RAM kullanımını gösteriyor. Google'ın
oluşturma işlemi bu VM için kota/kaynak kontrolünü geçti; Frankfurt toplam
kota/usage tablosu ayrıca okunmuş sayılmıyor. Terminaldeki 00:58:32 UTC
6 Ekim bilgisi Türkiye saatinde 03:58:32'dir; VM oluşturma anı veya kesin
otomatik durma zamanı bu karşılama damgasından çıkarılmadı. Henüz pilot
paket kurma/işleme sonucu yok. Sonraki aşamada hazırlanan ZIP SSH tarayıcısından yüklenecek; Ubuntu venv hazırlığı ve SHA doğrulaması uygulanacak.

Resmî ayar kaynakları:
[süre sınırı](https://docs.cloud.google.com/compute/docs/instances/limit-vm-runtime),
[Linux ve boot disk formu](https://docs.cloud.google.com/compute/docs/create-linux-vm-instance),
[Ubuntu 24.04 Python 3.12 paketi](https://packages.ubuntu.com/en/noble/python3.12),
[kota arayüzü](https://docs.cloud.google.com/docs/quotas/view-manage).

Kaynaklar:
[global proje kotası komutu](https://docs.cloud.google.com/sdk/gcloud/reference/compute/project-info/describe),
[bölgesel kota komutu](https://docs.cloud.google.com/sdk/gcloud/reference/compute/regions/describe),
[kotalar ve kaynak bulunabilirliği](https://docs.cloud.google.com/compute/resource-usage),
[VM listesi](https://docs.cloud.google.com/sdk/gcloud/reference/compute/instances/list),
[disk listesi](https://docs.cloud.google.com/sdk/gcloud/reference/compute/disks/list).
