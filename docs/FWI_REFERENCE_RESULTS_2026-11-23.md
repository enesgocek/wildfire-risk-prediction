# Önceki gün FWI referansı ile sabit modellerin karşılaştırması

23 Kasım 2026. Araştırmacının somut A önerisinden sonra verdiği
“projeye devam et” yönü, bu sınırlı karşılaştırmaya devam talimatı
olarak kaydedildi; açıkça “A” yazdığı iddia edilmedi. Yeni eğitim,
indirme, gerçek Y/L veya nihai birleştirme yetkisi çıkarılmadı.

**Karşılaştırma ve bağımsız geri okuma tamam. Bu küçük Haziran
kesitinde dokuz modelin FWI'ye belirgin üstünlüğü gösterilmedi.**
Bu bir gerçek yangın testi, AP, operasyonel geçmiş tahmin başarımı
veya ana PU yönteminin kabul/red kanıtı değildir.

## Ne yapıldı ve ne bulundu?

Mevcut Mersin takviminde 2–30 Haziran 2022 için 7 hücre / 203
hücre-gün, 7 kaynak takvimi anahtarı var. Önceki nominal günün
FWI'si, her hücre merkezine en yakın özgün 0,25° noktadan alındı.
Dokuz modelin önceki skor CSV'leri kullanıldı; model dosyalarının
hash'i korundu, modeller yüklenmedi veya yeniden fit edilmedi.
203 satırın tamamında FWI ve dokuz skor sonlu; eksiklik nedeniyle
satır/çift kaybı yok. Diğer günler gerçek negatif yapılmadı.

| Aynı 196 hücre–ay içi gün çifti | Doğru sıralama kredisi | Yardımcı çift AUC |
|---|---:|---:|
| Önceki nominal gün FWI | 125 / 196 | 0,637755 |
| Dokuz sabit modelin aralığı | 120–126 / 196 | 0,612245–0,642857 |

Bu kesitte en yüksek model değeri FWI'den yalnız bir çift daha
fazla kredi alıyor; dokuz ayardan üretim kazananı seçilmedi.
İstatistiksel anlamlılık, genellenebilir iyileştirme veya yüzde
yangın doğruluğu iddiası kurulmadı. 196 çift, **196 bağımsız yangın
değil**: aynı yedi kaynak günü tekrar tekrar karşılaştırılıyor.

| Gün yakınlığı/yönü | Çift | FWI | Dokuz modelin aralığı |
|---|---:|---:|---:|
| 1–3 gün uzaklık | 42 | 0,547619 | 0,476190–0,547619 |
| 4–30 gün uzaklık | 154 | 0,662338 | 0,649351–0,675325 |
| Karşılaştırılan gün kaynak gününden önce | 120 | 0,733333 | 0,708333–0,758333 |
| Karşılaştırılan gün kaynak gününden sonra | 76 | 0,486842 | 0,394737–0,500000 |

Yakın gün ayrımı zayıf; daha uzak tarihlerde daha yüksek sonuç
elde ediliyor. Bu, tek başına nedeni kanıtlamaz. Kaynak günü
anlamı, mevsim içi değişim, kayıt kapsamı ve gözlem belirsizliği
ayrı konular olarak kaldı. Sonuçtan yalnız modelin veya yalnız
kaynağın yanlış olduğu çıkarılmadı.

Somut örnek: `C661/R875` hücresinin 9 Haziran kaynak gününde önceki
nominal gün FWI'si yaklaşık 0,074219. O hücredeki diğer 28 güne
karşı FWI yalnız 2 çiftte yüksek kalıyor. `C647/R866` hücresinin
23 Haziran kaynak gününde ise 28/28. Bu fark, her kaynak kaydının
meteorolojik endeksle aynı biçimde sıralanmadığını gösterir;
gerçek yangın etiketi veya kaynak hatası tanısı değildir.

## Coğrafya, zaman ve örneklem sınırları

Tam hücre geometrisinin EPSG:6933 merkezi, hücre kimliğinden
bağımsız hesaplanan merkezle 1 cm sayısal tolerans içinde eşleşti.
En büyük geri dönüş farkı yaklaşık 0,54 mm. WGS84 enlem/boylamı
özgün coğrafi ızgarayla açısal olarak hizalama varsayımı açık:
GRIB küresi ile WGS84 jeodezik datumlarının eşdeğerliği kanıtlanmış
sayılmadı. Kaynak küresi uzaklığı, bağımsız haversine hesabı ve
birim küre üzerindeki kiriş uzaklığı aynı düğümleri verdi.
WGS84 uzaklığı kullanıldığında da bu yedi seçim değişmedi.

