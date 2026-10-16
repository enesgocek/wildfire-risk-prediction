# Eğitim bölümünden öğrenilen ön işleme hazırlığı

Tarih: 16 Ekim 2026. Durum: yalnız sentetik veriyle sınanmış teknik
hazırlık. Gerçek özelliklere eksik değer doldurma veya ölçekleme uygulanmadı;
etiket kabulü, sınıflandırıcı eğitimi ve nihai birleştirme yapılmadı.

## Amaç ve kapsam

Eksik değer istatistiklerinin veya ölçeklerin bütün veri setinden
hesaplanması, değerlendirme bölümünü eğitim hesabına karıştırabilir.
Yeni `fold_preprocessing` katmanı, her denemenin yalnız eğitim kısmından
öğrenir. Ayrımın diğer tarafındaki özellik değerleri fit fonksiyonunun
parametresi değildir. Bu yaklaşım [resmî veri sızıntısı rehberiyle](https://scikit-learn.org/stable/common_pitfalls.html)
uyumludur; gelecekteki bütün eğitim komutlarının otomatik olarak güvenli
olduğunu kanıtlamaz. Bu hazırlık henüz gerçek model girişine bağlanmadı.

Eski hash ile bağlı kod/yapılandırmalar değiştirilmedi. Yeni küçük
[yapılandırmada](../configs/fold_preprocessing_v1.json) gerçek eksik değer,
ölçekleme ve tamamen boş sütun tercihleri `null` kaldı. Medyan doldurma,
ölçekleme açık/kapalı ve tamamen boş sütun için durdur/çıkar seçenekleri
uygulanabilir adaylardır; araştırma için seçilmiş yöntem sayılmaz.

## Veri sözleşmesi

Fit öncesinde iki tarafın 2018–2023 içinde kalması, UTC gece yarısı
anahtarları, zaman/ek aralık ve çözülmüş olay üyelikleri kontrol edilir.
Belirtilirse adlandırılmış mekânsal bloklar da ayrık olmalıdır; fiziksel
uzaklık/tampon hesabı yapılmaz. Prova için kullanılan sıfır saat ek aralık
gerçek embargo tercihi değildir. Bu teknik kontroller bilimsel olay
tanımının veya üyelik tamamlığı beyanının bağımsız doğrulaması değildir.

Özellik tablosu tam olarak iki anahtar ve açıkça belirtilmiş 27 adayın
bir alt kümesini içermelidir. Hedef, kalite, gözlem ve kaynak/zaman izleri
sayısal özellik tablosuna alınmaz. String sayılar, boolean, karmaşık veya
sonsuz değerler reddedilir; sayısal eksikler korunarak işlenir. Anahtarlar
metadata ile birebir eşleşir. Satır veya sütun sırası değişebilir; içerik
anahtarla denetlenir, seçilen sütun sırası açık tutulur.

Tamamı eğitimde boş bir sütun için açık `error` seçimi işlemi durdurur.
`drop` seçimi yalnız o fold içinde sütunu çıkarır; diğer tarafta sonradan
değer bulunması sütunu geri getirmez. Bütün sütunlar boşsa işlem yine durur.
Eksik sütuna otomatik sıfır atanmaz. Eksiklik göstergesi, ileri/geri zaman
doldurma, kalite eşiklerini değiştirme ve tüm veride özellik seçimi bu
sürümde uygulanmaz. [SimpleImputer sözleşmesi](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html).

Mevcut kilitli kurulumdaki scikit-learn 1.9.1 `SimpleImputer` medyanları
yalnız eğitimden öğrenir. İstenirse `StandardScaler`, doldurulmuş eğitim
matrisinden ortalama ve `ddof=0` varyansına dayalı ölçek öğrenir. Sabit veya
sayısal olarak sabite yakın sütunlarda kütüphanenin ölçek koruması kullanılır.
Ölçekleme kapalıysa ortalama/ölçek raporda `null` olur; sıfır ortalama
ölçüldüğü iddia edilmez. [StandardScaler tanımı](https://scikit-learn.org/stable/modules/generated/sklearn.preprocessing.StandardScaler.html).
Yeni bağımlılık yüklenmedi; mevcut dolaylı bağımlılık ve `uv.lock` bağlandı.

Öğrenilen sayılar değiştirilemez tuple alanlı bir istatistik nesnesinde
tutulur. Dönüşüm yalnız denetlenen eğitim veya dışarıda tutulan bölümün
tam anahtar kümesine uygulanır; eksik/fazla satır ve 2024/2025 reddedilir.
Sonuç sonlu olmalıdır; uç değere sessiz kırpma yapılmaz. Anahtarlar, seçilen
sütun sırası ve eğitim float64 değerleriyle eğitim girdisi SHA-256'sı
hesaplanır. Bu nesne imzalı kabul belgesi, gerçek veri yetkilendirme kapısı
veya genel üretim/tahmin nesnesi değildir. Değişmiş parçaların nihai kabulü
ayrı manifest ve onay protokolüne tabidir.

## Gerçekleşen kontroller

**45 yeni davranış vakası dahil 158 ilgili test**, Deprecation/Future
uyarıları hata sayılarak geçti. Üç yeni Python dosyasında lint/format geçti.
Testler elle hesaplanabilen medyan/ortalama/ölçeği, değerlendirme uçlarının
istatistikleri değiştirmemesini, fold nesnelerinin ayrılığını, sabit/sabite
yakın sütunları, taşma reddini, boş sütun politikasını, anahtar/şema hatalarını
ve zaman/olay/blok korumalarını kapsar. Kaynak tabloların değişmediği sınandı.

Ağ bağlantısı kapatılmış çevrimdışı provada **40 sentetik örnek**, bağımsız
NumPy medyan ve popülasyon standart sapması hesabıyla karşılaştırıldı.
4–43 eğitim satırı ve her örnekte yedi dışarıda tutulan satır kullanıldı;
ölçekleme açık/kapalı ve tamamen boş sütun seçenekleri denendi. 1e-12
mutlak/bağıl toleransta en büyük mutlak fark **0** oldu. Bu kontrollü
sayısal aralıkların sonucu bütün olası girdiler için eşdeğerlik veya
gerçek model başarısı değildir. Ek uç değer dönüşümleri istatistikleri
değiştirmedi. Sınıflandırıcı veya kalibratör fit edilmedi.

Önceki değerlendirme raporunun 17 bağlı girdisi ve dokuz çıktısı tekrar
hash ile kontrol edildi; gerçek pilotun 156 hedefinin kabul edilmediği
rapor kaydı korundu. Bu provada gerçek özellikler veya ham uydu geometrisi
yeniden işlenmedi. 2024/2025 kaynağı açılmadı; ağ/bulut işi başlatılmadı.

Çıktı: `outputs/reports/dataset/fold_preprocessing_v1/20261016T011740Z_706c3793/`.
**33 bağlı girdi/dört çıktı** kapanışı kontrol edildi. Sentetik istatistikler,
40 vaka karşılaştırması, kapsam koruması ve girdi manifesti ayrı saklanır.
Readback SHA-256:
`8cc2ac561d0fc73e5b71a080de497451bbe5424ad6593b0cefee45ea0569caae`.
Kapanış SHA-256:
`2e8c90d155de6e971b1d3d0f8c467dab8a04d093c62b55c350f1a9f2082b6fd5`.

## Açık işler

Medyanın gerçek veri/model için uygunluğu, eksiklik göstergeleri ve hangi
modellerin ölçekleme gerektirdiği henüz deneyle seçilmedi. Eksik değer
doldurmak, eksik gözlemi veya etiketi düzeltmez. Gerçek olay/negatif kabulü,
2024 seçim/kalibrasyon rolleri, olay düzeyi değerlendirme ve bağımlılığa
uygun güven aralıkları açık kalır. Sonraki bağımsız hazırlık, deney manifesti
ile bu dönüşümlerin, fold anahtarlarının ve kapalı kabul koşullarının aynı
deney kaydına bağlanmasıdır. Nihai birleştirme öncesi ayrı son kontrol ve
araştırmacı onayı koşulu korunur.
