# Sınıf ağırlıkları ve kalibrasyon karşılaştırma planı

Tarih: 16 Ekim 2026. Durum: kaynaklarla hazırlanmış **deney taslağı** ve
sentetik kontrol. Gerçek sınıf oranı ölçülmedi; ağırlık/kalibrasyon yöntemi
seçilmedi. Gerçek model veya kalibratör eğitilmedi, kabul kapıları açılmadı.

## Kaynak dayanakları

16 Ekim'de aşağıdaki birincil teknik belgeler web üzerinden kontrol edildi.
Bağlantılar dinamiktir; web sayfalarının tamamı yerel arşivlenmedi.

| Kaynak | Bu plana dayanağı |
|---|---|
| [scikit-learn: sınıf ağırlığı](https://scikit-learn.org/stable/modules/generated/sklearn.utils.class_weight.compute_class_weight.html) | Balanced ağırlığın sınıf sayısından hesaplanması; hiçbir üstünlük garantisi vermez |
| [imbalanced-learn: veri sızıntısı](https://imbalanced-learn.org/stable/common_pitfalls.html) | Ayrımdan önce yeniden örnekleme bilgi sızdırabilir; değerlendirmeyi yapay dengelemek kullanım dağılımını değiştirir |
| [scikit-learn: kalibrasyon](https://scikit-learn.org/stable/modules/calibration.html) | Modelden ayrı kalibrasyon verisi, sigmoid/isotonic sınırlamaları ve güvenilirlik grafikleri |
| [CalibratedClassifierCV sözleşmesi](https://scikit-learn.org/stable/modules/generated/sklearn.calibration.CalibratedClassifierCV.html) | Hazır eğitilmiş modelde ayrık veri sorumluluğu ve küçük örnekte isotonic aşırı uyum riski |

Bu kaynaklar yöntem davranışını açıklar; Antalya/Muğla/İzmir/Mersin'deki
modelimizin başarılı olacağına kanıt değildir. Bu çalışmada kullanılan
yerel scikit-learn sürümü 1.9.1'dir; yeni kütüphane kurulmadı.

## Önerilen ilk karşılaştırma

Önerim, yeniden örnekleme yapmadan iki ağırlık kolunu aynı temel modellerde
karşılaştırmaktır. Ağırlıksız kol referanstır; balanced kol yalnız temel
modelin fit bölümündeki kabul edilmiş sınıflardan hesaplanır. Çok küçük bir
pozitif sınıfta ağırlık büyüyebilir; gürültülü etiketi daha etkili kılma riski
de değerlendirilir. Kullanıcı gerçek yöntemi henüz seçmedi.

| Temel modelin fit ağırlığı | Olasılık çıktısı | Taslak durumu |
|---|---|---|
| Ağırlıksız | Ham | Referans adayı |
| Ağırlıksız | Sigmoid | Kalibrasyon karşılaştırması adayı |
| Ağırlıksız | Isotonic | Yeterli veri/olay desteği varsa aday |
| Balanced | Ham | Sınıf ağırlığı etkisi adayı |
| Balanced | Sigmoid | Ağırlık + kalibrasyon adayı |
| Balanced | Isotonic | Yeterli veri/olay desteği varsa aday |

Bu altı hücre, çalıştırılmış altı deney veya altı model sonucu değildir.
Gerçek arama bütçesi/seed ve kabul edilen özellik/etiket evreni henüz
dondurulmadı. Isotonic iki kolun da otomatik zorunlu parçası değildir.
Model API'lerinin ağırlık uygulaması ayrıca doğrulanacak; farklı modellerin
benzer isimli ağırlık parametreleri eşdeğer kabul edilmeyecektir.

İkili balanced formülü `w_c = N_fit / (2 × N_fit,c)` olarak kontrol edildi.
Gerçek `N_fit,c` yalnız kabul edilmiş eğitim hedeflerinden hesaplanabilir;
mevcut unknown kayıtlar negatif yapılamaz. Örneğin 90 negatif/10 pozitif
**sentetik birimde** ağırlıklar 0,555556 ve 5'tir. Bu 100 birim bağımsız
yangın sayısı veya gerçek veri setinin sınıf oranı değildir.

SMOTE/oversampling/undersampling ilk önerilen matrise alınmadı. Sonradan
gerekirse ayrı deney, yalnız fit bölümü ve kayıtlı örnekleme olasılıklarıyla
ele alınır. Amaçlı inceleme örneklerinin seçim ağırlıkları, sınıf dengeleme
ağırlığıyla aynı şey değildir; körlemesine çarpılıp olasılık düzeltmesi
diye sunulamaz. Kabul edilmiş değerlendirme evreninin oranı korunur;
bu evren bütün gerçek yangınların veya bütün Türkiye'nin dağılımı değildir.

## Veri rolleri: araştırmacının seçtiği hazırlık yönü

Kalibrasyon model skorundan olasılığa bir eşleme öğrenir. Kalibratörün
öğrendiği kayıtlar, temel modelin fit kayıtları ve bağımsız değerlendirme
kayıtlarıyla karıştırılmamalıdır. Önerilen yıllar bir takvim taslağıdır:
hedef penceresi, aynı olayın yıl sınırını aşması, embargo ve mekânsal
bağımlılık denetimleri uygulanmadan gerçek ayrım sayılmaz.

| Aşama | Temel model/ön işleme fit | Kalibratör fit | Karşılaştırma |
|---|---|---|---|
| Eğitim içi yöntem incelemesi adayı | 2018–2021 | 2022 | 2023 |
| 2024 doğrulamasına götürülecek aday | 2018–2022 | 2023 | 2024 |
| Dondurulmuş son değerlendirme | Önceden dondurulmuş model | Önceden dondurulmuş kalibratör | 2025, tek final |

Bu yön, 2018–2023 eğitim geliştirme döneminin içinde roller ayırır;
2023 atılmaz, temel sınıflandırıcı yerine kalibrasyonda kullanılır.
Avantajı, 2024'ü kalibratör fitine harcamadan karşılaştırmada tutmaktır.
Bedeli, temel modelin 2023 kayıtlarından doğrudan öğrenmemesi ve zamanla
değişen ilişkilere uyumun sınanması gereğidir. Gerçek etiketlerin il/mevsim,
bağımsız olay ve iki sınıf desteği bilinmediğinden uygunluk onaylanmadı.

Alternatif olarak 2024'ün ayrık kalibrasyon/karşılaştırma bölümleri
tasarlanabilir. Bu durumda 2024'e ait roller ve seçim yanlılığı açıkça
yeniden kararlaştırılmalı; aynı kayıt kalibrasyonun bağımsız başarısı diye
kullanılmamalıdır. 12 Ekim makale protokolü bu rol ayrımını henüz öneri
olarak bırakmıştı. Araştırmacı 16 Ekim'de **2023 kalibrasyon, 2024
karşılaştırma yönünü hazırlama** seçeneğini açıkça kabul etti. Bu, etiket
dağılımı/olay desteği doğrulaması veya eğitime başlama onayı değildir.
Eski protokolün geçmiş metni ve bağlı deney kayıtları değiştirilmedi;
yeni yönün gelecekteki deney girişine ayrıca bağlanması gerekir.

Her ham/kalibre karşılaştırma **aynı fit edilmiş temel model ve aynı
değerlendirme satırlarıyla** yapılacaktır. Ön işleme ve sınıf ağırlığı yalnız
temel fit bölümünden öğrenilir; kalibrasyon/değerlendirmeye sınıf dengeleme
uygulanmaz. Sonradan temel model 2023 eklenerek yeniden fit edilirse eski
kalibratör otomatik taşınamaz; yeni ayrık kalibrasyon düzeni gerekir.
Kalibrasyona giren ham skorlar, ait oldukları model kimliğiyle saklanmalıdır.

## Ölçüm ve kabul planı

AP ana sıralama ölçütü olarak korunur. Kalibrasyon tercihi yalnız AP'ye
bakılarak seçilmez: Brier, log-loss ve güvenilirlik eğrisi birlikte raporlanır.
Bu kayıplar yalnız kalibrasyonu ölçmez; ayrıştırma gücünden de etkilenir.
Ham ve kalibre sonuçlar eşlenik aynı satırlarda, il/mevsim ve kabul kapsamı
paydalarıyla gösterilir. Isotonic'in basamakları eşit skorlar oluşturabilir;
AP'nin değişmeyeceği varsayılmaz. Nihai seçim kuralı ve kabul toleransları
önceden yazılacaktır; şu anda sayısal eşik uydurulmadı.

Sigmoid daha kısıtlı biçim varsayar; isotonic daha esnektir ve küçük örnekte
aşırı uyuma açıktır. Hücre-gün sayısının büyük olması yeterli bağımsız olay
desteği olduğu anlamına gelmez. Kütüphane örnek sayısı önerileri bağımsız
yangın olayı alt sınırına çevrilmedi. Asgari olay sayısı, güven aralığı
blokları, histogram dilimi, günlük K ve seçim kuralı açık kalır.
Tek sınıflı veya olayı yetersiz bölümde yöntemi otomatik değiştirmek veya
unknown kayıtları doldurmak yerine neden ve eksik destek kaydedilecektir.

2024 doğrulamasındaki seçim sonuçları bağımsız final başarısı sayılmaz.
2025, veri/model/kalibrasyon/etiket sürümleri ve seçim kuralı dondurulduktan
sonra değerlendirilir. Mevcut negatif etiket ve son birleştirme onay kapıları
aynen korunur; bu taslak gerçek deney girişini açmaz.

## Gerçekleşen hazırlık kontrolleri

[Sürümlü plan](../configs/imbalance_calibration_plan_v1.json) ve
`prepare_imbalance_calibration_plan.py` eklendi. Betik ağ bağlantısını
kapatır; mevcut deney hazırlığının 44 girdisini ve dört çıktısını hash ile
geri kontrol eder. Altı aday karşılaştırma satırı üretir, hepsi çalıştırılmadı
durumundadır. Gerçek 0/1 hedef veya özellik tablosu fit edilmez.

Altı sentetik sınıf dağılımında balanced hesap mevcut kütüphaneyle 1e-12
toleransta uzlaştı; toplam sınıf ağırlıkları da kontrol edildi. Üç eğitim
yılına ait birer oyuncak metadata satırıyla geçerli rol sırası geçti.
Fit/kalibrasyon, fit/değerlendirme ve kalibrasyon/değerlendirme ortak olayları,
modelin kendi kayıtlarında kalibrasyon ve 2025 kullanımı: **beş hatalı
senaryo reddedildi**. Bu oyuncak kontroller gerçek olay üyeliği doğrulaması
veya hazır bir üç bölümlü eğitim/kalibrasyon uygulaması değildir.

**Mevcut 193 ilgili test yeniden çalıştırıldı ve geçti**; yeni birim testi
sayısı eklenmedi. Yeni betikte lint/format geçti. Önceki bilimsel kaynaklar
değiştirilmedi. Son kapanış **52 bağlı girdi/beş çıktı** içerir. Gerçek
sınıflandırıcı/kalibratör fit sayısı, ağ baytı ve bulut işi sıfırdır;
2024/2025 veri kaynağı açılmadı.

Yanıt öncesi geliştirme çıktısı korundu; kullanıcı kararı sonrası plan ve
betik yeniden çalıştırılarak yeni sonuç üretildi. Aşağıdaki kapanış güncel
karar ve girdilere aittir; önceki geliştirme kapanışı güncel kabul sayılmaz.
Çıktı: `outputs/reports/dataset/imbalance_calibration_plan_v1/20261016T130102Z_b916804c/`.
Readback SHA-256:
`9fe78387323202ff09ff68a06215f1bc3540da434c74c053b6669df096e0a4f6`.
Kapanış SHA-256:
`8bb1ac8b53d58d995b95872eecc859d7933eea12e319abc9ce0a60900734dec1`.

## Açık kararlar ve sonraki adım

Araştırmacının veri rolü yönü tercihi kaydedildi; gerçek sınıf ağırlığı,
kalibrasyon yöntemi, embargo ve destek eşikleri seçilmedi. Etiketler
kabul edildiğinde sınıf/hücre/tekil olay ve kapsam sayımları her rol için
ayrı çıkarılmalı; önerilen takvimin uygulanabilirliği yeniden incelenmelidir.
Bağımsız ilerletilebilecek sonraki hazırlık, hata analizinde il/mevsim ve
gözlem kapsamı paydalarını birlikte gösterecek rapor şemasıdır.
