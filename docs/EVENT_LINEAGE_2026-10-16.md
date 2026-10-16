# Başlangıç adayları, devam ve birleşme geçmişi

16 Ekim 2026. Durum: mevcut nokta grafiğinin kronolojik geçmiş tanısı
tamamlandı. Fiziksel olay kimliği, yeni gruplama politikası veya 0/1
etiket kabulü değildir. Araştırmacının A tercihiyle bütün ilk hücreler
korunur; kaynak/özellik dosyaları değiştirilmedi.

**181 bileşen bağlamının 11'inde birden fazla başlangıç adayı sonradan
birleşiyor.** Başlangıç kayıtları silinmeden ve birleşme sonrasındaki
tespite tek bir kök keyfî atanmadan izlenebiliyor. Buna rağmen aynı
19 duyarlı birimin 171 örnek×ayar karşılaştırmasında ilk-gün aday
eşleşmeleri değişmedi. Bu tanı etiketleri çözmüş veya daha iyi bir
tahmin modeli üretmiş sayılmaz.

## İncelenen kapsam ve kural

2018–2023 eğitim kaynağındaki aynı 19 amaçlı duyarlı birime bağlı dokuz
senaryo kullanıldı: 500/1.000/2.000 m nokta komşuluğu × 24/48/72 saat
kenar aralığı. 5.436 farklı kaynak tespiti, farklı senaryolarda tekrar
yer aldığı için **38.639 tespit×bağlam satırı** incelendi. 181 bağlamın
nihai üye kümeleri ve toplam 1.119.420 olan senaryoya özgü kenar sayımı
önceki sabit sonuçlarla eşleşti. Bu sayılar bağımsız yangın sayısı değildir.

Yeni `event_lineage_diagnostic_v1` bu grafiği kayıtlı zaman sırasıyla izler:

| Geçiş | Kaydedilen durum |
|---|---|
| Başlangıç adayı (`birth`) | Yeni zaman grubunun bağlandığı önceki bileşen yoktur; değişmez bir aday kimliği oluşturulur. |
| Devam (`continuation`) | Önceki tek bileşene bağlanır; mevcut geçmiş durumu korunur. |
| Birleşme (`merge`) | İki veya daha fazla önceki bileşen birleşir; başlangıçlar silinmez, önceki geçmiş durumları yeni kayda bağlanır. |

Aynı kayıtlı zaman damgasındaki tespitler **tek bir toplu adımda** işlenir.
Bu eşitlik fiziksel eşzamanlılık iddiası değildir. Bir toplu adım üç eski
bileşeni birleştirirse bir birleşme kaydı ve bileşen sayısında iki azalma
olur. Yeni noktalar önceki ortak bileşen üzerinden bağlanıyorsa satır
sırasına göre fazladan başlangıç oluşturulmaz. Bütün ilk hücreler korunur.

Özgün `source_cluster_id` ortak üst aday kimliği olarak bütün tablolarda
korunur. `birth_candidate_id` bunun grafik geçmişindeki alt kaydıdır;
bağımsız yangın kimliği değildir. Özgün bileşenin en erken zamanında
oluşan alt başlangıçlardaki hücrelerin birleşiminin, özgün ilk hücre
kümesiyle eşitliği kontrol edildi.
Böylece A kararı değiştirilmedi ve yeni bir olay politikası seçilmedi.

Her tespitin alındığı andaki geçmiş durumu değişmez olarak saklanır.
Sonraki birleşme önceki tespitin kimliğini geriye dönük yeniden atamaz.
Birleşmeden sonra gelen tespit, birden fazla başlangıç kaydı taşıyan
duruma bağlanabilir. Bu **birikimli grafik geçmişidir**; her başlangıcın
fiziksel olarak o tespitin nedeni olduğu veya eşit olasılıkla ona ait
olduğu iddia edilmez. Olasılık ve ağırlık ataması yapılmadı.

Geçmiş, üst durumlara işaret eden döngüsüz bir kayıt grafiğinde saklanır.
Her nokta için bütün uzun geçmişi tekrar yazmak yerine durum kimliği
kullanılır. Bu yapı ayrı bir geri okuma ile baştan çözüldü: eksik/gelecek
üst kayıt, döngü, yanlış geçmiş sayımı ve kayıp başlangıç kontrol edildi.

Bu tanı FEDS uygulaması değildir; çevre poligonu, yakıt bilgisi veya
fiziksel yayılım yönü kullanmaz. Nokta grafiği birikimli olduğu için
**fiziksel bölünmeyi modellemez**. Aynı fiziksel yangın gözlem boşluğu
veya mesafe kuralı nedeniyle birkaç başlangıç adayı üretebilir; yakın
bağımsız yangınlar aynı grafikte birleşebilir. Nihai grafiğin eski
grafikle eşitliği uygulama kontrolüdür, bağımsız doğrulama değildir.

## Gerçek sonuç ve sayım birimleri

| Ölçüm | Sonuç |
|---|---:|
| Bileşen bağlamı | 181 |
| Birden fazla başlangıç içeren bağlam | 11 |
| Başlangıç adayı kaydı, bütün senaryolar toplamı | 904 |
| Devam kaydı, bütün senaryolar toplamı | 723 |
| Birleşme kaydı, bütün senaryolar toplamı | 128 |
| Birleşmelerin toplam bileşen azaltımı | 723 |
| Ayrı doğrulanan geçmiş durumu | 1.032 |
| Aday eşleşmesi değişen örnek×ayar | 0/171 |

