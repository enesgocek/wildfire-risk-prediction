# FIRMS yanıtı: koleksiyon açıklığı ve açık teslim sürümü

Tarih: 21 Ekim 2026. Kaynak: araştırmacının paylaştığı Earthdata/FIRMS yanıt
ekran görüntüsü. Özel posta kutusu, e-posta başlıkları veya destek portalı
kimliği bağımsız doğrulanmadı. Kişi adı, ticket numarası ve özgün görüntü
bu kayda alınmadı. Kamu kaynakları aşağıda ayrı belirtilir.

## Yanıt neyi doğruluyor?

- CSV'deki `version=2`, **Collection 2** anlamındadır; aylık ürünün üretim
  sürüm numarası değildir. Kaynak sürümünü yorumlama sorumuzun bu kısmı yanıtlandı.
- Destek ekibi, yanıt anında FIRMS üzerindeki VIIRS verisinin v4, MODIS verisinin
  v3 olduğunu belirtiyor. Bu, destek yanıtının beyanıdır; yerel dosyalarımıza
  ait üretim sürümü makbuzu değildir.
- Ekip indirme zamanımızı bilmediği için önceki teslimlerimizin sürümünü
  doğrulayamadığını açıkça söylüyor ve şüphe varsa yeniden indirmeyi öneriyor.
- Destek kaydının çözüldü olarak görünmesi, proje veri setinin veya Type
  etiketlerinin bilimsel kabul edildiği anlamına gelmez.

Yanıt, mevcut Type=0 kayıtlarının tamamının gerçek bitki yangını olduğunu,
iki ertelenmiş L2/geolocation gününün çözüldüğünü veya güvenilir negatif
örneklerin doğrulandığını söylemiyor. MODIS için belirtilen sürüm de
MCD64A1 yanmış alan ürününün maske/koleksiyon sorularını kendiliğinden çözmez.

## Kamu kaynağı ile ayrı kontrol

21 Ekim'de [VIIRS Collection 2 kılavuzu v1.2](https://ladsweb.modaps.eosdis.nasa.gov/archive/Document%20Archive/Science%20Data%20Product%20Documentation/VIIRS_C2_AF-375m_User_Guide_1.2.pdf)
yeniden açıldı. Bu **Haziran 2025** belgesinin bölüm 3.2.1'inde koleksiyon
ile koleksiyon içi üretim sürümü ayrı ad bileşenleridir. Bölüm 6.1, aylık
ürün sürümleri 1/2'de bazı sabit kaynakların Type=0 yazılabildiğini ve Mayıs
2025 düzeltmesiyle dosyaların sürüm 3'e yeniden işlendiğini açıklar.
Type=0 ifadesi varsayılan bitki yangını sınıfıdır; bağımsız olay doğruluğu değildir.

