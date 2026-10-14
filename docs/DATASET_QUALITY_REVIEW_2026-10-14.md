# Eğitim adaylarının kalite incelemesi — 14 Ekim 2026

## Gerçekleşen çalışma ve kanıt düzeyi

2018–2023 eğitim döneminin **72/72 ayı, 2.191 günü ve 6.351.709
hücre-günü**, 27 aday özellikle birleştirildi. 70 yeni ay hazırlandı;
Ocak/Ağustos 2018'in iki eski adayı kaynaklarıyla geri okunarak kullanıldı.
Birleştirme 14 Ekim **17:24:16 Türkiye**'de hatasız bitti; **17:32:54**'te
ayrı tam takvim denetimi de geçti. Her iki stderr boş, aday yazıcı kilidi
yok; kapanış kontrolünde ilgili yerel üretim ve son audit süreçleri yoktu.
Bu işler için bilgisayarın açık tutulması artık gerekmiyor.

Tam takvim denetimi, bütün günlük özellik/kalite parçalarını kaynak ve
parça hash'leriyle geri okudu; anahtar, takvim, kayıp değer sayımları ve
atanmamış hedef eşleştirmesini kontrol etti. Sonraki yeni kalite profili
bu kabul edilmiş **72 aylık raporun hash ile bağlı sayımlarını** derledi.
Profilde 6,35 milyon satır yeniden okunmadı; yeni bağımsız veri çekimi,
geometri hesabı veya saha doğrulaması yapılmadı.

## Eksik değer bulguları

Aşağıdaki oranların paydası her sütun için **6.351.709 eğitim hücre-günü**;
eksik payları sütun bazındadır. Sütunların aynı satırlarda boş olduğu
veya toplamda kaç tam gözlemli/uygun eğitim satırı bulunduğu bu marjinal
sayımlardan çıkarılamaz. Oranlar dört ilin kayıtlı 2.899 hücresini
kapsar; habitat ve etiket kabulü sonrası örneklem değildir.

| Özellik grubu | Sütun başına eksik hücre-gün | Eksik oranı |
|---|---:|---:|
| 11 meteoroloji sütununun her biri | 414.099 | %6,5195 |
| Yedi arazi örtüsü alan payının her biri | 0 | %0 |
| Yükseklik ortalaması/standart sapması ve eğim | 0 | %0 |
| northness/eastness yön bileşenlerinin her biri | 6.573 | %0,1035 |
| 30 günlük NDVI ve NDMI sütunlarının her biri | 439.599 | %6,9210 |
| 60 günlük NDVI ve NDMI sütunlarının her biri | 119.012 | %1,8737 |

Meteoroloji sayımı, [önceki destek incelemesindeki](DECISION_REVIEW_2026-10-10.md)
189 desteksiz hücre × 2.191 gün = 414.099 ile uyumludur. Bu profil
tek başına aynı hücre kimliklerinin sürekliliğini yeniden kanıtlamaz.
Bu alanların habitatla kesişimi incelenmeden 189 hücre doğrudan
dışlanmaz. Sıfır eksik değer de alan paylarının orman kapalılığı veya
habitat uygunluğu olarak yorumlanmasını sağlamaz.

30 günlük NDVI ve NDMI'nin en yüksek aylık eksikliği **Şubat 2019'da
%38,4517**; 60 günlük adaylarda **Mart 2019'da %13,8413**. Bu durum
mevsimsel eksiklik ve görüntü yaşı incelemesini gerekli kılar. 60 günlük
pencerenin daha dolu olması, model başarısının daha yüksek olduğunu
göstermez; eski görüntü, destek alanı ve aynı kabul edilmiş örneklemde
ablasyon birlikte incelenmelidir. Eksik değer doldurma veya özellik
seçimi uygulanmadı.

## İki kaynak gününün hedef penceresine etkisi

13 Haziran 2018 ve 31 Aralık 2023 kaynak eksikleri korunur. Özellik
takviminin 72 ay olması, uydu kapsamını 72 tam ay yapmaz: uydu kabulü
ayrı Temmuz referansıyla **70 tam ay + 59 uygun kısmi gün**dür.

Hedef `(T,T+24 saat]` olduğundan, yalnız günlük eksiklik bilgisiyle
ihtiyatlı bir **inceleme listesi** üretildi: **12–13 Haziran 2018 ve
30–31 Aralık 2023**. Önceki günün sağdan dahil 00:00 uç noktasının
etkisi ayrıca değerlendirilmelidir. Dört tarih × 2.899 hücre = **11.596
takvim hücre-günü inceleme üst kapsamı**; bunların tümü gözlemsiz,
etiketlenemez veya mutlaka dışlanacak kayıt sayısı değildir.

Bu liste otomatik dışlama veya ikili hedef üretmez. Kaynak granüllerinin
tam zamanı ve kabul edilmiş gözlem politikasıyla daraltılabilir. Geçmiş
yangın girdisi eklenirse ayrıca geçmiş pencere etkisi gerekir; henüz
böyle bir pencere uzunluğu seçilmedi. Aylar veya yıllar toptan dışlanmaz.

