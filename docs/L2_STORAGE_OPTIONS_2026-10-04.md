# Uydu verisini sınırlı diskle işleme seçenekleri — 4 Ekim 2026

## Depolama sınırı ve kapsam kararı

67 GB boş alan bildirdim; en az 40 GB boş alanın korunmasını planladım.
Yeni indirme, geçici çalışma dosyaları ve çıktılar için toplam ek alan üst
sınırı **27 GB**. İnternet hızlı; bulutta işleme seçeneği de değerlendirilecek.
Bu sınır toplam internet trafiğiyle aynı değildir. Kapsam, bilimsel yöntem ve hizmet/maliyet kararları alternatifler karşılaştırılarak alınacaktır.
Şehir/yıl/sensör azaltılması, veri ürünü değiştirilmesi veya ücretli hizmet
kullanımı seçilmedi. Büyük indirme ve bulut işi başlatılmadı.

## Ölçülen hacim

2018–2023 eğitim sorgularının 40 metadata sayfasında 37.705 kayıt var.
Katalog boyutları toplamı **3,170596 TiB / 3,486107 TB**; bu tam dosyaları
alma senaryosudur, gerekli bölgesel çıktının boyutu değildir. Birim yorumu
mevcut 18 yerel dosyanın gerçek bayt sayılarıyla kontrol edildi. Metadata
önbelleği yaklaşık 5,97 MB. Konum dosyaları toplam hacmin yaklaşık %99'u.
En büyük katalog dosyası yaklaşık 198 MB; bu RAM/geçici çıktı gereksinimini
tek başına göstermez. Nihai eğitim tablosunun disk boyutu henüz ölçülmedi.

Nominal zaman eşlemesi 18.711 aday çift verdi: S-NPP 9.691, NOAA-20 9.020.
NOAA-20'de 2 yangın/280 konum ve S-NPP'de 1 konum kaydı eşsiz kaldı.
Bunlar sorgu içindeki eşleşmeme durumları; kaynak ürünün gerçekten eksik
olduğunu kanıtlamaz. Gerçek geolocation InputPointer eşlemesi ayrıca gerekir.
Hiçbiri otomatik negatif yangın etiketi değildir.

## Seçenekler

| Yol | Yerel disk ve maliyet | Kapsam ve sınırlama |
| --- | --- | --- |
| Ücretsiz Colab'da küçük partiler | Bilgisayara yalnızca doğrulanmış çıktılar; kalıcı bulut sonuçları için kota gerekir | Şehir/yıl azaltmak gerekmez. Oturum kaynakları garanti değil; kalıcı ilerleme kaydı ve yeniden başlatma gerekir. |
| Bilgisayarda küçük partiler | Geçici alanı sınırlayabiliriz; ücretli bulut gerekmez | Kapsam korunabilir; toplam indirme trafiği azalmayabilir. Sonuç büyüklüğü ve RAM küçük örnekte ölçülmeli. |
| Ücretli bulut hesaplama | Ham veri bilgisayara gelmez; hesaplama/depolama maliyeti var | Uzun işler için daha fazla kontrol; fiyat ve hesap açma kararı proje yürütücüsüne ait. Önce pilot maliyet ölçümü gerekir. |

Ham arşivi başka bir bulut diske tamamen kopyalamak tek başına verimli çözüm
değildir. Tercih edilecek yol, kaynak dosyalarını geçici veya uzaktan okuyup
hesaplamak ve gerekli bölgesel sonuçları kalıcı saklamaktır. Disk bütçesine
sığma ya da aynı bilimsel sonucu üretme henüz vaat edilmez; pilotla ölçülür.

## Hizmet kontrolü

[Harmony kapasite API'si](https://harmony.earthdata.nasa.gov/docs), dört exact
collection ID için HTTP 200 döndü: C2734202914-LPCLOUD, C2105092163-LAADS,
C2734197957-LPCLOUD, C2105086226-LAADS. Dördünde services boş ve bölge/değişken
kırpma false. Dolayısıyla bu ürünler için Harmony kırpma çözümü doğrulanmadı.
Yerel kanıt: outputs/reports/observation_coverage/l2_harmony_capabilities.json.

CMR konum kayıtları OPeNDAP bağlantısı taşıyor. Yetkisiz örnek sorgular yangın
ürününde 401, konumda Earthdata giriş HTML'i verdi. Bu, hizmetin çalışmadığını
göstermez; kimliği doğrulanmış küçük örnek testi yapılmadı. OPeNDAP ile değişken
ve native dizin altkümesi almak hacmi azaltabilir; ürün bazında eşitlik ve gerçek
aktarımı ölçmeden miktar taahhüdü verilmeyecek. Gerekli komşu pikseller, QA,
zamanlar, native dizinler ve gerçek girdi kimliği korunmalı.

[LAADS bulut belgesi](https://ladsweb.modaps.eosdis.nasa.gov/cloud/), verinin
bulutta okunup işlenebildiğini, NASA veri erişiminin ücretsiz olduğunu ve
kullanıcının kendi bulut kaynaklarının maliyetinden sorumlu olduğunu açıklıyor.
Doğrudan S3 erişimi için aynı AWS bölgesi gereksinimi ayrıca dikkate alınmalı.
[Colab resmi açıklaması](https://research.google.com/colaboratory/faq.html)
ücretsiz kaynakların ve oturum sürekliliğinin garanti olmadığını belirtiyor.

## Kapsam seçimi sonrası küçük pilot

1. Mevcut, zaten denetlenmiş tek bir eğitim dosya çifti seçilir; tam dönem başlamaz.
2. Seçilen ortamda kaynak kimliği ve gerekli alanlarla hesap yeniden üretilir.
   Uzaktan altküme kullanılırsa özgün pikseller/QA/zaman/native dizinlerle eşitlik
   sınanır; bulutta tam kaynak kullanılırsa yerel hesap ve özetlerle karşılaştırılır.
3. Aktarılan bayt, en yüksek geçici disk, RAM, süre ve varsa ücret kaydedilir.
   Sonuçlar yeniden okunup kaynak/çıktı özetleri ve kayıt sayıları kontrol edilir.
4. Geçici kaynak ancak çıktı doğrulanıp yeniden üretme manifesti kaydedildikten
   sonra temizlenir. Mevcut elle indirilen örnekler bu planla otomatik silinmez.
5. Pilot bulguları ve güvenlik paylı kapasite planı çalışma planında değerlendirilir; sonra
   tüm dönem için seçim yapılır. Yaklaşık ayak izi ve nihai etiket konuları açık kalır.

4 Ekim'de tek geçiş Colab pilotu gerçek NASA erişimiyle geçti. Iki
sensörlü bir günlük genişlemeyi onayladım. 1,46 GB kaynak sırayla bir çift
halinde işlenecek; doğrulanmış küçük sonuçlar yazıldıktan sonra geçici ham
kopyalar temizlenecek. [Çalıştırma ve sınırlar](COLAB_DAY_PILOT.md).
Tam dönem platformu ve kalıcı çıktı depolama kararı hâlâ açık. Yerel partili
işleme de 27 GB disk sınırı için geçerli bir adaydır.
