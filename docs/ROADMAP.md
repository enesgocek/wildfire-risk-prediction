> **3 Ekim 2026 durum notu:** Bu belge başlangıç yol haritasıdır; tamamlanmış
> işler ve kesinleştirilmiş kapsam için PROJECT.md esas alınır. Pilot iller
> Antalya, Muğla, İzmir ve Mersin; grid 2.899 hücredir. Örtü uygunluk eşiği ve
> olay gruplama kuralı seçilmedi, model/etiket üretimine geçilmedi. FIRMS Type
> üretim teyidi açık; ilk e-postada teslim sorunu yaşandı. 2018–2024 meteorolojisi
> tamamlandı ve denetlendi: 2.557 gün, 7.412.743 hücre-gün. İlk meteoroloji kullanım
> kuralı tam döneme uygulandı ve günlük çıktılar doğrulandı. Nihai olay/etiket
> hazırlığı sırada.
> Kısa güncel durum STATUS.md'de, kullanım kuralı WEATHER_POLICY.md'de.
> 2025 final test kapalı tutuluyor.

# **EGE VE AKDENİZ ORMAN YANGINI ERKEN UYARI SİSTEMİ** 

## **Bitirme Projesi — Teknik Yol Haritası v2.0** 

### **Proje amacı** 

Ege ve Akdeniz bölgelerinde orman/bitki örtüsü bulunan alanlar için meteorolojik, uzaktan algılama, topografik ve antropojenik verileri birleştirerek **önümüzdeki 24 saat içerisinde yangın meydana gelme riskini mekânsal olarak tahmin eden bir karar destek sistemi** geliştirilecektir. 

Sistem kesin olarak “yangın çıkacak/çıkmayacak” iddiasında bulunmayacaktır. 

Sistem her bölge için: 

#### **0–1 arasında yangın risk olasılığı** 

üretecektir. 

Birincil tahmin ufku: 

#### **T+24 saat** 

Opsiyonel ikinci tahmin ufku: 

#### **T+72 saat** 

# **1. PROBLEMİN RESMÎ TANIMI** 

## **Tahmin birimi** 

Çalışma alanı düzenli mekânsal gridlere bölünecektir. 

Başlangıç için önerilen çözünürlük: 

#### **5 × 5 km** 

Yalnızca yangın açısından anlamlı bitki/orman alanı içeren gridler modele dahil edilecektir. 

Her veri satırı: 

```
grid_id + prediction_date
```

birimini temsil edecektir. 

1 

### **Target** 

```
fire_next_24h = 1
```

Eğer ilgili grid içerisinde tahmin zamanından sonraki 24 saat içerisinde yeni bir yangın olayı/ilk aktif yangın tespiti bulunuyorsa. 

Aksi durumda: 

```
fire_next_24h = 0
```

Modelin tahmin tarihinde veya daha sonrasında oluşan hiçbir bilgi özellik olarak kullanılamaz. 

Bu kural projenin değiştirilemez **anti-leakage kuralıdır** . 

# **2. COĞRAFİ KAPSAM** 

## **TASK 1 — AOI'yi kesinleştir** 

Mevcut plandaki yalnızca Antalya, Muğla, İzmir ve Hatay'ın birleştirilmesi, projenin adı gerçekten “Ege ve Akdeniz Bölgeleri” olacaksa yeterli değildir. 

İki kapsam seçeneğinden biri proje başlangıcında sabitlenmelidir: 

#### **A — Ana proje kapsamı** 

Türkiye'nin Ege ve Akdeniz bölgelerinde tanımlanan çalışma illerinin tamamı. 

#### **B — Pilot kapsam** 

Antalya + Muğla + İzmir + Hatay gibi belirlenen yüksek riskli pilot iller. 

Pilot kapsam seçilirse raporda projenin “Ege ve Akdeniz bölgelerinin tamamını kapsadığı” söylenmeyecektir. 

### **Deliverable** 

