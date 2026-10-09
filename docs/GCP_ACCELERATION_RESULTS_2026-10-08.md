# Gerçek hızlandırma sonucu — 8 Ekim 2026

Yeni VM karşılaştırması bağımsız yerel kontrolden geçti. İndirme
sonrası VM'nin Stopped olduğunu teyit ettim. Dört profil aynı 32 vCPU ortamında
13–15 Ekim 2023'ün 28 çiftini ve üç tam günlük ürünü yeniden işledi.
Deney yeni üretim ayı eklemedi.

## Ölçülen hız

| Profil | Çift / günlük işçisi | Süre | Çift/saat | CPU ort. / tepe | Süreç RSS tepe |
| --- | ---: | ---: | ---: | ---: | ---: |
| Eski yöntem, ilk baz | 8 / 1 | 637,308 sn — 10:37 | 158,17 | %9,42 / %25,28 | 3,74 GiB |
| Yeni hat | 8 / 1 | 532,233 sn — 8:52 | 189,39 | %10,69 / %22,66 | 3,76 GiB |
| Yeni hat, geniş havuz | **24 / 4** | **436,957 sn — 7:17** | **230,69** | **%15,73 / %75,25** | **10,83 GiB** |
| Eski yöntem, tekrar baz | 8 / 1 | 643,416 sn — 10:43 | 156,66 | %9,29 / %25,10 | 4,17 GiB |

Baz tekrar oranı 1,00958: son baz ilk bazdan yaklaşık %0,96 uzun.
İki bazın ortalamasına karşı 24/4 throughput **%46,55 arttı**;
aynı işin duvar süresi **%31,76 kısaldı**, hız oranı **1,4655**.
Her iki bazdan da önceden belirlenen en az %15 hızlı olma koşulu sağlandı.
24/4, pipeline8'den yaklaşık %21,8 fazla throughput sağladı.
Bu sonuç **2–3 kat hız hedefinin gerçekleştiği anlamına gelmez**.

Önceki E2/8 vCPU deneyi aynı 28 çift için 644,200 saniyeydi;
yeni 24/4 oranı buna karşı 1,4743. Ayrı oturum/ağ koşulları olduğundan bu
tarihsel kıyas saf donanım etkisi kanıtı değildir. Yeni makinedeki eski
yöntem bazları da yaklaşık aynı süreyi verdi: yalnız VM'yi büyütmenin
büyük kazanç sağladığına ilişkin kanıt yok.

24/4 profilinde en az 111,21 GiB kullanılabilir RAM ve 18,82 GiB boş disk
ölçüldü; 4 GiB rezervler ihlal edilmedi. CPU yüzdeleri tüm 32 vCPU üzerinden.
RAM tepe sütunu yalnız örneklenmiş süreç ağacı RSS toplamıdır, tüm VM
belleği değildir. İki saniyelik örnekler kısa tepe değerlerini kaçırabilir.

## Süre hâlâ nerede harcanıyor?

24/4 profilinde çift yayın/doğrulama 264,114 saniye; günlük yayın dahil
314,623 saniye. Bu süre çocukların işlemesiyle örtüşür; child toplamına
eklenerek duvar süresi hesaplanamaz. SCI doğrulaması ve Drive çağrıları
birlikte ölçülmüştür; yalnız ağı suçlayacak ayrıştırılmış ölçüm yok.
Üç günlük birleştirme çocuk süresi toplamı 143,187 saniye; yeni hat bunları
farklı günlerin çiftleriyle örtüştürür. Ortalama CPU doluluğunun düşük kalması
bu seri yayın/doğrulama ve bekleme evreleriyle uyumludur.
Yeni bir donanım büyütmesiyle ek kazanç gösterilmiş değil.

## Bağımsız kontroller

Arşiv 7.883.736 bayt / 21 üye:
`dce040c41daa140ce83c93a24f21aebb280ab010b14af2f020b56cec97750609`.
Controller manifest:
`102c9e4ab16e4450d0d94eb3511dfdbf360fd6b6292809c5457efc93d2be5837`.

- Paket üye SHA/CRC, proof manifest/plan/metadata birebir.
- Dört profil tamam; 112 cold çift kaydı ve 12 günlük payload mevcut.
- Tamamlanma kayıtlarının scope/task/worker/payload hash ve boyutları geçti.
- CMR, ham kaynak SHA ve dört native CSV referansı bütün profillerde eşleşti.
- Günlük merkez/sayım/grid/alan/tarama zamanı ve source journal kontrolleri,
  profiller arasında tablo karşılaştırması geçti.
- Resource CSV'den istatistikler yeniden hesaplandı. Son bazın CSV'sinde
  profil summary snapshot'ından bir fazla örnek var; rapor son CSV'yi kullanır.
- Production progress unchanged True, resource guard False, yeni ay 0.
  Günlük gözlem unknown ve negatif etiket izni false.

Drive'dan yeniden canlı okuma bu yerel denetimde yapılmadı; VM sürücüsü
yayın sırasında taze uzak geri okumayı yapmıştı. Yerel tam ham indirme yok.
Orijinal bilimsel kod ve üretim kapsamı değişmedi.

## Uzun çalışma kararı ve bütçe senaryosu

Bağımsız kontrol **24 çift işçisi + en fazla 4 günlük işçisi** için hazır-kaydı
oluşturdu. Dosya `outputs/gcp_acceleration/readback/production_readiness.json`;
SHA `ac1f974daaf97a0a8392e9d6b225b4a7753147a9e527ec05caca4e6ea1cac3ef`.
Bu ölçümün üç günlük kapsamı bütün yıllar için hız garantisi değildir.

17.768 kalan çift, aynı 230,69 çift/saat oranında yaklaşık **77 aktif saat**
senaryosu verir. Başlangıç, eski kayıt restore, yeni metadata hazırlama ve
aylık kapanışlar bu senaryonun dışındadır; tarihe göre ham boyut/iş yükü ve
ağ değişir. Sekiz saatlik sınır bütün ayların bitiş süresi değildir.

Hesaplayıcıda aylık 1.462,65 USD gördüm. Bir VM/730 saat ve
taahhütsüz fiyat varsayımıyla kaba 2,004 USD/saat; sekiz saat yaklaşık
16,03 USD kredi. Disk/ağ ve gerçek açık VM süresi ayrıca değerlendirilir.
Test profilleri toplam 37 dakika 29,914 saniye; bu toplam VM'nin faturalandırılan
açık süresi değildir. Hız artışı maliyet/çiftin daha düşük olduğunu göstermiyor.
Kalan krediye bütün işin kesin sığacağı taahhüdü yok; gerçek üretim ilerlemesi
ve krediyle oturumlar sırasında yeniden hesaplanacak. Free Trial korunur.

Güncel üretim kaydı hâlâ üç tam ay (Temmuz/Ağustos/Eylül 2023), Ekim 1–14
ve 15 Ekim'in 10 pair kaydı. Kalan 69 tamamlanmamış ay / 17.768 ham çift.
[Sekiz saatlik devam rehberi](GCP_ACCELERATED_PRODUCTION_2026-10-08.md).
