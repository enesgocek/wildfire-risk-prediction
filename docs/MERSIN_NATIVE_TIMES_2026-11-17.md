# Mersin ham dosyalarında gerçek tarama saatleri — 17 Kasım 2026

Önceki yerel envanterin sekiz çifti 24 kayıtlık saat örnekleminin
77 komşu nominal günüyle tarih üzerinden kesişmişti. Bu çalışmada
16 ham dosyanın hash'leri yeniden doğrulandı. Geolocation dosyalarından
1.617 taramanın başlangıç/bitiş değerleri ve kayıtlı TAI93 farkı okundu.
UTC zamanları mevcut açık-sol, kapalı-sağ proje penceresiyle sınandı.

Tarih kesişimi yalnız WF1487 kaydının Türkiye saati yorumunda oluşuyor.
Bu yorumda bildirilen zaman 16 Ağustos 2021 21.30 UTC, hedef pencere
16 Ağustos 00.00 UTC sonrasından 17 Ağustos 00.00 UTC dahil aralık.
Sekiz çiftin bütün taramaları 15 Ağustos'ta. Hedef penceresine giren
tarama sayısı sıfır. En son dosya 15 Ağustos 23.35.59,699 UTC'de
bitiyor; bildirilen zamandan yaklaşık 21 saat 54 dakika önce.

17 Kasım yerel kaynak raporundaki tarih kesişimi bulgusu korunuyor.
Bu yeni zaman kontrolü, söz konusu dosyalardan olay anındaki nokta
sınıfını değerlendirme beklentisini düzeltiyor. Piksel sınıflandırması
uygun zamanlı ham kaynak bekliyor. Günlük gözlem `unknown`, negatif
etiket izni `false`. Birinci aşama açık.

## Hedef zamandaki kaynak

Kabul edilmiş Ağustos paketinin 15–17 Ağustos günlük üyeleri hash'leriyle
geri okundu. Aynı hücrede, bildirilen zamandan sonra hedef penceresi
içinde iki tarama satırı var. İkisi de `N20:2021228.2312` çiftinde.
Başlangıçları 16 Ağustos 23.16.12,219 ve 23.16.14,006 UTC.
Seçili kara merkezi sayıları sırasıyla 5 ve 104. Bu hücre sayıları
olay noktasının bulutsuz gözlendiğini henüz belirlemiyor.

Çift önceki 292 çiftlik kaynak planında mevcut. İki dosyanın toplam
boyutu 176.557.039 bayt. Mevcut tek çift indirme aracı için yeni plan
hazırlandı ve aracın normal plan okuma girişinden doğrulandı.
Yerel çalışma, 900 saniyelik sınır ve önceki dosya koruma kuralları
bu planda kayıtlı. Kimlik doğrulaması için kullanıcı girişi gerekiyor.

Plan
`outputs/reports/dataset/observation_core_transfer_v1/20261117T205200Z_ec3e6131/native_plan.json`.
PowerShell'de proje klasöründen çalıştırılabilir.

```powershell
.\.venv\Scripts\python.exe scripts/firms/run_observation_core_pair.py --plan outputs/reports/dataset/observation_core_transfer_v1/20261117T205200Z_ec3e6131/native_plan.json --run-one --prompt-login
```

Sonraki aşamada bu çiftin dosya/header kabulü ve olay konumunun piksel
geometrisiyle karşılaştırılması yapılacak. Koordinatın başlangıcı temsil
etmesi ve kaynak saati belirsizliği ayrıca açık.

## Yeniden üretim

`python scripts/quality/audit_mersin_native_times.py` yerel saat denetimini
ve tek çift hazırlığını yeniden üretir. İlgili 110 test ve Ruff geçti.
Yerel makbuz
`outputs/reports/dataset/mersin_native_times_v1/20261117T205152Z_0aff74dc/readback.json`.
SHA-256 `12d6fbcf982808e1fc953506368f5a2896ebaaaa946c72f97e005c89bb447fdc`.
