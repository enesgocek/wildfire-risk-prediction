# Örtü kanıtının zamanı ve ek kaynak gereksinimi — 27 Ekim 2026

## Tamamlanan yerel kontrol

İki ayrı örtü kontrolü tasarımından sonra, mevcut görüntülerin hangi
amaçla kullanılabileceği denetlendi. 2018–2023 eğitim döneminden seçilmiş
25 noktanın 25 ilk ve 12 alternatif tarih kaydı birlikte incelendi.
37 nokta–görüntü kaydı 31 farklı Sentinel-2 ürününe karşılık gelir;
aynı sahnenin farklı noktalardaki kesitleri bağımsız sahne sayılmadı.

| Kontrol | Sonuç | Anlamı |
|---|---:|---|
| Çekimi T öncesindeki 60 gün içinde olan kayıt | 37/37 | Geriye dönük olay öncesi görüntü bağlamı var |
| Kullanılan ürün sürümü T sonrasında oluşturulan kayıt | 20/37 | Bu sürüm T anındaki model girdisi olamaz |
| Geçmişte erişilebilirliği doğrulanmış kayıt | 0/37 | Ürün oluşturulması ile geçmişte erişilebilirlik aynı kabul edilmedi |
| Birden fazla tarih bulunan nokta | 6/25 | Diğer 19 nokta hâlâ tek tarihli |
| En az bir tarihte yerel SCL bulut/sirüs sayımı sıfır nokta | 21/25 | Otomatik sayım; insan görünürlük veya örtü kabulü değil |
| En az bir tarihte seçili altı kalite işareti sıfır nokta | 9/25 | Doğal orman/tarım ayrımı bu sayımla çözülmez |
| En az bir ürünü T'ye kadar oluşturulmuş nokta | 13/25 | Geçmiş erişim kanıtı yerine geçmez |

Altı işaret: bulut/sirüs, bulut gölgesi, koyu/gölge, eksik/bozuk piksel,
sınıflandırılamayan piksel ve kar/buz. Sıfır değer bir üretim kabul eşiği
olarak seçilmedi. Toplam 25 nokta korunmuş, hedefler boş bırakılmıştır.
İnsan ön notları 10/25 olarak ayrı kaynaklarında kalır; otomatik kontrol
yeni insan değerlendirmesi üretmez.

## Örneğe göre ilerleme

| Örnek | Yerel bulgu | Gereken ek kanıt |
|---|---|---|
| C | İnsan orman/çalılık ön notu; tek tarihte altı kalite işareti sıfır | Doğal/yönetilen kullanım ayrımını destekleyen kanıt; otomatik nihai kabul yok |
| D | Tek görüntü; karışık alan ön notu; sınıflandırılamayan piksel var | Parsel ve doğal odunsu alanın konumsal ayrımı |
| E | Tek görüntüde altı kalite işareti sıfır; insan tarla benzeri diyor | Görünürlükten ziyade arazi kullanımını ayıran kaynak gerekir |
| F | Tek görüntü; kullanılan ürün sürümü T sonrası; tarla benzeri ön not | Geriye dönük inceleme sürdürülebilir; dönemine uygun kullanım kanıtı gerekir |
| R03 | Üç tarih; alternatiflerden birinde altı işaret sıfır | Yeşil/parlak yüzeyleri doğal orman veya bulut diye kesinleştirmeden kullanım bağlamı |
| R11 | Altı işaret sıfır; insan kuru görünüm notu | Kuruluk ile seyrek/doğal örtü yokluğunu ayıran dönemsel bağlam |
| R15/R16 | Birer tarih; insan sınıf ayıramadı/benzerlik belirtti | Arazi kullanım bağlamı ve konum belirsizliği; aynı görsele tekrar zorunlu sınıf seçtirilmez |

Bu tablo veri talebini somutlaştırır. E'de yalnız bulutsuz başka bir
görüntü bulmak, doğal örtü–tarımsal kullanım sorusunu kendiliğinden çözmez.

## Resmî kaynakların uygunluğu

27 Ekim'de aşağıdaki birincil kaynaklar kontrol edildi:

