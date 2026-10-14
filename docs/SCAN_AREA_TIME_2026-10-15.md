# Tarama alanı, zamanı ve kalite pilotu — 15 Ekim 2026

Durum: tek eğitim günündeki üç amaçlı hücrede ham kaynakla bağlı pilot
tamamlandı. Gözlem eşiği veya negatif etiket protokolü kabulü değildir.

## Amaç ve önceden belirlenen kapsam

[Önceki mekânsal incelemede](OBSERVATION_SUPPORT_2026-10-15.md) günlük
alan birleşimiyle tek granül desteği ayrılmıştı. Yeni iş, aynı alanın
**nerede ve hangi tarama zamanlarında** tekrar görüldüğünü hesaplar.

Seçim `configs/scan_support_pilot_v1.json` içinde hesap öncesinde yazıldı:
14 Ocak 2019, önceki rapordaki günlük birleşim kazancı en büyük üç hücre,
aynı sekiz kaynak dosyası, tanısal 1/6/12 saat kesimleri. Bu hücreler
rastgele veya temsili doğruluk örnekleri değildir. Sonuçlar dört ildeki
bütün hücrelere, 181 arka plan adayına veya altı yıla genellenmez.

Sekiz dosya **yedi farklı sensör/yörünge kimliği** taşır. S-NPP'nin
10:18 ve 10:24 dosyaları aynı `SNPP:37385` kimliğine aittir; bunlar
iki ayrı geçiş sayılmaz. Bu kimlikler ham geolocation ürünündeki
`OrbitNumber` ile önceki kabul edilmiş zaman raporuna karşılaştırıldı.
Farklı sensör/yörünge kimliği istatistiksel bağımsızlık iddiası değildir.

## Yöntem ve kontroller

Yeni betik `scripts/quality/review_scan_area_time.py`, sabit hash'lerle
doğrulanan mevcut geometri ve zaman yardımcılarını kullanır. Üretim/bulut
kodları değiştirilmez. Yereldeki **16 ham yangın/geolocation dosyası**
yeniden hash'lenir; ürün adı, eş geolocation bağı, dizi boyutu, tarama
zamanları/kalite kodları ve yörünge kimliği doğrulanır.

Önceki tam AOI incelemesinde kayıtlı aday taramalar kullanılarak üç
hücrenin yaklaşık piksel iç alanları yeniden kurulur. Aynı merkezler
arası köşe yöntemi, tarama kenarı dışlaması ve nominal yangın olmayan
kara QA koşulu korunur. Her taramanın yeniden kurulmuş alanı, nominal
kara desteği ve bulut alanı ayrı geometriyle kaydedilir. Ham piksellerin
kesin köşeleri veya bitki örtüsüne özel gözlem alanı elde edilmiş sayılmaz.

Her granül/hücre/sınıf birleşimi önceki GPKG ile karşılaştırılır:
**72 karşılaştırma** geçti; en büyük simetrik fark yaklaşık
**4,27 × 10⁻⁷ m²**, kullanılan geometrik işlem toleransının altındadır.
Bu tolerans etiket kabul eşiği değildir.

Toplam **1.617 tarama × üç hücre = 4.851 satır** saklandı. Boş alanlar
sıfır alan olarak açıkça bulunur; eksik ürün yerine konmaz. Bunların
26'sında yeniden kurulmuş alan, 13'ünde nominal kara desteği pozitiftir.
Bütün tarama zarfları `(T,T+24h]` içindedir. Önceki AOI tarama planını
kullanmak ve granül birleşimini eşleştirmek, komşu kaynak günlerinde yeni
bir eksiksizlik denetimi yapıldığı anlamına gelmez.

### Zamanla bağlı tekrar alanı

İki tarama için şu koşullar birlikte aranır:

1. Her ikisinin nominal QA kara geometrisi aynı yerde kesişir.
2. Sensör/yörünge kimlikleri farklıdır; aynı yörüngedeki taramalar/dosyalar
   ayrı geçiş gibi sayılmaz.