**904 − 723 = 181** korunumu, her özgün bileşen için ayrıca doğrulandı.
128 birleşme ile 723 azalma farklı birimlerdir. Aynı kaynak noktaları
senaryolar arasında tekrar eder; bu toplamlar yangın istatistiği değildir.

35 farklı örnek tespiti dokuz senaryoda **315 satırda** incelendi.
Bunların **18 tespit×senaryo satırı**, iki hücre-gün birimindeki üç
farklı kaynak tespitine aittir ve birden fazla başlangıç geçmişi taşır.
Tüm bu satırlarda `event_membership_complete=false` ve hedef boş kaldı.
Bu alanlar retrospektif hedef incelemesidir; model girdisi değildir.

### 5 Ağustos 2021, C606_R882

Örneğe bağlı büyük bileşenin geçmişi ayara göre değişir:

| Senaryo | Bileşen tespitleri | Başlangıç adayları | Birleşme kayıtları |
|---|---:|---:|---:|
| 500 m / 24 saat | 3.578 | 236 | 38 |
| 1.000 m / 24 saat | 3.708 | 8 | 4 |
| 2.000 m / 24 saat | 5.303 | 3 | 1 |

Üye kümeleri de değiştiği için bu tablo aynı sabit noktalar üzerinde
ölçülmüş bir iyileştirme oranı değildir. Daha az başlangıç adayı daha
doğru yöntem demek değildir. 236 başlangıç kaydı, 236 gerçek yangın
veya tek bir doğru yangın olduğu sonucunu vermez.

### 5 Kasım 2022, C520_R916 — küçük inceleme örneği

2.000 m / 72 saat bileşeninin kayıtları daha kısa bir örnek sunar:

| Kayıtlı UTC zamanı | Grafik kaydı |
|---|---|
| 28 Ekim 2022, 01.01 | C520_R916'da ilk başlangıç adayı |
| 28 Ekim 2022, 23.02 | C519_R916'da ayrı başlangıç adayı |
| 29 Ekim 2022, 23.35 | İki önceki bileşenin birleşmesi |
| 5 Kasım 2022, 23.53 | İncelenen tespitin iki başlangıç kaydı taşıyan geçmişe bağlanması |

5 Kasım tespitini iki yeni yangın veya otomatik yeni başlangıç olarak
saymadık. İki 28 Ekim kaydının aynı fiziksel olayın parçaları mı, ayrı
olaylar mı olduğu bu grafikle kesinleşmez. [Tespit geçmişleri](../outputs/reports/dataset/event_lineage_v1/20261016T190431Z_31a64912/anchor_ancestry.csv)
ve [başlangıç kayıtları](../outputs/reports/dataset/event_lineage_v1/20261016T190431Z_31a64912/birth_candidates.csv)
somut kaynak kimliklerini korur.

## Açık konu ve insan incelemesinin amacı

Öncelik bu iki örnekte uygun bağımsız olay kaydı veya yeterli dış kanıtla
başlangıç/devam/birleşme yorumlarını sınamaktır. İnceleyenin bakacağı konu,
referansın zaman/konum kapsamının hangi başlangıçları desteklediğidir;
sadece nokta sayısından yangın sayısı tahmin etmesi istenmez. Gerekli
kesinlikte referans yoksa karar belirsiz kalır.
[Mevcut referans alım koşulları](REFERENCE_INTAKE_2026-10-15.md) korunur.
Bu çalışmada yeni kurum yanıtı veya özel yazışma okunmadı.

0/171 değişim, seçilmiş bu örneklerde geçmişi saklamanın aday varlığını
değiştirmediğini gösterir; başka örneklerde aynı sonucu garanti etmez.
Gruplama eşiği, kaynak anlamı, habitat ve güvenilir negatif/gözlem
protokolü hâlâ açık. Bilinmeyen veya eşleşmeyen kayıt 0 yapılmadı.
2024 karşılaştırması, 2025 final verisi ve nihai birleştirme açılmadı.

## Tekrar üretim ve kontroller

Komut: `python scripts/quality/audit_event_lineage.py`.
Çıktı: `outputs/reports/dataset/event_lineage_v1/20261016T190431Z_31a64912/`.
12 girdi/sekiz çıktı kapanışı ve CSV geri okuması geçti. 904 başlangıç,
1.032 geçmiş durumu ve 38.639 tespit-durum bağı ayrı doğrulandı.
**15 yeni davranış vakası dahil 110 ilgili test** ve üç dosyada lint/
format geçti. Sınamalar aynı zaman sırası, çoklu birleşme korunumu,
gelecek veri eklenince eski kayıtların korunması, kapalı zaman kenarı,
bozuk geçmiş bağlantısı ve mevcut kabul kapılarını içerir. Bütün depo
testleri çalıştırılmış sayılmaz. İlk geliştirme çıktısı korunarak son
kodla ayrı sonuç üretildi. Ham veriler/çıktılar Git'e eklenmez.

Readback SHA-256:
`dd4652f7bb900c08f3de8e5a96bc9f0f329d90f3eb43b314d4d9c615577b792b`.
Kapanış SHA-256:
`e7a1a75aabaab78deaf05eb36f24df5385dbf32fecfcacb9e0409e01091024d4`.

Ağ/bulut işi, gerçek etiket/model ve nihai birleştirme yapılmadı;
`daily_observation_status=unknown`, `negative_label_permitted=false` korundu.
