# İki sensörlü bir günün Colab denemesi

> Dönemsel uygulama kaydı. Kurulum, maliyet ve bekleyen iş ifadeleri belgenin
> ilgili çalışma aşamasına aittir. Güncel durum [STATUS.md](STATUS.md), mevcut
> üretim yolu [devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md) izlenir.

Amaç: bütün ham arşivi saklamak yerine bir dosya çiftini indirip işlemek,
doğrulanmış küçük sonuçları saklamak ve geçici ham kopyayı silmek. Başarılı tek geçiş denemesinden sonra bu genişlemeyle devam etmeyi planladım.
Ücretsiz CPU kullanılır; tam dönem veya ücretli kaynak başlatılmaz.

Deneme 14 Ocak 2019 eğitim gününe sabit: mevcut eğitim katalog sorgusunda
5 S-NPP ve 3 NOAA-20 dosya parçası (granule), toplam 16 kaynak dosyası. Bu liste dört ilin
katalog arama bölgesine dayalıdır; kesin fiziksel kesişim veya tam gün gözlem
alanı değildir. Gece ve gündüz geçişleri birlikte korunur. Kaynak boyutları
**1.460.346.055 bayt**, en büyük çift **187.346.392 bayt**. Toplam indirme
trafiği yaklaşık 1,46 GB; aynı anda sekiz çift biriktirilmez. Ortam kurulumu,
Python belleği ve çalışma dosyaları için ayrıca alan gerekir.

5 Ekim terim düzeltmesi: bu belgedeki “sekiz geçiş”, sekiz işlenen granule
anlamındadır. Doğal OrbitNumber denetiminde yedi farklı sensör/yörünge kaydı
bulundu; S-NPP 10:18/10:24 aynı yörüngenin parçaları. Sekiz bağımsız yeniden
gözlem iddiası yok. [Denetim](OBSERVATION_TIMING_2026-10-05.md).

## Çalıştırma

Yeni dosyalar outputs/cloud_day dizininde:

1. `l2_day_isolated.ipynb` dosyasını Colab'a yükle. Önceki pilotun ayrı venv
   kurulumu kullanılabilir; Python 3.12 ve ücretsiz CPU ortamı gerekir.
2. İlk kod hücresi ayrı ortamı ve HDF5 sürücüsünü doğrular. Sistem paketlerini
   değiştirmez.
3. Paket yükleme hücresinde **l2_day_bundle.zip** seç. İlk çalıştırmada yalnızca
   bu dosya yeterli. Kesinti sonrası yeni oturuma dönüyorsan aynı paketle birlikte
   daha önce indirdiğin **l2_day_results.zip** dosyasını da seçebilirsin.
4. Giriş hücresinde Earthdata kullanıcı adı ve parolanı gizli isteme yaz.
   İlk Python süreci bir geçişi tamamlayıp durur; ikinci süreç ilk sonucu tekrar
   doğrular, indirmeyi/hesabı atlayıp kalan geçişleri işler. Günlük sonuç durumu
   `passed_all_eight_references` olmalı.
5. Son hücre **l2_day_results.zip** indirir. Projede outputs/cloud_day/received
   klasörüne koy veya İndirilenler'de bırakıp haber ver; bağımsız kontrol yapılır.
   Bu ZIP küçük sonuçları ve devam kayıtlarını içerir; ham uydu veya parola içermez.

İşleme sırasında hata olursa varsa tamamlanan kayıtların ZIP'ini son hücreyle
indir ve sakla. Kod her doğrulanmış çiftten sonra ZIP'i yeniden yazar. Çalışma
zamanı tamamen kapanmadan ZIP indirilmemişse Colab geçici diskindeki ilerleme
kaybolabilir; bu pilot henüz Drive'a otomatik kalıcı kayıt yapmaz.
İndirme sırasında kesilen geçici dosya aynı oturumda sonraki çalıştırmada
yeniden alınır; doğrulanmış dosyalar korunur. Dosya veya kaynak özetleri
değişmişse tamamlanmış checkpoint sessizce kullanılmaz; işlem durur.

## Denetim ve sınırlar

Her çiftte boyut/SHA, CMR kimliği, gerçek geolocation InputPointer, native
HDF5 yönü ve mevcut bütün seyrek termal koordinatlar denetlenir. Tam QA JSON'u
ve 2.899 hücrenin bütün CSV sütunları yerel referanslarla karşılaştırılır.
Sıfır merkezli hücreler korunur; günlük gözlem unknown, negatif izin false.
Çocuk süreç bitince Linux ru_maxrss ile tepe RSS belleği kaydedilir. Disk
boşluğu 0,2 saniyede bir örneklenir; çok kısa disk sıçramaları kaçabilir ve
başka süreçlerin disk kullanımı ölçümü etkileyebilir. Bu RAM ölçümü Colab'ın
tüm ortamının eşzamanlı toplam belleği değildir.

Ham çift yalnızca karşılaştırma, çıktı özetleri, checkpoint ve sonuç ZIP'i
başarılı yazıldıktan sonra silinir. Sadece Colab denemesinin belirtilen iki
geçici kaynak dosyası temizlenir; mevcut proje örnekleri silinmez. Yerel prova
orijinal kaynaklara ek ham alan tüketmeyen bağlantılarla çalışır ve silme yapmaz.