```
data/aoi/aoi.geojson
```

```
data/aoi/grid_5km.geojson
```

```
docs/AOI_DEFINITION.md
```

### **Definition of Done** 

- AOI tek bir GeoJSON olarak oluşturulmuş olacak. 

- Tüm gridlerin benzersiz <mark>`grid_id`</mark> alanı olacak. 

2 

- Orman/bitki örtüsü olmayan gridler işaretlenecek. 

- Proje boyunca AOI değiştirilmeden kullanılacak. 

# **3. VERİ MİMARİSİ** 

Projenin veri kaynakları dört gruba ayrılacaktır. 

## **Yangın etiketleri** 

Birincil: 

NASA FIRMS VIIRS 

İkincil doğrulama: 

EFFIS burnt-area/perimeter 

EFFIS final yangın sınırını ve olay eşleştirmesini desteklemek için kullanılacak; EFFIS <mark>`Start date`</mark> doğrudan ignition time olarak kabul edilmeyecektir. 

## **Meteorolojik veriler** 

Tarihsel eğitim: 

ERA5-Land / uygun tarihsel meteorolojik veri. 

Canlı tahmin: 

Operasyonel weather forecast. 

FWI ayrıca bağımsız benchmark olarak tutulacaktır. 

## **Uzaktan algılama** 

Sentinel-2 L2A. 

Ana ürünler: 

- NDVI 

- NDMI 

- gerekirse NBR 

- 

- çok bantlı Sentinel-2 patch'i 

## **Statik özellikler** 

- ESA WorldCover 

3 

- yükseklik • eğim • aspect • yerleşime uzaklık • yola uzaklık 

- mümkünse yakıt/fuel sınıfı 

Antropojenik özellikler özellikle ignition prediction açısından ayrı feature grubu olarak değerlendirilecektir. 

# **4. HAFTA 1 — PROJE VE REPRODUCIBILITY ALTYAPISI** 

## **Görevler** 

Repository oluştur. 

Önerilen yapı: 

```
project/
├── configs/
├── data/
│   ├── raw/
│   ├── interim/
│   └── processed/
├── docs/
├── notebooks/
├── src/
│   ├── data/
│   ├── features/
│   ├── labels/
│   ├── models/
│   ├── evaluation/
│   ├── inference/
│   └── api/
├── tests/
├── frontend/
└── models/
```

Python sanal ortamını oluştur. 

Dependency'leri sabitle. 

GitHub repository oluştur. 

<mark>`.gitignore`</mark> ve <mark>`.env.example`</mark> oluştur. 

4 

Büyük raster/veri/model dosyalarını normal Git repository içerisine koyma. 

MLflow veya W&B seç. 

GEE non-commercial erişimini doğrula. 

## **Deliverable** 

Çalışan repository. 

Tek komutla oluşturulabilen Python ortamı. 

MLflow/W&B üzerinde ilk test experiment'i. 

## **Definition of Done** 

Başka bir bilgisayarda repository clone edilip environment kurulabiliyor olmalı. 

# **5. HAFTA 2 — YANGIN OLAY KATALOĞU** 

## **Görevler** 

2018–2025 dönemini başlangıç veri aralığı olarak kullan. 

FIRMS VIIRS tarihsel verilerini indir. 

NRT yerine mümkün olduğunca standard/science-quality geçmiş veri kullanılacak. 

EFFIS olay/perimeter verisini temin et. 

EFFIS geçmiş raw perimeter erişimi otomatik ve garanti kabul edilmemeli; gerekirse EFFIS data request süreci bu hafta başlatılmalı. 

FIRMS hotspot'larını olaylara dönüştür. 

Yakın zaman ve konumdaki hotspot'ları aynı event altında grupla. 

Her event için: 

```
event_id
first_detection_time
latitude
longitude
country
province
sensor
```

5 

```
confidence
effis_event_id
burned_area_ha
```

alanlarını oluştur. 

## **Kritik kural** 

