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
