# Kalan eğitim aylarının süre senaryosu — 6 Ekim 2026

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
her üç günde kullanıcıdan yeni manuel aktarım bekleyen kalıcı plan değildir.

Önerilen hız adımı aynı mevcut VM'de 4 işçiyi kontrollü ölçmek. İki kat hız
elde edildiği varsayılmayacak; NASA sunucusu/ağ/CPU ve günlük union etkileri
ölçülmeli. Daha büyük makine veya yeni VM ancak somut seçeneklerle kullanıcı
kararı sonrasında ele alınır. Mevcut 2 saat/Stop değişmedi. Sonraki 6/8 veya
daha uzun sınırlı oturumlar kullanıcı kararı ve ölçüm gerektirir; sınırsız
otomatik restart/ücretli yükseltme yok. Kullanıcının paylaştığı Free Trial
bitişi 26 Ekim; 8 saat/gün ve mevcut iki işçi senaryosu bu tarihe sığmıyor.

Hesap kaynağı: `scripts/cloud/plan_gcp_production.py`;
`outputs/reports/observation_coverage/gcp_production_readiness_plan.json`
içindeki time_planning_scenarios. Ham yerel indirme/bulut kaynak değişikliği
yapılmadı. Mevcut Drive VM raporunun yerel doğrulaması bu plana eklendi.