Bir olayın **ilk detection zamanı** ile sonraki hotspot'ları birbirinden ayrılmalı. 

Model yangının başlamasından önce risk üreteceği için zaten devam eden bir yangının sonraki hotspot'ları yeni ignition olarak etiketlenmemeli. 

## **Deliverable** 

```
fire_event_catalog.parquet
```

## **Definition of Done** 

Her yangının benzersiz bir <mark>`event_id`</mark> değeri bulunmalı. 

Duplicate hotspot'lar temizlenmiş olmalı. 

EFFIS/FIRMS eşleştirme başarısı raporlanmalı. 

# **6. HAFTA 3 — LABEL PIPELINE VE GRID DATASET** 

Her gün ve her grid için training observation oluştur. 

Pozitif: 

önümüzdeki 24 saat içinde yeni yangın başlayan grid. 

Negatif: 

aynı zaman diliminde yeni yangın başlamayan uygun grid. 

## **Negatif örnekleme** 

Tamamen rastgele negatif seçmek yasaktır. 

Negatif örnekler mümkün olduğunca pozitif örneklere: 

- mevsim, 

- coğrafya, 

- arazi örtüsü 

6 

açısından benzer olmalıdır. 

Aksi halde model yalnızca “Temmuz = yangın, Ocak = yangın yok” gibi trivial ilişkiler öğrenebilir. 

Training sırasında kontrollü negative sampling kullanılabilir. 

Ancak validation ve test mümkün olduğunca gerçek sınıf dağılımını korumalıdır. 

## **Deliverable** 

```
labels_daily_grid.parquet
```

# **7. HAFTA 4 — FEATURE ENGINEERING PIPELINE** 

Her <mark>`(grid_id, date)`</mark> satırı için aşağıdaki özellikleri üret. 

## **Meteoroloji** 

- sıcaklık 

- maksimum sıcaklık 

- bağıl nem 

- rüzgâr hızı 

- 

- rüzgâr yönü • yağış 

- son 3 gün yağış 

- son 7 gün yağış 

- son 14 gün yağış 

- mümkünse toprak nemi 

## **Vegetation** 

Prediction tarihinden ÖNCE elde edilen son geçerli Sentinel-2 görüntülerinden: 

- NDVI 

- NDMI 

- NBR opsiyonel 

Cloud masking zorunlu. 

Aynı gün veya yangından sonraki görüntü kullanılamaz. 

## **Topografya** 

- elevation 

- slope 

- aspect 

7 

## **Land cover** 

- forest 

- shrub 

- grassland 

- 

- agriculture 

- 

- diğer 

## **İnsan etkisi** 

Mümkünse: 

- nearest road distance 

- nearest settlement distance 

- built-up fraction 

## **Deliverable** 

```
feature_table_v1.parquet
```

## **Otomatik kontrol** 

Her dinamik feature için: 

```
feature_timestamp <= prediction_timestamp
```

olduğu script ile doğrulanacaktır. 

# **8. HAFTA 5 — TRAIN / VALIDATION / TEST PROTOKOLÜ** 

Mevcut plandaki “bazı büyük Türkiye yangınlarını elle test setine ayır” yaklaşımı kaldırılacaktır. 

Büyük ve bilinen yangınları özellikle test için seçmek selection bias oluşturabilir. 

Ana temporal split: 

### **TRAIN** 

2018–2023 

### **VALIDATION** 

2024 

8 

### **FINAL TEST** 

2025 

2025 sonuçları final değerlendirme aşamasına kadar görülmeyecektir. 

Training döneminde ayrıca spatial cross-validation yapılacaktır. 

Yakın gridlerin hem train hem validation fold'una girmesini engellemek amacıyla gridler mekânsal bloklar halinde gruplanacaktır. 

## **Leakage testleri** 

- Aynı <mark>`event_id`</mark> iki split'e giremez. 

- 

- Aynı event çevresindeki hotspot'lar farklı splitlere dağıtılamaz. 

