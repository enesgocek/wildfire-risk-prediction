# Temmuz 2023 aylık sonuç denetimi

Colab işini tamamlayıp sonuç ZIP'ini ilgili klasöre yerleştirdim.
Tam ayın bağımsız yerel tablo/kaynak/zaman denetimi geçti. FIRMS arşivi ile
karşılaştırma, resmî eksik veri günleriyle örtüşen ayrı bir kalite bulgusu verdi.
Bu sonuç nihai eğitim tablosu veya yangın etiketi değildir.

## Tamamlanan kapsam

| Ölçüm | Sonuç |
|---|---:|
| Eğitim dönemi | 1–31 Temmuz 2023 |
| Gün | 31/31 |
| Dosya çifti | 270: 264 yeni, 6 hazır günden |
| Hücre | 2.899 |
| Günlük hücre kaydı | 89.869 |
| Hücre/tarama satırı | 921.155 |
| Tam granül tarama satırı | 54.517 |
| Gelen ZIP | 16.894.316 bayt, yaklaşık 16,89 MB |
| Bulut sınıfı merkezi görülen gün | 25 |

ZIP SHA256:
`d2c3fd4f057a093343da86eed2df78e205eed913fbd56878210361990f2e3857`.
Paket SHA256:
`201a8b21874bd98d22a92e6ac8d93301a4beb05e7274396450c2f76a70313374`.
Manifest SHA256:
`6bb86e800e9045eefd7ee5290460c706065a9e651ed27068a8d4fc85ce81714e`.

156 ZIP üyesi/CRC, paket/kod/coğrafya kimlikleri, 31 gün, 270 kaynak kimliği,
2899 hücre/gün anahtarları, CSV özetleri, alan sınır/oranları, sınıf sayımları,
tarama zaman eşleşmeleri ve bağımsız zaman birleşimi/boşluğu kontrol edildi.
Her çiftin sınıf ve QA sayımları, günlük hücre/tarama satırlarıyla ayrıca
geri karşılaştırıldı. Kaynak ve gelen ZIP'ler değiştirilmedi.

58.629.036 piksel merkezi kaydı farklı uydu geçişlerindeki tekrarları içerir;
tekil alan veya bağımsız yangın sayısı değildir. Doğal sınıflarda 800 nominal,
44 yüksek ve 60 düşük güvenli termal kayıt var. Bunlar bitki yangını nedeni,
FIRMS Type sınıfı veya bağımsız yangın olayı anlamına gelmez.

## Resmî FIRMS arşiv boşluğu

Yerel FIRMS arşivindeki 783 nominal/yüksek güvenli Temmuz kaydının tamamı
seçilen granül aralıklarına tekil eşleşti. 260 çiftte güven/hücre sayımları
aynı. NOAA-20'nin 10 diğer çiftinde doğal ürün 59 nominal + 2 yüksek güvenli
termal kayıt içeriyor; ilgili FIRMS arşivinde bunlar yok.

Farkların tamamı **19–22 Temmuz 2023** günlerinde. Değişmemiş özgün Türkiye
NOAA-20 arşiv CSV'si bu dört günün her birinde sıfır kayıt içeriyor; dolayısıyla
fark pilot alan filtresinden kaynaklanmıyor. NASA'nın güncel
[FIRMS eksik veri tablosu](https://firms.modaps.eosdis.nasa.gov/api/missing_data/)
bu dört günü NOAA-20 Standard Data için eksik olarak listeliyor.
Sayfanın kendi JavaScript'inin kullandığı public JSON uç noktası okunup ayrı
SHA'lı snapshot olarak saklandı. Mevcut MODAPS sensör kesinti snapshot'ları
değiştirilmedi.

Bu kanıt **FIRMS veritabanı boşluğunu** destekler; fiziksel sensörün hiç
gözlem yapmadığını veya tarihsel üretim hatasının nedenini kanıtlamaz.
L2 kaynaklarında gözlem ve termal sınıflar mevcut. 61 kayıt arşive sessizce
eklenmedi; kaynak farkı olarak saklandı. FIRMS Type teyidi hâlâ açık konu.
FIRMS arşivindeki yokluk, bu gün/hücrelerde negatif yangın etiketi kanıtı
olarak kullanılmayacak. Günlük durum `unknown`, negatif etiket izni `false`.

## Denetim sınırları ve sonraki adım

Küçük ZIP'te tam geometri veya ham kaynaklar bulunmadığı için bütün ayın
alanlarını sıfırdan geometriyle yeniden hesaplamadık. Geometrik birleşim
Colab işinde yapıldı; B günündeki bağımsız geometri provası önce tamamlandı.
Yerel denetim sayısal alan/kaynak/zaman tutarlılığını sınar. Uzak Drive yeniden
bağlamasını ZIP tek başına bağımsız kanıtlamaz.

Kompakt ZIP, çift başına süre, CPU/RSS ve indirme/kayıt sürelerinin ayrıntılı
metriklerini içermiyor. Tam iş süresi veya hız darboğazı bu ZIP'ten kesin
çıkarılmayacak; gelecekteki bulut hız denemesinde adımlar ayrı ölçülecek.
270 çiftin toplam nominal kaynak boyutu yaklaşık 49,40 GB; hazır gün dışındaki
264 yeni çiftin kaynak boyutu toplamı 48,30 GB. Bu değer başarısız yeniden indirmeler
dahil gerçek ağ trafiği ölçümü değildir.

Temmuz ayı gözlem tanıları tamamlandı. 6 Ekim'de Google Cloud Free trial
kredisi ve son tarihi, global ve us-central1 kotaları okundu. Frankfurt formunu seçtim; o bölgenin kotası ve GCP işçisi açık. Oluşturma
sabah oturumuna ertelendi; yeni kaynak/harcama başlatılmadı.
Yeni bulut işi tamamlanan ayı yeniden işleme kapsamına dahil etmeyecek.

Yerel raporlar:

- `outputs/reports/observation_coverage/colab_month_received_verification.json`
- `outputs/reports/observation_coverage/colab_month_completed_diagnostics.json`
- `outputs/reports/observation_coverage/colab_month_archive_gap_resolution.json`
- `outputs/reports/observation_coverage/month_2023_07_archive_gap.csv`
- `outputs/reports/observation_coverage/month_sources/FIRMS_missing_data.json`

Ek bağımsız yerel betikler `outputs/verification/audit_completed_month.py` ve
`outputs/verification/resolve_month_archive_gap.py` altında; kaynak sonuçlarla
birlikte Git kapsamı dışında. Üretim işleyicisi/paket değiştirilmedi.
