# CORINE 2018 teslimi ve 25 merkez kontrolü — 4 Kasım 2026

## Sonuç

Araştırmacının resmî portaldan indirdiğini bildirdiği `7858.zip` yerelde
kontrol edildi. Paket özgün CORINE 2018 durum katmanının **v2020_20u1**
sürümünü içeriyor. Accounting veya değişim katmanı değil. Dosya alımı ve
sınırlı merkez örneklemesi başarılı; nihai habitat/olay/etiket kabulü açık.

İndirme URL'si veya oturum bilgisi saklanmadı. Sağlayıcının bağımsız dosya
checksum'u elde edilmedi; kaydedilen SHA-256 yerel dosya kimliğidir.

## Arşiv ve raster kontrolleri

- Dış ZIP: **130.418.464 bayt**, içinde tek özgün ürün ZIP'i.
- İç ZIP: **131.037.466 bayt**, 71 üye, açılmış toplam **256.904.175 bayt**.
- İki ZIP'in tüm üyelerinde CRC geçti; tekrarlı/tehlikeli yol, symlink ve
  şifreli üye kontrolleri geçti. İçerik çalıştırılmadı; yalnız gerekli
  ana raster ve yedi yardımcı metadata/legend dosyası yeni çıktı dizinine alındı.
- Paket README'si katman adını, Şubat 2020 güncellemesini ve Türkiye'nin
  2018 kapsamına eklendiğini açıklıyor. Metadata ve dosya adı birlikte korundu.
- Ana raster: 46.000 × 65.000 piksel, 100 × 100 m, tek bant **int8**;
  raster NoData **−128**. Legend'deki **48 → 999/NODATA** ayrıca korunur.
- 1–44 raster değeri, üç haneli CORINE koduna QGIS legend'inden eşlendi.
  DBF `Value` / `CODE_18` alanlarıyla 45 eşleme birebir uzlaştırıldı.
  Örneğin raster değeri 24, sınıf kodu 312'dir; değer 24 sınıf kodu değildir.
- Raster eski ETRS89 WKT'sinde EPSG:3035 olarak beyan edilmiş; otomatik
  `to_epsg()` tanıması None döndü. LAEA yöntemi/parametreleri ve GRS 1980
  elipsoidi doğrulandı. 25 koordinatta kaynak WKT ile EPSG:3035 dönüşümleri
  arasındaki en büyük fark **0 m**; bağımsız TFW kaydı TIFF dönüşümüyle eşit.

İlk betik çalışması otomatik EPSG tanıması/uint8 varsayımında durdu.
Kaynak dosya değiştirilmedi. Gerçek WKT/parametre ve işaretli 8 bit biçimi
incelenip açık kontroller eklendi; sonraki çalışma geçti. Önceki kısmi
çalışma dizini korunuyor. Terminalde bir metadata yazdırma girişimindeki
Unicode kodlama hatası dosya bozukluğu değildi; sonraki okuma tamamlandı.

## Ölçülen merkez sınıfları

Örneklem mevcut 2018–2023 incelemesindeki amaçlı **25 nokta / 21 hücre-gün**
ile sınırlı; bağımsız yangın sayısı veya tüm verisetinin dağılımı değildir.
Merkezler dönüştürülüp sınıf interpolasyonu olmadan okundu. 25/25 geçerli
sınıf var. Her merkez değeri ayrı 3×3 raster okumasının orta pikseliyle
eşleşti. 10/25 noktada 300 × 300 m komşulukta birden fazla sınıf bulunuyor;
bu yaklaşık uydu tespit alanının tamamı veya hücre örtü oranı değildir.

| CORINE kodu | Sınıf | Nokta |
|---|---|---:|
| 121 | Sanayi veya ticaret birimleri | 5 |
| 122 | Karayolu/demiryolu ve ilişkili alanlar | 1 |
| 211 | Sulanmayan ekilebilir arazi | 1 |
| 212 | Sürekli sulanan arazi | 4 |
| 213 | Pirinç tarlaları | 1 |
| 222 | Meyve ağaçları ve üzümsü meyve plantasyonları | 2 |
| 243 | Doğal bitki örtüsü de içeren, ağırlıkla tarımsal arazi | 1 |
| 321 | Doğal çayırlar | 4 |
| 323 | Sklerofil bitki örtüsü | 1 |
| 324 | Geçişli ağaçlık–çalılık | 1 |
| 333 | Seyrek bitki örtülü alan | 1 |
| 411 | İç kesim bataklıkları | 2 |
| 511 | Akarsu yatakları | 1 |