- **Copernicus 100 m yıllık örtü:** 2015–2019 dönemini kapsar. 2018/2019
  için daha yakın referans sağlayabilir; 2021–2023'ü yıllık olarak çözmez.
  [Ürün kaydı](https://land.copernicus.eu/en/products/global-dynamic-land-cover/copernicus-global-land-service-land-cover-100m-collection-3-epoch-2015-2019-globe).
- **WorldCover:** 2020 ve 2021 ürünleri vardır; sürüm farkları doğrudan
  gerçek arazi değişimi olarak yorumlanamaz. 2021 haritası 28 Ekim 2022'de
  yayımlandı. Ağaç sınıfı zeytin gibi plantasyonları da içerir; odunsu
  tarım ağaç/çalı sınıfına girebilir, seralar yapılaşmada ele alınır.
  Dolayısıyla daha ince çözünürlük doğal örtü sorununu tek başına çözmez.
  [Erişim ve sürüm açıklaması](https://esa-worldcover.org/en/data-access),
  [ürün kılavuzu, sınıflar ve zaman kapsamı](https://esa-worldcover.s3.eu-central-1.amazonaws.com/v200/2021/docs/WorldCover_PUM_V2.0.pdf).
- **Dynamic World:** 2015'ten başlayan Sentinel-2 temelli sınıf olasılıkları
  vardır. Aynı Sentinel kaynak ailesiyle ilişkisi korunmalı; bağımsız
  olay/örtü gerçeği sayılmamalı. Resmî katalog, tarım gibi zaman içinde
  tanımlanan sınıflarda tek görüntü olasılıklarının zayıf kalabileceğini belirtir.
  [Resmî katalog](https://developers.google.com/earth-engine/datasets/catalog/GOOGLE_DYNAMICWORLD_V1).
- **CORINE 2018:** 44 sınıfta kullanım bağlamı sağlar; meyve bahçesi (222)
  ve zeytinlik (223) gibi ayrımlar mevcut sorumuzla ilgilidir. 25 hektar
  asgari haritalama birimi ve 100 m asgari genişlik nedeniyle küçük veya
  karışık piksel alanlarını kesin sınıflandıramaz. 2017–2018 referansıdır;
  ileriki yıllara otomatik taşınmaz. [Ürün kaydı](https://land.copernicus.eu/en/products/corine-land-cover/clc2018),
  [resmî sınıf kılavuzu](https://land.copernicus.eu/content/corine-land-cover-nomenclature-guidelines/docs/pdf/CLC2018_Nomenclature_illustrated_guide_20190510.pdf).

CORINE araştırması bağımsız yangın kaydı yerine geçmez. Harita ürünlerinin
genel doğruluk oranları bu 25 noktanın doğruluğu olarak kullanılmadı.

## CORINE erişim kontrolü

EEA'nın açık `Corine/CLC2018_WM/MapServer` hizmetinde önce tek C kontrol
noktası sorgulandı; HTTP 502 döndü. Tek sınırlı tekrar sırasında katman
metadata isteği ReadTimeout, nokta isteği yine HTTP 502 verdi. Yanıt
başına 256 KiB sınırı ve kısa bağlantı/okuma süreleri kullanıldı.
Kimlik bilgisi veya bulut işi kullanılmadı. 25 noktalık sorguya geçilmedi;
bu servisten hiçbir nokta sınıfı alınmış sayılmıyor.

Saklanan tekrar tanısı:
`outputs/reports/dataset/corine_access_probe_v1/20261027T190218Z/readback.json`.
SHA-256: `3c519932661fa6b19eba51193a6b44fae183e723188eca4fdcd3a4936ee1b65b`.
502 gövdesi ayrı saklandı; veri sınıfı veya çalışma talimatı olarak işlenmedi.

## Uygulanacak inceleme sırası

1. Mevcut görüntü kimliği, çekim zamanı, ürün zamanı ve yerel kalite
   kayıtları ayrı kalır. Bu kontrol 37 kayıt için tamamlandı.
2. Doğal/yönetilen örtü sorusuna uygun arazi kullanım kaynağı eklenir.
   CORINE için sıradaki teknik adım resmî alternatif erişim/indirme
   yolunu doğrulamak; servise sürekli tekrar isteği atılmayacak.
3. Kaynak gelirse önce aynı 25 merkezin sınıf kodu ve eksik kapsamı
   denetlenir. Sonra karışık alanlar için konumsal inceleme yapılır.
   Merkez sınıfı bütün uydu pikseline veya 5 km hücreye yayılmaz.
4. Harita–görüntü–insan notu çelişkileri korunur. Çözülemeyen adaylar
   etiket almadan incelemede kalır. Bu protokol yeni 0/1 veya kapsam
   eşiği onayı içermez; son kabul ayrıca gereklidir.

## Yerel doğrulama

114 kaynak/kod kimliği, 37 makbuz ve 74 TCI/SCL dosyasının bütünlüğü
kontrol edildi; kimlik/zaman dilimi, 60 günlük pencere, nokta başına
farklı tarihler, SCL toplamları, kapalı kabul alanları ve JSON geri
okuması geçti. Yeni betik lint/format kontrolünü geçti. Raster kalite
sayımları bu adımda yeniden hesaplanmadı; hash ile korunan önceki
ölçümler kullanıldı. Bu denetim 2024/2025'i açmadı.

Güncel çıktı:
`outputs/reports/dataset/habitat_temporal_evidence_audit_v1/20261027T190350Z_207a4734/readback.json`.
SHA-256: `38e03a124e6c5da221ae545941997cb6f34cfd0ff3700bb412b25effc458dda9`.
İlk çalışma `20261027T190326Z_47040425` korunmuştur; satır adı/sayım
açıklığı ve biçim kontrolü tamamlanan bu sonraki çıktı rapor esasını oluşturur.