Bu tarihli kılavuz, destek yanıtındaki güncel v4 beyanının bağımsız teyidi
olarak kullanılmadı. Eski belgede v3 yazması, daha yeni bir v4 bulunamayacağını
göstermez. Genel [FIRMS Readme](https://firms.modaps.eosdis.nasa.gov/download/Readme.txt)
de talebe özgü işlem sürümü makbuzu olarak kullanılmadı. İlgisiz sürüm
arama sonuçları kanıta alınmadı; yeni ham kaynak indirilmedi.

## Yerel dosyalarda yapılan sınırlı kontrol

İki özgün VIIRS CSV'nin byte hash'i, önceden kayıtlı arşiv denetimleriyle
eşleştirildi. Yalnız ilk satırdaki sütun adları okundu; veri satırları
yeniden parse edilmedi veya 2024 üzerinden yöntem seçimi yapılmadı.

| Kaynak | Boyut, bayt | Önceki denetimle eşleşen SHA-256 |
|---|---:|---|
| S-NPP arşivi | 22.246.341 | `346d9e4e09d49d21166e98049635d64326c9330cd42b15b2f44c19456b54d5d2` |
| NOAA-20 arşivi | 22.864.689 | `f3b0a716c335e89976fcc2620cc29dc871938411c6ad5b7f8737a4e55c6e46ec` |

Korunan eski denetimler bütün kayıtların CSV version değerini 2 olarak
bildiriyor. Başlıklarda `version` ve `type` var; `update_version` veya ayrı
bir aylık üretim sürümü alanı yok. Tam indirme zamanı veya alttaki aylık
ürün VV kimliği bu kontrolle belirlenmedi. Dosya sistemi değiştirilme/oluşturma
tarihi sunucu indirme makbuzu yerine kullanılmadı. Yerel kaynakların aynı
olması, güncel v4 teslimiyle eşit olduklarını kanıtlamaz.

## Önerilen sonraki işlem: yeni teslimle sınırlı karşılaştırma

Bu plan henüz uygulanmadı; yeni kaynak talebi veya büyük iş başlatılmadı.

1. Eski dosyaları koruyarak S-NPP ve NOAA-20 için aynı coğrafi kapsamın
   **2018–2023 eğitim dönemi standart arşiv CSV** teslimini yeni dizinde almak.
   Yeni talep/teslim zamanı, sensör/koleksiyon, dosya hash'i ve varsa üretim
   sürümü açıklamasını ayrı kaydetmek. Bu aşamaya 2025 final testi dahil edilmez.
2. Kaynak adlarını, şemayı ve birimleri kontrol etmek. Yeni arşivde satır sırası
   değişebileceği için eski satır numaraları veya talebe bağlı kayıt kimlikleri
   doğrudan eşleştirme anahtarı yapılmaz. Sensör, UTC zaman ve özgün koordinatlar
   üzerinden karşılaştırma hazırlanır; çakışan/yuvarlaması değişmiş anahtarlar
   otomatik tekilleştirilmez veya yakınlıkla aynı olay kabul edilmez.
3. Aynı kapsamdaki eklenen/çıkarılan tespitleri, Type/güven/zaman/koordinat
   farklarını ve yalnız biçim/sıralama değişimlerini ayrı saymak. Hash değişmesi
   tek başına bilimsel kayıt değişimi değildir; değişmemiş CSV version=2 değeri
   de yeni teslimin eski aylık sürüm olduğu anlamına gelmez.
4. Güncel teslimle eşitlik veya fark sonucunu raporlamak. Aylık VV metadatası
   yine yoksa, karşılaştırmanın neyi desteklediği ve neyi doğrudan doğrulamadığı
   açık kalır. Gerekirse eldeki somut teslim makbuzuyla dar teknik soru hazırlanır;
   bu dosyayla e-posta gönderilmiş sayılmaz.
5. Değişen kayıtların aday filtrelerine, olay incelemelerine ve ilgili
   kaynak planlarına etkisini belirlemek. Yeniden üretim gereksinimi bu
   rapordan çıkarılır; 72 aylık VM işi doğrudan yeniden başlatılmaz.

Güncel Type bilgisi tek başına fiziksel yangın doğrulaması veya negatif etiket
izni değildir. Bağımsız olay verisi için üniversite/OGM yolu ayrıca sürer.
Bilimsel kapsam veya etiket kabulü araştırmacı kararı olmadan değiştirilmez.

## Kapanış ve kabul sınırı

Yerel salt okunur sonuç:
`outputs/reports/dataset/nasa_firms_response_v1/20261021T135735Z_312afe91/`.
Readback SHA-256:
`fda123c71c1e80a0861ba6340cde72f72617518100031e4376e4a8652c0629b1`.
Kapanış SHA-256:
`539421e9dda39a2196348e60bb021d91cb1c3dc9df024be2707db797fb0660dc`.

İki arşivin kimlikleri/başlıkları ve eski raporların bağlantısı kontrol edildi;
çıktı JSON'u ve girdi hash'leri geri okundu. Yeni bilimsel davranış testi veya
model başarı sayısı üretilmedi. `source_type_semantics_verified` kapalı kaldı:
koleksiyon anlamı açıklanmış olsa da mevcut teslimin düzeltilmiş aylık Type
üretimine bağlanması henüz doğrulanmadı. `daily_observation_status=unknown`,
pozitif/negatif izin false; eğitim ve nihai birleştirme yapılmadı. Önceki
hash ile bağlı çıktı/manifestler ve ham CSV'ler değiştirilmedi.

## Aynı gün sonraki adım: araştırmacı için indirme ayarları

Araştırmacı güncel teslimleri kendisi indirmeyi ve karşılaştırma için yerel
klasöre aktarmayı istedi. İki ayrı manuel talep ayarı ve giriş klasörü
hazırlandı. Talebin gönderildiği veya indirmenin tamamlandığı henüz teyit edilmedi.

[Resmî Archive Download](https://firms.modaps.eosdis.nasa.gov/download/)
sayfası 21 Ekim'de tekrar açıldı. Earthdata hesabı veya e-posta koduyla
giriş ve veri hazır olduğunda e-postayla indirme yönergesi destekleniyor.
Giriş sonrası kişisel oturumun formu bu incelemede görülmedi; aşağıdaki
değerler seçilecek araştırma parametreleridir, görülmemiş düğme adları değildir.

| Seçim | S-NPP talebi | NOAA-20 talebi |
|---|---|---|
| Kaynak | VIIRS S-NPP 375m | VIIRS NOAA-20 375m |
| Koleksiyon | Collection 2 | Collection 2 |
| Başlangıç | 2018-01-01 | 2018-04-01 |
| Bitiş, dahil | 2023-12-31 | 2023-12-31 |
| Coğrafi kapsam | Turkey/Türkiye, ülke kapsamı | Turkey/Türkiye, ülke kapsamı |
| Buffer alanı sunulursa | 0 km | 0 km |
| Çıktı | CSV, standart arşiv tespit kayıtları | CSV, standart arşiv tespit kayıtları |
| Ek filtre alanları sunulursa | Bütün güven/Type sınıfları, gündüz ve gece | Bütün güven/Type sınıfları, gündüz ve gece |

NOAA-20 başlangıcı resmî arşiv sayfasında 1 Nisan 2018 olarak gösteriliyor;
bu tarih eski yerel talebin başlangıcıyla da uyumlu. Eski CSV'ler 2024'ü de
içerdiğinden sonraki karşılaştırma eski kaynakların yalnız aynı eğitim
aralığına uygulanacak. Yeni talebe 2024/2025 eklenmez. Ülke kapsamı korunur;
dört il kesimi sonraki yerel denetimin parçasıdır. Yıllık özet/toplam
tablosu olay bazlı CSV yerine kullanılmaz.

FIRMS CSV'sinde Collection 2 seçimi aylık v4 seçimiyle karıştırılmaz;
ayrı üretim sürümü seçeneği görüldüğü varsayılmaz. İndirilen kaynağın
sürüm kanıtı ayrıca değerlendirilecek. MODIS/NOAA-21/Landsat bu iki
karşılaştırma talebine dahil edilmez.

Yeni dosyaların hedefi:

- `outputs/verification/firms_refresh_2026-10-21/received/SNPP/`
- `outputs/verification/firms_refresh_2026-10-21/received/NOAA20/`

Gönderilen talebin sensör/tarih/ülke ayarları ve manuel indirme tarih-saati
saklanmalı; bağlantıdaki erişim kodu veya kişisel e-posta Git'e aktarılmamalı.
ZIP'ler özgün adlarıyla ilgili sensör klasörüne konulacak. CSV'ler elektronik
tablo programıyla yeniden kaydedilmeden ve eski kaynakların üstüne yazılmadan
korunacak. Paket içeriği, anahtarlar ve Type değişimleri aktarım sonrasında
kontrol edilecek. Doğrudan CSV teslim edilirse özgün dosya da aynı klasöre konabilir.

Makinece okunabilir niyet kaydı `outputs/verification/firms_refresh_2026-10-21/expected_requests.json`.
SHA-256 `cb7c4e02c509b5fdbcce36e951858667a185cfde1e5fb04b882ad9ce207df8b8`.
Bu dosya indirme/karşılaştırma kabul makbuzu değildir; plan kimliği olarak saklanır.

## Aynı gün teslim sonrası karşılaştırma

Araştırmacı iki düzeltilmiş talebin ZIP dosyalarını aktardı. Ortak eğitim
döneminde S-NPP 230.286 ve NOAA-20 232.892 kaydın bütün 15 alanı eski
verilerle aynı çıktı; yalnız sıra değişti. Yukarıdaki plan ve indirme
hazırlığı günün önceki aşamasını anlatır. Sonraki gerçek uygulama, iki hesap
yöntemi, rapor hash'leri ve kabul sınırları
[teslim karşılaştırmasında](FIRMS_REFRESH_COMPARISON_2026-10-21.md) kayıtlıdır.
Eski kaynaklar korundu; aylık VV metadata veya fiziksel yangın doğrulaması
varmış gibi kabul alanları değiştirilmedi.
