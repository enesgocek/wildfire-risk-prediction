# 8 Ekim 2026 — Gerçek VM paralellik ölçümü

**Mevcut VM'de 8 işçi, sonraki üretim sürücüsü için ölçülen adaydır.**
12 işçi daha fazla CPU/RAM kullanmasına rağmen 8 işçiden %4,18 yavaş kaldı.
Üretim sürücüsü henüz değiştirilmedi; yeni 8 saatlik oturum başlatılmadı.
Arşivi indirdikten sonra VM'nin Stopped olduğunu teyit ettim.

## Bağımsız ürün kontrolü

Arşiv `outputs/gcp_tuning/received/gcp_tuning_results.zip`: 7.894.454 bayt,
21 üye; SHA256 `8c0ff39f053196d2bfcd108b3544b13224cec73b4d6e7f0e8dfabd48c8c23ab7`.
Test scope'u `dacb09d6cc2833b9853fbe3cba617e98e84a4ac2138459130eb7cbd1c27ad077`.
Paket SHA ve gömülü plan/metadata hazırlanmış yerel paketle birebir.

`verify_gcp_tuning_results.py` gerçek arşiv üzerinde başarılı:
`independent_matched_tuning_readback_passed`. 4/8/12/4 sırası ve her profilde
aynı 28 çift / üç tam gün doğrulandı. 112 çifte ait cold indirme kaydı,
CMR kimlik/boyut/checksum/zaman bağlantıları, ham SHA ve dört native CSV
hash'i referansla eşleşti. Nominal ham indirme toplam 20.559.071.684 bayt.
12 günlük payload SHA/marker/schema, 2.899 grid satırı, alan/oran/merkez
sayımı ve tarama/zaman kontrolleri geçti. Profillerin günlük tabloları
eşleşti; sayısal alanlar rtol 1e-10 / atol 1e-4 ile karşılaştırıldı.
Production progress aynı; RAM/disk guard tetiklenmedi. Gözlem unknown,
negatif izin false; yeni üretim ayı/günü eklenmedi.

Kaynak CSV'den CPU/bellek/disk özetleri, child RSS sınırları, kaynak byte
toplamı ve throughput/publication aritmetiği ayrıca yeniden hesaplandı.
Rapor `outputs/gcp_tuning/readback/tuning_readback.json`; karşılaştırma
`outputs/gcp_tuning/readback/comparison.json`. Girdi arşivi değiştirilmedi.

Yeni yerel ham indirme veya canlı Drive API isteği yok. Export edilen
günlük journal'lar native hash'leri içeriyor; 112 ayrı pair payload'ın
tamamı bu yerel ZIP içinde değil. VM'nin yayın işaretleri ve günlük
journal bağlantıları kontrol edildi; canlı Drive'dan yeni bağımsız
native ürün indirmesi yapılmadı.

## Ölçülen süre ve kaynak kullanımı

Her satır aynı 28 çift + üç günlük union + doğrulanmış Drive yayınını içerir.
CPU tüm VM'nin örneklenmiş ortalaması; RAM deney süreç ağacının RSS tepesi.

| Profil | Toplam süre | Çift/saat | Ortalama CPU | Tepe süreç RAM'i |
|---|---:|---:|---:|---:|
| İlk 4 işçi | 12 dk 30,90 sn | 134,24 | %28,19 | 2,34 GiB |
| 8 işçi | 10 dk 44,20 sn | 156,47 | %39,89 | 4,31 GiB |
| 12 işçi | 11 dk 11,15 sn | 150,19 | %42,11 | 6,28 GiB |
| Son 4 işçi | 12 dk 53,73 sn | 130,28 | %28,44 | 2,39 GiB |

4 işçi tekrar süre oranı 1,0304: yaklaşık %3,04 fark; önceden belirlenen
0,8–1,25 sınırının içinde. İki 4 işçi süresinin ortalaması 762,3147 sn.
8 işçinin throughput kazancı **%18,335**; aynı işin süresi **%15,494 daha
kısa**. 8 işçi her iki 4 ölçümünü de en az %15 throughput kazancıyla geçti.
12 işçi ortalama bazdan %13,584 hızlı ama her iki baza karşı %15 eşiğini
sağlamadı. Önceden tanımlı karar kuralının seçimi **8**.

Dört profil toplamı 2.839,976 sn, yaklaşık 47 dk 20 sn; son kaynak örneği
2.842,124 sn. VM'nin faturalandırılmış tüm süresi ve oturum maliyeti bu
ZIP'ten ölçülmüyor. 8 işçide CPU tepesi %98,778; 12 işçide %99,637.
En düşük MemAvailable 8 işçide 26,48 GiB, 12 işçide 24,72 GiB;
en düşük disk boşluğu 12 işçide 20,72 GiB. RAM/disk rezervleri geniş kaldı.

## Daha fazla işçi neden aynı oranda hızlandırmadı?

8 işçide pair/publication evresinin CPU ortalaması %51,47; günlük union
evresi %12,57. 8 vCPU'da %12,5 yaklaşık bir CPU'nun tam çalışmasına denk;
donmuş günlük reducer seri çalışıyor. Üç günlük union 133,61 sn sürdü.

8 işçide parent'ın ölçülen kayıt/doğrulama çağrıları toplam 441,87 sn,
pair kaydı 376,50 sn. Bunlar pair alt süreçleriyle **örtüşür**; birbirinden
ayrı süreler gibi child toplamına eklenemez. Yalnızca ağ transfer süresi
olarak yorumlanamaz; yerel bilimsel geri okuma da bu evreye dahil.
Bu veriler seri yayın/doğrulama ve günlük union'ın optimizasyon için önemli
adaylar olduğunu gösteriyor. RAM'i doldurmak veya worker sayısını yükseltmek
tek başına daha yüksek throughput sağlamadı.

## Üretime aktarım sınırları ve sonraki adım

Deney üç ardışık eğitim günüyle sınırlı; 8/12 için birer ölçüm var.
Yaklaşık 2 sn örnekleme kısa tepeleri kaçırabilir. Deney havuzu sürekli
doldurur ve üç günün günlük union'larını çiftler bittikten sonra yapar.
Asıl üretimin gün/dalga sırası farklı. Önceki 92,65 çift/saat tüm VM
süresini, testteki 156,47 ise profil bloklarını kapsar; farkı doğrudan
tüm yıllarda %69 hız kazancı diye sunmuyoruz. Metadata, queue restore,
aylık kapanış ve dönem boyut farkları test throughput'una dahil değil.

Kalan 17.768 çift aynı test throughput'u ile yaklaşık 114 aktif saatlik
profil senaryosu verir; tüm dönem bitiş garantisi değildir.

Sonraki üretim hazırlığı: 8 işçili sürekli havuz, donmuş bilimsel alt
işçiler, eski pair/day/month checkpoint'lerini yeniden işlemeden kullanma,
seri yayın/günlük union için ölçümlere uygun zamanlama ve kaynak/süre
korumaları. Scope/worker/reuse sözleşmesi ayrıca doğrulanacak. Eski paketin
hardcoded 4 değerini değiştirip aynı manifest altında çalıştırmak yapılmayacak.
Sonraki aşamada VM süresi yeniden 8 saate alınarak doğrulanmış sürücü manuel olarak başlatılabilir. Şu an VM'yi yeniden açmaya gerek yok; hazırlık yerelde yapılabilir.
