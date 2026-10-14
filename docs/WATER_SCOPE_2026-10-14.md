# Tamamen su sınıflı hücrelerin kapsam kararı — 14 Ekim 2026

Araştırmacı, sunulan A seçeneğini kabul etti: mevcut referans haritada
tamamen su sınıflı alanlar risk hesabının kapsamı dışında kalacak;
karışık kara/su hücreleri korunacak. Bu, proje kapsamına ilişkin bir
yöntem kararıdır. Tarihsel görüntüyle bağımsız doğrulama, danışman onayı
veya bütün habitat politikasının kabulü olarak kaydedilmez.

## Uygulanan kural

`configs/water_scope_v1.json`, karar tarihini, yetkiyi, referans yılını ve
etiket sınırlarını kaydeder. Donmuş 2017 örtü tablosunun ayrık sınıfları
kullanılır. Copernicus sınıf 80 kalıcı su, 200 deniz/okyanus; 90 ise otsu
sulak alandır ve yalnız su sayılmaz.
[Resmî Earth Engine veri kataloğu](https://developers.google.com/earth-engine/datasets/catalog/COPERNICUS_Landcover_100m_Proba-V-C3_Global).
Bu kural sürekli su örtü bandına veya güncel uydu görüntüsüne dayanmaz.

Bir hücre ancak **80 ve 200 dışındaki bütün ayrık sınıf payları tam sıfır**
ve su payı pozitifse kapsam dışında işaretlenir. Sınıf toplamları, türetilmiş
paylar, referans yılı, anahtarlar ve alan desteği ayrıca denetlenir.
Negatif bileşen kabul edilmez. Çok küçük pozitif kara/örtü payı sıfıra
yuvarlanmaz; belirsiz sınıf ve sulak alan payı da korunur.

`src/wildfire_risk_prediction/water_scope.py` bütün gridleri içeren ayrı
kapsam tablosu üretir. `attach_water_scope` satır sırasını, eksikleri,
hedefleri ve gözlem alanlarını değiştirmeden kapsam sütunlarını bağlar.
`retain_water_scope` bu tablodan açıkça istenen modelleme kapsamı görünümünü
seçer. Asıl özellik/gözlem dosyaları yeniden yazılmadı veya silinmedi.
Sonraki veri seti üreticisi bu sürümlü kapsamı uygulamalıdır; eski okuyucular
kendiliğinden filtrelenmiş kabul edilmez.

## Gerçek yerel sonuç

| Ölçü | Sonuç ve kapsam |
|---|---|
| Kaynak grid sayısı | 2.899 |
| Tamamen harita suyu nedeniyle kapsam dışı | 10 hücre |
| Yalnız su kuralını geçen | 2.889 hücre; nihai habitat kabulü değildir |
| Korunan karışık kara/su hücresi | 727 |
| Su sınıfı bulunmayan korunan hücre | 2.162 |
| Dışlanan hücrelerin AOI içindeki alanı | 0,612400689 km² |
| Aynı hücrelerin örtü rasterı destek alanı | 0,612400612 km²; ayrı payda |
| 2018–2023 tam takvim | 2.191 gün |
| Önceki tam grid × gün kapsamı | 6.351.709 hücre-gün |
| Su kuralının kapsam dışında bıraktığı | 21.910 hücre-gün |
| Su kuralı sonrasında kalan | 6.329.799 hücre-gün; etiketli eğitim satırı sayısı değildir |
| Eğitim aday tespit envanteri | 30.295 farklı tespit; dışlanan hücrelerde 0 |
| Önceki 400 hücre-günlük pilot | 399 kapsam içi, 1 kapsam dışı; özgün 400 örnek korunur |

Dışlanan 10 hücrenin yedisinde meteoroloji desteği `none`, üçünde `full`.
Meteoroloji desteği dışlama gerekçesi yapılmadı. Önceki `water_only_flag`
tanısıyla bütün hücrelerde uyum var. Yalnız sayısal duyarlılık için
0, 1e-12, 1e-9 ve 1e-6 toleranslarıyla su payının bire yakınlığı karşılaştırıldı;
bu veri sürümünde hepsi aynı 10 hücreyi buldu. Uygulanan kural toleranslı
yakınlık değil, su dışı bileşenlerin yokluğudur.

Tespit etkisi, hash ile bağlı `d500m_t24h_assignments.csv` dosyasının yalnız
tespit kimliği/hücre/zaman/sensör envanteri kullanılarak ölçüldü. Küme kimlikleri
karşılaştırmaya alınmadı; olay senaryosu seçilmedi. Bütün tarihler eğitim
döneminde, tespit kimlikleri tektir. Sıfır etkilenmiş aday, bu hücrelerde
gerçekte hiç yangın olmadığına ilişkin kanıt değildir.

## Karışık hücreler için ölçüm; eşik seçilmedi

Orman + çalı **ayrık sınıf alan payı** için aşağıdaki olası kesimler yalnız
ilerideki kapsam kararını değerlendirmek üzere hesaplandı. Ağaç tepe kapalılığı
veya bağımsız habitat doğruluğu ölçüsü değildir. 727 karışık hücrenin tamamı
şimdiki kapsamda kalır.

| Olası alt sınır | Karışık hücrelerden sınırı sağlayan / 727 | Su sınıfı olmayanlardan sağlayan / 2.162 |
|---|---|---|
| 0,01 | 702 | 2.037 |
| 0,10 | 650 | 1.924 |
| 0,25 | 577 | 1.776 |
| 0,50 | 474 | 1.570 |
| 0,75 | 331 | 1.294 |

Bu tablo bir eşik önerisinin bilimsel kabulü değildir. Şimdilik ilave
orman/çalı veya küçük alan kesimi uygulamadan gözlem penceresi ve etiket
kanıtını çözmek önerilir. Tarım, kent ve sulak alanların nihai uygunluğu açıktır.

## Doğrulama ve izlenebilirlik

58 ilgili test geçti: su kapsamı, habitat tanıları, arazi hesabı ve hedef
kabul korumaları. Üç yeni Python dosyası lint/format kontrolünden geçti.
İlk çalıştırmada mevcut dört testin geçici klasör izni nedeniyle kurulumu
tamamlanamadı; proje içindeki yeni geçici dizinle bütün 58 test geçti.
Çok küçük gerçek kara payı, sulak alan, bilinmeyen sınıf, bozuk anahtar,
negatif bileşen, değişmiş politika ve nullable hedef/gözlem alanlarının
korunması sınandı. Gerçek 400 örneğe filtre bağlama ve geri okuma uygulandı;
özgün örnekleme ağırlıkları değiştirilmedi, pilot yeniden örneklenmedi.

Çalıştırma: `.venv\Scripts\python.exe scripts/quality/prepare_water_scope.py`.
Ağ engellenir. Yeni sonuç dizini:
`outputs/reports/dataset/water_scope_v1/20261014T185242Z_f2e469bd/`.
Beş CSV, kaynak/kod/politika hash'leri, `readback.json` ve kapanış makbuzu
yerelde tutulur. 22 donmuş bulut girdisi ve önceki pilot çıktıları aynı kaldı.
`readback.json` SHA-256:
`7b5d296bae6c3744790817409db4bce3a947e92919a06abde9271eac07814cae`.
`completion_readback.json` SHA-256:
`092c966d2a1e85613dddfc139ba47ebaecdf6aa6cd7eb53a528fb738b0d17a97`.

`daily_observation_status=unknown`, pozitif/negatif etiket izinleri ve
`model_ready=false` korunur. Kapsam dışı hücreye sıfır risk veya negatif hedef
atanmaz; üründe risk hesabı kapsamı dışında gösterilmesi amaçlanır. 2017
haritasının sonraki yıllardaki doğruluğu ve geçmiş erişilebilirliği doğrulanmış
sayılmaz. 453 insan değerlendirme formu doldurulmadı. 2024/2025 verisi,
yeni bulut işi, model eğitimi veya kaynak kaldırma yoktur.