3. Tarama zarfları hedef penceresinin bütünüyle içindedir.
4. `sonraki başlangıç − önceki bitiş ≥ h` koşulu sağlanır.

Bu fark, iki temsili alanın edinim zamanları arasındaki ayrım için
**alt sınırdır**; her pikselin kesin zamanı değildir. Uyan bütün
kesişimlerin geometrik birleşimi alınır, örtüşen alan tekrar toplanmaz.
1/6/12 saatler tanısal kesimlerdir; etiket koşulu olarak seçilmediler.

## Ölçülen sonuç

Bütün yüzdelerin paydası hücrenin AOI ile kesilmiş alanıdır; habitat
filtresi uygulanmış nihai eğitim paydası değildir.

| Hücre | Günlük nominal kara birleşimi | En büyük tek sensör/yörünge desteği | En az 1 saat arayla tekrar | En az 6 saat arayla tekrar | En az 12 saat arayla tekrar |
|---|---:|---:|---:|---:|---:|
| C632_R868 | %86,51 | %38,03 | %16,48 | %16,48 | %16,48 |
| C643_R863 | %81,64 | %46,88 | %12,60 | %12,60 | %12,60 |
| C630_R868 | %94,45 | %59,91 | %43,25 | %43,25 | %43,25 |

Hücre kimliklerinin ortak öneki `E6933_5K_V1_`'dir. Her hücrede üç
sensör/yörünge kimliğinin nominal kara desteği vardır; bu, üç kez bütün
hücrenin gözlendiği anlamına gelmez.

Uzamsal olarak kesişen ve en az bir saat ayrılan **11 tarama çifti**
bulundu. Bu çiftlerdeki zaman ayrımının alt sınırları yaklaşık
**12,345–22,848 saat** olduğu için bu üç örnekte 1/6/12 saat kesimleri
aynı tekrar alanını veriyor. Bu eşitlik bütün döneme ait bir sonuç veya
kesimlerin genel olarak eşdeğer olduğu iddiası değildir. Çift sayısı
bağımsız gözlem/olay sayısı değildir; aynı alan birden fazla çiftte bulunur.

**En az 12 saat arayla tekrar görülmek, her 12 saatte bir görülmek
değildir.** Nominal kara alanı bulunan tarama zarfları arasındaki en uzun
boşluklar üç hücrede sırasıyla **22,01 / 12,35 / 22,01 saat**tir.
Bunlar günün iki kenarı dahil tarama zarfları arasındaki boşluklardır;
her konumun tam gözlemsiz kaldığı süre veya yangın kaçırma oranı değildir.
Dolayısıyla bu ölçülerden doğrudan negatif etiket çıkarılmadı.

### Kalite yorumu

1.617 taramanın geolocation tarama kalite kodu sıfırdır. Sensor mode
kodlarının 1.010'u 4, 607'si 5'tir; kodlar olduğu gibi tutulur. Nominal
kara tanısı mevcut yangın girdisi QA/residual koşulunu kullanır. Yeni
bir geolocation kalite dışlama politikası seçilmedi. Sıfır dışı gerçek
kalite vakalarının alan etkisi bu pilotla sınanmış sayılmaz.