## Sıradaki bilimsel kabul işleri

| Açık karar | Mevcut kanıt | Sonraki somut işlem |
|---|---|---|
| Type/sürüm ve tespit kapsamı | NASA teknik yanıtı bekleniyor; kaynak istisnaları kayıtlı | Yanıtla üretim semantiğini değerlendirmek; bekleme süresinde bilinmeyeni korumak |
| Yeni olay ve tekrar tespit | Dokuz keşif gruplaması ve zor vaka paketi | Zincir/tekrar/ilk an örneklerini danışman veya bağımsız uzmanla incelemek; karar gerekçesi ve sürümünü kaydetmek |
| İlk anda birden çok hücre | İlk hücre belirsizlik işaretleri mevcut | Tek veya çok hücre kuralını veri anlamı ve konum belirsizliğiyle gerekçelendirmek |
| Habitat ve mekânsal destek | Örtü ve meteoroloji destek kesişimi hazır | Kıyı/su/odunsu tarım ve kısmi destek vakalarını değerlendirip kapsamı açık tanımlamak |
| Negatif etiket ve gözlem | Kompakt uydu ürünleri kabul edildi; günlük durum unknown | Gözlem hesabının anlamını ve yeterlilik kanıtını belirlemek; eksik gözlemi sıfıra çevirmemek |
| Dönem kenarı ve iki gün | İhtiyatlı dört hedef tarihi inceleme listesi | Dahil sağ uç, ortak olay ve eğitim/doğrulama sınırı için sürümlü dışlama/embargo kararı |

Bu kararlar nihai veri seti kabulünden önce gerekir. Yeni profil bunları
onaylanmış saymaz; `model_ready=false`, `negative_label_permitted=false`
ve hedefler atanmamış kalır. 2024 doğrulama bileşenleri ayrı hazırlanmalı;
2025 final testi kapalıdır. Araştırma sorusu, önceden belirlenmiş deney
karşılaştırmaları ve başarı/sınırlama ayrımı
[makale protokolünde](research/ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md)
korunur. Bu kayıt TÜBİTAK'a başvuru, destek veya danışman onayı değildir.

## Tekrar üretim ve dosyalar

Yeni `scripts/quality/profile_training_dataset.py`, beklenen SHA ile
tam aday audit'ini, bitmiş kaynak indeksi ve 72 aylık raporunu kontrol
eder; donmuş kaynak registry'sini kullanır. Ortak sayım yöntemi
`src/wildfire_risk_prediction/dataset_quality.py` içindedir. Üretim
ve kabul edilmiş bilimsel kod/paketler değiştirilmedi. Ağ engelli profil
ayrı yeni sonuç dizinine yazılır; eski çıktılar üzerine yazılmaz.

```powershell
.\.venv\Scripts\python.exe scripts/quality/profile_training_dataset.py `
  --accepted-audit outputs/reports/dataset/candidate_audit_v1/20261014T143254Z_0a72ff05/readback.json `
  --expected-audit-sha256 c39536f74cf1b44dec1eec08b94941b495132e759d6ed0005a88110c1f46dbe8
```

- Tam batch indeksi SHA-256:
  `1964c76f773f2a0c48ae1128d47f43d8772a5c2829e9fcedd55b3ef095876647`.
- Tam takvim audit'i SHA-256:
  `c39536f74cf1b44dec1eec08b94941b495132e759d6ed0005a88110c1f46dbe8`.
- Son kalite profili:
  `outputs/reports/dataset/quality_profile_v1/20261014T144247Z_851417d0/readback.json`;
  SHA-256 `ecd617369a1a24237059361b53c95edb8fe58a49d8bb95ea61e8f20a8c649911`.
  İlk profil `20261014T143917Z_863886e0` altında, SHA-256
  `1530a4b0e7d74e4a0fa42d16cfee85e728dcada90fc8e37a3c2443df436255c9`
  ile korunur. Son sürüm kaynak indekste unknown koşulunu ayrıca
  zorunlu kıldı; iki profilin sayım/ay/yıl/inceleme sonuçları eşittir.
- Kapanış geri okuması:
  `outputs/reports/dataset/training_join_2026-10-14/completion_quality_readback_20261014.json`;
  SHA-256 `fbaa3e19d92e4143387be93597a3ac7f08e75178390f62a08874309a9cdb49e7`.
  83 kalite kaynak/yöntem kimliği ve 22 donmuş bulut girdisi eşleşti;
  eski kabul dosyaları değiştirilmedi.
- Yeni kalite, mevcut hazırlık ve CLI testleri **58 passed**; lint ve
  format geçti. Hatalı sayım, değişmiş kapı/şema, kısmi/tekrarlı ve
  kapalı dönem takvimi reddi; ağırlıklı oran ve hedef uç noktası test edildi.

Makine raporları ve veri parçaları Git'e eklenmez. Kod, testler ve bu
araştırma kaydı gizlilik denetimi sonrası sürümlenir.
