# Parçalı özellik kaydı ve güvenli okuyucu — 10 Ekim 2026

## Amaç ve kapsam

Tam dönem birleştirmesine hazırlanmak için, kabul edilmiş dört eğitim
gününün özellik ve kaynak/kalite tabloları günlük parçalara kaydedildi.
Amaç bütün dönemi tek DataFrame'e almadan okumayı ve dosya/anahtar
değişikliğinin fark edilmesini sınamaktır. Yeni kaynak çıkarılmadı;
model eğitilmedi ve eksikler doldurulmadı.

1, 8, 9 ve 31 Ağustos 2018 önceki kesim, taşıma ve ay sonu denemelerinin
günleridir; bütün ay veya temsil edici bir model örneklemi değildir.
2.899 hücre × dört gün = **11.596 hücre-gün**, 27 aday özellik korunmuştur.

## Kayıt ve okuma yöntemi

`feature_partition.py` her gün için ayrı `features.csv` ve
`provenance.csv` üretir; dosyalar ay dizininde bulunur. Manifest,
günleri, hücre envanterinin kimliğini, sütun listelerini, satır ve
eksik değer sayılarını, dosya boyutlarını ve SHA-256 özetlerini içerir.
CSV bu sınırlı pilotun biçimidir; tam dönem depolama/verim kıyası veya
nihai veri seti biçimi seçimi yapılmış değildir.

Yeni çıktı dizini zorunludur; mevcut dizin üzerine yazılmaz. Her parça
geri okunduktan sonra manifest yayımlanır. Öncesindeki hata, manifesti
olmayan kısmi çıktıyı bırakır; eski kabul edilmiş kaynaklara dokunmaz.
Manifestin yayımlanması nihai bilimsel veri seti kabulü değildir.

Okuyucu dışarıdan verilen manifest hash'ini ve kayıtlı eğitim kapsamını
kontrol eder. Bütün günlerin 2018–2023 içinde olduğunu veri parçalarını
okumadan denetler. Yalnız sabit üretilmiş yollar kabul edilir; değişmiş
dosya, yanlış envanter, farklı sütunlar ve tekrar/kayıp hücre reddedilir.
İki tablo aynı hücre anahtarıyla sıralanır; kaynak satır sırasına
dayanarak birleştirme yapılmaz. Her çağrıda bir gün döndürülür;
kalite tablosu model özelliklerinden ayrı kalır.

Hash kontrolü verilen kimliğe göre değişikliği denetler; kaynağın
bilimsel doğruluğunu veya işletim sistemi erişim izolasyonunu kanıtlamaz.
Kaynak zaman denetimlerinin dayanağı önceki kabul edilmiş
[özellik birleştirmesi](FEATURE_JOIN_PILOT_2026-10-10.md) ve
[gün geçişleri](TARGET_ADMISSION_REVIEW_2026-10-10.md) kayıtlarıdır.

## Gerçek geri okuma

Son çıktı:

`outputs/reports/dataset/feature_partition_v1/20261010T135514Z_3672d40a/`

Rapor `readback.json` SHA-256:
`16b508109c3531a3c3e92d463f9d4067a4108279d40122d11716cb8e5f96fe07`.

Manifest SHA-256:
`c490b03b7bb40bf548b912207aa38f222b0cd41eccb6ff69708b4b54603355af`.

Durum `feature_partition_pilot_readback_passed`. Ağ bağlantıları
engellenmiş süreçte kaynak ve parça değerleri tam eşitlikle karşılaştırıldı;
44 girdi/kod dosyasının hash'i kontrol boyunca değişmedi. Sekiz veri
parçasının toplam boyutu 17.887.495 bayttır; bütün dönem boyut tahmini
değildir. Manifest Ağustos'un yalnız dört gününü içerir.

Korunan eksikler, dört günün toplam hücre-gün sayılarıdır:

| Alan | Her sütundaki eksik sayı |
|---|---:|
| 11 meteoroloji adayının her biri | 756 |
| Northness ve eastness, ayrı ayrı | 12 |
| 30 günlük NDVI ve NDMI, ayrı ayrı | 14 |
| 60 günlük NDVI ve NDMI, ayrı ayrı | 12 |

Sıfırla doldurma, kısa/uzun pencereyi birbirine taşıma veya örnek dışlama
yapılmadı. `labels_created=false`, `model_ready=false` ve tarihsel
erişilebilirlik belirsizliği manifestte ve raporda korundu.

## Kontroller ve sonraki adım

13 yeni parça denetimi ile özellik/hedef sınır testleri toplam **47 test**
olarak geçti. Bozulmuş içerik, yanlış manifest hash'i, eksik/tekrarlı
hücre, yanlış gün, sonsuz değer, ek hedef sütunu, yol kaçışı, envanter
değişimi, 2024/2025 kapsamı ve uydurulmuş kabul işaretleri sınandı.
Lint ve format denetimleri geçti.

İki canlı bitki örtüsü kod dosyası ile eski 136 baseline dosyası
değişmedi. Son yerel progress kaydı 13:47:37 UTC'de 20 doğrulanmış ay ve
Eylül 2019 hazırlığında `running` bildiriyor; canlı VM sorgusu değildir.
Bulut veya Earth Engine işi bu hazırlık için başlatılmadı.

Kuyruklar tamamlanınca ilgili aylık kaynak kabulü, tam takvim envanteri,
etiket politikası ve final veri seti manifesti ayrıca hazırlanacaktır.
Bu okuyucu pilotu tamamlanmış eğitim veri seti veya performans sonucu
olarak kullanılmaz.
