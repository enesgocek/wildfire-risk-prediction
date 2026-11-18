# Veri setinin dört aşaması ve koşullu süre planı — 19 Kasım 2026

Birinci aşama için güvenilir bitiş tarihi henüz yok. Kaynakların teknik
incelemesiyle etiket üretimine bilimsel geçişin aynı şey gibi
anlatılmaması gerekiyor. Birkaç seçili vakada çalışan izleme, dört il
için güvenilir pozitif küme veya değerlendirilebilir risk hedefi sağlamıyor.

## Dört aşamanın sabit kapsamı

4 Kasım planındaki ilk üç iş paketi, aşağıda birinci aşamada birlikte
ele alınıyor. Diğer üç paket ayrı aşamalar. İş sayısının dört olarak
anlatılması, eski altı pakete yeni gereksinim eklemek veya mevcut
kabul koşullarını kaldırmak anlamına gelmiyor.
[Önceki altı paket](DATASET_COMPLETION_PLAN_2026-11-04.md).

| Aşama | Çıktı ve geçiş koşulu | Durum ve süre |
|---|---|---|
| 1. Olay, örtü, gözlem ve etiket yöntemi | Güvenilir pozitif kabulü, belirsizlik politikası, PU ve değerlendirme dayanağı gerekçelendirilmeli | Planlanmış Salur/Anamur/Menderes teknik karşılaştırması tamamlandı. Bilimsel kabul açık; bitiş tarihi belirlenemiyor. |
| 2. Hedef parçası ve model satırları | Kabul edilen protokolle anahtar, zaman, kapsam ve P/U veya hedef alanlarının üretilmesi | 1 kabul edildikten sonra yaklaşık 1–2 aktif çalışma günü için planlanabilir. |
| 3. Son parça kontrolleri ve araştırmacı onayı | Güncel manifest/hash, şema, eksiklik, zaman ve split kontrolleri; rapora bağlı açık onay | Yaklaşık yarım–1 aktif çalışma günü, ayrıca araştırmacının onay bekleyişi. |
| 4. Birleştirme ve incelenebilir teslim | Aynı onaylı parçaların birleştirilmesi, geri okuma, veri sözlüğü ve örnekler | Yaklaşık yarım–1 aktif çalışma günü. |

**2–4. aşamalar için toplam 2–4 aktif çalışma günü bir planlama
tahminidir; ölçülmüş tam üretim süresi veya teslim taahhüdü değildir.**
Bu aralık, birinci aşamanın kabul edilmiş olmasını, mevcut parçaların
yeterli olmasını ve yeni veri indirme gerekmemesini varsayıyor. Bekleme,
yeni kaynak ihtiyacı veya önemli veri uyuşmazlıkları bu aralığı değiştirir.
Bu süre yalnız veri setinin üretim, son kontrol ve paketlenmesine aittir.
Kabul sonrası ilk küçük üretim provasında satır hacmi ve süre ölçülerek
tahmin güncellenecek. Birinci aşama belirsizliği toplam süreye ekleniyor;
bugünden itibaren 2–4 günde veri seti hazır sonucu çıkarılmıyor.

## Bu turda kapatılan teknik karşılaştırma

Mevcut izleme çekirdeği, 10–11 Temmuz 2023 için üç katalog grubuna
uygulandı. Toplam 19 farklı tespit, dokuz ayarda 27 grup×ayar
karşılaştırması ve 54 zaman kesiti içeriyor. Bunlar iki vaka bağlamı
ve üç keşif grubu; gerçek yangın sayımı değil.

| Grup | Farklı kaynak tespiti | Dokuz ayarda ilk hipotez | Yeni başlangıç hipotezi / birleşme |
|---|---:|---|---|
| Menderes güney | 12 | 10 Temmuz 11.03 UTC, C524_R906 | Her ayarda 1 hipotez, 0 birleşme |
| Menderes kuzey | 2 | 10 Temmuz 11.54 UTC, C525_R906 | Her ayarda 1 hipotez, 0 birleşme |
| Anamur Belensazak | 5 | 10 Temmuz 22.33 UTC, C632_R864 | Her ayarda 1 hipotez, 0 birleşme |