- 

- Future imagery kullanılamaz. 

- 

- Final test hiperparametre seçiminde kullanılamaz. 

- 

## **Deliverable** 

```
split_manifest.parquet
```

```
leakage_check.py
```

# **9. HAFTA 6 — REFERANS / BASELINE MODELLER** 

Bu hafta DL kullanılmayacaktır. 

Üç baseline oluştur. 

### **Baseline 0** 

FWI tabanlı risk benchmark. 

### **Baseline 1** 

Random Forest. 

### **Baseline 2** 

XGBoost veya LightGBM. 

Amaç “AI kullandık” demek değil; daha karmaşık modelin gerçekten değer katıp katmadığını ölçmektir. 

## **Metrikler** 

Primary: 

9 

#### **PR-AUC** 

Secondary: 

- ROC-AUC • Precision • Recall • F1 • Brier Score 

Calibration: 

- reliability diagram 

- Expected Calibration Error 

Ek operasyonel metrik: 

#### **Top-risk %X alan içerisinde yangınların yüzde kaçı yakalanıyor?** 

IoU ana metrik listesinden çıkarılacaktır. 

IoU ancak daha sonra doğrudan raster segmentation problemi kurulursa kullanılacaktır. 

## **Deliverable** 

```
baseline_results.csv
```

Model comparison report. 

# **10. HAFTA 7 — HATA ANALİZİ VE FEATURE ABLATION** 

Feature importance hesapla. 

SHAP analizi yap. 

Şu grupları ayrı ayrı çıkar: 

- weather • vegetation • terrain • land cover • anthropogenic 

Performans değişimini ölç. 

False positive'leri incele. 

10 

False negative'leri özellikle incele. 

Analizi: 

- il, • ay, • land cover, • yangın büyüklüğü 

bazında gerçekleştir. 

## **Gate** 

Baseline pipeline güvenilir değilse DL aşamasına geçilmez. 

# **11. HAFTA 8 — SATELLITE IMAGE DATASET** 

Her grid/date için Sentinel-2 patch oluştur. 

Ancak “son 10–15 günün her gün görüntüsü” şartı kullanılmayacaktır. 

Bunun yerine: 

prediction date öncesindeki yaklaşık 30–45 günlük pencereden en son 1–3 geçerli cloud-free observation/composite kullanılacaktır. 

Patch boyutu seçimi yapılan model mimarisine göre sabitlenecektir. 

Metadata mutlaka saklanmalıdır: 

```
grid_id
prediction_date
image_date
cloud_percentage
bands
```

Yangın başlangıcından sonraki hiçbir görüntünün patch dataset'e girmediği otomatik test edilmelidir. 

# **12. HAFTA 9 — EARTH OBSERVATION** 

# **FOUNDATION MODEL** 

Prithvi, Clay veya başka bir EO foundation model kör şekilde seçilmeyecektir. 

11 

Seçim kriterleri: 

- Sentinel-2 desteği 

- lisans 

- GPU ihtiyacı 

- dokümantasyon 

- 

- input band uyumu 

- 

- fine-tuning kolaylığı 

## **İlk deney** 

Encoder'ı DONDUR. 

Sentinel görüntüsünden embedding çıkar. 

Embedding üzerine: 

- Logistic Regression, veya 

- küçük MLP 

eğit. 

Bu aşamada foundation model full fine-tuning yapılmayacaktır. 

## **Neden?** 

Önce pretrained representation'ın probleme gerçekten fayda sağlayıp sağlamadığı gösterilmelidir. 

# **13. HAFTA 10 — MULTIMODAL MODEL** 

İki model ailesini karşılaştır. 

### **Tabular model** 

XGBoost. 

### **EO model** 

Satellite embeddings. 

Ardından fusion dene. 

Önerilen düşük riskli yöntem: 

12 

```
P_final =
w1 × P_tabular +
w2 × P_satellite
```

