# Gözlem protokolü için saat ve kalite kanıtı

Tarih: 15 Ekim 2026. Durum: tamamlanan sabit yöntem pilotunda ek çevrimdışı
tanı; etiket politikası seçilmedi. Aynı dört il, 12 eğitim günü ve 156 amaçlı
hücre-gün korunur. 2024/2025 açılmadı, yeni kaynak indirilmedi.

## İncelenen soru

[Tamamlanan pilotta](OBSERVATION_PILOT_RESULTS_2026-10-15.md) günlük
nominal kara birleşimi birçok örnekte büyük olsa da bu, gün boyunca
tekrarlı veya sürekli gözlem anlamına gelmiyordu. Yeni iş mevcut tarama
geometrilerini gerçek zamanlarıyla bağlayarak bu farkın kapsamını ölçer.
Eşik veya sınıflandırma sonuçları bütün döneme genellenmez.

## Yöntem ve sınırlar

`scripts/quality/review_pilot_observation_protocol.py`, önceki teknik
kapanışın rapor hash'ini, planın bağlı girdilerini ve 98 çiftin saklanmış
tarama CSV/GPKG dosyalarını doğrular. Nominal kara geometrisinin CSV alanı,
CRS ve tarama/hücre anahtarları geri okunur. Her birimde günlük birleşim
yeniden hesaplanarak önceki alanla 0,05 m² sayısal toleransta uzlaştırılır.
Bu tolerans gözlem veya etiket kabul eşiği değildir.

Gün `(T,T+24h]`, açıklayıcı dört **6 saatlik UTC dilimine** ayrılır:
00–06, 06–12, 12–18, 18–24. Bir taramanın bütün zaman zarfı dilimin
kesin içinde değilse o dilimin kesin alanına alınmaz; sınır ayrı tutulur.
Dilim geometrileri kendi içinde birleşir. Dört dilimin ortak kesişimi,
aynı yerde her dilimde nominal kara desteği bulunan yaklaşık alanı verir.
Bu dilimler önceden kabul edilmiş negatif etiket kuralı değildir; başlangıç
saatleri ve çözünürlük seçimi değişirse sonuç değişebilir.

Hücrenin **herhangi bir kısmında** pozitif nominal kara alanı bulunan
kesin pencere içi tarama zarfları arasındaki en uzun boşluk ayrıca ölçülür.
Günün iki kenarı da hesaba katılır. Farklı taramalardaki destek yerleri
farklı olabilir. Dolayısıyla bu ölçü her noktanın gerçek gözlemsiz kalma
süresi değildir; bütün hücreyi iyimser biçimde bir araya getiren bir zaman
tanısıdır. Tarama zarfı süresi de sürekli gözlem süresi değildir.

Farklı dosyalar aynı sensör/yörünge kimliğini taşıyorsa tek kimlikte toplanır;
747 birim/yörünge tanık satırı bağımsız olay veya istatistiksel bağımsız
geçiş sayısı olarak yorumlanmaz. Tanık tablosundaki ilk/son tarama aralığı
aralarında kesintisiz gözlem olduğu anlamına gelmez.

Nominal/yüksek güven sınıflarındaki **termal piksel merkezi** sayıları,
kesin pencere içi/sınır/yüklenmiş pencere dışı olarak ayrılır. Bunlar NASA
ürününün kendi iç denetimidir; bağımsız yangın doğrulaması değildir. Dışarıda
sayısı yalnız yeniden yüklenen 98 çiftteki kayıtlardır; zaman tanığıyla
önceden dışlanan 194 çiftin tüm tespitlerini kapsadığı iddia edilmez.

## Bu amaçlı pilotta ölçülen sonuçlar

- En uzun herhangi-bir-kısım nominal kara tarama boşluğu: medyan **11,50
  saat**, en küçük **10,63 saat**, en büyük **24 saat**; **44/156** birimde
  en az 12 saat. Bu değerlerden yangın kaçırma oranı hesaplanmadı.
- Aynı yerde dört dilimin her birinde pozitif nominal kara desteği bulunan
  alan **25/156** birimde pozitiftir; **131/156** birimde sıfırdır.
- Dilim bazında pozitif nominal kara alanı olan birim sayıları sırasıyla
  **133 / 145 / 25 / 139**'dur. Günlük birleşimden bu dağılım çıkarılamaz.
- Bu veride iç dilim sınırlarını aşan pozitif nominal kara alanı yoktur;
  sınır dışlama kodu bu gerçek sonuçla sınanmış sayılmaz, sentetik test vardır.
- Nominal seçim grubundaki **60 termal merkez bulunan** ve **96 bulunmayan**
  örneğin tamamı kesin hedef penceresi hesabıyla aynı grupta kaldı.
  Sınırda termal merkez bulunan birim yoktur. Bu tutarlılık gerçek
  yangın/yangın yokluğu veya olay başlangıç zamanı kabulü değildir.

### Aynı alan yüzdesi farklı protokollerde farklı örnekleri tutuyor

Yalnız **açıklayıcı %95 alan kesimi**, AOI ile kesilmiş aynı hücre paydasında:

