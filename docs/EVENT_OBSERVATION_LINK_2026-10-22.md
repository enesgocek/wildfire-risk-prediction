# Olay adaylarının ayrıntılı gözlem pilotuyla kesişimi

22 Ekim 2026. Bu çalışma iki korunmuş kanıt tablosunun anahtar eşleştirmesidir;
etiketli veri setinin nihai birleştirmesi veya yeni gözlem politikası değildir.
İlk-gün adayı bulunmaması, termal tespit bulunmaması ve yangın yokluğu ayrı tutulur.

## Kapsam ve sonuç

[Tam aday duyarlılığı](EVENT_SENSITIVITY_2026-10-22.md) 2018–2023 için
7.610 ilk-hücre/tahmin-günü anahtarı içerir. Mevcut [gözlem yöntem pilotu](OBSERVATION_PROTOCOL_EVIDENCE_2026-10-15.md)
aynı dönemdeki seçilmiş 12 tarihte 156 hücre-gündür. Pilot amaçlıdır;
karşılaştırmanın örneklem büyüklüğü bütün 7.610 aday değildir.

| Pilot içindeki durum | Hücre-gün | Yorum |
|---|---:|---|
| Dokuz ayarda ilk zaman/üyelik eşit aday | 15 | Gözlem tanılarıyla bağlantı var; olay doğruluğu kabulü yok |
| İlk-gün adayı ayara veya zaman/üyelik seçimine duyarlı | 6 | İki varlık-eşit/zaman-üyelik duyarlı, dört varlık duyarlı |
| Hiçbir ayarda ilk-gün adayı yok, yüklü kesin pencere içinde termal merkez var | 39 | Devam, filtre veya başka nedenler araştırılmalı; neden henüz belirlenmedi |
| Hiçbir ayarda ilk-gün adayı yok, yüklü kesin pencere içinde termal merkez yok | 96 | Gerçek yangın yokluğu veya negatif kabulü değildir |
| Toplam | 156 | Dört ayrık grup bütün pilotu koruyor |

7.610 adaydan **21'i** bu ayrıntılı pilotla eşleşti, **7.589'u** bu pilotun
dışında kaldı. İkinci sayı ham uydu verisi bulunmadığı, günlük üretimin
başarısız olduğu veya adayın gözlenmediği anlamına gelmez. Yalnız bu
ölçekteki alan/zaman/QA pilot kanıtının ilgili anahtarda bulunmadığını belirtir.
Pilot dışındaki alan ve termal tanı alanları eksik bırakıldı; sıfır yazılmadı.

Tüm 156 birimde planlanmış gerekli geometri çiftleri işlenmiş görünüyor.
Bu, bütün günün veya bütün kaynakların kusursuz gözlendiği iddiası değildir;
günlük gözlem durumu yine `unknown`. Önceki 98 çiftin ham dizileri/geometrileri
bu eşleştirme sırasında yeniden açılmadı ve hesaplanmadı.

## Alan ve zaman desteği aynı karar değildir

Yalnız önceki çalışmalardaki **açıklayıcı %95 alan kesimi** yeniden sayıldı:

| İlk-gün aday grubu | Pilot paydası | Günlük nominal kara alanı ≥%95 | ≥12 saat ayrımlı tekrar alanı ≥%95 | Dört dilim ortak alanı ≥%95 |
|---|---:|---:|---:|---:|
| İlk zaman/üyelik eşit | 15 | 14 | 13 | 1 |
| Ayara duyarlı | 6 | 6 | 5 | 0 |
| Toplam eşleşen | 21 | 20 | 18 | 1 |

Bunlar yalnız seçim tanılarıdır; üç kabul alternatifi onaylanmış değildir.
En çok veya en az satır bırakan kesim doğru ilan edilmedi. Nominal kara,
bulut ve zaman ölçülerinin fiziksel sınırları önceki pilot belgesinde korunur.
Hiçbiri tek başına yangının kaçırılmadığını kanıtlamaz.

