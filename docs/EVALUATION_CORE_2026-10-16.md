# Model değerlendirmesi için hesap ve ayrım çekirdeği

Tarih: 16 Ekim 2026. Durum: değerlendirme hesapları, eğitim içi ayrım
kontrolleri ve günlük hücre uyarısı muhasebesi hazırlandı. Sentetik kod
provası tamamlandı; gerçek model veya kalibratör eğitilmedi.

## Araştırmacının ölçüt kararı

Araştırmacı 16 Ekim'de **Average Precision ana, trapez PR-AUC yardımcı**
seçeneğini açıkça kabul etti. Bu karar etiket doğrulaması, nihai birleştirme
veya eğitime başlama onayı değildir. Pozitif sınıf 1 ve hedef `(T,T+24h]`
olarak kalır. Yeni sürüm [evaluation_core_v1.json](../configs/evaluation_core_v1.json)
ile kaydedildi.

Eski `configs/project.yaml` içindeki genel `pr_auc` başlangıç kaydı ve
doğrulayıcısı, hash ile bağlı geçmiş paketlerin bütünlüğü için değiştirilmedi.
Yeni değerlendirme girişinin kesin ölçüt tanımı yeni yapılandırmadır;
gelecekteki gerçek eğitim/değerlendirme komutunun bunu açıkça okuması gerekir.
Bu çekirdek henüz gerçek eğitim giriş noktası değildir.

## Hesap sözleşmesi

`evaluation_metrics` yalnız bilinen 0/1 hedef ve sonlu [0,1] olasılıklarını
işler. Bilinmeyen hedefler sıfır yapılmaz veya sessizce atılmaz; girdi
reddedilir. Sayılar ve prevalans birlikte raporlanır. Bu sürüm ağırlıksız
hücre-gün hesabıdır; örnekleme ağırlığı ve olay düzeyi başarı uygulamaz.

AP eşit skorları birlikte değerlendirir; satır sırası sonucu iyileştiremez.
Trapez PR-AUC ayrı adla hesaplanır; iki farklı tanım birbirine karıştırılmaz.
[AP tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html),
[PR eğrisi](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.precision_recall_curve.html).

Brier, ikili ortalama kare olasılık hatasıdır ve [0,1] ölçeğindedir.
Log-loss doğal logaritma/float64 makine epsilon'u kullanır; hesap için
sınırlanan uç olasılıkların sayısı kaydedilir, kaynak tahmin değiştirilmez.
Tek sınıflı grupta AP/trapez PR-AUC/ROC-AUC bu uygulama sözleşmesinde
`null` ve `undefined_single_class` olur; Brier/log-loss hesaplanabilir.
[Brier](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.brier_score_loss.html),
[log-loss ve sınırlandırma](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.log_loss.html).

Kalibrasyon tanısı eşit genişlikli `[sol,sağ)` dilimler kullanır; son dilim
1'i içerir. Boş dilim sıfır oranla doldurulmaz. Dilim sayısı açık parametre,
gerçek deney için seçilmemiştir; kalibratör fit edilmez. Ondalık sınırın
çarpma yuvarlamasıyla yanlış dilime taşınması ayrı testle önlendi.

İki modelin karşılaştırmasında aynı UTC hücre-gün anahtarları ve aynı
hedefler zorunludur. Satırlar anahtarla hizalanır; iç birleştirmeyle örnek
kaybı, değiştirilmiş hedef veya tekrar reddedilir. Sayısal fark hesaplanır;
bağımlılığı koruyan güven aralığı henüz hesaplanmaz.

## Ayrım ve uyarı kontrolleri

`evaluation_folds` yalnız 2018–2023 eğitim içi metadatayı kontrol eder;
2024/2025 bu hazırlıkta kabul edilmez. Tekil UTC gece yarısı anahtarı,
tamamlığı açık boolean ile belirtilmiş olay üyelikleri gerekir. Aynı olay
bir satırdaki çoklu kimliklerden biri olsa da iki tarafta bulunamaz.
Bilinmeyen üyeliğe boş liste atanmaz; teknik tamamlık beyanı bilimsel olay
tanımının doğrulandığı anlamına gelmez.

