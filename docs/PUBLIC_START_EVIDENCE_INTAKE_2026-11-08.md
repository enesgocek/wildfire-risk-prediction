# Açık yangın kayıtlarının alım denetimi — 8 Kasım 2026

Yerel uydu karşılaştırması yapılan 11 açık kaynak vaka kaydı, mevcut
[olay alım kuralları](REFERENCE_INTAKE_2026-10-15.md) üzerinden denetlendi.
Kaynaklar 2019, 2021 ve 2022'den seçili olayları anlatıyor. Manavgat'tan
gelen yedi kayıt aynı yangın dönemine ait. Bu grup, dört ilin olay
sıklığını veya uydu algılama oranını ölçen bir örneklem oluşturmaz.

| Kayıt grubu | Sayı | Başlangıç saati dayanağı | Konum dayanağı |
| --- | ---: | --- | --- |
| Antalya, Manavgat | 7 | OGM kayıt fişlerinden yayına aktarılan saat | Harita işareti |
| Antalya, Akseki/Kuyucak | 1 | Saha haberinde yaklaşık saat | Mahalle temsil noktası |
| İzmir, Tırazlı | 1 | Saha haberinde yaklaşık saat | Köy ve araştırma alanı |
| Muğla, Marmaris | 1 | OGM'nin bildirdiği yaklaşık saat | Koy kıyısındaki iki nokta |
| Mersin, Gülnar | 1 | Bakanlığın dakika düzeyinde verdiği saat | Mevki ve mahalle |

Kaynak saatleri yerel saat ve UTC olarak saklandı. Yaklaşık noktalar
alım tablosunun özgün koordinat alanına aktarılmadı. Alım kuralları
**11 kaydın tamamını kaynak incelemesinde bıraktı**. Hiçbirinde özgün
başlangıç koordinatı, ölçülebilir konum belirsizliği veya kaynak
zamanını sınırlayan doğrulanmış UTC aralığı bulunmadı. Değerlendirme
için olay kayıt kapsamı da belgelenmiş değil.
[Manavgat](MANAVGAT_REPORTED_STARTS_2026-11-08.md) ·
[Kuyucak](OPEN_REFERENCE_ANTALYA_2026-11-08.md) ·
[Tırazlı, Marmaris ve Gülnar](THREE_PROVINCE_START_CONTEXT_2026-11-08.md).

## Kaynak ayrımının sonucu değiştirdiği örnekler

- **Marmaris.** AA, 19.45 sıralarındaki bildirimi aktarırken OGM
  yaklaşık 20.02 başlangıç ve 20.10 ilk müdahale bildiriyor. TTB
  saha raporu üç başlangıç noktası bildirildiğini kaydediyor. Bu
  saatler tek bir tutuşma aralığına, bildirilen noktalar da üç ayrı
  olay kimliğine dönüştürülmedi. [AA](https://www.aa.com.tr/tr/gundem/marmaristeki-orman-yangininin-faili-polis-ve-jandarmanin-detayli-calismasi-sonucu-yakalandi/2621277) ·
  [OGM](https://www.ogm.gov.tr/tr/haberler/marmaris-orman-yangiyla-mucadelemiz-tum-hiziyla-devam-ediyor) ·
  [TTB saha raporu](https://ttb.org.tr/haber_goster.php?Guid=59a61f7c-fb7f-11ec-8f77-41ecdd8d2c36).
- **Gülnar.** TMMOB saha raporu, Karadere'de enerji hattı altındaki
  kuru otların ilk tutuşan yakıt olarak bildirildiğini ve yangının
  orman alanlarını etkilediğini kaydediyor. Kuru ot tanımı tek başına
  başlangıç noktasının arazi örtüsü sınıfını belirlemiyor.
  [TMMOB saha raporu](https://www.tmmob.org.tr/icerik/tmmob-mersin-ikk-orman-yangini-raporu).
- **Manavgat.** 3 ve 4 numaralı kayıtlar farklı saatlere sahip. Üç
  yarıçap ve dokuz küme ayarının 27 birleşiminde ikisi aynı tek
  uydu kümesine bağlandı. Uydu kümesinin bu iki kaydı ayrı fiziksel
  olaylara karşılık getirme yeteneği bu örnekte gösterilemedi.
  [Küme denetimi](MANAVGAT_CLUSTER_OVERLAP_2026-11-08.md).

## Kullanım ve devam koşulu

11 kayıt, yeni bir kaynağın önce hangi alanları tamamlaması gerektiğini
gösteren karşılaştırma tablosu olarak inceleme paketine eklendi. Başlangıç
noktası veya belgelenmiş konum belirsizliği, zaman alanının tanımı ve
kaynak olay kimliği bir vakanın eşleştirme incelemesine geçmesini
sağlayabilir. PU değerlendirmesi için kayıt kapsamı ve pozitif örneklerin
seçilme süreci ayrıca açıklanmalı. Günlük gözlem `unknown`, hedef
alanı boş ve etiket izinleri kapalıdır.

Üretici `python scripts/quality/audit_public_start_evidence.py`.
Dört girdi makbuzu SHA-256 ile doğrulandı. 120 ilgili test geçti.
Yerel makbuz `outputs/reports/dataset/public_start_evidence_v1/20261108T025127Z_ce9218f2/readback.json`.
SHA-256 `26c5fb18cfb2f444004d6d06c2aed00e298dfb26b7359643cf6aeb756bd5f6f4`.