Alternatif: 

Satellite embedding + meteorological features → küçük MLP. 

## **Gate** 

Satellite model baseline'a anlamlı katkı sağlamıyorsa sadece “DL kullandık” demek için sistemde tutulmayacaktır. 

Bu negatif sonuç da akademik olarak geçerli bir sonuçtur. 

# **14. HAFTA 11 — OPSİYONEL FINE-TUNING** 

Yalnızca önceki haftalarda foundation modelin fayda sağladığı gösterilmişse encoder fine-tuning yapılacaktır. 

Önce: 

son bloklar açılacak. 

Sonra gerekirse daha fazla layer fine-tune edilecek. 

2–3 learning-rate kombinasyonundan fazlası denenmeyecektir. 

Colab/Kaggle GPU yeterliyse Vertex AI kullanılmayacaktır. 

Cloud GPU yalnızca ihtiyaç varsa devreye alınacaktır. 

## **Deliverable** 

DL vs frozen embeddings vs tabular karşılaştırması. 

# **15. HAFTA 12 — GENELLEME DENEYİ** 

Burada mevcut yol haritasındaki Mediterranean dataset fikri korunacaktır. 

Türkiye dışında: 

• Yunanistan • İtalya 

13 

• İspanya • Portekiz 

gibi Akdeniz iklimine sahip bölgelerden uyumlu veri kullanılabilir. 

Model: 

önce Akdeniz havzası üzerinde eğitilir. 

Ardından Türkiye train seti üzerinde adapte edilir. 

Ancak Türkiye 2025 test verisi hiçbir aşamada kullanılamaz. 

Karşılaştır: 

A — Türkiye-only. 

B — Mediterranean pretrained/adapted. 

Amaç: 

Daha geniş coğrafyanın Türkiye genellemesini iyileştirip iyileştirmediğini ölçmek. 

# **16. HAFTA 13 — CALIBRATION VE FINAL MODEL FREEZE** 

En iyi model validation set kullanılarak seçilir. 

Probability calibration uygula. 

Örneğin: 

- Platt scaling 

- isotonic regression 

Final operating threshold validation setinden belirlenir. 

2025 final test açılır. 

Final test **yalnızca bir kez** raporlanır. 

Final model: 

```
model_v1
```

olarak freeze edilir. 

14 

Model card oluştur. 

Model card: 

• training dates • data sources • features • metrics • limitations • expected usage • unsupported usage 

içermelidir. 

# **17. HAFTA 14 — OPERASYONEL INFERENCE PIPELINE** 

Mevcut yol haritasındaki: 

API isteği geldi → GEE'ye git → feature çek → model çalıştır 

mimarisi kullanılmayacaktır. 

Bu yaklaşım yavaş ve kırılgandır. 

Bunun yerine **batch inference** kullanılacaktır. 

Örneğin günde bir defa: 

```
weather forecast
        ↓
latest vegetation state
        ↓
static features
        ↓
model
        ↓
all AOI grids risk prediction
        ↓
risk_map.parquet / GeoJSON
```

API sadece hazır sonucu servis edecektir. 

Bu yapı gerçek bir erken uyarı mimarisine çok daha yakındır. 

15 

# **18. HAFTA 15 — FASTAPI** 

Endpoint'ler: 

```
GET /health
GET /risk
?lat=
&lon=
&date=
GET /risk/grid/{grid_id}
GET /risk-map
?date=
GET /model-info
```

Örnek response: 

```
{
"grid_id":"TR_ANT_00214",
"prediction_date":"2026-07-18",
"forecast_horizon_hours":24,
"risk_probability":0.73,
"risk_class":"high",
"model_version":"v1"
}
```

Input validation zorunludur. 

AOI dışındaki koordinatlar reddedilmelidir. 

# **19. HAFTA 16 — DOCKER VE DEPLOYMENT** 

FastAPI Docker image oluştur. 

Model artifact container veya object storage üzerinden yüklenebilir. 

