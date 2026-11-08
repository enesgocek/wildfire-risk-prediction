# Mersin açık olay arşivinin ilk denetimi — 8 Kasım 2026

Yüksek ve çalışma arkadaşlarının yayımladığı Zenodo paketi,
Mersin Orman Bölge Müdürlüğünden gelen anonim olay verilerini
içeriyor. Yayın ve paketin lisans dosyası, Müdürlüğün anonim
kayıt ve koordinatların kamuya açılmasına izin verdiğini belirtiyor.
Veri lisansı CC BY 4.0. Kaynak atfı, veri sağlayıcısı olarak
Mersin Orman Bölge Müdürlüğünü, derleyenler olarak makalenin
yazarlarını kapsar. Yayımlanan paket 2.774.804 bayt ve Zenodo
MD5 özetiyle eşleşti. İnceleme yalnız 2018–2023 satırlarını
kullandı. Yayımlanan model çıktıları ve 2024–2025 olayları
analize alınmadı.
[Yüksek vd. ve erişim beyanı](https://doi.org/10.1177/00368504261495731) ·
[Zenodo arşivi](https://doi.org/10.5281/zenodo.21455927) ·
[Veri lisansı](https://creativecommons.org/licenses/by/4.0/).

## Kayıt kapsamı ve iki tablo arasındaki bağlantı

| Yıl | Açık coğrafya tablosu | OGM Mersin il toplamı |
| --- | ---: | ---: |
| 2018 | 71 | 71 |
| 2019 | 90 | 90 |
| 2020 | 84 | 87 |
| 2021 | 88 | 89 |
| 2022 | 91 | 99 |
| 2023 | 82 | 82 |
| Toplam | 506 | 518 |

Bu karşılaştırma yayımlanan satır toplamlarıdır. On iki satırlık
farkın kaynağı açık. Toplamların eşleştiği yıllarda da olayların
tek tek aynı olduğunu gösterecek ortak OGM sicili yok.
[OGM il ve yıl kapsamı](OGM_PROVINCE_YEAR_2026-11-08.md).

Coğrafya dosyasında 506, saat dosyasında 505 eğitim dönemi satırı
bulundu. Anonim `event_id` her dosyada kendi içinde tekil. İki
dosyada ortak görünen 503 kimliğin yalnız birinde tarih, ilçe ve
alan birlikte uyuştu. Dosyalar bu kimlikle birleştirilmedi.
Tarih, ilçe ve yanan alan üçlüsü, iki tarafta da yalnız bir kez
görüldüğünde, 500 olası bağlantı sağladı. Aynı üçlüyü tekrarlayan
beş coğrafya satırı ve saat tablosunda karşılığı olmayan bir
satır ayrı kaldı. Bu bağlantı ön inceleme içindir. Kaynağın
ortak ve belgelenmiş olay kimliği yok.

## Başlangıç konumu, örtü ve saat

- Yayımlayanların konum elemesinden 504 satır geçti. Projenin
  Mersin il sınırı içinde 485 nokta kaldı. Her merkez tek bir
  5 km hücreye düştü. Varsayımsal 250 m ve 1 km konum payları
  kullanıldığında sırasıyla 396 ve 188 noktanın çevresi tamamen
  tek hücrede kaldı. Kaynak gerçek ölçüm hata payını vermiyor.
- Aynı 485 merkezin CORINE 2018 pikselinde 341 orman/çalılık,
  130 tarım ve 14 başka örtü sınıfı görüldü. Bu tek nokta ve
  2018 haritası karşılaştırması, olay günündeki ilk örtünün
  kabulü için yeterli değil. Hücrenin model kapsamı ve
  noktanın yerel örtüsü ayrı incelenir.
- Tek merkez hücresi ve geçici saat bağlantısı birlikte bulunan
  479 satırın 458'inde, saat UTC veya Türkiye saati varsayıldığında
  aynı 24 saatlik UTC pencere elde edildi. 21 satırda pencere
  değişti. Arşiv sözlüğü ondalık başlangıç saati alanını tanımlıyor.
  Saat standardı ve kaydın nasıl oluşturulduğu açıklanmıyor.

## İki bilinen olayla karşılaştırma

**7 Eylül 2022, Gülnar.** Bakanlık 07.13 başlangıç ve 07.20 ilk
müdahale bildiriyor. Arşivde Gülnar ve Silifke satırlarının
ikisinde de 07.13 yazıyor. Noktalar yaklaşık 3,48 km aralıklı.
Saha raporu Gülnar'daki başlangıcı ve Silifke'ye yayılan etkiyi
anlatıyor. İki idari satır tek yangının farklı kayıtları olabilir.
Olay kimliği çözülemediği için bunlar iki yeni başlangıç olarak
sayılmadı. Bu vaka yerel saat yorumuyla uyumlu. Tek örnek tüm
arşivin saat standardını doğrulamıyor.
[Bakanlık açıklaması](https://www.tarimorman.gov.tr/Haber/5402/Soma-Ve-Gulnardaki-Orman-Yanginlari-Kontrol-Altinda) ·
[TMMOB saha raporu](https://www.tmmob.org.tr/icerik/tmmob-mersin-ikk-orman-yangini-raporu).

**11 Temmuz 2023, Anamur.** Aynı günün tek Anamur satırı,
yaklaşık 01.47 ve 0,436 hektar bildiriyor. OGM duyurusu
yaklaşık 01.30, 0,70 hektar orman ve 4,45 hektar meyve bahçesi
veriyor. Yayımlanan nokta önceki optik değişim ve uydu tanısıyla
aynı 5 km hücreye düşüyor. Saat ve alan farkı korundu. Saat
Türkiye saati olarak okunursa arşiv zamanı 10 Temmuz 22.47 UTC,
önceki uydu kaydı 22.33 UTC. Fark, arşiv saatinin fiziksel
tutuşma dakikası olarak doğrudan kullanılmasını desteklemiyor.
[OGM Anamur duyurusu](https://www.ogm.gov.tr/mersinobm/haber-sitesi/Sayfalar/anamur%E2%80%99da-orman-yangini0712-2774.aspx) ·
[Önceki hücre incelemesi](JULY_CASE_ADMISSION_2026-11-08.md).

## Uydu adaylarıyla sınırlı karşılaştırma

479 satır için, bildirilen merkez hücresinde ve varsayılan
hedef gününde bir FIRMS aday kaydı bulunup bulunmadığına
bakıldı. UTC saati okumasında 63, Türkiye saati okumasında 68,
iki okumada da 62 satırda aday var. Yanan alanı 1 hektardan az
377 satırın 20'sinde (%5,3), 1 hektar ve üzerindeki 102 satırın
42'sinde (%41,2) iki okumada da aday var. Sayım, olayın
kendisiyle uydu tespitinin eşleştiğini veya uydu tarafından
kaçırıldığını göstermez. Aynı gün ve hücredeki herhangi bir
aday yeterli sayıldı. Ölçüm uydu algılama oranı olarak
kullanılamaz.

## Birinci aşama için kalan iş

Bu açık kaynak Mersin'de bağımsız idari kayıtlarla çalışmayı
mümkün kıldı. Olayların tekilleştirilmesi, koordinatın özgün
başlangıcı temsil edip etmediği, saat dayanağı ve olay anındaki
örtü alt örneklerde ayrıca sınanacak. Kayıt kapsamı ve değerlendirme
dayanağı dört il için açık. Günlük gözlem `unknown`, etiket izinleri
kapalı ve ikinci aşama hedef protokolünün kabulünü bekliyor.

`python scripts/quality/audit_mersin_open_incidents.py` sabit
girdileri doğrular, iki CSV'yi yıl filtresiyle okur ve yalnız
denetim makbuzu üretir. Bağlantı, geometri, pencere, örtü ve
katalog sayımları ayrı Python hesabıyla yeniden üretildi.
58 ilgili test geçti.
Yerel makbuz `outputs/reports/dataset/public_start_geometry_v1/20261108T150016Z_5e98d034/readback.json`.
SHA-256 `2763c4a59dfe351296a33c1d2787288f7a51cc1d2bc5af5bf8a8c71df0a1ea7a`.