| Tanı grubu | Günlük nominal kara ≥%95 | ≥12 saat ayrımlı tekrar ≥%95 | Dört UTC diliminin ortak alanı ≥%95 |
|---|---:|---:|---:|
| Seçilmiş termal merkez bulunmayan 96 birim | 72 | 49 | 9 |
| Termal merkez bulunan 60 birim | 59 | 51 | 5 |
| Toplam 156 birim | 131 | 100 | 14 |

0,50/0,80/0,90/0,95/0,99 kesimlerinin tamamı ayrı tabloda korunur;
hiçbiri seçilmiş etiket kuralı değildir. Daha katı dilim koşulunun çok az
örnek tutması onun daha doğru olduğunu göstermez. 60 termal merkezli
birim de gözlem şartlarının farklı tanı gruplarında nasıl seçilim yarattığını
göstermek için korunur; bunlara otomatik negatif atama yapılmaz.

## Araştırma önerisi ve karar noktası

**Öneri (henüz kabul edilmiş protokol değil):** günlük alan, tekrar desteği
ve zaman boşluklarını ayrı kanıt sütunları olarak korumak; güçlü destekli
arka plan adaylarının bağımsız olay kayıtlarıyla doğrulama tasarımını
hazırlamak. Bu teknik pilotta örnek sayısını artıran veya azaltan bir
kesimi doğruluk ölçütü gibi seçmek uygun değildir.

Olası protokol karşılaştırmasında şu üç konu birlikte değerlendirilmelidir:

1. Hangi gözlem koşullarıyla hangi adayların seçildiği ve kapsam dışında
   kaldığı; il/mevsim/örtü/termal tanı grubuna göre seçilim.
2. Bağımsız referansın kaynağı, zaman/konum belirsizliği ve uydu ürünüyle
   aynı bilgiye dayanıp dayanmadığı. Yalnız uydu eşleşmesi bağımsızlık değildir.
3. Kaçırılmış olay riskini değerlendirebilecek örnekleme tasarımı ve açık
   referans eksikleri. Bu amaçlı pilot popülasyon hata oranı vermez.

Bu araştırma hazırlığı kullanıcıdan yeni eşik onayı istemeden yapılabilir.
Negatif kabul koşulu veya öğrenme hedefi değişecekse gerekçeli seçenekler
kullanıcıya sunulur. Resmî uzman/araştırmacı incelemesi gerçekleşmiş gibi
kaydedilmez; şu an kabul edilmiş yeni etiket protokolü yoktur.

## Somut insan incelemesi ve teknik kapanış

Önceki beş örnek için `review_timelines.png` hazırdır. Turkuaz noktalar
tarama başına nominal kara alan payını, gri noktalar bulutu gösterir;
kırmızı üçgen termal merkez tanığıdır. Noktalar arasındaki süreler çizgiyle
doldurulmaz. Örneğin `C677_R879 / 2018-11-15`, büyük günlük alanına rağmen
öğleden sonra desteğinin eksik kalışını gösterir. Grafik araçla görsel
olarak kontrol edildi; insan etiket onayı değildir. Araştırmacıdan beklenen,
günlük alan ile zamana dağılım farkını ve ek referans ihtiyacını incelemektir;
yalnız bu grafikle gerçek yangın yokluğu kararı verilmez.

Güncel çıktı dizini:
`outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c/`.

- `unit_protocol_evidence.csv`: aynı 156 birim, kapalı etiket bayrakları.
- `six_hour_support.csv`: **624** birim/dilim kaydı; sınır tanıları ayrı.
- `orbit_witnesses.csv`: 747 birim/sensör-yörünge tanığı.
- `thermal_window_comparison.csv`: 60/96 tanı grubunun pencere karşılaştırması.
- `descriptive_protocol_comparison.csv`: kabul edilmemiş alan kesimleri.
- `review_timelines.png`: beş açıklayıcı zaman grafiği.
- `input_manifest.json`: kapanışta aynı kalan **562 girdi dosyası**.

Readback SHA-256:
`c87a96944635f650a9eb30005d959a56d998cd73154b3b48441a80e0e1a59df2`.
Kapanış SHA-256:
`ee2e47cba8c3641e8ff7d5ff30f8edab41d97a2f5611fc02feba7429f507ae15`.

İlk tanı dizini `20261015T143021Z_cefb27d6` korunur. Bu ilk rapordaki
"ham dosya yeniden açılmadı" muhasebe alanı, miras planın iki native
dosyasının yalnız hash için okunmasını ayırmıyordu. Güncel sürüm iki
hash okumasını, sıfır ham dizi okumasından ayrı kaydeder. Yeni sürümde
156 satırlık bilimsel CSV'nin hash'i aynı kaldı; eski rapor elle düzeltilmedi.

**11 yeni davranış vakası dahil 53 ilgili test**, Deprecation/Future
uyarıları hata sayılarak geçti. Üç yeni Python dosyasında lint/format geçti.
Günlük alanı tam/üç dilimi boş tanık, farklı yerlerdeki dört destek,
sınır aşan tarama, termal sınır ayrımı, boş destek ve kabul kapıları sınandı.
Yeni indirme/bulut işi, yeni etiket, model veya nihai birleştirme yapılmadı.
