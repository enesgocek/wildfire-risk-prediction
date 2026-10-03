# Veri hazırlama kalite incelemesi — 2 Ekim 2026

**Sonuç:** İncelenen mevcut çıktılarda bütünlük kontrolleri geçti. Nihai eğitim
verisi onayı verilmedi. Devam eden indirmeye, ham verilere ve 2025 testine müdahale edilmedi.

| Alan | Yapılan kontrol |
|---|---|
| Proje dosyaları | Kod, yapılandırma, betik ve belgeler incelendi; dosya envanterinde boş/bozuk metin veya JSON bulunmadı. Gizli ayarlar ve büyük veri Git kapsamı dışında. |
| Ortam | 119 kurulu paket uyumlu; kilit dosyası çevrimdışı doğrulandı. 35 test ve Ruff lint/format geçti. |
| Coğrafya | AOI/grid kaynak özetleri, 2.899 benzersiz kimlik, geçerli geometriler, hücre alanları ve AOI kesişimleri doğrulandı. |
| FIRMS | İki ham arşivden pilot seçimi yeniden hesaplandı; kaynak kayıt numaraları, tüm ham alanlar, UTC zamanları ve koordinat-grid eşleşmeleri kontrol edildi. 33.255 birleşik aday kaynak tablolarla eşleşti. |
| Gruplama | Dokuz denemede eğitim tespitlerinin birer kez atanması ve küme sayımlarının tutarlılığı kontrol edildi. Bu, kümelerin gerçek yangın olduğunun doğrulaması değildir. |
| Örtü/MODIS | Örtü oranlarının sınırları, toplamları ve alanları kontrol edildi. Üç MODIS ham/çalışma raster çiftinin piksel değerleri ve hizası aynı; çalışma CRS'si doğru. Native HDF kaynak özeti eşleşti. |
| Meteoroloji | Ocak ayının 31 günü, kaynak/CSV özetleri, metadata, UTC pencereleri ve geçerli alan oranları doğrulandı. Bütün 13 özellik rasterlardan alan ağırlıklarıyla tekrar hesaplandı. |

## Düzeltilen açık

Meteoroloji indirme önbelleği ve hazırlama aşaması önceden dosya özeti ile grid
manifestini doğruluyordu; doğru dosya özetiyle yanlış tarih, kaynak, sürüm veya
özellik sırası eşleşmesi ayrıca reddedilmiyordu. `verify_archive` bu alanları,
zaman penceresini ve erişilebilirlik iddiasını da denetliyor. Geçerli dosya ve
sekiz bozuk metadata senaryosu testlere eklendi. Mevcut rasterlar yeni kontrolden
geçti; hesaplama yöntemi/sürümü ve veri değerleri değişmedi.

## Eğitimden önce kapanması gerekenler

- FIRMS Type üretim geçmişi, sabit kaynak incelemesi, olay birleştirme ve
  yıl/çalışma alanı sınırını aşan olayların ele alınması.
- Sensör/gözlem kapsamı; tespit olmayan günlerin güvenilir negatif sayılma koşulları.
- Meteoroloji eksik/kısmi kapsam politikası, ham negatif yağışın nasıl işleneceği.
  Ocak: günlük 189 eksik hücre, sıcaklıkta 310 kısmi hücre; 35 hücre-günde
  minimum -0,0000119209 mm olan negatif 24 saat toplamı.
- Tarihsel örtü ve dinamik özelliklerin yayımlanma zamanı. ERA5-Land yeniden
  analizi için `available_at` bilinmiyor; gerçek zamanlı kullanıma uygunluğu
  gösterilmiş değildir. 2017 örtü yılı, 2017'de yayımlanmış olmasını garanti etmez.
- Nihai etiket/özellik birleştirmeleri, yalnızca eğitimde öğrenilen dönüşümler,
  ayrım sınırları, mekânsal doğrulama, uçtan uca sızıntı testleri ve veri sürümü.
- Veri hacminin yeterliliği, bağımsız olay sayısı ve il/mevsim dağılımıyla ölçülecek.
  89.869 hücre-gün satırı aynı sayıda bağımsız örnek anlamına gelmez.

## Tekrar çalıştırma ve sınırlar

`scripts/quality/audit_project.py` yerelden okur, yalnızca kendi JSON raporunu yazar.
Varsayılan hava dönemi Ocak 2018'dir. Tamamlanmamış bir dönem seçilirse denetim
başarısız olur; eksik günler sessizce atlanmaz. Komutlar betik rehberindedir.
Rapor: `outputs/reports/quality/project_audit_2018-01-01_2018-02-01.json`.

Tam arazi örtüsü piksel çıkarımı yeniden çalıştırılmadı. Meteoroloji denetimi
mekânsal hazırlamayı tekrar hesaplar; tüm saatlik Earth Engine kaynağını bağımsız
yeniden indirmez. Önceki bağımsız saatlik karşılaştırma iki gün/dört noktadır.
JavaScript ihracı, dış servisler ve model performansı bu yerel denetimde yeniden
çalıştırılmadı. Devam eden Şubat–Aralık indirmesinin tamamı henüz doğrulanmadı.


## 3 Ekim takip kontrolü

2018 ve 2019 yıllarının tamamı sonradan denetlendi; toplam 730 gün ve
2.116.270 hücre-gün. Yukarıdaki Ocak/indirme durumu 2 Ekim'deki ilk incelemenin
kapsamıdır. 2019 kaynak/CSV yeniden hesaplama ve fiziksel ilişki kontrolleri
geçti; 35 test ve kod/bağımlılık kontrolleri başarılı. 2019'da günlük aynı
189 eksik hücre, 310 kısmi sıcaklık kapsamlı hücre var. Ham 24/72 saat yağışta
10.221/909 negatif hücre-gün; minimum -0,0000163227 mm. Bu değerler korundu;
eksik/kısmi kapsam ve yağış işleme politikası açık. 2025 final testi kapalı.