Cloud Run kullanılabilir. 

Scale-to-zero maliyeti azaltmak amacıyla kullanılabilir fakat “kesinlikle maliyet oluşturmaz” varsayımı yapılmayacaktır. 

16 

CI testleri: 

- lint • unit test • API test 

minimum olarak çalıştırılmalıdır. 

# **20. HAFTA 17 — FRONTEND** 

React + MapLibre kullanılabilir. 

Harita üzerinde grid tabanlı risk haritası göster. 

Risk seviyeleri: 

- çok düşük • düşük • orta • yüksek • çok yüksek 

şeklinde kullanıcıya sunulabilir. 

Ancak backend'deki ham probability de görüntülenebilir olmalıdır. 

# **21. HAFTA 18 — EXPLAINABILITY** 

Kullanıcı bir grid'e tıkladığında yalnızca: 

“Risk = %78” 

göstermek yerine: 

risk üzerinde etkili başlıca faktörleri göster. 

Örneğin: 

```
Risk: %78
```

- `Başlıca faktörler: ↑ Yüksek sıcaklık ↑ Çok düşük son-7-gün yağış` 

```
↑ Düşük NDMI
```

17 

- `↑ Kuvvetli rüzgâr` 

- `↑ Ormana yakın yerleşim` 

Bu bilgi SHAP veya uygun feature contribution yöntemiyle üretilebilir. 

Bu özellik projeyi sıradan bir sınıflandırıcıdan karar destek sistemine yaklaştıracaktır. 

# **22. HAFTA 19 — SYSTEM TEST** 

Aşağıdaki senaryolar test edilir: 

Normal prediction. 

AOI dışındaki koordinat. 

Eksik hava verisi. 

Eksik Sentinel görüntüsü. 

Cloud-covered Sentinel görüntüsü. 

API timeout. 

Model dosyası bulunamıyor. 

Eski risk haritası. 

Aynı API'ye eşzamanlı istek. 

## **Deliverable** 

```
tests/
```

Test raporu. 

# **23. HAFTA 20 — PROSPECTIVE / SHADOW TEST** 

Mümkünse sistem geçmiş bir yıl üzerinde değil, güncel dönemde de sessiz şekilde çalıştırılır. 

Model tahminleri kaydedilir. 

Sonradan FIRMS detections ile karşılaştırılır. 

Bu aşamada model yeniden eğitilmez. 

18 

Amaç: 

Gerçek dünyada veri pipeline'ının çalışıp çalışmadığını görmek. 

Bu değerlendirme final testten ayrı raporlanmalıdır. 

# **24. HAFTA 21 — SON DENEY TABLOSU** 

Tek bir master tablo oluştur. 

Örneğin: 

|Model|Weather|EO|Human|PR-AUC|Recall|Brier|
|---|---|---|---|---|---|---|
|FWI|✓|-|-|...|...|...|
|RF|✓|✓|✓|...|...|...|
|XGBoost|✓|✓|✓|...|...|...|
|EO Encoder|-|✓|-|...|...|...|
|Fusion|✓|✓|✓|...|...|...|



Aynı evaluation protocol dışında üretilen iki sonuç aynı tabloda karşılaştırılmayacaktır. 

# **25. HAFTA 22 — AKADEMİK RAPOR** 

Rapor yapısı: 

1. Problem tanımı 

2. Literatür 

3. Study area 

4. Data sources 

5. Fire event construction 

6. Feature engineering 

7. Data leakage prevention 

8. Models 

9. Evaluation protocol 

10. Results 

11. Ablation 

12. Error analysis 

13. System architecture 

14. Deployment 

15. Limitations 

16. Future work 

17. Conclusion 

19 

Özellikle limitations kısmı saklanmayacaktır. 

Örneğin: 

- Satellite cloud cover. 

- Fire ignition label uncertainty. 

- Human ignition factorsının eksikliği. 

- 

- Meteorological forecast uncertainty. 