## Önceki görsellerle birlikte yorumlanacak örnekler

| Kod | Yeni merkez bağlamı | Araştırmaya etkisi ve sınırı |
|---|---|---|
| D | 324 geçişli ağaçlık–çalılık | Karışık ağaçlık ön notuna ek bağlam; komşulukta meyvelik ve mera da var |
| E | 243 tarım + doğal örtü mozaiği | Araştırmacının tarla benzeri yorumuyla uyumlu bağlam; tamamen tarım veya tamamen doğal sayılmaz |
| F | 222 meyve bahçesi/plantasyon | Eski haritanın ağaç sınıfının doğal orman anlamına gelmeyebileceğini somutlaştırıyor |
| C | 321 doğal çayır | Önceki ağaçlık yorumuyla uyuşmazlık korunuyor; 3×3 komşulukta 312 iğne yapraklı orman da var |
| R03 | 323 sklerofil örtü | Odunsu örtü için ek bağlam; komşulukta tarım sınıfları da var |
| R11 | 333 seyrek bitki örtüsü | Kuru/açık görünüm notuna bağlam; meteorolojik kuraklık ölçümü değildir |
| R15/R16 | 411 iç kesim bataklığı | İki noktanın benzer görünümüne bağlam; aynı hücre-gün bağları korunuyor |
| A / B | 122 yol alanı / 212 sulanan tarım | Önceki yapılaşma belirsizliği ve tarım yorumlarıyla birlikte incelenecek |

Sınıflar, özellikle 2021–2023 noktaları için olay tarihindeki arazi
kullanımının doğrulanması değildir. 2017–2018 referansı, 25 ha haritalama
birimi ve konum/sınır belirsizliği sürüyor. Bu ürünün T anındaki girdiye
uygunluğu kabul edilmedi. İnsan ön notları yeniden yazılmadı; 10/25 olarak
kalıyor. CORINE merkezi hücreye yayılmadı; 0/1 etiket veya dışlama yapılmadı.

## Kanıt ve devam

Çıktı: `outputs/reports/dataset/corine_delivery_review_v1/20261103T212921Z_3cc30ebb/`.
Dizin UTC tarihini taşır; Türkiye'deki çalışma tarihi 4 Kasım'dır.
`readback.json` SHA-256:
`be52cf11729cec66f84a8abf8d45c3ac9bfaf8d764f68255f2c5ab4ae3b4313f`.
Dış ZIP SHA-256:
`aefe9f5175ca05d9e786b9ef221a78236018398b8d93649dc3fa33b161f090db`.
Ek geri okuma: aynı dizinde `independent_readback.json`, SHA-256
`31047a2c82659f4557fabd8382ed1e06dec7ab708b908780ce1298a6de28afe5`.

11 kaynak/kod/karşılaştırma dosyasının hash'i çalışma sonunda tekrar
doğrulandı. JSON geri okuması, DBF–QML eşlemesi, iki örnekleme yolu,
TFW karşılaştırması ve lint/format geçti. Bu, Avrupa rasterının bütün
piksellerinin bilimsel denetimi değildir; arşiv CRC kapsamı tamdır.
Yeni ağ veya GCP işlemi yapılmadı. Eski 27 Ekim alım hazırlığı değişmedi;
teslim yeni tarihli makbuzla kaydedildi.

Sıradaki iş C/D/R03 gibi sınıf sınırı veya kullanım karışımı olan
noktalarda yaklaşık tespit alanının sınıflarla kesişimini incelemek ve
mevcut olay öncesi görüntülerle uyuşmazlıkları değerlendirmektir.
Alan hesabı ve tarihe aktarım kuralı henüz kabul edilmiş değildir.
