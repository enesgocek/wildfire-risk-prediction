# Tam aylık aday özellik birleştirmesi — 12 Ekim 2026

## Amaç ve kapsam

Kuyruklar devam ederken, dört günlük birleştirme pilotu tam takvim ayına
genişletildi. Hazır kaynakları bulunan Ocak ve Ağustos 2018 seçildi; amaç
kış/yaz koşullarında bütün günleri, geçmiş görüntü taşımasını ve eksik
değerleri kontrol etmektir. Bu iki ay temsil edici model örneklemi veya
mevsimsel başarı ölçümü değildir. Yeni indirme, EE/Drive isteği, bulut işi
ve model eğitimi yapılmadı. 2024 özellik dosyaları ve 2025 final testi açılmadı.

## Yöntem

Yeni `feature_month.py`, dondurulmuş günlük `feature_partition.py`
biçiminin çevresinde ayrı bir aylık takvim manifesti tutar. Tam ayın bütün
günleri artan sırada ve her gün bütün 2.899 hücre bulunmalıdır. Eksik,
tekrarlı veya ay dışı gün kabul edilmez. Mevcut çıktı üzerine yazılmaz;
başarısız hazırlık kabul edilmiş kaynakları değiştirmez.

`scripts/quality/verify_feature_month.py`, önce eğitim dönemi kapısını,
önceki kabul raporunu ve seçilmiş ayın bitki örtüsü geri okuma hash'ini
kontrol eder. Meteoroloji, statik tablo, aylık bitki örtüsü ve kesim
manifestleri kaynak kimlikleriyle eşleştirilir. Bitki örtüsü belleğe yalnız
bir ay için alınır; birleştirme ve parça okuyucu bir günlük tabloyla çalışır.
12 GiB başlangıç ve 10 GiB çalışma disk rezervi kullanılır. CLI'da ağ
bağlantıları engellenir; canlı kuyrukların yazıcı kilitlerine müdahale edilmez.

Her gün 27 aday girdi, ayrı kalite/kaynak tablosuyla kaydedilir. İkinci
okuma yolunda kaydedilen değerler doğrudan kaynak hücre anahtarlarına
göre karşılaştırılır; yeniden birleştirme sonucuyla karşılaştırma yapılmaz.
NDVI/NDMI yanında pencere, kesim, yaş, destek ve kaynak alanları da
eşleştirilir. Kaynak ve yöntem dosyaları işlem sonunda yeniden hash'lenir.

Ham meteoroloji ile önceden kabul edilmiş işlenmiş meteoroloji CSV'leri
arasındaki ondalık gösterim kontrolü, önceki günlük pilotta kullanılan
`rtol=atol=1e-12` ile yapılır. İlk tam eşitlik denemesi çok küçük CSV
yuvarlama farkını yakaladı; kaynaklar düzeltilmedi. İki ayda ölçülen en
büyük mutlak fark sırasıyla `2,842170943040401e-14` ve
`7,105427357601002e-15`. Yeni parçaların model kaynağına göre değer ve
eksiklik eşitliği ise round-trip okuyucuyla tam eşitlikte denetlendi.

## Gerçek sonuç

Her ay 31 gün × 2.899 hücre = **89.869 hücre-gün**; toplam **179.738
hücre-gün ve 62 gün**. Bitki örtüsü kaynaklarının iki pencereli uzun
tablosunda satır sayısı bunun iki katıdır; bu iki sayım karıştırılmaz.

| Her sütunda eksik hücre-gün | Ocak 2018 | Ağustos 2018 |
|---|---:|---:|
| 11 meteoroloji adayının her biri | 5.859 | 5.859 |
| Northness ve eastness, ayrı ayrı | 93 | 93 |
| 30 günlük NDVI ve NDMI, ayrı ayrı | 6.344 | 105 |
| 60 günlük NDVI ve NDMI, ayrı ayrı | 795 | 93 |

Diğer statik aday özelliklerde bu iki ay için eksik hücre-gün yoktur.
Bu, habitat uygunluğu veya statik kaynakların saha doğruluğu kabulü değildir.
Eksik değerler NaN kaldı; sıfırla doldurma, hücre dışlama ve kısa/uzun
pencere arasında değer aktarma yapılmadı. Eksik sütun sayıları aynı
hücre-günleri tekrar içerir; toplam farklı eksik örnek sayısı olarak toplanmaz.

Günlük özellik/kalite CSV'lerinin toplamı **275.957.027 bayt**. Bu, yalnız
iki aylık pilotun boyutudur; bütün dönem biçim/verim seçimi veya bütün
veri seti boyut tahmini değildir. Gerçek çağrılar yaklaşık 47,49 ve 41,77
saniyede tamamlandı; kıyas deneyi veya diğer aylara süre garantisi değildir.

## Kanıt ve kontroller

Çıktı kökü `outputs/reports/dataset/feature_month_v1/`:

- Ocak: `20261012T012405Z_598fce4c/readback.json`, SHA-256
  `79c4debcc8bc208b38c72ef1d3d022dec62643f5c959a56311272c58bc9405de`.
  Aylık manifest SHA-256
  `ceeb296790d6a5cfa71f2085a041742b7c4f3305f81b527c5bc53eaa66f398f1`.
- Ağustos: `20261012T012518Z_0a4d0f5f/readback.json`, SHA-256
  `8f69fe80b83caf4e31e65a1ef26258cfd682d01be87ffa05f95bed14a7070dc1`.
  Aylık manifest SHA-256
  `b4ba022d021e1393123f6771e2f3b5edf3a0514b675000930d3a7e8ea660c761`.
- Birleşik kabul: `two_month_readback_20261012.json`, SHA-256
  `ba00e9b1b612094964a4b767b889b4699a477c72888fbcd4a71abe05fe2c98da`.
  **165 farklı kaynak/yöntem dosyası aynı hash'te**; canlı V2/ISO/V6 girişleri
  ve mevcut günlük birleştirme/parça kodu da bu envanterdedir.

19 yeni aylık kontrol ve 47 mevcut parça/birleştirme/hedef kontrolü,
toplam **66 test** geçti. Artık yıl, eksik/ek/tekrarlı/sırasız gün,
değişmiş veri veya manifest, yanlış hücre envanteri, hedef sütunu ve
uydurulmuş negatif kabulü sınandı. 2024/2025 kapsamının CSV okumasından
önce reddedilmesi kontrol edildi. Ruff ve biçim kontrolü geçti.

## Kabul sınırı ve sonraki adım

Bu sonuç tam ay **aday özellik** kabulüdür. `labels_created=false`,
`model_ready=false`, `daily_observation_status=unknown` ve
`negative_label_permitted=false` korunur. Kaynak çıkarımı, ham uydu
işleme ve bağımsız saha doğrulaması yeniden yapılmadı. İki ayın birleştirilmesi,
uydu gözlem kuyruğuna yeni tamamlanmış ay eklemez.

Tam eğitim dönemi birleştirmesi için aynı kabul yolu kullanılabilir;
her ay ayrı kaynak geri okuması ve takvim manifesti gerektirir. Nihai
etiketli teslim hâlâ [kabul sözleşmesindeki](DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md)
kaynak semantiği, olay/ilk hücre, habitat, gözlem ve dönem kenarı
kararlarını bekler. Bu bilimsel kararlar yalnız kuyruk bitişi veya kod
testiyle onaylanmış sayılmaz.
