# Açık yangın vakalarının il, yıl ve mevsim dağılımı — 8 Kasım 2026

Daha önce yerel incelemeye alınmış 20 vaka kaydı ve üç yeni
kamuya açık vaka, 2018–2023 OGM il tablosuyla karşılaştırıldı.
Önceki 20 satır, 11 kayıtlık alım denetiminden, üç Milas/Anamur
vakasından, dört İzmir Temmuz vakasından ve iki Urla/Aydıncık
vakasından geliyor. Aynı Menderes veya Anamur vakasının optik,
uydu ve müdahale raporları ek vaka olarak sayılmadı.
[İlk 11 kayıt](PUBLIC_START_EVIDENCE_INTAKE_2026-11-08.md) ·
[Milas ve Anamur](JULY_2023_START_CONTEXT_2026-11-08.md) ·
[İzmir Temmuz](IZMIR_JULY_EVENT_CONTEXT_2026-11-08.md) ·
[Urla ve Aydıncık](PUBLIC_EVENT_CONTEXT_2026-11-08.md).

## Üç yeni vaka

| Vaka | Kaynakta verilen saat | Konum dayanağı ve sınırı |
| --- | --- | --- |
| Antalya, 22 Temmuz 2018 | MGM yaklaşık 12.50 | Antalya Orman İşletme Şefliği. Aynı gün AA, Aksu'da Kurşunlu ve Yurtpınar çevresindeki müdahaleyi bildiriyor. Ortak sicil numarası ve başlangıç noktası bulunamadı. |
| Buca, 13 Temmuz 2018 | MGM yaklaşık 15.10. AA yaklaşık 15.00. | AA, Buca Gölet tesisleri yakınındaki otluk alandan ormana yayıldığını bildiriyor. Gölet adı başlangıç koordinatı sağlamıyor. |
| Menderes–Çile, 2 Ağustos 2020 | Bakanın saha açıklamasında 13.24 | Bakanlık, İHA'nın ekiplere konum ilettiğini bildiriyor. İncelenen açık metinlerde koordinat değeri ve özgün İHA zaman kaydı görülmedi. |

MGM raporu 2018 Temmuz yangın verilerini OGM'den aldığını
belirtiyor. Haritalar ve çalışma alanları tek bir başlangıç
hücresi seçmek için kullanılmadı. Buca'daki iki yaklaşık
saatin farkı 10 dakika. Bu fark güvenilir bir zaman aralığı
oluşturmuyor. Çile için Bakanlık duyurusu 4 Ağustos tarihli.
2 Ağustos olay günü ve 13.24 saati, Bakanın ertesi günkü
saha açıklamasını aktaran DHA kaydıyla ayrıldı. Yayımlanmış
saatler kaynakta bildirildiği biçimde saklandı. UTC hedefi
ve ilk tutuşan örtü bu kayıtlardan atanmadı.
[MGM vaka çalışması](https://www.mgm.gov.tr/FILES/genel/kitaplar/antalya-izmir.pdf) ·
[AA Antalya](https://www.aa.com.tr/tr/turkiye/antalyadaki-orman-yangini-kismen-kontrol-altina-alindi/1210712) ·
[AA Buca, yayımlanan kopya](https://www.yenisafak.com/gundem/izmirde-orman-yangini-3383826) ·
[Bakanlık İHA duyurusu](https://www.tarimorman.gov.tr/Haber/4674/Mendereste-Yanginin-Ciktigi-An-Ihalarca-Goruntulendi) ·
[DHA saha açıklaması](https://www.dha.com.tr/gundem/bakan-pakdemirli-menderes-yangini-yuzde-90-insan-hatasi-kaynakli-1784542).

## İl ve yıl karşılaştırması

Her hücrede önce seçilen inceleme kaydı, ardından OGM'nin
yayımladığı il toplamı verilmiştir. Yan yana yazılan sayılar
bir eşleşme veya algılama oranı oluşturmaz.
[OGM il toplamları ve coğrafi kapsam](OGM_PROVINCE_YEAR_2026-11-08.md).

| Yıl | Antalya | Muğla | İzmir | Mersin |
| --- | ---: | ---: | ---: | ---: |
| 2018 | 1 / 244 | 0 / 299 | 1 / 167 | 0 / 71 |
| 2019 | 0 / 199 | 0 / 264 | 1 / 146 | 0 / 90 |
| 2020 | 0 / 260 | 0 / 260 | 1 / 167 | 0 / 87 |
| 2021 | 7 / 294 | 0 / 296 | 1 / 148 | 1 / 89 |
| 2022 | 1 / 189 | 1 / 234 | 0 / 169 | 1 / 99 |
| 2023 | 0 / 171 | 2 / 261 | 4 / 163 | 1 / 82 |

En az bir inceleme kaydı bulunan il-yıl sayısı 10'dan 13'e
çıktı. Kalan 11 il-yılda OGM yangın kaydı yayımlamış olsa da
bu inceleme listesinde vaka yok. Muğla 2018 ve 2021 buna örnek
olup il toplamları sırasıyla 299 ve 296. Seçilen 23 kaydın
21'i Temmuz veya Ağustos'ta. Bu yoğunlaşma, inceleme listesinin
seçim biçimini gösteriyor. Tüm yangınların mevsimsel dağılımı
veya PU örneğinin seçilme olasılığı bu listeden hesaplanamaz.

Çile vakasında özgün İHA kaydı erişilebilir olursa ölçümün
zaman standardı, koordinatın neyi gösterdiği ve konum
belirsizliği önce denetlenebilir. Buca'da kaynakların
bildirdiği ilk örtü ile sonradan yanan orman ayrı ele
alınmalı. Az temsil edilen dönemlerde yeni bir kaynak
bulunursa olay kapsamı ve küçük yangınları hangi kuralla
içerdiği de kayda alınır. Bu listede eşleştirme incelemesine
hazır kayıt sayısı sıfır. Günlük gözlem `unknown`, etiket
izinleri kapalı. 2024 ve 2025 bu denetime dahil edilmedi.

## Yeniden üretim

`python scripts/quality/audit_public_case_distribution.py`
beş yerel girdinin SHA-256 değerini doğrular. 23 inceleme
satırı ve 24 il-yıl sayımı ikinci yöntemle kontrol edildi.
85 ilgili test geçti. Yerel sonuç
`outputs/reports/dataset/public_case_distribution_v1/20261108T130911Z_460265b4/readback.json`.
SHA-256 `13e3a6d3def4836ce32907e46ca1ba0723c5b75f41992b9558934dc27527a20d`.
