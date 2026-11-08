# İlk tespitlerde örtü kanıtı ve inceleme önceliği — 8 Kasım 2026

71 ilk tespitin merkez sınıfı, yaklaşık alan aralığı, varsa olay öncesi görüntü ve araştırmacı ön notu aynı tespit kimliğiyle bağlandı. Pilot için risk hücresinin 2017 örtü bağlamı ayrıca taşındı. Açık olay noktalarına pilot hücre bilgisi aktarılmadı. [71 satırlık yerel inceleme tablosu](../outputs/reports/dataset/candidate_cover_readiness_v1/20261108T001455Z_723d1e85/inceleme_tablosu.md).

## Görüntü ve not kapsamı

| Örneklem | Tespit | Olay öncesi görüntüsü olan | Araştırmacı ön notu olan |
|---|---:|---:|---:|
| Yöntem pilotu | 25 | 25 | 13 |
| Aydıncık–Pembecik | 34 | 11 | 0 |
| Urla–Karaburun | 12 | 6 | 0 |
| Toplam | 71 | 42 | 13 |

Pilotun 37 görüntü kaydı, önceki yaklaşık piksel çevresine bağlı okuma kayıtlarından taşındı. Açık olaylarda aynı görüntü birden fazla merkezi kapsayabiliyor. İki raster kesiti bir tespitin kendi 250 m çevresini tam içerdiğinde bu tespit için SCL sınıf ve kalite sayıları yeniden ölçüldü. Aydıncık'ta yalnız bir yeni nokta için iki küçük kesit alındı. Açık olaylarda 34 nokta–görüntü kaydı, dört farklı çekim tarihine karşılık gelir. Kalan 29 nokta için bu yerel pakette tam çevre kesiti bulunmuyor. Bu sayı kaynak katalogda sahne bulunmadığı anlamına gelmez.

## Kanıtın sonucu değiştirdiği örnekler

| Örnek | Birlikte okunan kanıt | İnceleme durumu |
|---|---|---|
| C | Merkez doğal çayır, önceki yaklaşık alanın %78'i orman kodunda. 20 Temmuz 2021 görüntüsünde seçili kalite işaretleri yok ve önceki araştırmacı notu ağaçlık/çalılık bağlamını destekliyor. | Ağaçlık bağlam destekli. Olay ve başlangıç yeri ayrı doğrulanmalı. |
| R03 | Merkez sklerofil örtü, önceki yaklaşık alanda orman/çalılık kodları yaklaşık %37. İki daha temiz alternatifte açık/parlak yüzeyler ve yeşil örtü birlikte. Araştırmacı ön yorumu da belirsiz. | Karışık örtü, tek sınıfa zorlanmaz. |
| R05 | Eski harita ekilebilir arazi, 5 Ağustos 2023 kesitinde araştırmacı yapay yüzey görünümü bildirdi. | Kaynaklar arası bağlam farkı korunur. Değişimin zamanı ve ısı kaynağı bilinmiyor. |
| R06 | 6 Ekim 2018 görüntüsünde araştırmacı tarım görünümü bildirdi. CORINE yaklaşık alanı sulanan tarım ve meyvelik kodlarıyla örtüşüyor. | Tarımsal bağlam destekli. CORINE referans döneminin tahmin sonrasına uzandığı kaydı korunur. |
| R07 | Ön notta çevrede tarım ve merkezde karışıklık var. CORINE alanı tarım, akarsu ve kentsel doku içeriyor. Görüntüde kalite işaretleri var. | Yerel örtü ayrımı açık. |
| Aydıncık, 135300 / 135313 / 135314 | Her noktada 7 ve 12 Temmuz 2021 RGB kesitlerinde yeşil örtü ile açık/yol/parsel benzeri yüzeyler birlikte görülüyor. Altı 250 m çevrenin tamamında en az bir SCL kalite işareti var. | Üç nokta yönelim ve örtü bakımından ayrı kaydedildi. Aynı olay adayındaki bağları korunur. |
| Urla, 146706 | 5 ve 10 Ağustos 2021 görüntülerinde kıyı kesişimi görülüyor. Eski haritalar merkezde farklı sınıflar veriyor. | Kıyı konumu belirsiz, ortak adayda tutulur. |

Aydıncık'ın 135313 noktasında SCL bitki örtüsü sınıfı iki tarihte de yaklaşık %43. 135314'te yaklaşık %59–62. Bunlar 250 m daire içindeki 20 m piksel merkezlerinin genel bitki örtüsü sınıfı oranlarıdır. CORINE alan oranının veya doğal orman payının yerine kullanılmaz. Aydıncık görselinde beyaz çarpı tespit merkezi, sarı çizgi görüntü inceleme çevresidir. [Aydıncık karşılaştırması](../outputs/reports/dataset/candidate_cover_readiness_v1/20261108T001455Z_723d1e85/aydincik_review.png).

## Sonraki uygulama

Bu tablo mevcut 71 tespitin örtü incelemesini tek yerde kullanılabilir hale getirir. Önerilen sonraki pilot, eğitim dönemi aday havuzundan il, yıl ve örtü bağlamına göre seçilmiş örneklerde doğal örtüyü destekleyen, yönetilen örtüyü destekleyen ve çözülemeyen inceleme durumlarının dağılımını ölçmektir. Aydıncık'taki üç noktada insan gözü, yerel görünümün tarımsal, doğal veya karışık olup olmadığına ek yorum katabilir. Bu yorum tek başına ilk ısı kaynağına konum veremeyeceği için bu aşamanın ilerlemesine ön koşul yapılmadı.

Örtü kabulü ve yangın hedefi açık. Görüntüsü eksik noktalar, gözlemin yetersiz olduğu günler ve bağımsız olay eşleşmesi ayrı tutulur. Kullanıcının kabul ettiği hücre–yerel örtü ayrımı korunur. %50 yalnız merkez–alan inceleme işaretinde kullanılır. Eşik kabulü, otomatik dışlama, yangın etiketi ve nihai birleştirme uygulanmadı.

## Yerel kontrol

Üretici `scripts/quality/build_candidate_cover_readiness.py`. Okuma kaydı `outputs/reports/dataset/candidate_cover_readiness_v1/20261108T001455Z_723d1e85/readback.json`, SHA-256 `917dcb087c237a7290ecf5aa4e6f71723380bd9260d17b8cc794097755e728aa`. 74 girdi/dosya özeti, iki üretilen artefakt, 71 kimlik, 13 araştırmacı notu, tablo bağlantıları, tarih sırası ve açık olay SCL paydaları yeniden kontrol edildi. 64 ilgili test geçti.
