# Kalan eğitim aylarının süre senaryosu — 6 Ekim 2026

## 8 Ekim: ilk canlı üretim oranı

Yaklaşık 80 dakikada 131 kaydedilmiş/doğrulanmış çift ve 14 tam
gün bildirdim. Bu yaklaşık süre varsayımıyla 98,25 çift/saat ve Ağustos'un
278 çifti için yaklaşık 2,83 saat elde edilir; son aylık kayıt ek yükü
ayrıştırılmadı. Colab süresini yaklaşık 7 saat olarak düzelttim;
bu süreyle aynı veri/koşul karşılaştırması
değildir. Bütün kuyruk aynı oranda ilerleseydi başlangıçtaki 18.441 çift
yaklaşık 187,69 aktif saat / 7,82 kesintisiz gün ederdi. Bu bir senaryo,
farklı boyutlu yılların bitiş garantisi değildir. Sekiz saatlik eşdeğer
blok 23,46; gerçek rezerv/restore/yeniden açılış daha fazla oturum gerektirebilir.

Dört işçi gerçek üretimde aktif, bir/iki/dört işçili eş veri karşılaştırması
yapılmadı. CPU/bellek/disk örneği ve kaynak aktarım süreleriyle darboğaz
belirlenmeden canlı donmuş paket veya VM kapasitesi değiştirilmez.
Sekiz saat ilk oturumun güvenlik sınırı; günde yalnızca bir oturum zorunluluğu yok.

## 8 Ekim: kapasite artırma değerlendirmesi

Mevcut oturumun tüketimi uygun bulunursa daha güçlü VM ile Free Trial kredisinin proje kapsamında değerlendirilmesi planlandı. Kişisel
ödeme çıkmaması ve Paid Upgrade yapılmaması koşulları değişmedi.
Yaklaşık 7 / 2,83 saat karşılaştırması 2,47 kat hızlanma / %59,6 süre
azalması senaryosudur; eş veri kontrollü benchmark değildir.

