# CORINE kaynak seçimi ve yerel alım hazırlığı — 27 Ekim 2026

## Sonuç ve kapsam

Özgün CORINE 2018 raster dosyasının resmî katalog kimliği doğrulandı.
Verinin kendisi henüz alınmadı; 25 tespit merkezinin karşılaştırma dosyası
hazırlandı. Amaç, mevcut görsellerdeki doğal odunsu örtü ile tarımsal kullanım
belirsizliğine ek bağlam sağlamaktır. Bu ürün bağımsız yangın kaydı değildir.

Ürün sayfasının REST bağlantısı artık `image.discomap.eea.europa.eu`
adresini gösteriyor. Bu adreste kimliksiz katman isteği HTTP 502 / 450 bayt
ile sonuçlandı (terminal çıktısı). Önceki `copernicus.discomap` denemeleri
ayrı raporda korunuyor. Buna karşılık CLMS ürün API'si ve EEA katalog XML'i
HTTP 200 ile alınıp dosya olarak saklandı. Harita servisi hatası, bütün
indirme yollarının kapalı olduğu şeklinde yorumlanmadı.

## Doğrulanmış dosya seçimi

| Alan | Resmî katalog değeri |
|---|---|
| Ürün | CORINE Land Cover 2018 (vector/raster 100 m), Europe, 6-yearly |
| Paket | `u2018_clc2018_v2020_20u1_raster100m` |
| Sürüm | `v2020_20u1` |
| Tür / biçim | Raster / Geotiff |
| Çözünürlük | 100 m |
| Katalogda bildirilen boyut | 125 MB; gerçek indirilen byte sayısı henüz bilinmiyor |
| Dataset UID | `0407d497d3c44bcd93ce8fd5bf78596a` |
| Paket kimliği | `3d9e2413-46ca-4f6e-abf8-b6eb429a4e48` |
| Katalog DOI | `10.2909/960998c1-1870-4e82-8051-6485205ebbac` |

[Ürün ve indirme sayfası](https://land.copernicus.eu/en/products/corine-land-cover/clc2018).
[Resmî ürün API'si](https://land.copernicus.eu/api/en/products/corine-land-cover/clc2018).
[EEA metadata kaydı](https://sdi.eea.europa.eu/catalogue/srv/api/records/960998c1-1870-4e82-8051-6485205ebbac/formatters/xsl-view?approved=true&language=eng&output=pdf)
indirme için kimlik doğrulaması gerektiğini belirtiyor.

Araştırmacının yapacağı işlem: ürün sayfasında hesabına giriş yaparak
Download / Download pre-packaged data collections bölümündeki bu raster
satırını seçmek, indirme isteğini tamamlamak ve hazır olan ZIP'i açmadan
`data/raw/landcover/corine_2018_review/incoming/` klasörüne koymak.
Klasör oluşturuldu. Portalın verdiği özgün dosya adı korunabilir; sayı
ile adlandırılmış teslimin içeriği daha sonra denetlenecek. 4 GB GPKG ve
5 GB GDB alternatifleri bu ilk karşılaştırma için istenmiyor.
Şifre, oturum belirteci veya kişiye özel indirme bağlantısı rapora konulmaz.

## Alternatif ürünün neden seçilmediği

EEA'nın Eylül 2026 tarihli **2018 accounting v21** kaydı, 2018 katmanının
2024 durum haritası ve değişim katmanından geriye türetildiğini açıklıyor.
Bu ürün özgün 2018 durum katmanıyla aynı değildir. Yıl etiketinin 2018
olması zamansal kökenin aynı olduğunu göstermediği için bu alımda
yerine kullanılmadı. Bu kaynağın yalnız metadata açıklaması incelendi;
2024/2025 proje verileri veya yeni accounting rasterı açılmadı.
[EEA accounting ürününün köken açıklaması](https://sdi.eea.europa.eu/catalogue/srv/api/records/0f878901-6c51-41ae-b54d-52e794870e9c?language=all).

Seçilen özgün ürün de T anında erişilebilir model girdisi olarak kabul
edilmiş değildir; 2017–2018 referansı sonraki yılların gerçeği sayılmaz.
25 ha haritalama birimi ve 100 m ölçek küçük/karışık alanları sınırlıyor.

## Hazırlanan yerel karşılaştırma

Sabit 25 nokta / 21 hücre-gün birimi için WGS84 merkez GeoJSON'u üretildi.
2018–2023 tahmin zamanları, nokta kimlikleri, mevcut inceleme kodları ve
birden fazla ilk noktanın ortak birim ilişkileri korundu. Eski karar
kuyruğu yalnız bu kimlikler için kullanıldı; eski insan notu sayısı güncel
inceleme durumu olarak aktarılmadı. Güncel insan ön notu sayısı 10/25'tir.

Yedi kaynak/kod/ayar hash'i çalışmadan önce ve sonra, çıktı hash'i ve
JSON geri okumaları kontrol edildi. 25 tekil kimlik, 21 birim ilişkisi,
eğitim dönemi ve 6933 → 4326 → 6933 koordinat geri dönüşü doğrulandı.
Dönüşüm kontrolü coğrafi doğruluk veya gerçek yangın konumu kanıtı değildir.
Yeni betik lint/format kontrolünü geçti. CORINE sınıfı sayısı **0/25**;
hedefler boş, gözlem unknown, etiket ve birleştirme izinleri kapalıdır.

Dosya geldiğinde önce ZIP bütünlüğü ve güvenli dosya yolları, ürün sürümü,
CRS/çözünürlük, NoData ve paket içindeki sınıf kodu eşlemesi denetlenecek.
Rasterdaki 8 bit değer doğrudan üç haneli CORINE kodu sanılmayacak.
Merkez örneklemesinde sınıf interpolasyonu yapılmayacak; merkez sınıfı
tüm tespit alanı veya 5 km hücreye yayılmayacak. Harita–görüntü–insan
uyuşmazlıkları korunacak. Eşik veya nihai habitat kabulü bu alımın sonucu değildir.

## Kanıt yolları

- Kaynak yanıtları: `outputs/reports/dataset/corine_source_discovery_v1/20261027T191433Z_140ee9d2/`.
  `product.bin` SHA `927ee9f99a45e922694ee89dc0243239800bf7a6907301364e5f526b0e2aef2a`;
  `catalog.bin` SHA `417673dc464e2f5c02b0e108577a32779d18f6c8e513d6f4d61e1ca9148be595`.
- Karşılaştırma hazırlığı: `outputs/reports/dataset/corine_review_intake_v1/20261027T191612Z_2cba6fc4/`.
  `readback.json` SHA `b89e638e3e3983304e20dca61ec1eafc9b246e2050e3deb4078260103f79d806`.
- Açık alım koşulları: `configs/corine_2018_review_intake_v1.json`.
  Gerçek veri hash'i henüz yoktur; katalog kimliği veri bütünlüğü kabulü değildir.
