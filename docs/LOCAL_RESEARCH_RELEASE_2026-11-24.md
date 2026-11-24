# Sabit skor desteği ve yerel araştırma teslimi

24 Kasım 2026. Yeni eğitim, tahmin çağrısı, veri indirme veya etiket
üretmeden tamamlanan inceleme ve paketleme. Araştırmacının mevcut
koşullu prototip yönü ve özerk teknik çalışma tercihi esas alındı.

## Tamamlanan üç iş

1. Mevcut 2022 skorları il/ay/öğrenmede görülmüş hücre bağlamlarında
   incelendi; çift, kaynak-gün, hücre–ay ve hücre ağırlıkları ayrıldı.
2. [Veri kartı](research/DATASET_CARD_2026-11-24.md) ve
   [model kartı](research/MODEL_CARD_2026-11-24.md) hazırlandı.
3. Ayrı veri parçaları, dokuz model, skorlar, arayüz, kanıt ve kod
   anlık görüntüsü tek yerel dizin/ZIP tesliminde toplandı; ayrı denetlendi.

Bu çalışma nihai etiketli birleştirme değildir. Kabul edilmiş parçalar
elle değiştirilmedi; özellikler/üyelikler/kaynak izleri ayrı dosyalardır.
`target`/L boş, gözlem durumu unknown, negatif etikete izin false kaldı.
2023–2025 bilimsel değerleri açılmadı. Git'e ham veri, model veya ZIP gitmez.

## Mevcut ölçümün neye dayandığı

Önceden sabit tam-alan meteoroloji kuralıyla öğrenmiş dokuz modelin
mevcut 2022 skorları kullanıldı. Her S-bağlamlı gün, aynı hücre/ayda
atamasız diğer uygun günlerle karşılaştırıldı: üstünlük 1, eşitlik 0,5.
Bu kaynak-bağlam sıra kredisidir; gerçek yangın AP'si veya olasılığı değildir.
Bağımlı çiftlerin sayısı bağımsız yangın sayısı olarak kullanılmaz.

Örneğin bir kaynak gününün 30, başka birinin 10 karşılaştırılabilir
günü varsa çift ortalaması ilkine üç kat ağırlık verir. Ek raporda
kaynak günleri ve hücreler ayrıca eşit ağırlıklandırıldı. Bu tanı,
önceki ana yardımcı ölçüyü değiştirmez veya daha yüksek çıkan özeti seçmez.

Ana tam-alan XGBoost için dokuz ayar boyunca:

| Kapsam | Dört-il aday takvimi | Ayrı Mersin kaynak takvimi |
|---|---:|---:|
| Karşılaştırma çifti | 4.702–5.287 | 1.921 |
| Ölçüye katkı veren kaynak günü | 165–186 | 65 |
| Ölçüye katkı veren hücre | 135–143 | 56 |
| Çift ağırlıklı kredi | 0,567280–0,601843 | 0,528110–0,566892 |
| Kaynak gününe eşit ağırlıklı kredi | 0,567930–0,603620 | 0,527666–0,567111 |
| Hücreye eşit ağırlıklı kredi | 0,565556–0,609538 | 0,527512–0,569478 |
| En yoğun hücrenin çift payı | %2,65–3,06 | %3,12 |
| Bir değerlendirme hücresi çıkarılınca kredi farkı | −0,005608 / +0,007794 | −0,013878 / +0,014029 |

Aralıklar dokuz senaryonun uçlarıdır; güven aralığı değildir. En yoğun
hücre azami yaklaşık %3,1 pay taşır; sonuç tek hücreden oluşmamaktadır.
Bu bulgu kaynak seçimi, gözlem/etiket belirsizliği veya bağımlılığı
ortadan kaldırmaz. Değerlendirmeden hücre çıkarma yeniden öğrenme,
mekânsal çapraz doğrulama veya anlamlılık testi değildir. İl kesişimleri
örtüşebilir; il sonuçları toplanarak yeni toplam üretilmez. Desteksiz
kesitte ölçü boş tutulur; sıfır başarı yazılmaz.

Ana model, eski geniş meteoroloji XGBoost ve dondurulmuş doğrusal
skor için 54 genel özet, 864 bağlam özeti, 6.456 kaynak-gün/model ve
5.262 tek-hücre çıkarma satırı vardır. Ayrı denetleyici, üreticinin
yardımcı hesap fonksiyonunu çağırmadan ham sabit skorları ilişkisel
öz-eşlemeyle çiftlere çevirdi. Tam sayılı üstünlük/eşitlikler ve
kesirli ortalamalar eşleşti; önceki 54 genel sonuç aynen geri üretildi.

## Yerel teslimi açmak

Teslim kökü:
`outputs/reports/dataset/local_research_release_v2/20261124T023339Z_6f277b31/`.