## 3 Ekim ikinci oturum — bütün meteoroloji dönemi

2020 kullanıcı tarafından hazırlandı ve denetlendi; kullanıcı devriyle
2021–2024 indirme, hazırlama ve yıllık denetim tamamlandı. Toplam 2.557 gün,
7.412.743 hücre-gün; eğitim 6.351.709, doğrulama 1.061.034 kayıt.
Tüm yıl denetimleri passed_with_open_gates durumunda, hata listeleri boş.

Yıllık denetime fiziksel ilişkiler ve özellik bazında min/max, eksik ve negatif
kayıt istatistikleri eklendi. Sıcaklık min/ortalama/max, çiy noktası/sıcaklık,
rüzgâr ortalama/max ilişkileri aynı alan kapsamıyla kontrol ediliyor; toprak
nemi ve negatif yağış saat sayıları sınırları denetleniyor. Ham yağışın küçük
negatif değerleri düzeltilmedi. Yeni akış ve kalite testleriyle toplam 47 test geçti.

Tüm dönem kapanış kontrolünde yıllık aralıklar eksiksiz ve tekrarsız birleşti;
aynı işleme betiği kullanıldığı ve bütün günlük CSV özetlerinin yıllık denetimle
hâlâ eşleştiği doğrulandı. 2.557 günlük native rasterda 13 özelliğin geçerli
piksel kapsamı aynı; fiziksel karşılaştırmalarda farklı kapsam sorunu bulunmadı.
Yerel rapor: outputs/reports/quality/meteorology_2018_2024_summary.json.

Günlük 189 eksik hücre ve 310 kısmi sıcaklık kapsamı tüm dönemde sürüyor.
483.273 kayıtta eksik özellik, 6.929.470 kayıtta tüm özellikler dolu. Ham
24/72 saat yağışta 28.728/1.296 negatif kayıt; minimum yaklaşık -0,0000484151 mm.
Bu sayılar nihai model uygunluğunu göstermez. Yukarıdaki kaynak erişilebilirliği,
etiket doğruluğu, eksik/kısmi kapsam ve işleme politikası sınırları devam ediyor.
2025 final testi okunmadı; saatlik kaynak tüm dönem için bağımsız yeniden
hesaplanmadı. Tek seferlik toplu akış bitti; manuel çalışma düzenine dönülecek.

## 3 Ekim sonraki aşama — model meteorolojisi kural incelemesi

[weather_model_v1](WEATHER_POLICY.md) eklendi. Kaynak ve günlük gözlem özetleri
korunarak yalnızca 2018–2023 eğitim dönemi tarandı. Alan kapsamı, eksik değer,
küçük/büyük negatif yağış ve tam/%90/pozitif kapsam profillerinin etkisi ölçüldü.
Kurallar model performansına fit edilmedi; nihai etiket ve arazi uygunluğu değildir.
Ana profil 5.291 geçici adayın bulunduğu kayıtları kapsamıyor; kayıtlar tutulur
ve bu sınır model değerlendirmesinde raporlanmalıdır.

14 yeni sınır/eksik veri/negatif yağış/test izolasyonu testiyle toplam 61 test
geçti. Üç gerçek günde çıktı geri okundu; kaynak sütunlar korundu, uygun satırlarda
model değerleri dolu ve yağış negatif değil. Kaynak dosya özetleri değişmedi.
2018–2024 için türetilmiş tabloların tam üretimi ve kapanış kontrolü henüz
yapılmadı; kullanıcı manuel prepare komutuyla bu adımı başlatacak.

## 3 Ekim kapanış — tam dönem türetilmiş meteoroloji

Kullanıcı hazırlama işlemini tamamladı. Dönem raporu ile 2018–2024'ün bütün
2.557 günlük kaynak ve çıktı dosyası salt okunur kapanış denetiminden geçti.
Tarih/grid/sürüm/şema ve dosya özetleri eşleşiyor; özgün sütunlar, NaN değerler
ve 7.412.743 kaydın tamamı korunuyor. Yağış dönüşümü ve bütün kapsam/uygunluk
bayrakları hazırlama dönüşümü çağrılmadan kaynak değerlerden tekrar hesaplandı.
Eğitim sayıları önceki eğitim incelemesiyle aynı; doğrulamaya sabit kural uygulanmış.

Ana meteoroloji profili 5.258.400 eğitim ve 878.400 doğrulama kaydını kapsar;
%90 profili 5.403.006/902.556, pozitif kapsam profili 5.937.610/991.860.
483.273 eksik kayıt ve 792.670 dolu/kısmi kayıt korunuyor. 24/72 saatte
28.728/1.296 küçük negatif toplam bayraklandı; daha büyük negatif yok.
Rapor: outputs/reports/quality/model_weather_2018_2024_audit.json.
Saatlik kaynak tekrar hesaplanmadı; önceki yıllık kaynak denetimleri kullanıldı.
2025 final testi okunmadı. Bu kontrol meteoroloji aşamasını kapatır; FIRMS tür
üretim geçmişi, olay/etiket, negatif gözlem kapsamı ve kaynak erişilebilirliği
konuları açık. Nihai eğitim veri setinin hazır olduğu anlamına gelmez.
