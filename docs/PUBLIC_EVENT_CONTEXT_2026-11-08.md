# Açık müdahale kayıtlarıyla iki olay incelemesi — 8 Kasım 2026

Urla–Karaburun ve Aydıncık için açık müdahale kaynakları, yerel
FIRMS kataloğu ve 2021 EFFIS yaz kesiti karşılaştırıldı. Bu iki
amaçlı vaka, olay ve ilk uydu tespiti arasındaki farkı denetlemek
için ayrıldı. Açık olay kaydı olmayan bir günü sıfır yapma
veya eşleşme oranını tüm döneme yayma işlemi yapılmadı.

## Açık olay bilgisi

- **Urla–Karaburun, 14 Ağustos 2021.** İzmir İtfaiyesi açık API'si
  Karaburun için 72, Urla için 294 ilçe kaydı döndürdü. 13–16
  Ağustos aralığında sırasıyla üç ve beş kayıt var. 14 Ağustos
  Urla orman/fidanlık satırında ekip çıkışı 07.28. Aynı gün
  Karaburun'da bu türde kayıt bulunmadı. Urla'daki 15 Ağustos
  orman/fidanlık satırı ayrı tutuldu. Yerel saha haberi olayı
  Küçükbahçe–Karareis olarak ve yaklaşık 07.30 ile anlatıyor.
  Portalın 2021 sözlüğünde ilçe var, olay koordinatı yok.
  Çıkış saati, başlangıç veya ilk uydu saati olarak kullanılmadı.
  [İzmir açık veri ve sözlük](https://acikveri.bizizmir.com/dataset/izmir-itfaiyesi-yangin-mudahale-istatistigi/resource/bb53e102-882c-4231-a8d0-2910b9c7882d) · [Saha haberi](https://www.bizimyarimada.com/foto/karaburun-da-yangin_396/).
- **Aydıncık, 15 Temmuz 2021.** Mersin Valiliği'nin 17 Temmuz
  açıklaması Pembecik, Şırşır mevkiinde sabah başlayan orman
  yangınını kaydediyor. Başlangıç koordinatı ve kesin dakika
  verilmedi. 28 Temmuz'daki başka Aydıncık kaydıyla karıştırılmadı.
  [Mersin Valiliği açıklaması](https://www.mersin.gov.tr/bakan-pakdemirli-mersinde-3-gundur-devam-yangin-kontrol-altina-alindi).
- **C için yeni bağlam.** 15 Ağustos 2021 tarihli İHA haberi
  Kuyucak–Öteoluk adını veriyor. Başka bir haber yaklaşık
  15.00 başlangıç bildiriyor. C'nin ilk uydu tespiti Türkiye
  saatiyle 13.24. Saatler yaklaşık veya farklı gözlem
  türlerini ifade ediyor. Bu fark ve başlangıç koordinatının
  eksikliği nedeniyle C ile olay birleştirilmedi. Belediye
  planı Öteoluk adını doğruluyor ve kesin yangın konumu vermiyor.
  [İHA haberinin yayımlanan kopyası](https://www.haberler.com/3-sayfa/antalya-da-orman-yangini-basladi-14332674-haberi/) · [Yaklaşık saat](https://m.haber7.com/guncel/haber/3130626-canakkale-ve-antalyada-orman-yangini) · [Belediye planı](https://antalya.bel.tr/Content/UserFiles/Files/imar_plan_tadilat%2F%C4%B0GA%20PLAN%20A%C3%87IKLAMA%20RAPORU_12122018.pdf).

2023 İzmir kaynağının API şeması ayrıca kontrol edildi.
`ADRES_BOLGESI` alanı var ve koordinat yok. İki yılın
kayıtlarının yapısı aynı kabul edilmedi. Adres içeriği çekilmedi.

## Yerel FIRMS ve sınır karşılaştırması

Tarih ve il bağlamına uygun, önceden indirilmiş iki EFFIS
poligonu kullanıldı. Bu sınırlar sonradan elde edilmiş mekânsal
bağlamdır. VIIRS ile ortak kaynak ihtimali ve yangının ilerlemesi
nedeniyle bağımsız başlangıç konumu olarak kullanılmadı.
Önceki üç UTC günde iki poligonun içinde seçili Type 0 katalog
satırı yok. Bu, olay olmadığını kanıtlamaz.

| Bağlam | EFFIS kimliği ve alanı | Aday gününde sınır içinde tespit | Sınır içindeki ilk uydu tespiti (UTC) | Dokuz gruplamada ilk hücre |
|---|---|---:|---|---|
| Urla–Karaburun | 52498, 349 ha | 19 | 14 Ağustos 10.44, aynı anda 11 nokta | Tek hücre, tüm ayarlarda aynı |
| Aydıncık–Pembecik | 50667, 2.410 ha | 128 | 15 Temmuz 10.05, aynı anda 31 nokta | Dört hücre, tüm ayarlarda aynı |

Urla'da ekip çıkış saati Türkiye yerel saati olarak okunursa,
seçili katalogdaki ilk tespit 6 saat 16 dakika sonradır.
Bu, iki ayrı kaydın saat farkıdır. Olay kimliğinin kesin
eşleşmesi veya ölçülmüş uydu gecikmesi değildir. Aydıncık'ta
Valilik açıklamasındaki yaklaşık 1.500 ha etkilenme ile EFFIS
2.410 ha sınırı, farklı kapsam ve ölçüm olarak saklandı.

İlk tespit zamanı sabit olsa da üye sayıları Urla'da 20–21,
Aydıncık'ta 296–300 aralığında. Aydıncık'ta dört ilk hücrenin
yalnız üçünde en erken tespit merkezlerinden biri son sınırın
içinde. İlk hücreleri yalnız son sınırdan üretmek
`C640_R864` hücresini kaybettirirdi. Dört hücre korunur ve
aynı olay adayı ayrı yangınlar gibi sayılmaz. 2017 örtü
tablosunda bu beş hücrenin orman/çalılık payı %91,31–%99,92.
Bu hücre bağlamı, ilk noktadaki olay tarihli yerel örtüden ayrıdır.

## Eşleştirme koşulu ve doğrulama

Açık kayıt ileride olay başlangıcına ait doğrulanabilir nokta
ve zaman aralığı sağlarsa mevcut alım protokolüyle incelenir.
Önce zamanın anlamı ve konum kökeni doğrulanır. Belirsizlik
birden fazla gün veya hücreye uzanıyorsa hepsi incelemede
korunur. En yakın uydu tespitini seçmek tek başına yeterli
değildir. Bu iki vaka, yeni olay için bağlam referansı olarak
kalır. Eşleştirmeye hazır kesin konumlu kayıt ve üretilmiş etiket
sayısı sıfırdır.

Üretici `scripts/quality/review_public_reference_cases.py`.
Yerel çıktı `outputs/reports/dataset/public_reference_cases_v1/20261107T231732Z_424d1731/readback.json`.
SHA-256 `b1aac4c4bec040d0446dc64a99f3312a3ba9c86e90a1c478a3c4b0782984596c`.
26 girdi/kod kimliği, 18 vaka×ayar, JSON ve Ruff kontrolleri geçti.
Beş eski hücre bağlamı ayrı hash kontrolüyle okundu. API'nin SQL
sorgusu HTTP 400 döndürdü. Sonuçlar normal açık API filtresi ve
ISO tarih metniyle yeniden kontrol edildi. 2024 satırları
analizden önce tarih filtresinde çıkarıldı, 2025 kapalı kaldı.
Olay, sınır ve referans alımıyla ilgili 73 mevcut test, çalışma
alanında ayrı bir geçici dizinle geçti. İlk test çağrısında
varsayılan geçici dizin oluşturulamadığı için bir kurulum hatası vardı.
