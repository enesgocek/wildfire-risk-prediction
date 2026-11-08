# Eğitim dönemi örtü örneklemi — 8 Kasım 2026

Dört ilde 2018–2023 dönemindeki yeni uydu olay adaylarının yerel örtüsünü daha geniş bir örneklemde incelemek için 24 tespit seçildi. Seçim görüntü katalog sorgusundan önce dosyaya yazılıp özeti sabitlendi.

## Örneklem

- Dokuz mevcut gruplama tablosunun her birinde aynı noktada tek ilk tespit koşulunu sağlayan **4.873 farklı tespit** bulundu. Önceki 71 noktalık incelemeyle kesişen 15 tespit çıkarılınca örneklem çerçevesi **4.858 noktadan** oluştu. Birden çok eşzamanlı ilk nokta içeren adaylar bu küçük pilotun dışında kaldı ve asıl kayıtlarında korundu. Gruplamaya göre ilk görünme, yeni yangın veya bağımsız olay doğrulaması sağlamaz.
- Antalya, İzmir, Mersin ve Muğla'da, her il ve her yıl için bir yer ayrıldı. CORINE 2018 merkez kodu, haritalanmış orman/çalılık, tarım ve karışık/diğer olarak üç örnekleme tabakasına ayrıldı. Tarım/doğal mozaik kodu 243 karışık/diğer tabakasına alındı. Tabaka il ve yıl boyunca döndürüldü. Her tabakadan sekiz örnek geldi. Uygun küme içinden sabit bir dizge ile kimliğin SHA-256 sıralamasında ilk nokta alındı.
- İl, tespit merkezinin mevcut GAUL sınırına göre konumudur. CORINE 2018 eski harita bağlamı olarak kullanıldı. 2018 içindeki tespitler için harita referans dönemi tahmin zamanının sonrasına uzanabilir. Bu kullanım tarihsel model girdisi uygunluğu sağlamaz. Dengeli küçük örneklem, proje genelindeki örtü oranlarını tahmin etmek için kullanılmaz.

## Görüntü ve örtü sonucu

Tahmin kesiminden önceki 30 günlük aralıkta nokta başına bir Sentinel-2 sahnesi seçildi. Katalog sıralaması önce sahne bulut oranı %20 veya altında olanları, sonra kesime yakın olanları öne aldı. 250 m çevresinde yerel kalite ayrıca ölçüldü. İlk okumada 10 kesit geldi ve 14 genel okuma hatası kaydedildi. Sabit seçimin aynı 14 noktası ortak erişim oturumuyla yeniden okundu. Sonuç 24/24, ilk 10 dosya korundu. İlk hatanın kesin nedeni belirlenmedi.

| Merkezdeki eski harita tabakası | Ağaçlık/çalılık görünümü | Tarımsal/parsel görünümü | Yapılaşma görünümü | Karışık veya belirsiz |
|---|---:|---:|---:|---:|
| Orman/çalılık | 4 | 0 | 0 | 4 |
| Tarım | 0 | 5 | 0 | 3 |
| Karışık/diğer | 1 | 0 | 2 | 5 |
| Toplam | **5** | **5** | **2** | **12** |

Görüntülerdeki ön görünüm gruplarını asistan, tek tarihli doğal renk kesitlerinden atadı. Ağaçlık/çalılık görünümü, doğal örtü veya arazi kullanımı doğrulaması sayılmaz. Bir örnek için görsel grup, harita tabakasından bağımsız bir arazi gözlemi değildir. Görsel sayfalarında eski harita sınıfı yazılmadı. Asistan harita tabakalarını önceden gördü. Araştırmacı ve uzman görüşü alınmadı.

