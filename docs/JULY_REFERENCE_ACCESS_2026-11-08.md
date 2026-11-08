# Temmuz vakalarında bağımsız kayıt erişimi ve tarih belirsizliği — 8 Kasım 2026

Menderes ve Anamur için olay başlangıcını yer ve saat bilgisiyle
destekleyebilecek açık kayıtlar tarandı. İdari envanterin dosya
erişimi ayrıca denetlendi. Mevcut iki vakanın yaklaşık saatleri,
yalnız tarih verilse UTC hedef penceresinin nasıl değişeceğini
göstermek için kullanıldı.
[Önceki vaka karşılaştırması](JULY_CASE_ADMISSION_2026-11-08.md).

## Envanterin açık erişim durumu

Ekberzade'nin OGM kayıtlarından türettiği envanter daha önce PU
incelemesine kaydedildi. 8 Kasım saat 15.43 Türkiye saati itibarıyla
Zenodo kayıt bilgisi ve DataCite DOI kaydı erişilebilirdi (HTTP 200).
Zenodo'nun herkese açık dosya listesi erişim reddi verdi (HTTP 403).
Kayıt revizyonu 3'te açık dosya sayısı sıfır, ambargo tarih alanı
**31 Mayıs 2027**. Bu alan yayımlanma günü taahhüdü sağlamıyor.
ESSD ön baskısı değerlendirme aşamasında. Bu denetimde olay satırı
alınmadı.
[Önceki PU incelemesi](PU_BATCH_REFERENCE_2026-11-08.md) ·
[Zenodo kayıt bilgisi](https://zenodo.org/records/21887740) ·
[DataCite DOI kaydı](https://api.datacite.org/dois/10.5281/zenodo.21887740) ·
[ESSD ön baskısı](https://essd.copernicus.org/preprints/essd-2026-701/).

Ön baskının sözlüğünde özgün idari konum, son konum ve konum
kökeni ayrı alanlar. Bağımsız eşleştirme incelemesinde öncelik
özgün ve değiştirilmemiş OGM koordinatlarına verilebilir. İlçe
içinde kalma kontrolü, özgün noktanın doğruluğunu veya belirsizlik
yarıçapını belirlemiyor. VIIRS ile taşınmış noktalar aynı uydu
tespitini bağımsız doğrulamak için kullanılamaz. Sınır toleransı,
kıyı düzeltmesi ve doldurulmuş konumlar ayrı tutulmalı. Sözlük
2019 ve 2020 için bildirilen saatin özgün arşivde eksik olduğunu
belirtiyor. Gelecekte dosya açılırsa önce 2018–2023 ve dört il
ayrılır, ardından alanların gerçek kapsamı ve kullanım koşulları
yerelde doğrulanır.
[Ön baskı, Ek A ve Veri Erişimi](https://essd.copernicus.org/preprints/essd-2026-701/essd-2026-701.pdf).

## Açık vaka kaynaklarının sınırı

- **Menderes.** AFAD'ın İzmir risk azaltma planı, AYDES'e atıfla
  10 Temmuz 2023 Oğlananası vakasında 270 ha etkilenen alan
  bildiriyor. EFFIS kaydının alanı 416 ha. Yayımlanan iki değer
  arasındaki 146 ha fark için ortak bir alan tanımı ve ölçüm
  yöntemi doğrulanmadı. AFAD anlatımında bu vakaya ait başlangıç
  koordinatı veya saat aralığı bulunmadı.
  [AFAD İzmir planı, s. 181](https://izmir.afad.gov.tr/kurumlar/izmir.afad/E-KUTUPHANE/Il-Planlari/IRAP_Izmir--2024.pdf) ·
  [Yerel EFFIS denetimi](MENDERES_PATCH_CONTEXT_2026-11-08.md).
- **Anamur.** Sivrikaya ve arkadaşları Anamur Orman İşletmesinde
  2015–2022 arasındaki 133 OGM başlangıç noktasını kullanmış.
  Yayımlanan harita ve toplu tablo 2023 Belensazak vakasını
  kapsamıyor. OGM'nin 2023 vaka duyurusu yaklaşık saat ve
  mevki veriyor. Ölçülebilir başlangıç konumu ve zaman
  belirsizliği açık kalıyor.
  [Anamur konum çalışması](https://dergipark.org.tr/tr/pub/ajfr/article/1456067) ·
  [Mersin OBM vaka kaydı](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx).

## Yalnız yerel tarih verilirse

Türkiye'de incelenen yerel günler UTC 21.00'de başlayıp ertesi
UTC günü 21.00'de sona eriyor. Projenin `(T,T+24 saat]` kuralıyla
yerel günün 3 saati önceki, 21 saati aynı takvim adlı UTC
penceresine düşüyor.

| Vaka | Kaynak yerel tarihi | Yalnız tarihle olası UTC hedef günleri | Mevcut yaklaşık saatin düştüğü UTC hedef günü |
| --- | --- | --- | --- |
| Menderes | 10 Temmuz 2023 | 9 ve 10 Temmuz | 10 Temmuz |
| Anamur | 11 Temmuz 2023 | 10 ve 11 Temmuz | 10 Temmuz |

2019–2020'nin **731 yerel takvim gününün tamamında** aynı iki
pencere ayrımı doğrulandı. Bu sayı olay satırlarına ait değil.
Anamur örneğinde 11 Temmuz tarihini otomatik olarak 11 Temmuz
UTC'ye atamak, bildirilen yaklaşık saatin düştüğü pencereyi
değiştirirdi. Tarih aralığı adayları daraltmak için saklanabilir.
Tek bir pencereyi seçmek için olay saatinin tanımı ve belirsizliği
ayrıca gerekir. Günlük gözlem durumu `unknown`, etiket izinleri
kapalı ve vaka hedefleri boş. Olay kaydı kapsama denetimi açık.

## Yeniden üretim

Üretici `python scripts/quality/audit_july_reference_access.py`.
Üç girdi özeti, açık erişim yanıtları, 731 takvim günü ve iki
vakanın saat dönüşümü geri okumayla doğrulandı. UTC dönüşümleri
ikinci bir yöntemle kontrol edildi. 103 ilgili test geçti.
Yerel makbuz
`outputs/reports/dataset/july_reference_access_v1/20261108T124523Z_0eae0348/readback.json`.
SHA-256 `7857dd6d12fd2794dbbf802825176db230218d0ee94a965c428c79ee8e6b4a61`.