NASA geolocation kılavuzunun D.3 tablosundaki kalite alanları, SCE taraf
bilgisini diğer durum kodlarından ayırır; örneğin yalnız taraf B olması
tek başına hata değildir. Kılavuz tarama zamanını piksel bazında kesin
zaman veya bu projenin negatif kabul eşiği olarak doğrulamaz.
[NASA VIIRS L1B kılavuzu, Ağustos 2021, bölüm 4.3 ve Ek D; 15 Ekim erişimi](https://ladsweb.modaps.eosdis.nasa.gov/api/v2/content/archives/Document%20Archive/Science%20Data%20Product%20Documentation/NASA_VIIRS_L1B_UG_August_2021.pdf).

## Teslim ve teknik kapanış

Komut: `.venv/Scripts/python.exe scripts/quality/review_scan_area_time.py`.
Son çıktı dizini:
`outputs/reports/dataset/scan_support_v1/20261014T225710Z_3182a434/`.
UTC dizin tarihi 14 Ekim; Türkiye saatiyle çalışma 15 Ekim'dir.

- `scan_support.csv`: 4.851 anahtarlı tarama/hücre satırı, zaman/kalite ve
  üç sınıfın alanları; dosya kimlikleri metin olarak korunur.
- `scan_support.gpkg`: alanı pozitif 26 tarama/hücre için üç geometri
  katmanı; kara/bulut boş geometrileri de korunur. CSV'deki diğer satırlar
  açık sıfır alanlıdır.
- `orbit_support.csv`: üç hücre × yedi sensör/yörünge; aynı yörüngedeki
  granül/taramaların alan birleşimleri.
- `temporal_repeat.csv`, `repeat_support.gpkg`, `repeat_pairs.csv`:
  dokuz hücre/kesim sonucu, konumları ve 11 zaman/kesişim tanığı.
- `scan_inventory.csv`, `reconciliation.csv`: kaynak tarama sayıları ve
  72 eski/yeni geometri karşılaştırması.
- `grid_summary.csv`, `support_by_time.png`: üç hücrenin karşılaştırması;
  grafik görsel olarak kontrol edildi.

İlk geri okuma, `2019014.0100` benzeri metin kimliklerinin ondalıklı sayı
gibi yorumlanmasını yakaladı ve teslimi durdurdu. Okuyucu açık metin türü
ve bileşik tarama kimliği kontrolüyle düzeltildi; yeni dizinde yeniden
üretildi. Eski kabul edilmiş dosya elle değiştirilmedi.

**29 yeni test dahil 92 ilgili test** uyarısız geçti. Testler zaman
sınırları, bir nanosaniyelik kesim farkı, aynı yörünge tekrarları, aynı
yörünge numarasının farklı uydularda ayrılması, ortak konum koşulu,
alanın bir kez sayılması, bozuk girdiler, kapalı test dönemi ve metin
kimliği geri okumasını kapsar. Üç Python dosyasında lint/format geçti.
CSV/GPKG anahtar, alan ve geometri konumu geri okumaları ile
**93 giriş ve 10 çıktı** kapanışı geçti; **22 donmuş bulut girdisi** aynı.

`readback.json` SHA-256:
`ce98df81cf6efcc72a48a2095d062ce01f978e3c88ec2f09470e9b72de8db740`.
`completion_readback.json` SHA-256:
`6613cb4d39a4084304fb6c01bca3dba7caa2a669f06836026f4152388fba8dc6`.

## Sonuç ve devam

Alan, zaman ve kalite artık bu üç örnekte aynı kayda/geometriye bağlıdır.
Bu mekanik bağlantı, negatif etiketin bilimsel doğruluğu değildir.
`daily_observation_status=unknown`, `negative_label_permitted=false`,
boş hedefler ve nihai birleştirme onayı korunur. Yeni bulut işi, veri
indirme, model veya 2024/2025 CSV erişimi yapılmadı.

Önerilen devam, bu çalışan yöntemi temsil kapsamı önceden yazılmış
bir eğitim pilotuna genişletmek; mevsim/il/habitat ve kaynak eksikliği
etkisini, referans olay incelemesiyle birlikte ölçmektir. Ölçümler
hazır olmadan bir saat/yüzdeyi ana kabul eşiği seçmek önerilmez.
Geniş pilot için gerekli kaynak kapsamı ve hesap yükü ayrıca çıkarılmalı;
bütün ham arşivi yeniden işlemek kendiliğinden zorunlu sayılmamalıdır.

İnsan gözüyle bu aşamada `support_by_time.png` ve üç satırlık
`grid_summary.csv` açıklayıcı olarak incelenebilir: mavi çubuk günlük
birleşimi, diğerleri tek yörünge veya zamanla bağlı tekrar alanını gösterir.
Burada kullanıcıdan yangın var/yok kararı veya eşik kabulü istenmiyor.
Bilimsel yöntem tercihi gerektiğinde ölçülmüş seçenekler ayrıca sunulacaktır.
