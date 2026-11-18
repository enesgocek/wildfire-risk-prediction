# Mersin referanslarında ortak kanıt tablosu — 18 Kasım 2026

Saat ve konum duyarlılığı, CORINE 2018 örtüsü ve önceki yakın kayıt
incelemesi aynı 479 eğitim dönemi arşiv satırında birleştirildi.
Bu işlem araştırma kanıtlarının bağlanmasıdır. Nihai etiketli eğitim
veri setinin birleştirilmesi ayrıca son kontrol ve kullanıcı onayı bekliyor.

## Kayıtların birlikte görünümü

| İnceleme kapsamı | Kayıt | Merkez orman/çalılık | Merkez tarım | Merkez diğer |
|---|---:|---:|---:|---:|
| Saat bağlantılı bütün kayıtlar | 479 | 337 | 129 | 13 |
| Hedef günü aynı ve 250 m çevre tek hücrede | 375 | 268 | 98 | 9 |
| Hedef günü aynı ve 1 km çevre tek hücrede | 174 | 127 | 44 | 3 |

Bu yarıçaplar kaynakta ölçülmüş koordinat hatası yerine varsayımsal
konum duyarlılığı ölçekleri olarak kullanıldı. Hedef gününün aynı kalması
yalnız iki saat yorumuna karşı kontrol edildi. İki tablonun geçici saat
bağlantısı ve olay kimliği belirsizlikleri korunuyor.

## Merkez ve çevre örtüsü

CORINE haritasında 100 m raster piksellerinin merkezleri kullanıldı.
250 m ve 1 km çevreler önce EPSG:6933 düzleminde kuruldu, sonra
rasterin koordinat sistemine dönüştürüldü. Çevre içindeki örneklenen,
haritada karşılığı bulunan, orman/çalılık ve tarım pikselleri ayrı sayıldı.
Her iki çevrede 479 kaydın tamamında örneklenen pikseller haritada tanımlı.
Bu kaynak desteği olay tarihindeki örtü doğruluğunu belirlemiyor.

| Merkezi orman/çalılık olan kapsam | Kayıt | 250 m çevrede tarım pikseli var | 1 km çevrede tarım pikseli var |
|---|---:|---:|---:|
| Bütün saat bağlantılı kayıtlar | 337 | 138 | 260 |
| Hedef günü aynı ve 250 m çevre tek hücrede | 268 | 112 | 205 |
| Hedef günü aynı ve 1 km çevre tek hücrede | 127 | 51 | 97 |

Tarım komşuluğu bulunan kayıtların olay örtüsü belirsizliği ayrı
incelenecek. 2018 haritasındaki merkez sınıfı, 2018–2023 olaylarının
başlangıç örtüsünü tek başına belirlemiyor. Bu incelemede asgari
orman oranı veya tarım komşuluğuna göre dışlama eşiği seçilmedi.

## Olay kimliği işaretleri

Yakınlık işaretleri bütün 479 kayıt üzerinden hesaplandı. Önce alt grup
seçilip komşuların görünmez hale gelmesine izin verilmedi. Önceki
60 dakika/5 km karşılaştırmasındaki 7 çift ve 11 satır, 24 saat/10 km
karşılaştırmasındaki 35 çift ve 46 satır tekrar bulundu.

Merkezi orman/çalılık olan 337 kaydın 4'ü dar, 28'i geniş yakınlık
işareti taşıyor. Ortak 250 m grubundaki 268 orman/çalılık merkezinin
4'ü dar, 25'i geniş işaret taşıyor. 1 km grubunda bu sayılar 2 ve 17.
Yakınlık işareti aynı yangını veya ayrı başlangıcı doğrulamıyor.
Bu işaretin bulunmadığı satırların da özgün olay kimliği açık.

## Sonuç ve sonraki iş

479 kayıt artık aynı inceleme satırında saat, konum, merkez/çevre
örtüsü ve yakın kayıt bilgisiyle izlenebiliyor. Sonraki adım,
ortak grupları mevcut olay tarihi görüntüleri ve bağımsız başlangıç
kanıtlarıyla eşleştirmek. İlk örtü, olay kimliği ve kayıt kapsamı
kabulü açık. Günlük gözlem `unknown`, negatif etiket izni `false`.
Birinci aşama sürüyor.

`python scripts/quality/audit_mersin_joint_reference.py` önceki makbuz,
arşiv, il sınırı, grid, CORINE makbuzu ve raster hash'lerini doğrular.
479 kayıt korundu, dört yakınlık sayımı önceki sonuçla uyuştu. İç içe
çevrelerde piksel sayılarının tutarlılığı ve orman merkezlerinin yakın
çevrede bulunması kontrol edildi. 54 ilgili test ve Ruff geçti.

Yerel makbuz
`outputs/reports/dataset/mersin_joint_reference_v1/20261118T140734Z_19b35a6d/readback.json`.
SHA-256 `20c458af72b4a77e69d9e4713acfe91bbeaaaac2322165fa6e2a4fe248bcf5bc`.
