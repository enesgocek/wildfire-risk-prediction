# Google Cloud kredisiyle hızlandırma — 5 Ekim 2026

Kullanıcı mevcut Google Cloud deneme kredisini veri hazırlamayı hızlandırmak
için kullanmayı önerdi. 6 Ekim'de paylaştığı Billing ekranında **13.650 TRY**
kalan deneme kredisi, başlangıç **13.988 TRY**, **20 gün** ve
**26 Ekim 2026** bitiş tarihi görünüyor. İlk ekranda hesap kapalıydı.
Kullanıcı Reopen onayını kendisi tamamladı; son Overview ekranında kapalı
uyarısı kalktı, **Free trial account**, 13.650 TRY ve 20 gün korunuyor.
Ücretli Upgrade düğmesi hâlâ ayrı seçenek olarak görünüyor ve kullanılmadı.
CPU kotası terminalden okundu: global 32, us-central1 E2 24 vCPU; kullanım
sıfır. VM/disk listeleri terminal ve konsolda boş doğrulandı. Uygun fiyat
ve hız denemesi henüz ölçülmedi.
Kaynak oluşturulmadı, hesap yükseltilmedi, harcama başlatılmadı.

**Kullanıcının kesin sınırı: cebinden ödeme çıkmayacak.** Kredi kullanımı
yetkisi yalnızca bu sınır içinde. Ücretli hesaba yükseltme, kredi dışı kullanım,
peşin ödeme veya başka bir ücretli billing hesabına bağlama yetkisi yok.
Account type Direct ücretsiz/ücretli billable status alanı olarak yorumlanmadı.
Kullanıcı tarafından yeniden açıldıktan sonraki Overview ekranı Free trial
durumunu ve kredi geçerliliğini doğruluyor. Hesap yönetimi kullanıcının
ekranında; yeniden açma/upgrading agent tarafından yapılmadı.

[Google Free Trial FAQ](https://cloud.google.com/signup-faqs), ücretli hesaba
manuel yükseltme olmadan deneme kullanımının faturalandırılmadığını, kredi
veya süre tükenince işlerin durduğunu açıklıyor. Ücretsiz statüyü korumak
bu gereksinimin temelidir; sıradan bütçe e-postası tek başına güvence değildir.
Ücretsiz durum sürdürülemiyorsa mevcut Colab yolu kullanılacak.

Temmuz Colab işi tamamlandı; 31 gün/270 çift/89.869 hücre-gün küçük çıktı
yerel denetimden geçti. Resmî FIRMS boşluğuyla örtüşen 61 termal kayıt farkı
ayrı kalite bulgusu. Tamamlanan ay yeni bulut işine yeniden eklenmeyecek.

Global/bölgesel kota sorguları başarıyla tamamlandı; kullanıcı Compute
Engine API etkinleştirmesini onayladı. Önerilen 8 vCPU denemesi görünen
kotalara sığıyor; kaynak bulunabilirliği henüz doğrulanmadı. Sıradaki bilgi
makine yapılandırması ve toplam deneme maliyetidir. VM/disk envanteri
terminal ve web ekranlarıyla boş doğrulandı. Cloud Shell
ücretsizdir; describe/list komutları kaynak oluşturmaz. us-central1
yalnızca ilk kapasite sorgusu için adaydır; konuşlandırma/bölge kararı değildir.
[Kapasite sorgusu](GCP_CPU_PREFLIGHT.md). [Resmî hesap yönetimi](https://docs.cloud.google.com/billing/docs/how-to/close-or-reopen-billing-account).

## Seçenekler

| Yol | Uygulama | Karar için gereken bilgi |
|---|---|---|
| Tek CPU sunucusu, önerilen ilk deneme | Kotaya göre 4–8 vCPU; 2–4 ayrı süreçle kısa karşılaştırma | Makine/bölge fiyatı, disk, kota, saatlik bütçe |
| Cloud Batch | Gün/çift görevlerini birden fazla işçiye dağıtmak | Gerçek hız testi, hesap erişimi, toplam iş ve maliyet sınırı |
| Colab'da devam | Mevcut kayıtlar korunur; bulut hazırlığı sırasında iş sürer | Ücretli kaynak gerekmez; oturum ve işlem süresi değişken |

İşçiler ayrı çalışma/çıktı dizinleri kullanmalı; mevcut tek işçi scriptini
aynı klasörde birkaç kez çalıştırmak doğru paralelleştirme değildir.
İndirilen kaynak ve bilimsel hesap kuralları aynı kalmalı. Günlük birleşim
bütün beklenen çiftler doğrulanınca yapılmalı; kaynak/çıktı izleri, belirsiz
gözlem politikası ve kesintiden devam korunmalı.

Bu işin mevcut kütüphaneleri CPU kullanıyor. GPU seçmek kodu otomatik
hızlandırmaz. GPU'nun ayrıca deneme hesabında kısıtlı olması, CPU seçeneğinin
önce değerlendirilmesini destekler. Bir saatlik ay sonucu henüz ölçülmedi.

## Krediyi kullanmadan önce somut hazırlık

1. Billing hesap türü, kalan kredi/para birimi ve son tarih doğrulanır.
2. Proje/bölge CPU kotası ve uygun makine fiyatı okunur. Fiyat ve kota bilinmeden
   bütün dönemin krediye sığacağı iddia edilmez.
3. Kısa deneme için sabit iş kapsamı, işçi sayısı ve azami süre hazırlanır.
   CPU + disk + sonuç saklama + ağ/çıktı aktarımı maliyetleri birlikte hesaplanır.
4. İşçi zaman aşımı ve iş bitince kapanma ayarlanır. Disk/kalıcı depolama
   maliyetleri makine durunca otomatik sıfırlanmış sayılmaz. Sonuçlar kredi
   süresi dolmadan Drive/yerel kalıcı alana doğrulanarak aktarılır.
5. Küçük denemede aynı kaynaklardan çıkan sayım/alan/zaman sonuçları kontrol
   edilir. Ölçülen hız ve kredi bütçesine göre kalan eğitim grupları seçilir.

Bütçe bildirimi tek başına harcamayı durdurmaz; süre/kaynak sınırları ayrıca
gereklidir. Ücretsiz deneme ile ücretli hesaba yükseltilmiş durum ayrılmalıdır:
ücretli hesapta kredi dışındaki kullanım ödeme yöntemine yansıyabilir.
Kredi kullanma isteği hesaba ücretli yükseltme yetkisi olarak yorumlanmadı.

## Kontrol edilen resmî kaynaklar

- [Deneme kredisi ve sona erme koşulları](https://docs.cloud.google.com/free/docs/free-cloud-features).
  Standart teklif 90 gün / 300 USD; kullanıcının gerçek bakiyesi bu varsayımdan
  çıkarılmayacak. Ücretli yükseltme kalan kredinin özgün son tarihini uzatmaz.
- [Batch paralel görevler ve maliyet](https://docs.cloud.google.com/batch/docs/get-started).
  Batch hizmetinde ek kullanım bedeli yok; kullanılan kaynaklar ücretlidir.
- [CPU/kaynak kotaları](https://docs.cloud.google.com/compute/resource-usage).
  Deneme ve yeni hesap kotaları gerçek projede kontrol edilecek.
- [Bütçe uyarılarının sınırları](https://docs.cloud.google.com/billing/docs/how-to/budgets).