- 

- Spatial resolution. 

- 

- Train-serving weather differences. 

- 

# **26. HAFTA 23 — SUNUM VE DEMO** 

Sunum: 

**Problem → neden zor → veri → leakage problemi → yöntem → baseline → model → sonuç → harita → demo → sınırlamalar** 

akışıyla hazırlanmalıdır. 

Demo için internet kesintisi ihtimaline karşı önceden hazırlanmış prediction sonuçları bulunmalıdır. 

Canlı API çalışmasa bile demo devam edebilmelidir. 

# **27. HAFTA 24 — BUFFER** 

Yeni özellik eklenmeyecektir. 

Yalnızca: 

- bug fix • rapor • deployment • sunum • eksik test • reproducibility 

işleri yapılacaktır. 

# **PROJE BOYUNCA DEĞİŞTİRİLEMEZ KURALLAR** 

## **RULE 1 — Future data yok** 

Prediction zamanından sonraki hiçbir veri feature olamaz. 

20 

## **RULE 2 — Final test kör kalacak** 

2025 final test sonucu model seçmek için kullanılamaz. 

## **RULE 3 — Baseline geçilmeden karmaşıklık yok** 

DL modeli XGBoost'tan kötü ise XGBoost ana model olabilir. 

## **RULE 4 — Accuracy kullanılmayacak** 

Yangın problemi ciddi class imbalance içerdiği için accuracy ana başarı metriği değildir. 

## **RULE 5 — Dataset version'lanacak** 

Her deney hangi dataset sürümüyle üretildiğini kaydedecek. 

## **RULE 6 — Data ≠ Git** 

Büyük imagery/raster/model dosyaları normal Git repository içerisinde tutulmayacaktır. 

## **RULE 7 — Her experiment kayıt altında olacak** 

Model configuration + dataset + seed + metrics saklanacaktır. 

## **RULE 8 — Model “yangın çıkar” demeyecek** 

Model çıktısı: 

**yangın oluşma riskidir.** 

# **MVP — MUTLAKA BİTMESİ GEREKENLER** 

Zaman problemi yaşanırsa proje şu minimum kapsamın altına düşmemelidir: 

**FIRMS + meteoroloji + vegetation + terrain → XGBoost → calibrated risk → FastAPI → MapLibre risk haritası.** 

Bunlar projenin çekirdeğidir. 

21 

# **OPTIONAL — ZAMAN KALIRSA** 

Aşağıdakiler çekirdek proje değildir: 

- Foundation model full fine-tuning 

- 

- Mediterranean transfer learning 

- 

- uncertainty ensemble 

- 

- 72 saatlik ikinci model 

- 

- gelişmiş explainability 

- 

- complex multimodal fusion 

- 

- çoklu GPU 

- 

- Vertex AI training 

- 

Bunlardan biri yetişmediğinde proje başarısız sayılmaz. 

Ana projenin bilimsel sağlamlığı bunlardan daha önemlidir. 

# **PROJENİN BAŞARI TANIMI** 

Bitirme projesi başarılı kabul edilebilmek için: 

1. Veri pipeline'ı tekrar çalıştırılabilir olmalı. 

- Future-data leakage bulunmamalı. 

2. 

- Final test tamamen bağımsız olmalı. 

3. 

4. En az bir anlamlı baseline bulunmalı. 

- Model probability/risk üretmeli. 

5. 

- Calibration değerlendirilmiş olmalı. 

6. 

- Hata analizi yapılmış olmalı. 

7. 

8. API modeli servis edebilmeli. 

- Harita üzerinde mekânsal risk görülebilmeli. 

9. 

10. Kullanılan veriler ve sınırlamalar açık şekilde raporlanmalı. 

Temel hedef “en yüksek accuracy” değil; 

**bilimsel olarak savunulabilir, tekrar üretilebilir ve çalışan uçtan uca bir yangın risk tahmin sistemi geliştirmektir.** 

22 