Yedi ayrı özgün düğüm seçildi; eşit uzaklık yok. Hücre merkezinden
seçilen düğüme uzaklık yaklaşık 4,09–17,13 km. Bu uzaklıklar ve
0,25° ürün çözünürlüğü nedeniyle referans yerel 5 km ölçüm gibi
sunulmadı. En yakın nokta eksik çıksaydı başka geçerli komşuya
taşınmayacaktı; bu kesitte seçilen bütün örnekler sonlu.

Bir gün takvim kaydırması **yalnız bu geriye dönük referans
karşılaştırmasının** yönüdür. Örneğin 2 Haziran hedef takvimine
1 Haziran alanı bağlandı. Gerçek erişim gecikmesi, bütün ayın
forcing başlıkları ve tahmin anından kesin önce bilinme koşulu
doğrulanmış değil. Ana model girdisi veya operasyonel ürün
kabulüne dönüşmedi. [Özgün saat ve artım yorumunun sınırı](FWI_LOCAL_TIME_REVIEW_2026-11-23.md).

## Veriseti hazırlığına katkısı ve sonraki karar

Meteorolojik karşılaştırma referansının dosya, zaman varsayımı,
coğrafi örnekleme ve skor karşılaştırma yolu somut ve tekrarlanabilir
hale geldi. Günlük model ayrımındaki zayıflığın, bu küçük örnekte
FWI eklenince kendiliğinden çözüldüğü gösterilmedi. Mevcut ayarlarla
yeniden eğitim yaparak daha yüksek sayı arama gerekçesi oluşmadı.

[Birinci aşamanın üç bilimsel geçiş konusu](STAGE_ONE_DECISION_PACKET_2026-11-22.md)
bu sonuçla kapanmadı: kaynak/olay/örtü üyeliği, PU hedefe aktarım
varsayımları ve gerçek hedefi değerlendirme dayanağı. Daha geniş
FWI indirmek bu üç boşluğu tek başına gidermez; otomatik yeni
indirme veya daha fazla küçük model başlatılmadı.

Sıradaki karar hazırlığı, mevcut kanıtla hangi araştırma iddiasının
desteklendiğini ve hangi veriseti tesliminin savunulabildiğini
netleştirmektir. Özellik adaylarının varlığı ile kabul edilmiş
etiketli eğitim verisinin hazır olması ayrı kalır. Nihai beş parça
denetimi ve rapora bağlı kullanıcı birleştirme onayı korunur.

## Bağımsız kontrol ve incelenebilir çıktı

İkinci okuyucu 203 FWI örneğini ham dosyadan, dokuz modelin 1.827
kayıtlı skorunu eski CSV'lerden, 196 çift kimliğini ayrı gruplamayla
ve 50 özet / 70 hücre ölçüsünü skaler hesapla kontrol etti. Eşleşti.
İlk audit 1e-9 derece sayısal merkez toleransında durdu; merkez
farkları 0,45–0,54 mm bulundu. Üreticide zaten tanımlı 1 cm metre
toleransıyla kontrol edildi; en yakın düğüm seçimi ayrıca bağımsız
kaldı. Veri, eşleştirme veya sonuç değiştirilmedi; ilk deneme
kabul edilmiş audit sayılmadı.

Altı yeni davranış testi dahil son birleşik koşuda **39 ilgili test**
geçti; bu sayı bütün depo test sayısı değildir. Beş yeni Python
dosyası Ruff kod/biçim kontrolünden geçti. Yerel MLflow veritabanı
önce yedeklendi; 50 ölçü tam değerleriyle geri okundu. Yeni model
kaydı veya dış servis/bulut gönderimi yapılmadı.

Makbuz yolları `outputs/reports/dataset/` altında:

| Sonuç | Makbuz ve SHA-256 |
|---|---|
| Karşılaştırma | `fwi_reference_comparison_run_v1/20261123T101431Z_805e6449/readback.json` — `5e5a7bd7a920b15d1288c7969b9841c62ac9948af5e74255c901ff6eb5a4d40c` |
| Ayrı geri okuma | `fwi_reference_comparison_audit_v1/20261123T101705Z_98c1ab80/readback.json` — `3a52234b5aaf064037dd0404eb0b2c907054d91335339a952690a1f1732c7ae5` |
| Yerel kayıt | `fwi_reference_comparison_closure_v1/20261123T101840Z_4d88b019/readback.json` — `1979742ad884330fb9d40ebe124fc0e901ef247c5a37ab0c58e88b35a1b6c9a0` |

Yerel MLflow run: `08392c8a196648e29a09574452ccb21d`.
Karşılaştırma dizininde `common_calendar_review.csv`,
`native_node_mapping.csv`, `common_pairs.csv`,
`matched_reference_metrics.csv`, `per_cell_reference_metrics.csv`
bulunur. Ayrı audit dizininde `FWI_reference_comparison.png` ve
yeniden hesaplanan ölçü tablosu var. Üretilmiş CSV/JSON/PNG'ler
ve ham veri Git'e eklenmez; kod ve küçük yapılandırma izlenir.