Bu sonuçlar tanı sayımlarıdır; nihai eğitim girdilerinin yerine geçmez. Fiziksel
ayak izi ve günlük gözlem yöntemi kesinleşince gereken alan/zaman çıktıları da
bulutta hesaplanıp saklanmalıdır. Yöntem değişirse kaynak manifestiyle NASA'dan
aynı dosyalar yeniden alınabilir. NASA Type teyidi ve son etiket kuralı açık.
Dolayısıyla bu aşamada bilimsel yöntemi küçülterek disk tasarrufu seçilmedi.

Tam dönem kararı için gerçek Colab sonuçlarındaki süre/RAM/disk, çıktı boyutu
ve devam davranışı incelenecek. Sonra kalıcı bulut çıktı saklama ve partilerin
boyutu için seçenekler sunulacak. Ücretsiz oturumların sürekliliği garanti değil:
[Colab sınırları](https://research.google.com/colaboratory/faq.html).

Bağımsız denetim:

```powershell
.\.venv\Scripts\python.exe scripts/cloud/verify_l2_day_results.py outputs/cloud_day/received/l2_day_results.zip
```

Başarısız, eksik, değiştirilmiş veya yerel prova sonucu bulut başarısı olarak
kabul edilmez. Rapor: outputs/reports/observation_coverage/colab_day_received_verification.json.

## Hazırlık kontrolü — 4 Ekim 2026

Sekiz geçiş mevcut kaynaklarla yerelde yeniden işlendi. Birinci süreç bir
geçişte durdu; ikinci süreç bir checkpoint'i yeniden kullanıp kalan yediyi
tamamladı. Bütün QA JSON'ları ve CSV sütunları referanslarla eşleşti. Sonuç
ZIP'i 197.951 bayt. Ayrı bir oturum dizinine ZIP geri yüklendi; sekiz geçişin
tamamı yeniden hesaplanmadan doğrulanıp atlandı. Orijinal 16 dosyanın SHA'ları
korundu; yeni ham uydu indirilmedi.

18 koruyucu test eklendi; tam kümede 210 test başarılı. Yerel prova Windows'ta
çalıştığı için Linux RSS ölçümü mevcut değil ve raporda null. 58,6 saniyelik
yerel hesap süresi bulut indirme süresi sayılmaz; ham dosyalar zaten yereldeydi.
Hazırlık aşamasında gerçek Colab günü ve bulut RAM/disk ölçümü bekleniyordu;
tamamlanan bulut çalışmasının sonucu aşağıda.
Yerel denetim raporu:
outputs/reports/observation_coverage/colab_day_local_rehearsal.json.

## Gerçek Colab günü doğrulandı — 4 Ekim 2026

İndirdiğim ZIP proje içine özgün dosya değiştirilmeden kopyalandı:
outputs/cloud_day/received/l2_day_results_2e3dc9f61a8fa41f.zip.
Dosya 197.607 bayt; SHA256
2e3dc9f61a8fa41f072e4c1f183a2ee774b0e1adb046cb0e90b13e6aa87250e2.
25 beklenen dosyanın CRC'si, manifest/kod/kaynak özetleri, sekiz tam QA raporu
ve 8 × 2.899 = 23.192 hücre-geçiş satırının bütün sütunları denetlendi.
Her sütun yerel referansla tam eşleşti. İlk geçiş checkpoint ile atlandı;
ikinci süreç kalan yediyi işledi. Python 3.12.13 ve yedi paket sürümü doğru.

| Ölçüm | Gerçek bulut sonucu |
| --- | --- |
| Başarılı kaynak dosyası indirmeleri | 1.460.346.055 bayt / yaklaşık 1,46 GB |
| Geçişlerin indirme ve denetim süreleri toplamı | 165,94 saniye |
| En yüksek çocuk süreç RSS belleği | 543.686.656 bayt / yaklaşık 544 MB |
| En yüksek örneklenen geçici disk artışı | 187.617.280 bayt / yaklaşık 188 MB |
| Yerel bilgisayara indirilen sonuç ZIP'i | 197.607 bayt / yaklaşık 198 KB |

Süre ortam kurulumunu ve checkpoint/ZIP yazımının tamamını kapsamaz. Bellek
çocuk sürecin tepe RSS'sidir; bütün Colab ortamının toplam belleği değildir.
Disk 0,2 saniyelik örneklemedir; tüm dönem için kesin üst sınır değildir.

Ek bağımsız geri okuma bütün hücre anahtarlarını özgün grid ile, satır başına
sınıf toplamlarını piksel sayısıyla, sütun toplamlarını QA/JSON ile ve 16 dosyanın
indirilen toplamını kaynak baytlarıyla karşılaştırdı. Sıfır merkez içeren geçişin
2.899 satırı da korunmuş. Mevcut 16 yerel ham dosyanın SHA'ları değişmedi.
18 bulut günü koruyucu testi yeniden geçti. Günlük durum unknown, negatif
etiket izni false; bu günün pilotunda termal piksel görülmemesi negatif etiket
üretilmesi anlamına gelmez.

Bağımsız raporlar:
outputs/reports/observation_coverage/colab_day_received_verification.json ve
colab_day_grid_reconciliation.json. Ek geri okuma betiği yerel/ignored
outputs/verification/audit_colab_day_readback.py altında.

Bu örnekte bir çiftlik geçici disk stratejisi ve sonuçların yeniden üretimi
doğrulandı. Tam dönem başlamadı. Sırada kalıcı çıktı saklama/kesintiden kurtarma
planı ve fiziksel gözlem alanı yönteminin kalan kontrolleri var. Nihai yöntem
için gereken alan/zaman çıktıları hazırlanmadan tanı CSV'si final veri seti
sayılmaz.