| Ön görünüm | Pilot kodları | Açıklama |
|---|---|---|
| Ağaçlık/çalılık | H03, H04, H12, H14, H22 | Düzensiz ve süreklilik gösteren yeşil örtü. Yer yer yol veya açık alan bulunuyor. |
| Tarımsal/parsel | H05, H10, H18, H20, H23 | Parsel sınırı veya düzenli tarımsal desen belirgin. H18'de bulut bazı parselleri kapatıyor. |
| Yapılaşma | H06, H11 | Çatı/tesis benzeri geometriler ve yol ağı birlikte görülüyor. |
| Karışık veya belirsiz | H01, H02, H07, H08, H09, H13, H15, H16, H17, H19, H21, H24 | Açık, yapay, parsel ve yeşil örtü karışımı veya sınırlı görüntü kalitesi. |

24 görüntünün 11'inde seçili yerel kalite işaretleri sıfırdı. H02, H08, H16 ve H19'da çevre içi işaretli SCL piksel merkezlerinin payı %50'yi aştı. H08'in çevresi tamamıyla bulutlu. Bu dört kayıt belirsiz grupta kaldı. Bu oranlar bir kalite kabul eşiği olarak kullanılmadı.

### Merkez ve çevrenin ayrılmasının etkisi

24 tespitte katalog boyutlarına dayalı 180 olası dikdörtgen yönelimi ile CORINE alan oranı ölçüldü. H01'in nominal çevresi eski haritada tüm yönelimlerde yaklaşık %100 orman/çalılık kodunda. 19 Eylül 2018 kesitinde yeşil örtünün yanında geniş açık zemin var. H03'ün merkezi tarım/doğal mozaik kodunda, nominal çevrenin yalnız %0,8–5,4'ü tanımlı orman/çalılık kodlarına giriyor. 7 Kasım 2020 görüntüsündeki düzensiz yeşil örtü ağaçlık bağlamı destekliyor. Mozaik sınıfının içindeki doğal pay bu hesapta ayrıca ölçülmedi. H15'te SCL yaklaşık %90 genel bitki örtüsü gösterse de eski harita merkezi meyvelik. Tek tarihli yeşil görünümden doğal orman ayrımı yapılamadı.

## İnceleme ve sonraki adım

[Antalya H01–H06](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/recovery_20261108T002332Z_0e2a5d07/sheet_H01.png) · [İzmir H07–H12](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/recovery_20261108T002332Z_0e2a5d07/sheet_H07.png) · [Mersin H13–H18](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/recovery_20261108T002332Z_0e2a5d07/sheet_H13.png) · [Muğla H19–H24](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/recovery_20261108T002332Z_0e2a5d07/sheet_H19.png).

Sıradaki sınırlı kontrol, kalite nedeniyle belirsiz dört noktada farklı olay öncesi tarih denemek ve H01/H03/H15'te örtü karışımının farklı tarihlerde görülüp görülmediğini ölçmektir. Bu üç görselde araştırmacı yorumu, sarı çevrede düzenli parseller ile düzensiz doğal örtünün ayırt edilmesine katkı sağlayabilir. Ön yorumlar hedef ve örtü kabul alanlarına taşınmadı. Günlük gözlem durumu `unknown`, pozitif ve negatif etiket izinleri `false`.

## Doğrulama kaydı

Yerel dizin `outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547`.

- Seçim `plan.json`, SHA-256 `706a7c2ad0676f4bdb24df970e23880e81f7c94f082bde2d799a4a32ab0e55aa`.
- Görüntüler `recovery_20261108T002332Z_0e2a5d07/readback.json`, SHA-256 `76492ab0bcc075cc1184de0cc75373510d519f635d23017ffebeead91ba083ec`.
- CORINE alanları `corine_support_readback.json`, SHA-256 `7356d487df660fd577f2ae9a2b92a9c1fcd48a4f0f77f449406d062df9e4bcbc`. Alan hesabı `compare_candidate_center_footprint.py` içindeki mevcut kesişim işleviyle çalıştırıldı.

Seçilen 24 kimlik, dokuz senaryodaki tek ilk tespit üyeliği, 48 kesit dosyasının özeti, dört görsel sayfası, 30 günlük zaman pencereleri, SCL paydaları ve CORINE aralıkları denetlendi. İlgili 64 test geçti.