Somut örnek: **C677_R879 / 2018-11-15 (Mersin)** dokuz ayarda aynı ilk
zaman/üyelik adayına sahip. Günlük nominal kara alanı payı yaklaşık 1,
12 saat ayrımlı tekrar alanı payı 0 ve dört dilim ortak alanı payı 0.
Herhangi-bir-kısım nominal kara taramaları arasındaki en uzun zarf boşluğu
yaklaşık 12,35 saattir; her pikselin gözlemsiz süresi değildir. Bir kesin
termal merkez de bulunuyor. Bu örnek, ayar tutarlılığı ve günlük büyük alanın
sürekli gözlem anlamına gelmediğini gösterir; negatif aday değildir.
Araştırmacının bakabileceği mevcut görsel
`outputs/reports/dataset/observation_protocol_evidence_v1/20261015T143126Z_dc01eb0c/review_timelines.png`.
Beklenen inceleme, günlük alanla gün içi zaman dağılımını ayırt etmektir;
görselden yangın yokluğu veya etiket onayı istenmez. Önceki görsel bu işte yeniden üretilmedi.

## Uygulama, kontroller ve kayıt

`link_event_observation_pilot.py` kaynak rapor/artifact hash'lerini doğrular,
5 km hücre + UTC tahmin günü üzerinde bire bir sol eşleştirme yapar.
Bütün pilot satırları korunur; tamamlanmamış çift planı veya sınırda termal
zaman ayrı inceleme yollarıdır. Gelecek tarihler, tekrarlı anahtarlar,
etiketli/açılmış kabul alanları, yanlış sayımlar ve geçersiz alan payları reddedilir.
Kaynak tablolar değiştirilmez; kod hata durumunda eksikleri sıfıra çevirmez.

15 yeni davranış vakası dahil **43 ilgili test** geçti; bütün depo testleri
değildir. Üç yeni Python dosyasında lint/format geçti. Kaynak tablolarla
doğrudan küme-kesişim sayımı ikinci yöntem olarak uzlaştırıldı. Bütün çıktı
CSV değerleri, eksikler dahil, diskten geri okunarak bellekle karşılaştırıldı.
18 doğrudan girdi ve beş çıktı hash'i doğrulandı. Önceki pilotun 562 ham/ara
girdisinin tamamı yeniden denetlenmiş sayılmaz; önceki kabul sınırı korunur.

Sonuç `outputs/reports/dataset/event_observation_link_v1/20261022T205236Z_797195a6/`.
Readback SHA-256 `9b4be7d301436840819d3a9d90ece3a5ede5f6bd257c364ef7d5cc9cc08cf6bf`.
Başlıca çıktılar `pilot_evidence_links.csv`, `candidates_outside_detailed_pilot.csv`,
`category_thermal_counts.csv` ve `illustrative_observation_screens.csv`.

## Sonraki iş ve sınır

21 eşleşen örnekte ayar duyarlılığı ile gözlem bilgisi birlikte görülebiliyor;
bu çekirdek olay/örtü ve açık referans incelemesine somut girdi sağlar.
Öncelik bu sınırlı örneklerde adayın orman/çalılık bağlamı, devam eden olay
olasılığı ve bulunabilen referansın gerçekte neyi doğrulayabildiğidir.
7.589 aday için ayrıntılı gözlem hesabına topluca geçmeden önce gözlem
protokolü ve dar kapsamlı genişletmenin gerekçesi kararlaştırılmalı.
135 eşleşmeyen pilot birimi de korunur; otomatik negatif oluşturulmaz.

Bağımsız olay verisi gelmedi; yeni referans doğrulaması yapılmış sayılmaz.
`daily_observation_status=unknown`, pozitif/negatif izinleri false, hedefler
boş kaldı. Eğitim, model skoru, nihai onay/etiketli birleştirme, 2024/2025
erişimi, dış ileti veya bulut işi yok. OGM başvurusu zorunlu tutulmadı.
