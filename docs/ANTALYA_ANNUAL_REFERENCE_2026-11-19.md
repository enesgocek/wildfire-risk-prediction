# Antalya 2018: yıllık kaynak konumunun kullanım sınırı — 19 Kasım 2026

Amaç, yeni bir açık kaynağın 24 saatlik olay eşleştirmesine gerçekten
bilgi ekleyip eklemediğini belirlemek. Önceki Tırazlı/Muğla kaynakları
yeniden incelenmedi. Bu devam yeni bir yayınevi belgesini ve yalnız
2018 katalog bağlamını kapsar; yeni L veya yangın etiketi üretmez.

## Yeni kaynak ve konumun anlamı

Karabacak, Bayar ve Türkşen'in 2019 tarihli bildirisi, [İstanbul
Üniversitesi yayınevinin tam metninden](https://iupress.istanbul.edu.tr/book/1st-istanbul-international-geography-congress-proceedings-book/chapter/spatial-statistics-analysis-of-forest-fires-in-antalya-province)
alındı. DOI `10.26650/PB/PS12.2019.002.060`, basılı s. 615–630.
Yayın, 2018 için 242 kaynak kaydını kullandığını bildiriyor. Gün ve
koordinatları eşli özgün olay tablosu elde edilmedi. Bu sayı bizim
doğruladığımız gerçek yangın veya model örneği sayısı değildir.

Yöntemdeki **Central Feature**, kayıtlar arasındaki merkezi örneği
seçiyor; ortalama/ortanca merkezden ayrı. PDF s. 3'teki tanım ve
s. 11'deki Tablo 3 görüntüden okundu. 2018 için `(30.96; 36.93)`
veriliyor. Şekil 10, 2018 konumlarını neden sembolleriyle gösteriyor;
nokta başına olay günü/kimliği sunmuyor. Asistanın bu okuması
araştırmacı veya bağımsız uzman onayı olarak yazılmadı.

Tablodaki eksenlerin boylam/enlem ve datumun WGS84 olduğu **varsayıldı**;
bu yorum doğrulanmış kaynak koordinat sistemi değildir. İki ondalıklı
yazımdan hareketle ±0,005° kutusu yalnız en yakın değere yuvarlama
hipoteziyle, ±0,01° kutusu ayrı duyarlılık olarak incelendi. Bunlar
yangının toplam konum hatası veya güven aralığı değil. Keşif incelemesi,
ön kayıtlı deney olarak sunulmadı. Eşleşme yok diye aralık genişletilmedi.

## Yerel karşılaştırmanın sonucu

Her dosyada önce tarih metadata alanından **2018** seçildi; sonra
koordinatlar okundu. 2013 kaynak yılı ile 2023 kalibrasyon, 2024
karşılaştırma ve 2025 final bilimsel değerleri bu hesaba alınmadı.

| Yerel dosyanın kapsamı | Okunan 2018 tespit satırı | ±0,005° kutusu | ±0,01° kutusu |
|---|---:|---:|---:|
| Korunmuş proje aday kataloğu | 2.482 | 0 | 0 |
| Özgün S-NPP kaynak CSV'si | 37.316 | 0 | 0 |
| Özgün NOAA-20 kaynak CSV'si | 34.719 | 0 | 0 |

Kaynak CSV'lerine ek `type` veya güven filtresi uygulanmadı. Tablonun
satırları ayrı dosya kapsamlarıdır; toplanarak farklı yangın veya
bağımsız gözlem sayısı yapılmaz. Kaynak dosyaları sürekli/eksiksiz
gözlem sicili değildir. Özellikle NOAA-20 için 2018'in tüm günlerinde
gözlem bulunduğu iddia edilmez.

**Sıfır eşleşme, yangının olmadığı veya kaynak kaydının yanlış olduğu
anlamına gelmiyor.** Konumun yorumlanması, yayımlama hassasiyeti, tespit
edilebilirlik ve gözlem eksikliği bu karşılaştırmanın dışında kalıyor.
Olay günü uydu verisinden tahmin edilmedi; ortalama merkez yangın noktası
yapılmadı. Bu kaynaktan günlük pozitif veya negatif etiket çıkarılmadı.

## Katkı, kontrol ve devam sınırı

Bu kaynakta sayısal koordinat bulunması tek başına günlük hedef için
yeterli olmadı. Konumun rolü ile günün bilinmesi iki ayrı koşul olarak
somutlaştırıldı. İki olası L önerisi, WF1538'in atamasız tutulması ve
2.048 U anahtarı dosya kimlikleriyle korundu. Birinci aşama açık.

İki kutu için altı sayım ayrı Shapely hesabıyla da aynı bulundu;
ana hesap Decimal aralık karşılaştırması kullanıyor. Altı sonucun
sıfır olması sınır noktalarını zorlayan bağımsız gerçek veri testi
değildir; sınır davranışı ayrıca sentetik testte kontrol edildi.
**15 davranış testi**, Ruff ve biçim kontrolü geçti. Testler gelecekteki
yılların koordinatlarına erişmeme, toplam merkezlerin reddi, iki kutunun
ayrılması ve bulunan uydu tarihinden kaynak günü üretmeme koşullarını
sınadı. Kaynak anlamının otomatik doğrulandığı iddia edilmedi.

Bu belgenin günlük etiket edinimi yolu, açık tarihli olay tablosu veya
aynı kaynak konumuna bağlı başka bir olay-zaman kanıtı gelene kadar
incelemede kalır. Aynı yıllık haritayı daha ayrıntılı saymak bu eksik
tarihi sağlamaz. Açık kaynak devamında tarih, kayıt birimi ve konum
anlamını birlikte sağlayan teslimlere öncelik verilecek. Ana hedef,
PU varsayımları ve nihai birleştirme onayı değiştirilmedi.

## İzlenebilirlik

- PDF: **16 sayfa, 2.933.569 bayt**; SHA-256
  `c1ed88a6eb422627ad3d484546210e5f0ec8f64a6b813f51bea2fbb0867c659a`.
  DOI kimliği Crossref ile, tam metin yayıneviyle eşleşti. Tarayıcı
  indirme olayı zaman aşımından sonra yayınevinin görüntüleyicide açtığı
  CDN dosyası doğrudan HTTP 200 ile alındı; başarısız yol başarılı sayılmadı.
- [Yapılandırılmış kaynak/konum notu](research/antalya_annual_reference_2026-11-19.json).
- Tekrar üretim: `python scripts/quality/audit_antalya_annual_reference.py`.
- Yerel sonuç: `outputs/reports/dataset/antalya_annual_reference_v1/20261119T193111Z_13acb3c2/readback.json`;
  SHA-256 `819dbdd2596bdecc39ec06e47bda62adabae99a417304efa0ebbd19ebd25f531`.
- Ayrı geri okuma: aynı klasörde `independent_readback.json`;
  SHA-256 `848ce8ae9c9a68bfd82a825d8c727838e2111bcaedffbb60823cb64d5528ecf6`.
- Kaynak dosyaları, sayfa görselleri ve tespit tabloları yerel kaldı.
  Yeni yazışma, özel giriş, bulut işi veya eğitim başlatılmadı.
