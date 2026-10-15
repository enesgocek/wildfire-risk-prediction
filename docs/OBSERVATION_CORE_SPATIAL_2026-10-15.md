# İlk gözlem çekirdeği çiftinin mekânsal ve zaman kontrolü

Tarih: 15 Ekim 2026. Kapsam: eğitim dönemindeki SNPP:2018045.0000,
14 Şubat 2018 00:00–00:06 UTC. Kaynak: kabul edilmiş otomatik indirme
makbuzu ve yerel native diziler. Yeni indirme, VM veya Earth Engine işi yok.

## Amaç ve yöntem

[Önceki tek çift kabulü](OBSERVATION_CORE_CDN_2026-10-15.md#ilk-gerçek-otomatik-aktarımın-yerel-kabulü)
yalnız dosya baytları ve başlıklarını doğruluyordu. Bu aşamada aynı
yangın/konum dosyalarının piksel sınıfları, koordinatları, kalite alanları,
yaklaşık alanları ve native tarama zamanları incelendi.

`scripts/quality/review_observation_core_pair.py`, tek kabul edilmiş
makbuza ve plana bağlanır. Önceki bilimsel kodları değiştirmeden ayrı
modül örnekleriyle kullanır; çıktıları yeni nonce dizinine yönlendirir.
Kaynak dosyalar salt okunur tutulur. Ağ bağlantısı ve PROJ ağ erişimi
kapatılır; alt süreç 1.800 saniyeyle sınırlıdır. Tamamlanamayan çıktılar
korunur, başarı makbuzu yerine kullanılamaz. Gerçek alt süreç süresi
**113,266 saniye**; bu, geniş pilot için hız veya toplam süre tahmini değildir.

- Piksel merkezleri AOI poligonlarıyla eşleştirilir; tam swath sınıf
  toplamı ve seyrek termal kayıtlar native satır/sütunla uzlaştırılır.
- Önceki `scan_interior_center_midpoints_v1_approximate` yöntemiyle,
  tarama sınırını aşmadan komşu merkezlerden yaklaşık poligon üretilir.
  Hücre/AOI kesişimleri geometrik birleşimle alınır; örtüşmeler toplanmaz.
- TAI93 zamanı ürünün leap-second alanıyla UTC'ye çevrilir. Tarama
  sırası, kalite kodları, sensör modu ve `(T,T+24h]` sınırları kontrol edilir.
  T bu kaynak gününün 00:00 UTC anıdır; bütün pilot hedef günlerinin
  pencereleri bu tek çiftle değerlendirilmiş sayılmaz.
- Native diziler ikinci kez okunarak tarama/hücre sınıf ve QA toplamları
  ilk piksel denetimiyle karşılaştırılır. CSV anahtar/metin/sayıları,
  GPKG anahtar/CRS/geçerlilik/alan ve AOI içinde kalma koşulları geri okunur.

Bu çift daha önce ilk kronolojik aktarım denemesi için seçilmiştir;
temsilî veya rastgele popülasyon örneği değildir. Tarihi, sabit çekirdekteki
15 Şubat hedef gününden önceki kaynak günüdür. Pilotun 156 hücre-günü,
komşu günleri ve bütün sensörleri bu tek altı dakikalık geçişle kapanmaz.

## Ölçülen sonuç

| Ölçü | Sonuç ve kapsam |
|---|---|
| Native dizi | 6.496 × 6.400; 41.574.400 piksel |
| Geçersiz koordinat | Tam swath içinde 0 |
| AOI içinde merkez | 335.099 piksel merkezi |
| Kayıtlı coğrafi hücre | Sıfır merkezliler dahil 2.899 |
| Merkez bulunan hücre | Bu geçişte 2.593 |
| Kalite koşulunu geçen yangın dışı kara merkezi olan hücre | Bu geçişte 1.610 |
| Tarama | 203; kalite kodu 0, sensör modu 5 |
| Tarama/hücre satırı | 4.066; anahtarlar tekil |
| Kaynak gün penceresi | 203 taramanın tamamı inside |
| Seyrek termal kayıtla yönelim kontrolü | Tam swath'taki 61 kaydın tamamı eşleşti |

**61 seyrek termal kayıt, 61 bağımsız yangın değildir.** AOI içinde yalnız
bir nominal güven düzeyinde termal piksel merkezi vardır; bu da bağımsız
olay veya gerçek tutuşma zamanı olarak kabul edilmedi.

AOI içindeki merkezlerin sınıfları: bulut **185.154**, kara **136.161**,
bowtie silinmiş **12.857**, su **926**, nominal termal **1**; diğer sınıflar
sıfırdır. Sayımların toplamı 335.099 ile eşleşir. Merkez sayıları
yüzey alanı veya gözlem olasılığı olarak yorumlanmaz. Input non-nominal
12.857; geo non-nominal ve residual-bowtie tanıları sıfırdır. Bu geçişte
sıfır dışı geolocation scan-quality vakası sınanmış değildir.

Yaklaşık poligon birleşimleri: yeniden kurulan alan **54.023,76 km²**,
kalite koşulunu geçen yangın dışı kara **23.215,36 km²**, bulut
**30.714,38 km²**. Bunlar resmî piksel köşeleriyle hesaplanmış fiziksel
örtüm değildir; dış satır/sütunlar ve geçersiz/aşırı geniş komşuluklar
yeniden kurulmaz. Sınıf alanları farklı taramalarda örtüşebilir;
birbirinden ayrık alanlar gibi toplanmaz. Habitat uygunluk maskesi ve
günlük negatif kabul eşiği uygulanmadı.

## Çıktılar ve kapanış

Komut: `.venv/Scripts/python.exe scripts/quality/review_observation_core_pair.py`.
Çıktı dizini:
`outputs/reports/dataset/observation_core_spatial_v1/20261015T110104Z_9512936a/`.

Yerel geri kontrolde **132 giriş ve 11 çıktı** hash ile tekrar doğrulandı;
22 donmuş üretim girdisi korundu. Native kaynak, eski kabul edilmiş
makbuz ve üretim kodları değiştirilmedi.

- `readback.json` SHA-256: `e8870f29a99e2c7bb5aaad3b853cabda0f3df76442072c3ea7229a8e88c0fed2`.
- `completion_readback.json` SHA-256: `cff03f2ca5baabc2750344e9745974108a5c31391abe9a861f7adc01ab6ed1a5`.
- `scan_grid.csv`: sınıf/kalite ile tarama zamanı, sensör ve yörünge bağı.
- `all_scans.csv`: 203 taramanın zaman/kalite envanteri.
- `grid_time.csv`: sıfır merkezli hücreleri koruyan tek kaynak tanısı.
- `l2_sample_2018045.0000_area_estimate.csv` ve `.gpkg`: 2.899 hücrenin
  yaklaşık alanları ve üç ayrı geometri katmanı.

**Dokuz yeni davranış testi dahil 73 ilgili test** geçti. Yanlış dönem/çift,
etiket izni, tamamlanmamış/değişmiş makbuz, sıfırları kaybolabilen granül
anahtarı, bozulmuş sayım, alanı aynı olup konumu yanlış geometri ve mevcut
makbuzun üzerine yazma reddi sınandı. Deprecation/Future uyarıları testte
hata sayıldı. Yeni denetleyici, görselleştirici ve test dosyasında lint/format geçti.

## Görsel ve insan incelemesi sınırı

`scripts/quality/plot_observation_core_pair.py` kabul edilmiş raporun
giriş/çıktı kapanışını kontrol edip ayrı dizinde görsel üretir:
`outputs/reports/dataset/observation_core_figure_v1/20261015T110447Z_41be66de/observation_support.png`.
Üç panelde aynı hücrelerin yeniden kurulan alan, yangın dışı kara ve
bulut alanı oranları gösterilir. Payda hücrenin AOI içindeki alanıdır;
bütün panellerde ortak 0–1 ölçeği vardır. Görsel araçla açılıp yazılar,
paneller ve ölçek okunabilirlik açısından kontrol edildi.

Görsel SHA-256: `9a24e4f5fa768162404da4264fd289cd814c136eb88912cad972f8a65bfb04f9`.
Görsel `readback.json` SHA-256:
`ceb5f515113874fa4210dd802a0ba586867c81729d11e5270902f155d61f507d`.

Kullanıcı dilerse bu PNG'yi ve alan CSV'sini inceleyebilir: aynı konumun
üç panelde korunmasına ve kara desteği düşük olan yerde bulutun yüksek
olabilmesine bakılır. Bu aşamada istenen bir yangın var/yok kararı veya
etiket eşiği onayı yoktur. Görsel düzen kontrolü, bağımsız olay doğrulaması
ya da araştırmacının manuel etiket incelemesi olarak raporlanmaz.

## Sonraki aşama

Tek çiftte erişimden mekânsal/zaman tanısına kadar hat çalıştı. Devamda
bu hattın sabit pilot hücrelerine ve tam kaynak pencerelerine uygulanması,
tarama alanlarının zamanla birlikte bağlanması ve farklı sensör/geçişlerin
ortak alanının değerlendirilmesi gerekir. Kalan kaynak aktarımı için
özel girişli, disk/süre sınırı ve geri okuma kapıları olan daha geniş bir
plan hazırlanmalıdır; bu komut onu kendiliğinden başlatmaz.

`daily_observation_status=unknown`, `negative_label_permitted=false`,
`model_ready=false` ve boş hedefler korunur. 156 hücre-günlük geniş pilot,
güvenilir negatifler, bağımsız olay referansı ve etiketli nihai birleştirme
henüz kabul edilmiş değildir.
