# OGM il ve yıl kapsamı denetimi — 8 Kasım 2026

OGM'nin 2018–2023 yıllık il tabloları, ileride kullanılabilecek
bir olay listesinin idari kapsamını denetlemek için incelendi.
Altı il tablosundan İBBS 3. düzey kodlarıyla Antalya (TR611),
Muğla (TR323), İzmir (TR310) ve Mersin (TR622) seçildi.
2023 istatistik yayınının 2004–2023 bölge müdürlüğü tablosundan
aynı altı yıl ve aynı adlı dört müdürlük ayrı okundu.
[OGM ormancılık istatistikleri](https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/Pages/Ormancilik-istatistikleri.aspx) ·
[Yedi özgün dosya bağlantısı ve SHA-256 değerleri](../configs/ogm_province_year_sources_v1.json).

## İl sınırına göre yayımlanan orman yangını sayısı

| Yıl | Antalya | Muğla | İzmir | Mersin | Dört il toplamı |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2018 | 244 | 299 | 167 | 71 | 781 |
| 2019 | 199 | 264 | 146 | 90 | 699 |
| 2020 | 260 | 260 | 167 | 87 | 774 |
| 2021 | 294 | 296 | 148 | 89 | 827 |
| 2022 | 189 | 234 | 169 | 99 | 691 |
| 2023 | 171 | 261 | 163 | 82 | 677 |
| **Toplam** | **1.357** | **1.614** | **960** | **518** | **4.449** |

24 il-yıl satırının 15'inde aynı adlı bölge müdürlüğü sayısı
il sayısından farklı. Örneğin 2023'te İzmir ili 163, İzmir
Orman Bölge Müdürlüğü 314 yangın bildiriyor. Mersin'de iki
sayı da 82. Sayıların eşit olması olay listelerinin
örtüştüğünü göstermez. Aynı il için farklı yayınlar da
uzlaştırılmalı. Merkez il tablosunda 2023 Muğla sayısı 261,
Muğla OBM'nin raporundaki Muğla ili sayısı 264. Üç kaydın
farkına ilişkin olay listesi veya kapsam açıklaması görülmedi.
[2023 il tablosu](https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/Ormancilikistatistikleri/2.12%20%C4%B0llere%20g%C3%B6re%20orman%20yang%C4%B1nlar%C4%B1n%C4%B1n%20da%C4%9F%C4%B1l%C4%B1m%C4%B1%2C2023.xlsx) ·
[Bölge müdürlükleri tablosu](https://www.ogm.gov.tr/tr/e-kutuphane-sitesi/Ormancilikistatistikleri/2.11%20Orman%20yang%C4%B1nlar%C4%B1n%C4%B1n%20b%C3%B6lge%20m%C3%BCd%C3%BCrl%C3%BCklerine%20say%C4%B1sal%20da%C4%9F%C4%B1l%C4%B1m%C4%B1%2C2004-2023.xlsx) ·
[Muğla OBM raporunun kapsam denetimi](PUBLIC_FIRE_SOURCE_COVERAGE_2026-11-08.md).

Her yıl 81 il satırı ve ayrı bir Türkiye toplamı bulundu.
Altı yılda da sayısal il satırlarının toplamı, yayımlanan
Türkiye satırı ve bölge müdürlüğü tablosundaki Türkiye sayısıyla
eşleşti. Sekiz il-yıl satırındaki tire, hem sayı hem alan
için kaynak işareti olarak korundu ve sayısal toplama katılmadı.
İl alanları toplamı ile yayımlanan ulusal alan arasında
2018'de +0,400 ha, 2022'de −0,076 ha fark var. Diğer dört
yıl dört ondalık basamakta eşleşti. Farkların nedeni
doğrulanmadı. 2021 dosyasının ilk İngilizce başlığında
2020 yazıyor. İki Türkçe başlık, devam tablosunun İngilizce
başlığı ve D2 hücresi 2021'i gösteriyor. Kaynak dosya korundu.

## Araştırmada kullanım sınırı

Bir olay listesi erişilebilir olduğunda il sınırı, kayıt yılı,
olay türü ve yayın kapsamı eşleştirilir. Tekilleştirilmiş olay
sayıları il-yıl tablosuyla karşılaştırılır. Farklar, örtü veya
gözlem filtrelerinden önce ve sonra ayrı raporlanır. Örneğin
2023 İzmir ilini kapsadığı bildirilen bir OGM listesi için ilk
başvuru noktası 163 kayıttır. Ortak sayım tanımı ve yayın sürümü
kontrol edilir. Toplam eşleşse bile olayların kimliği,
tutuşma konumu ve saati ayrıca doğrulanır.

Bu tablolarda olay düzeyi tarih, saat, konum ve kimlik alanı
bulunmuyor. Coşkuner'in 2015–2019 uydu karşılaştırmasında
kullanılan koordinatlı ve saatli OGM kayıtları makalede
açık erişimli olarak sunulmuyor. Bu denetim yeni bir bağımsız
olay satırı sağlamadı. Yıllık idari toplamdan orman/çalılık
hücre-günü prevalansı veya PU sınıf oranı hesaplanmadı.
Günlük gözlem yeterliliği `unknown` ve etiket izinleri kapalı.
2024 ve 2025 bu denetime alınmadı.
[Coşkuner, 2022](https://iforest.sisef.org/contents/?id=ifor3754-015) ·
[Olay kaydı erişim denetimi](JULY_REFERENCE_ACCESS_2026-11-08.md).

## Yeniden üretim

Kaynak listesinde verilen yedi XLSX, anahtar adlarıyla
`outputs/reports/dataset/ogm_province_year_v1/sources/` altında
tutulur. `python scripts/quality/audit_ogm_province_year.py`
dosya boyutu ve SHA-256 değerlerini doğrular, tabloları yerelde
okur ve yeni bir çalışma dizininde sonuç üretir. Ayrı GDAL XLSX
okuyucusuyla 24 il-yıl kaydı, bölge karşılıkları, altı Türkiye
toplamı, alan farkları ve tire işaretleri tekrar doğrulandı.
85 ilgili test geçti.

Yerel sonuç
`outputs/reports/dataset/ogm_province_year_v1/20261108T125959Z_992396ed/summary.json`.
SHA-256 `e8ad9a0d4c0a3b70ccc135295d96bcbce2021bc5be06ff3db62ddb61d6391ac0`.