İlk aday 16 vCPU / 64 GB ve uygun kaynak bütçesiyle daha çok işçi;
32 vCPU sonraki aday olabilir. Güncel Frankfurt bölgesel ve tüm bölgeler
global kotası okunmadan erişilebilir kabul edilmez. Önceki global 32 kotası
ve us-central1 E2 24 kotası Frankfurt kapasitesini kanıtlamaz. Non-billable
Free Trial'da GPU ve kota artırma talebi yok:
[Google kısıtları](https://docs.cloud.google.com/free/docs/free-cloud-features).

Yeni VM yerine aynı E2 VM'nin durmuşken büyütülmesi ortam/diski/kimlik
korumak için önce değerlendirilecek. Kodda ilk gün sonrası işçi sayısı 4
olarak sabit; tek başına makine büyütmek paralelliği artırmaz. Yeni işçi
paketi için mevcut SHA bağlı Drive kayıtlarıyla devam davranışı ayrıca
doğrulanmalı; sessiz paket değişimi veya tamamlanan çiftleri baştan işleme yok.
[Makine tipi düzenleme](https://docs.cloud.google.com/compute/docs/instances/changing-machine-type-of-stopped-instance).

Doğru VM'den ilk 10 saniyelik örnek alındı: vmstat ilk satırı boot ortalaması,
sonraki satırlarda CPU boşta %87–100; iowait %0 ve runnable 0–1.
RAM yaklaşık 1,0 GiB kullanılmış, 30 GiB available; diskte 24 GB boş (%16 kullanım).
Bu aralıkta RAM/disk kapasitesi baskısı veya toplam CPU doygunluğu görülmedi.
Tek çekirdek kullanılan evre, NASA/Drive beklemesi veya dalga/gün geçişi
ayrıştırılmadı; 10 saniye tüm oturumu temsil etmez. Daha büyük VM tek başına
hız garantisi olarak seçilmeyecek. Güncel progress/log ve yalnızca PID,
süre/CPU/RSS/comm içeren süreç listesiyle aşama kontrolü sırada.
Önceki Cloud Shell 15 GiB RAM / overlay %91 disk çıktısı üretim VM ölçümü
olarak kullanılmadı. Oturum sonrası kredi farkı anlık
kesin maliyet sayılmaz: maliyet verileri genellikle bir gün içinde, bazen
24 saati aşarak yansır. Güncel saatlik form fiyatı ve Billing Reports gerçek
kullanımı birlikte değerlendirilecek. Seçim ölçülen çift/saat ve kredi/çift
ile yapılır; kesin hız/kredi garantisi yok. Üretim henüz durdurulmadı veya
yeni kapasiteye geçirilmedi.
[Rapor gecikmesi](https://docs.cloud.google.com/billing/docs/how-to/reports).

## Önceki planlama kaydı

7 Ekim güncellemesi: kesintiden devam eden tam dönem üretim paketi hazır;
ilk canlı uzun çalışma henüz başlamadı. Aşağıdaki hızlar eski iki işçili
benchmark senaryolarıdır; üretim süresi garantisi değildir. Güncel çalıştırma
ve süre seçimi için [üretim rehberi](GCP_PRODUCTION_RUN.md) kullanılır.

Temmuz 2023 tamamlandı; 2018–2023 eğitim döneminde **71 ay / 18.441 nominal
çift** kaldı. Eşleşmemiş 283 katalog kaydı korunuyor ve negatif sayılmıyor.
Son Drive denemesi bu ay sayısını azaltmadı; altyapı/kalıcılık kontrolüydü.

Doğrulanmış benchmark: 2 işçiyle 6 çift 229,294 saniye. Aynı hız tüm kalan
çiftlerde sürerse salt çift evresi **195,76 saat** eder. Bu evre kaynak
indirme, doğal ürün denetimi ve çift çıktıları kontrolünü içerir; günlük
geometrik birleşim, üretim Drive kaydı, kesinti/retry ve boş bekleme dahil
değildir. Altı yaz geçişi bütün yılları temsil eden ölçüm değildir.

| Sunucunun günlük aktif süresi | Salt çift evresi | %50 ek süre varsayımıyla senaryo |
|---|---:|---:|
| 8 saat | 24,47 gün | 36,70 gün |
| 12 saat | 16,31 gün | 24,47 gün |
| 24 saat | 8,16 gün | 12,23 gün |

%50 ek süre ölçülmüş bir katsayı veya üst sınır değil; planı görmek için
varsayım. Uygulama hazırlığı, 2024 doğrulaması, kalan özellikler/model eğitimi
bu tabloya dahil değil. İlk tam üretim gün/ay ölçümüyle süre yeniden hesaplanır.

Üretim hedefi, gün gün elle komut/dosya taşımak değil; onaylanmış tarihleri
aynı kuyruğa veren, çift/gün completion kayıtlarını otomatik Drive'a yazan ve
kesintide tamamlanmışları tekrar işlemeyen bir işçidir. Bu sarmalayıcı ilk
senaryo yazılırken tamamlanmamıştı; sonraki hazırlıkta tamamlandı.
İlk küçük kapsam üretimden süre/kalite ölçümü için önerilmişti;
her üç günde yeni manuel aktarım bekleyen kalıcı plan değildir.

Önerilen hız adımı aynı mevcut VM'de 4 işçiyi kontrollü ölçmek. İki kat hız
elde edildiği varsayılmayacak; NASA sunucusu/ağ/CPU ve günlük union etkileri
ölçülmeli. Daha büyük makine veya yeni VM ancak somut seçeneklerin değerlendirilmesi ve kapsam
kararı sonrasında ele alınır. Mevcut 2 saat/Stop değişmedi. Sonraki 6/8 veya
daha uzun sınırlı oturumlar kapsam kararı ve ölçüm gerektirir; sınırsız
otomatik restart/ücretli yükseltme yok. Paylaştığım Free Trial
bitişi 26 Ekim; 8 saat/gün ve mevcut iki işçi senaryosu bu tarihe sığmıyor.

Hesap kaynağı: `scripts/cloud/plan_gcp_production.py`;
`outputs/reports/observation_coverage/gcp_production_readiness_plan.json`
içindeki time_planning_scenarios. Ham yerel indirme/bulut kaynak değişikliği
yapılmadı. Mevcut Drive VM raporunun yerel doğrulaması bu plana eklendi.
