# Mersin olay kimliği ve İzmir İHA kaynağı denetimi — 8 Kasım 2026

Mersin arşivinde birbirine yakın satırların yeni başlangıç mı, aynı olayın
devamı mı olduğunu ayırmak için zaman ve mesafe taraması yapıldı. İzmir Çile
için olay yerini gösterebilecek açık İHA videosunun tarih bilgisi denetlendi.
İkisi de ana hedefin bağımsız kanıtını inceleme çalışmasıdır.

## Mersin arşivinde yakın kayıtlar

[Yayımlanan arşivin](https://zenodo.org/records/21455927) 2018–2023 dönemindeki
506 coğrafya satırının 485'i yayıncı konum kontrolünden geçti, Mersin il sınırı
içinde kaldı ve tek bir 5 km proje hücresine düştü. Bunların 479'unda tarih,
ilçe ve alanın iki tabloda da tekil eşleşmesiyle taşınabilen geçici saat vardı.
Kaynak saatin zaman dilimi doğrulanmadığı için yalnız kayıtlar arası göreli
farklar kullanıldı. Mesafe, arşivde yayımlanan noktalar arasında WGS84
elipsoidi üzerinde hesaplandı. Sınırlar dahildir. Bir çift en çok bir kez
sayılır; birbirine doğrudan veya dolaylı bağlı çiftler inceleme grubudur.

| Zaman farkı | Mesafe | Çift | Grup | Gruptaki satır | İlçeler arası çift |
|---:|---:|---:|---:|---:|---:|
| Aynı dakika | 5 km | 1 | 1 | 2 | 1 |
| 60 dk | 1 km | 3 | 2 | 5 | 1 |
| 60 dk | 5 km | 7 | 5 | 11 | 3 |
| 24 saat | 5 km | 20 | 16 | 34 | 3 |
| 24 saat | 10 km | 35 | 19 | 46 | 4 |

60 dakika ve 5 km karşılaştırmasındaki beş grup dört farklı güne dağılıyor:

| Tarih ve yer | Arşivde görülen | Açık kaynağın katkısı |
|---|---|---|
| 15 Ekim 2019, Anamur–Bozyazı | Biri 3 satır ve tek hücre, diğeri 2 satır ve iki hücre olan iki grup | Aynı gün yıldırım sonrası 13 ayrı noktada yangın başladığı bildiriliyor. Haber, bu beş satırın hangi başlangıçlara ait olduğunu göstermiyor. [DHA saha haberi](https://www.dha.com.tr/gundem/anamur-ve-bozyazida-13-noktada-orman-yangini-1729348) |
| 17 Mayıs 2020, Silifke | İki satır aynı yayımlanmış noktada, saat farkı 53 dk | Kargıcak yakınında yangın bildiriliyor; haberin iki satırla ilişkisi belirlenemedi. [Yerel olay haberi](https://www.mersinhaber.com/haber-mersin-silifke-mut-yolu-kargicak-koyu-cikisi-orman-yangini-meydana-geldi/394343) |
| 16 Ağustos 2022, Gülnar | İki hücreye düşen iki satır, 14 dk ve yaklaşık 4,13 km aralıklı | İki satırı ayıracak olay kaydı bu incelemede bulunmadı. |
| 7 Eylül 2022, Gülnar–Silifke | İki hücreye düşen iki satır, aynı dakika ve yaklaşık 3,48 km aralıklı | Saha raporu yangının Gülnar'da başlayıp Silifke'ye yayıldığını bildiriyor. Satırları bu olayla tek tek bağlayan özgün kimlik yayımlanmamış. [TMMOB saha raporu](https://www.tmmob.org.tr/icerik/tmmob-mersin-ikk-orman-yangini-raporu) |

İki vaka yakınlığın ne zaman yanıltacağını gösteriyor: farklı ilçelerdeki iki
kayıt bir yayılmayla ilişkili olabilir; aynı hücrede kısa aralıklarla kaydedilen
satırlar ise birden fazla tutuşmanın yaşandığı güne ait olabilir. Bu tarama olası
ilişkileri incelemeye öncelik verir. Mesafe, saat veya hücre tek başına
birleştirme kuralı olarak uygulanmadı. 27 satır bu ölçüme girmedi;
yakın eşiğin dışında kalan satırların benzersiz olay olduğu da varsayılmadı.

## İzmir Çile videosunda tarih karşılaştırması

[Tarım ve Orman Bakanlığı](https://www.tarimorman.gov.tr/Haber/4674/Mendereste-Yanginin-Ciktigi-An-Ihalarca-Goruntulendi)
Çile yangınına ilişkin 4 Ağustos 2020 duyurusunda İHA'nın ekiplere konum
ilettiğini bildiriyor. Olayın tarihi [AA'nın saha haberinde](https://www.aa.com.tr/tr/turkiye/menderes-yanginindan-geriye-kalanlar-yurekleri-yakti/1931227)
2 Ağustos. [Haber sitesinde yayımlanan video](https://www.dirilispostasi.com/video/ihalar-izmirdeki-yanginin-basladigi-anlari-goruntuledi-yangini-tespit-edip-koordinat-verdi-6164036)
yaklaşık 249 saniye. Örnek kareler ve videonun 3, 24, 70 ve 100. saniyesindeki
büyütülmüş yazılar incelendi. İHA bölümünde görülen tarih 27 Temmuz 2020.
Videonun saha görüntülerinde aynı tür zaman ve konum yazısı görülmedi.

Bu fark, incelenen kopyadan 2 Ağustos Çile olayına bir konum aktarmayı
engelliyor. Görüntüdeki saatin doğru ayarlanıp ayarlanmadığı, kopyanın
Bakanlıktaki özgün görüntüye karşılığı ve ekrandaki koordinatın hangi
geometriyi anlattığı doğrulanmadı. Bu nedenle özgün duyuru reddedilmedi;
video koordinatları olay tablosuna alınmadı. Yerel video SHA-256:
`25c345788724ef812b0c6f43677a637206b0e83fb0521fff4d4744875901ca48`.

## Yeniden üretim ve aşama sonucu

`python scripts/quality/audit_mersin_incident_proximity.py` arşiv, il sınırı
ve ızgara dosyalarının SHA-256 değerlerini doğrular. Bağımsız ikinci hesap
114.481 olası çifti toplu karşılaştırdı; beş senaryoda çift, grup, grup
büyüklüğü, satır ve ilçeler arası çift sayıları eşleşti. İlgili 58 test geçti.
Yerel sonuç: `outputs/reports/dataset/public_start_geometry_v1/mersin_incident_proximity_v1/20261108T192927Z_7d117512/readback.json`.
SHA-256 `10019753566f123dc1a2916fa49a357e95cc7988c52cc367d8b94071b09394aa`.

Birinci aşama açık. Bu inceleme Mersin'de olay kimliği belirsizliğini
ölçtü ve İzmir'de uyumsuz bir video kopyasının kullanımını engelledi.
Sonraki açık kaynak incelemesi, özgün olay kimliğini, başlangıç konumunu
ve kayıt kapsamını belgeleyen arşiv veya yayın eklerine odaklanır. Tekil
haberler bu kapsamın yerini tutmaz. Günlük gözlem `unknown`, negatif
etiket izni `false`. Satır silinmedi, etiket kabul edilmedi. 2024 ve 2025
kayıtları taramaya alınmadı.