Eğitim hedef penceresi, dışarıda tutulan ilk tahmin zamanından önce
bitmelidir. `(T,T+24h]` pencerelerinin eşit uçta buluşması örtüşme değildir;
nokta yalnız önceki pencereye aittir. Ek zaman aralığı tam saat olarak
açık parametre, varsayılan süre yoktur. İlk pandas/NumPy süre uyarısı
açık nanosaniye hesabıyla giderildi; uyarı bastırılmadı.

Mekânsal denetim yalnız belirtilmiş blok kolonlarının kesişimini kontrol
eder; fiziksel uzaklık/tampon hesaplamaz. Satır numarası zaman yerine
kullanılmaz. [İleri zaman ayrımı ve örnek aralığı koşulu](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html).
2019–2023 için beş ileri yıl takvim taslağında önceki yıllar eğitim içindir;
embargo/olay sınırı seçilmediği için bunlar çalıştırılabilir fold değildir.

`evaluation_alerts`, açık kapasite ve eşitlik kuralıyla hücreleri sıralar.
Prova eşitlikte hücre kimliği sırasını kullanır; gerçek K ve eşitlik kuralı
`null` kalır. UTC'nin Z/+00:00 yazımları iki günlük kapasite yaratamaz.
K'den az hücre varsa mevcut sayı aşılmaz; geçersiz skorlar atılmaz.
Pozitif, doğrulanmış negatif ve etiketi belirsiz uyarılar ayrı sayılır.
Belirsiz uyarı yanlış alarm değildir. Yanlış alarm oranının paydası yalnız
etiketi değerlendirilmiş hücre-gündür. Tekil olay yakalama, çok hücreli ilk
tespit politikası seçilmediğinden uygulanmadı ve `null` kalır.

## Gerçekleşen sınamalar

**67 yeni vaka dahil 113 ilgili test**, Deprecation/Future uyarıları hata
sayılarak geçti. Beş Python dosyasında lint/format geçti. Yeni NumPy
hesapları mevcut kilitli kurulumdaki **scikit-learn 1.9.1** ile **55
sentetik örnekte** karşılaştırıldı; tolerans 1e-12, en büyük mutlak fark
4,45e-16'dan küçüktür. Bu yazılım uyumu saha doğrulaması değildir.

Dört elemanlı oyuncak örnekte AP 0,833333, trapez PR-AUC 0,791667'dir;
model başarısı olarak sunulmaz. Aynı sentetik tahminler ters satır
sırasında karşılaştırıldığında anahtar hizalamasıyla fark sıfırdır.
Gerçek pilot CSV'sindeki **156 hedef boş/unknown** kaldı; skora sokma
denemesi reddedildi. Kullanılan sabit kontrol olasılığı model tahmini
değildir; gerçek skor/tahmin ve sınıflandırıcı/kalibratör fit sayıları sıfırdır.

Güncel dizin: `outputs/reports/dataset/evaluation_core_v1/20261016T010607Z_903eb104/`.
17 bağlı girdi ve dokuz çıktı kapanışta geri kontrol edildi. Ham geometriler
yeniden işlenmedi, 2024/2025 açılmadı. Readback SHA-256:
`ba1ac26003a370be4bfece12a92a41f270dfdb9965b5dbceff0a7d52b6bf3266`.
Kapanış SHA-256:
`7a164a4e87bb99f6dfb2618d488cf22fd552b2547056f39de85211764ec0f9a1`.
Önceki geliştirme denemeleri korunur; son sürüm ortak yardımcı kodları da
bağlar. Yerel provada ağ/bulut işi yok; tanımlar için resmî dokümantasyon
ayrıca web üzerinden kontrol edildi.

## Hazırlık sınırı ve sonraki adım

Bu değerlendirme çekirdeği bitmiş modelleme hattı değildir. Fold içinde
öğrenilen ön işleme, olay yakalama, blok güven aralıkları ve 2024 seçim/
kalibrasyon rolleri henüz uygulanmış deney sayılmaz. Yanıt beklerken
sıradaki hazırlık, eksik değer/ölçekleme dönüşümlerinin yalnız fold eğitim
kısmına fit edilmesidir. Gerçek eğitim için bilimsel kapılar, son parça
kontrolü ve nihai birleştirme öncesi araştırmacı onayı koşulu korunur.
