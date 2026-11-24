# Araştırma prototipi v3 — hücre konumu ve kanıt gezinmesi

24 Kasım 2026. Mevcut koşullu araştırma prototipinin yerel kullanım
güncellemesidir. Yeni yöntem, eğitim, tahmin veya risk kategorisi yoktur.
Sites becerisinin yerel depo akışı kullanıldı; kayıt, hosting, dış
kaynak veri yükleme ve yayın yapılmadı. Önceki prototip/paketler korunur.

## Kullanıcı için değişenler

**Açılış dosyası:**
`outputs/reports/dataset/historical_research_prototype_v3/20261124T173653Z_3a064f3e/inceleme.html`.

- **Hücrelerin konumu:** iki mevcut 2022 takviminin toplam 244 farklı
  hücresi kabul edilmiş grid dosyasındaki gerçek geometrilerine
  bağlandı. Hücre seçilince o hücrenin kayıtları filtrelenir.
  Harita tarih/il/kalite/kaynak filtrelerine uyar; hücre filtresi
  haritadaki diğer uygun hücreleri gizlemez.
- **Yaklaşma ve geri dönüş:** seçili hücreye yaklaşma, bütün çalışma
  alanını gösterme ve yalnız hücre filtresini kaldırma düğmeleri vardır.
  Hücreler tıklama ve klavyenin Enter/Space tuşlarıyla seçilebilir.
- **İncelenmiş 12 örneğe geçiş:** alt/orta/üst sıra örneği seçilince
  doğru takvim, hücre, ay ve kaynak günü açılır. Başka filtreye uymayan
  eski örnek seçimi temizlenir. Bunlar temsilî yangın örneklemi değildir.
- **Tamamlanan karşılaştırma:** 65/59/56 kaynak günü için mevcut
  ana modelin genel ve 1–3 gün aralıkları ekrandadır. Dokuz ayarın
  min–maks değeridir; yeni ölçüm veya risk yüzdesi değildir.
- **Kanıt bağlantıları:** veri kartı, model kartı ve kaynak-örtüşmesi
  sonuç/sınırlama belgesine aynı proje içinden ulaşılır. Bağlantılar
  mevcut proje klasör düzenini esas alır; dış sunucu veya veri indirme yoktur.

Harita, gri kayıtlı hücreler ve mavi seçili hücreyle **gezinme** sağlar.
Renkler risk veya yangın sınıfı değildir. Gösterilen alan 5 km hücrenin
tamamıdır; tutuşma konumu, yerel yangın pikseli veya yanmış alan sınırı
olarak yorumlanmaz. Konum geometrisi bulunmayan bir kayıt olursa liste
ve skoru korunur, konum eksikliği ayrıca açıklanır. Mevcut sürümde
244 hücrenin tamamı eşleşti; bu durum bütün hücrelerin bilimsel risk
yayımlama kapsamına kabulü değildir.

## Korunan bilimsel veri

`review_data.js` ile `research-core.js` v2'den byte kopyasıdır.
8.956 takvim üyeliği, 8.711 farklı hücre–gün, 27 özellik, dokuz ayar,
mevcut skorlar ve aynı hücre/ay sıra hesabı değişmedi. Dört-il başlangıç
sayımı 6.573 / 4.841 puanlanabilir / 225 kaynak-bağlamlı / 185 hücredir.
Ayrı Mersin 2.383 / 1.929 / 81 / 68 değerlerini korur. Takvimler ve
hücre listeleri örtüşebilir; sayılar bağımsız yangın sayısı değildir.

`target`/kabul edilmiş L boş, gözlem unknown ve negatif etiket izni
false kaldı. 2023–2025 bilimsel değerleri, yeni modeller/olasılık/
risk rengi ve nihai birleştirme açılmadı. Kaynak sırasının gerçek
yeni yangın hedefine aktarımı önceki sınırlamalarıyla açık kalır.

## Coğrafi işlem ve ayrı denetim

Kaynaklar `data/aoi/grid_5km.geojson`, `data/aoi/aoi.geojson` ve
mevcut coğrafi manifesttir; kaynak dosya hash'leri doğrulandı.
244 kayıtlı hücrenin tam geometrisi ve mevcut çalışma alanı çizildi.
WGS84 köşe noktaları, ekran için ters-y ve ortalama enleme göre
görünüm oranı düzenlenmiş afin dönüşümle yerleştirildi. Coğrafi
koordinatlar yeni modele/özelliğe eklenmedi; geometri sadeleştirilmedi.

Ayrı denetleyici üretici yardımcısını çağırmadan SVG köşelerini
kaynak koordinatlara geri dönüştürdü. **89.527 köşe**, hücre kimlikleri,
tam hücre sınırları ve yakınlaştırma sınırları eşleşti. Altı ondalıklı
ekran koordinatlarından geri dönüşün en büyük farkı
`4,659238328486026e-09` derecedir; bu ölçüm yangın konum doğruluğu veya
saha hata sınırı değildir. Örneklerin 12 anahtarı, ekrandaki 12 aralık
değeri ve üç yerel belge bağlantısı da mevcut kaynak/hash'lerle eşleşti.

## İşlev kontrolleri ve doğrulama sınırı

İki yeni geometri davranışı ile 28 mevcut hedef/birleştirme kapısı
testi bu devamda geçti: **30 Python testi**. Gerçek HTML/JS ve
denetlenmiş payload ile **14 çevrimdışı DOM testi** geçti: eski dokuz
sayım/filtre/ayrıntı testi ile yeni harita seçimi/klavye/yaklaşma,
12 örneğe geçiş, eksik geometri koruması ve bulgu/bağlantı kontrolleri.
jsdom 31.0.1 kullanıldı; paket veya bağımlılık eklenmedi.

Bu testler gerçek tarayıcıda CSS/görsel render doğrulaması değildir.
Önceki tarayıcı dosya erişimi sınırı farklı protokol veya yüzeyle
aşılmadı; önizleme sunucusu açılmadı. Bu sınırlama kullanıcıya rutin
teknik test görevi veya ilerleme kapısı olarak aktarılmadı.

## Sürümler ve makbuzlar

- Prototip: `historical_research_prototype_v3/20261124T173653Z_3a064f3e/`;
  makbuz SHA-256 `f6140ef72f09416f2a6fbc01e1fafa61d241b64e2b0cd63e95fc6604cf43f4a8`.
- Ayrı audit: `geographic_research_prototype_audit_v1/20261124T174542Z_20acbee4/`;
  makbuz SHA-256 `3b31d9886e2586cbf03a2e3185eabbe7d1009058755fd5421683e0e541f5c135`.
- Korunan bilimsel payload SHA-256:
  `b4276798851ad2a3a3a8dc1be2ae537bb3c033093eca6e44802f8ea7dbc8e12b`.
- Korunan hesap çekirdeği SHA-256:
  `4dba1caeb0bae2eb31b1f98e6e7b58c54a9473e4b362c8b5370f687668113533`.

## Projeye katkısı ve sonraki iş

Mevcut deneyler coğrafi bağlamı, iyi/zayıf örnekleri ve kaynak
kanıtlarını birlikte inceleyebilecek hale getirildi. Rutin teknik
kontroller asistan tarafından yapıldı; araştırmacıdan yeni test yanıtı
beklenmiyor. Sonraki çalışma bu araştırma sürümünü teslim/sunumda
anlaşılır biçimde kullanmak ve ana hedefin açık kanıt ihtiyacını
korumaktır. Bu arayüz güncellemesi bilimsel etiket kabulü değildir.
