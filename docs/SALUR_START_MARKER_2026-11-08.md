# Manavgat Salur–Yalamuklu başlangıç işaretinin konum denetimi — 8 Kasım 2026

28 Temmuz 2021 Manavgat yangını için bir ormancılık sunumunda doğrudan
başlangıç yeri olarak işaretlenmiş bir nokta bulundu. İşaret, iki ayrı
coğrafi görüntü üzerinde 5 km proje hücresine bağlandı. Uydu ısıl
tespitleri harita konumunu bulmakta kullanılmadı; sonradan kıyaslandı.

## Kaynak ve zaman

[Gürbüz'ün sunumu, s. 2](https://www.egeorman.org.tr/images/belgeler/yangininseyri.pdf#page=2)
Salur–Yalamuklu için 28 Temmuz 2021 saat 11.58'i bildiriyor ve
görüntü üzerinde bir başlangıç işareti gösteriyor. [Orman Mühendisleri
Odası saha raporu](https://www.ormuh.org.tr/files/2025/09/05/2_opbk_yangin_ulkemizin_akdeniz_ve_ege_bolgelerinde_20_temmuz_12_austos_2021_tarihleri_arasnda_meyda.pdf)
basılı s. 7–8'de aynı saat ve mevkii, ayrı ekip sevk saatleri ve 12.06
fotoğrafını veriyor. Görselde başlangıç yönü ve yangının ileride
oluşturduğu yeni alev noktaları ayrı işaretlenmiş. Saha raporu
basılı s. 14'te genç kızılçam ile maki örtüsü tarif ediyor. Bu kayıtlar
aynı idari bilgi ve bazı ortak görüntüleri kullanıyor olabilir.
11.58, bildirilen başlangıç olarak tutuldu. Türkiye saati yorumuyla
08.58 UTC, 28 Temmuz 00.00–29 Temmuz 00.00 UTC hedef penceresinde.

[Atalay vd., Tablo 1](https://doi.org/10.3390/ijgi14020065) ilk vakada
aynı saati OGM kaydından aktarır. [Antalya Valiliği](https://www.antalya.gov.tr/manavgatta-4-ayri-noktada-orman-yangini-cikti)
aynı gün Yeniköy için 12.05 verir. Mevki, saat tanımı ve özgün sicil numarası
uzlaştırılmadan bu iki bildirim zorla eşleştirilmedi. Farklı yer adları
ve saatler kaynaklarıyla korunur.

## Harita eşlemesi

Sunumun ikinci sayfası 125 dpi'da görüntülendi. İşaretin ucu ile altı
yol kavşağı veya yol kıvrımı ayrı okundu. İşaret ve su kıyısı uyum
hesabına alınmadı. Aynı yol referansları Esri World Imagery görünümü
ve 20 Temmuz 2021 tarihli, 10 m Sentinel-2B renkli görüntüde işaretlendi.
İki görüntünün ayrı dönüşümü UTM 36N'de çözüldü. Altı yol referansı
sırayla çıkarılarak hem o yolun konum farkı hem işaretin değişimi ölçüldü.
Esri görünümünün çekim tarihi bu incelemede doğrulanmadı; yol geometrisi
için kullanıldı. [Esri World Imagery](https://doc.arcgis.com/en/data-appliance/latest/imagery-elevation/world-imagery.htm) ·
[Sentinel sahne kimliği](https://planetarycomputer.microsoft.com/api/stac/v1/collections/sentinel-2-l2a/items/S2B_MSIL2A_20210720T083559_R064_T36SUF_20210720T201756).

| Görüntü | Yol çıkarıldığında en büyük yol farkı | En büyük işaret kayması | İşaretten hücre sınırına mesafe |
| --- | ---: | ---: | ---: |
| Esri World Imagery | 32,8 m | 10,9 m | 850 m |
| Sentinel-2B, 20 Temmuz | 57,2 m | 16,1 m | 862 m |

İki çözüm **16,2 m** arayla aynı hücreye (önceki geniş ölçekli haritada
bulunan hücreye) düştü. Önceki harita merkezinden fark **905–921 m**.
Her iki çözümde 50, 100, 250 ve 500 m daire tek hücrede kaldı; 1 km
daire iki hücreye dokundu. Sayılar yayımlanmış simgeyi yerleştirme
duyarlılığıdır. Sunum sahibinin işareti saha konumundan ne kadar
uzakta çizdiği, işaretin ölçüm yöntemi ve özgün olay kimliği bilinmiyor.
Bu daireler tutuşma konumu için güven aralığı olarak kullanılmadı.

## Aynı gün ısıl tespit karşılaştırması

Sabit 2021 FIRMS aday kataloğu, aynı UTC hedef penceresinde iki konum
çevresinde tarandı. Her iki çözüm için sonuç:

| İşaret çevresi | 08.58 UTC öncesi / sonrası aday satırı | Sonraki ilk aday | Bildirilen başlangıçtan fark |
| --- | ---: | --- | ---: |
| 500 m | 0 / 4 | 11.02 UTC | 124 dk |
| 1 km | 0 / 11 | 10.12 UTC | 74 dk |
| 2 km | 0 / 43 | 10.12 UTC | 74 dk |

Yarıçapı genişletmek ilk aday saatini değiştiriyor. Bu ölçüm yalnız
bu vakanın, bu kataloğun ve bu arama geometrisinin sonucudur. Tespitler
tek tek yangın kimliğiyle doğrulanmadı; katalogda daha erken kayıt
olmaması yeterli gözlem ya da yangın yokluğu göstermiyor.

Üç komşu nominal paket geri okundu; hedef UTC penceresine bütünüyle
giren **8 tarama satırı** bulundu. Aynı hücrede 00.31 UTC'deki iki
NOAA-20 satırında toplam **156 seçili kara merkezi ve sıfır nominal/yüksek
güvenli ısıl merkez** var. Sonraki yüklü tarama 10.12 UTC'de ve ilk
satırında **21 ısıl merkez** var. Arada yaklaşık **9 saat 40 dakika**
var; bildirilen 08.58 bu aralığa düşüyor. Bu sonuç yerel paketlerdeki
tarama kayıtları içindir. Tam gözlem, tutuşma saati ve nokta düzeyinde
algılanma olasılığı kanıtlanmadı. Hücredeki ısıl merkez sayıları, işaret
çevresindeki katalog satırı sayılarından ayrı tutuldu.

## Saha raporundan ek kalite kontrolleri

- **Marmaris–Armutalan:** 29 Temmuz'da 13.08 ihbar, 13.20 İHA görüntüsü,
  13.25.30 Palamut kule kamerası damgası. Basılı s. 17–19 ve 22'de
  ihbar, görüntü ve başlangıç örtüsü ayrı kanıtlar. İHA karesindeki
  telemetri kısmen kırpılmış ve bulanık; konumun anlamı açık olmadığı
  için başlangıç geometrisi alınmadı.
- **Güvercinlik:** Basılı s. 20'de 29 Temmuz 14.55 ihbarı, s. 21'de
  14.54 etiketli görüntü var. Görüntünün tarihi ve saat standardı
  bağımsız doğrulanmadan bir dakikalık sıra farkı veri hatası sayılmadı.
- **Fethiye–Hisarönü:** Basılı s. 21'de 31 Temmuz yaklaşık 00.40'da
  üç noktada yangın bildiriliyor. Yerel saat yorumuyla bu,
  **30 Temmuz 21.40 UTC**. Özgün nokta veya olay kimliği yayımlanmadığı
  için üç ayrı hücre etiketi türetilmedi. Aynı sayfada Marmaris
  yangınının Hisarönü'ne yayılması ayrı bir yer ve olay bağlamı.
- **Köyceğiz–Yeşilköy:** Rapor 15.45 bilgisini 29 Temmuz anlatısı içinde
  ve 31 Temmuz kayıtlarının ardından ikinci kez veriyor. İkinci yerde
  tarih açık yazılmamış. [Köyceğiz Belediyesi](https://www.koycegiz.bel.tr/tema/genel/uploads/faaliyet_raporlari/dosya/2021-Faaliyet-Raporu.pdf)
  ilçedeki yangın için 29 Temmuz'u bildiriyor; bu bilgi her iki anlatımı
  tek bir özgün sicile bağlamıyor. İkinci başlangıç eklenmedi.

Bu örnekler harita işareti, ilk gözlem, ihbar, sevk, yayılma ve
bildirilen başlangıcı ayrı tutmanın neden gerekli olduğunu gösteriyor.
Seçilen vakalar büyük yangın döneminden geldiği için dört ilde veya
küçük yangınlarda temsili değerlendirme dayanağı oluşturmuyor.

## Yeniden üretim ve sınır

`python scripts/quality/audit_salur_start_marker.py` 10 sabit girdinin
SHA-256 değerini, zaman penceresini, altı yol referanslı iki konum
çözümünü ve katalog taramasını denetler. Ham PDF'ler, görüntüler ve
koordinatlı makbuz yerel kaldı. Yerel makbuz:
`outputs/reports/dataset/public_start_geometry_v1/forestry_chamber_2021/salur_marker_v1/20261108T194701Z_a7895f19/readback.json`.
SHA-256 `fa15c440eb6a025aada777cab58544c23ba5083302ede626adb45a222da788d8`.
Komşu paket özeti ve tarama sırası aynı dizindedir. SHA-256 sırasıyla
`0d8a4058adc1c6555cba2818943545f8c827b4b7cedfe7f1010d0c47b13b71be` ve
`3709a9a067777aa7bea9a9031e9de95423cf15a66747b7b93149eb1df0d8ee2a`.
Tarama sırası mevcut `read_month_offline` ve `review_window` ile,
27–29 Temmuz paketlerinden yalnız işaret hücresi seçilerek çıkarıldı.
İlgili 94 test geçti.

Salur, kaynak haritası ve saat bilgisi olan güçlü bir inceleme
örneğidir. Özgün konumun belirsizliği ve dört ilde kayıt kapsamı
açık kaldı. Birinci aşama sürüyor; bu çalışma hedef etiketi
üretmedi. Günlük gözlem `unknown`, negatif etiket izni `false`.
2024 doğrulama veya 2025 final kayıtları incelenmedi.