Tam küme üyelikleri önceki atamalarla eşleşti. İlk tespit ve hedef
pencere sonuna kadarki geliş/geçmiş alanları, tam çalışmanın aynı
zamana kadarki alanlarıyla eşleşti. Son grafik üyeliği hash'i
retrospektif olduğu için geçmiş sabitliği kontrolünde ayrı tutuldu.
Anamur'un ertesi UTC penceresindeki iki kaydı yeni başlangıç üretmedi.
Menderes güneyde komşu hücrenin sonraki beş kaydı da ilk hücreyi
değiştirmedi. Bunlar kaynak kimliği doğrulaması değil, izleme kontrolleri.

Bu karşılaştırma, önceki saha ve örtü sorunlarını çözmedi. Menderes
kuzey tarımsal bağlam taşıyor ve bağımsız olay eşleşmesi açık. Güneyde
özgün başlangıç konumu/örtüsü; Anamur'da karışık meyvelik–orman hasarı
içinde gerçek başlangıç örtüsü ve konumu açık.
[Önceki kaynak kabul incelemesi](JULY_CASE_ADMISSION_2026-11-08.md).

## Birinci aşamanın geçiş kararı

Teknik izleme hazırlığı için planlanmış bu üç vaka karşılaştırması
tamamlandı. Aynı kayıtları yeniden çalıştırmak yeni bağımsız kanıt
olarak sayılmayacak. Birinci aşama aşağıdaki üç konu gerekçelendirildiğinde
etiket üretimine açılabilir.

1. Yeni olay, başlangıç hücre/gün belirsizliği ve orman/çalılık kapsamı
   için kullanılabilir pozitif kabul protokolü ve onu destekleyen kayıtlar.
2. Pozitiflerin seçilme biçimi, sınıf oranı veya gerekçeli belirsizlik
   sınırları açısından uygulanabilir PU dayanağı.
3. Dört ilde iddia edilecek sonucu değerlendirebilecek kapsamı açıklanmış
   referans/örnekleme dayanağı.

Bu liste 18 Kasım ortak incelemesindeki açık konuların aynısı.
[Ortak kabul incelemesi](STAGE_ONE_ACCEPTANCE_REVIEW_2026-11-18.md).
Mevcut kanıtla bu geçiş kabul edilmedi. Gözlem `unknown`, pozitif ve
negatif izinler kapalı; bu turda kabul edilen yeni yangın etiketi sıfır.
Özellik adaylarının hazır olması bu engeli kaldırmıyor.

Sonraki kabul ilerlemesi, bu açık konulardan en az birine bilgi ekleyen
kaynak veya gerekçeli yöntem kararı gerektiriyor. Yeni kurum talebi tek
zorunlu yol değil; araştırmacının böyle bir talep açmama ve ana hedefi
koruma kararları geçerli. Bilimsel kabul olmadan aşama sayacı ilerletilmeyecek.
Nihai birleştirme için son kontrol raporuna bağlı araştırmacı onayı ayrıca
korunuyor. Genel devam talimatı bu onayın yerine geçmiyor.

## Kontrol ve yeniden üretim

`python scripts/quality/review_july_lineage.py` kaynak ve dokuz atama
dosyasının hash'lerini doğrular. 27 karşılaştırma, 54 zaman kesiti,
geçmiş grafiği geri okuması, boş hedef alanları ve JSON/CSV geri okuması
geçti. Ruff ve biçim kontrolü geçti. Yeni çekirdek veya yeni eğitim
çalışması yok. 2024/2025 kayıtları analize alınmadı.

Yerel makbuz
`outputs/reports/dataset/july_lineage_validation_v1/20261118T233623Z_fff678e3/readback.json`.
SHA-256 `ec0b84b62e1d9d2781e161a474eb126d143bf68b7a1fd740dae8daaaa06350e6`.
Klasör UTC 18 Kasım 23.36, çalışma Türkiye tarihiyle 19 Kasım.
Makbuzdaki yerel çalışma süresi yalnız bu küçük karşılaştırmaya ait;
tam veri setine süre tahmini olarak kullanılmıyor.
