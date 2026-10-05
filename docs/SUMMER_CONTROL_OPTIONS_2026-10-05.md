# Yaz kontrolü için kapsam seçenekleri — 5 Ekim 2026

Kullanıcı, ayrıntılı yangın çıkış nedeni verisini bu aşamada toplamadan mevcut
veri hazırlama hattına devam etmeyi seçti. Hedef, hücre/gün bazında sonraki
24 saatte yeni yangın olayının ilk uydu tespitine ilişkin risk. Sebep tahmini
hedeflenmiyor. Bilinmeyen neden doğal yangın olarak kodlanmayacak; gerçek
yangınlar insan kaynaklı oldukları varsayılarak silinmeyecek. Neden bilgisi
eksikliği raporun sınırlamalarında tutulacak. Bu karar hedefi değiştirmiyor.

## Bu adımın amacı

14 Ocak 2019 kış kontrolünden sonra yaz döneminde termal tespit içeren küçük
örneklerle doğal uydu sınıf/kalite/zaman ve yaklaşık alan hesabını sınamak.
Henüz yeni ham indirme, Colab işi, nihai günlük etiket veya model yok.
Bu örnekler tüm dönemi temsil eden örneklem ya da üretim eşiği kalibrasyonu
olarak kullanılamaz.

## Kullanıcının seçimine sunulan alternatifler

Boyutlar mevcut katalogdan tahmin, GB ondalık (10⁹ bayt). Alternatifler
birbirine eklenmeyecek. Ham veri Colab'ın geçici diskine sırayla alınacak;
Drive'a doğrulanmış küçük sonuçlar saklanacak. Yeni işlem paketi henüz
hazırlanmadığı için nihai sonuç boyutu bu aşamada ölçülmüş değil.

| Seçenek | Eğitim günleri | Dosya çifti / dosya | Toplam tahmini trafik | Sağlayacağı kontrol |
| --- | --- | --- | --- | --- |
| A — küçük | 16 Temmuz 2023 | 2 / 4 | 0,35 GB | İki sensörün iki gece parçası; gündüz/gece veya günlük karşılaştırma sağlamaz |
| B — öneri | 16 Temmuz 2023 | 6 / 12 | 1,10 GB | İki sensörün katalogdaki aynı güne ait tüm parçaları; her sensörde gündüz/gece dosyası var |
| C — geniş | 18 Ağustos 2018, 31 Temmuz 2021, 16 Temmuz 2023 | 22 / 44 | 4,02 GB | Üç eğitim yılı; her gün iki sensör ve gündüz/gece |

En büyük geçici kaynak çifti B'de yaklaşık 187 MB, C'de 191 MB.
Bu değer ortam kurulumu, işleme belleği, ara çıktılar ve kayıt ZIP'leri için
gereken alanı içermez. Tam arşivin yaklaşık 3,17 TiB olması devam ediyor;
onu yerel bilgisayara veya Drive'a topluca indirmiyoruz. Bu kontrol kapsamı
tam dönem işlemesinin bittiği anlamına gelmiyor.

B'de arşiv güveni n/h olan 46 termal tespit var: Type 0 için 32, Type 2 için
14. A'da 38, C'de 1.680 n/h tespit var; bunlar bağımsız yangın sayısı değil.
NASA Type üretim geçmişi teyidi beklendiği için Type 0/2 sayımları ayrı
korunuyor, otomatik yangın nedeni veya bitki yangını kararı verilmiyor.

## Seçim ve denetim

- Yalnızca 2018–2023 eğitim dönemi ve Haziran–Ağustos kullanıldı. Mevcut
  pilot CSV'deki 2024 satırları sıralama/sayımdan çıkarıldı; 2025 açılmadı.
- Her yıl/sensör/gündüz-gece tabakasında n/h tespiti en fazla olan aday
  seçildi. Eşitlikte farklı hücre sayısı, gün ve dosya anahtarı kullanıldı.
  Altı yıl × iki sensör × iki mod için 24 aday var. Bu, yüksek tespitli
  stres örneklemi; yangın sıklığına ilişkin temsil iddiası yok.
- B, bu aday günlerden gerekli katalog eşleşmeleri ve her sensörde iki modu
  bulunan en az trafikli gün. C için aday yılların ilk/orta/son yılı
  (2018/2021/2023) aynı maliyet kuralıyla kullanıldı. En güçlü yangın günü
  veya bulut çeşitlemesi seçildiği iddia edilmiyor.
- 4 Ağustos 2021, katalogda S-NPP gündüz parçası bulunmadığı için bu günlük
  deneme seçeneklerine alınmadı. Bu, yangın tespitlerini silme veya günlük
  gözlemi eksiksiz sayma kararı değil.
- Dosya anahtarları metin olarak korundu. Kaynak/kod ve CSV SHA özetleri,
  bütün katalog çiftleri, tarihler, örnek sayımları ve boyutlar denetlendi.
  İkinci denetim, tüm eğitim tespitlerini bağımsız interval-tree eşleşmesiyle,
  seçilen 22 farklı çiftin sayımlarını doğrudan zaman maskeleriyle geri okudu.
  Boyut tahminlerindeki CSV kayan nokta dönüşümü için değer başına 10⁻⁶,
  toplamda 10⁻⁵ bayt tolerans kullanıldı; kimlikler ve sayımlar tam eşleşti.

## Açık konular

S-NPP'nin 31.010 eğitim pilot tespiti nominal dosya zamanlarına tekil eşleşti.
NOAA-20'nin 32.716 tespitinden 32.037'si eşleşti; **679 kayıt eşleşmedi**.
Bunlar 1 Nisan–4 Haziran 2018 arasında. Nedenleri mevcut katalog/zaman
incelemesinden belirlenmiş değil; günlük sayımları raporda korundu. Kayıtlar
silinmedi, yangın yok sayılmadı ve seçilen yaz günlerinin dışında kaldı.
Tam dönem etiket üretiminden önce bu fark ayrıca ele alınmalı.

Nominal arşiv dakikasının katalog [başlangıç, bitiş) aralığına eşleşmesi,
ham dosyanın gerçek InputPointer eşleşmesi veya doğal piksel tespiti değildir.
Bulut durumu, gerçek bitki yangını, neden, yörünge bağımsızlığı ve fiziksel
gözlem alanı bu envanterden doğrulanamaz. Günün bütün katalog parçalarını
seçmek 24 saat sürekli gözlem anlamına gelmez. `negative_label_permitted`
false; nihai negatif etiket/eşik henüz seçilmedi.

## Dosyalar ve sıradaki iş

Üretici: `scripts/firms/prepare_summer_l2_controls.py`.
Yerel bağımsız denetim: `outputs/verification/verify_summer_controls.py`.
Raporlar ve aday dosya listeleri `outputs/reports/observation_coverage/`
altındaki `summer_control_*` dosyalarında; veri/çıktılar Git kapsamı dışında.
`summer_control_readback.json` başarılı bağımsız geri okuma kaydıdır.

Kullanıcı **B seçeneğini seçti**. Eski doğrulanmış kış pilotunu değiştirmeyen
yeni Colab paketi hazırlandı. Ham çift kimliği, sınıf/kalite, yaklaşık alan
ve zaman kontrollerinden sonra sonuçlar Drive'a çift bazında kaydedilecek.
Ardından yerel sonuç denetimi yapılacak. [Çalıştırma](COLAB_SUMMER_CONTROL.md).
Katalogda
görünmeyen dosyalar veya başarısız indirmeler negatif etikete çevrilmeyecek.