- İnceleme ekranı: `package/interface/inceleme.html`.
- Ana 44.082 satır: `package/data/features.csv`.
- Ayrı üyelik, kaynak ve alan sözlüğü: `package/data/`.
- İki 2022 takviminin özellik/kaynak kayıtları: `package/assessment/`.
- Dokuz model, fit dizilimi, mevcut skorlar ve çift anahtarları: `package/models/`.
- 270 önceki ölçü ve yeni destek tanıları: `package/results/`.
- Veri/model kartları, AI katkı kaydı ve README: paket kökü.
- Dosya envanteri: `package/manifest.json`; taşınabilir arşiv: `research_release.zip`.

Ekranın varsayılanı dört-il 2022 takvimidir: 6.573 kayıt / 4.841
puanlanabilir. Ayrı Mersin grubu 2.383 / 1.929'dur; dört-il grubunda
Mersin il filtresi 2.038 verir. Ekran tüm 44.082 satırın görüntüsü
değildir. Kullanıcıya yeni bir rutin ekran testi görevi verilmemiştir.
Geçmiş dokuz DOM etkileşim testi korunur; bu devamda gerçek tarayıcı
görsel render kontrolü yapıldığı iddia edilmez.

198 dosya, 195 kaynakla aynı byte kopyası, iki üretilmiş rehber/sözlük
ve manifest içerir. ZIP **20.207.221 bayt**. Dizin/manifest envanteri,
bütün SHA-256/boyutlar, ZIP üye adları/tekilliği/CRC/byte eşliği ayrı
denetlendi. Aynı denetim, 44.082 benzersiz anahtar/27 özellik/822 hücre,
41.358 tam özellik, boş Y/L, dokuz üyelik bayrağı ve modelin 15 alan/
100 ağaç/öğrenme yılları koşullarını kontrol etti. Yeni tahmin çağrısı yoktur.

V1 ilk paketleme çıktısı ve v2'nin erken kopyası tarihsel hazırlanmış
dosyalardır; güncel teslim yukarıdaki son v2 makbuzuna bağlıdır. V2'de
veri kartındaki AI katkı bağlantısı için dosya pakete alındı, ardından
24 Kasım katkı kaydının güncel kopyasıyla son sürüm üretildi. Önceki
arşivler elle düzeltilmedi. Paket tek komutla ham kaynaklardan yeniden
eğitim iddiası taşımaz: kod/ortam anlık görüntüsü ve kaynak hash'leri
vardır; tam tarihsel veri bağımlılıkları özgün depoda korunur. Yerel
teslim veri lisansları bakımından dış yayın izni olarak yorumlanmaz.

Standart Python ile yalnız bütünlük kontrolü:

```powershell
.\.venv\Scripts\python.exe scripts/quality/verify_local_research_release.py --release outputs/reports/dataset/local_research_release_v2/20261124T023339Z_6f277b31
```

Bu denetim yapılmıştır; kullanıcıdan tekrar çalıştırması beklenmez.
34 ilgili test geçti: üç yeni tanı davranışı, üç yeni bütünlük testi ve
28 mevcut hedef/nihai birleştirme kapısı testi. Dosya değişimi, eksik
dosya ve dış ZIP hash'i yenilense bile ek yol/üye ekleme reddedildi.

## Makbuzlar ve açık bilimsel aşama

| Makbuz | SHA-256 |
|---|---|
| `frozen_score_support_diagnostic_v1/20261124T022210Z_e025acc0/readback.json` | `b888b1a1ea01af8b59728395a940f4f7f87b22c46830752e350dd686e4f1efc9` |
| `frozen_score_support_audit_v1/20261124T022742Z_5a966751/readback.json` | `2aa0472d9ab3480b9426b0ddbfd2978f1e6d3b111aceb8128879d27f5b1393d2` |
| Son yerel v2 `readback.json` | `0e11f0ef7d24d74a139e812a3b6f8faf659f81a2319c3ff2f72a8955660990d2` |
| `local_research_release_audit_v1/20261124T023357Z_4c357a37/readback.json` | `7b730b6ea993a136d071901aaa720ec25c394e0ae3ce3480b5c2da4a352d25de` |

ZIP SHA-256 `f727398b3629d4ffc7005f04d43c05efef911f0efda00f50322f09e74c599713`;
manifest SHA-256 `dd892361824793db31db711263530782e33c01f01cf7c55d02fab7d1218f9dd3`.

Teknik deneysel teslim ve açıklama kartları hazırdır. Ana 24 saatlik
yangın araştırma sorusu korunur. Kaynak/aday sırasının gerçek yeni
yangına aktarımı, seçim/gürültü varsayımları ve yeterli gözlem/güvenilir
değerlendirme açık bilimsel konulardır. Bugünkü destek tanıları bunları
çözmüş sayılmaz. Sonraki bilimsel çalışma mevcut iki 2022 takvimindeki
aktarımı ve hata örneklerini bu açık sınırlara göre tartışmalıdır;
otomatik yeni eğitim, kapalı yıl erişimi veya risk rengi eklenmez.
Nihai etiketli birleştirme kapısı ayrıca korunur.
