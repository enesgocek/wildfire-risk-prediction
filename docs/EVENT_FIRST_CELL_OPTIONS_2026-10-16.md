# İlk tespit hücresi: kaynak örnekleri ve karar seçenekleri

16 Ekim 2026. Durum: araştırmacı **A — bütün ilk hücreleri ortak aday
kimliğiyle koru** yönünü açıkça seçti; `first_cell_candidates_v1` kaydedildi.
Olay kimliği, yarıçap/zaman eşiği ve 0/1 etiket kabulü bu çalışmada yapılmadı.

19 duyarlı hücre-gün örneğinde **aynı kayıtlı en erken zamanın birden fazla
hücrede bulunması**, gruplama değişince ilk günün değişmesinden ayrı incelendi.
Öneri, bütün ilk hücreleri ortak bir olay adayı kimliği altında korumak ve
diğer kabul koşulları çözülene kadar hedefleri boş bırakmaktır. Tek bir hücreyi
alfabetik sıra veya dosyadaki ilk satırla seçmek bilimsel gerekçe sağlamaz.

## Bu aşamada gerçekten kontrol edilen kapsam

[14 Ekim duyarlılık izi](SENSITIVE_PILOT_TRACE_2026-10-14.md) yeniden açıldı.
13 doğrudan girdi dosyasının kimliği, beş eski çıktı ve bunların kapanış
makbuzu kontrol edildi. Kaynak üye tablosundan 181 bileşen bağlamının üye
hash'i, sayısı, ilk/son zamanı ve bütün ilk hücreleri tekrar hesaplandı.
19 örneğin dokuz senaryodaki `(T,T+24 saat]` ilk aday eşleşmeleri uzlaştırıldı.
Özgün grafik bölümlenmesi/komşuluk kenarları yeniden kurulmadı; bu kısım
önceki hash ile bağlı incelemeye dayanır. Kaynakların fiziksel olay kimliği
doğrulanmadı ve insan incelemesi yapılmış sayılmadı.

Örnekler 2018–2023 dönemindeki 400 amaçlı inceleme biriminden seçilen
**19 duyarlı birimdir**. Dokuz senaryo, 500/1.000/2.000 m komşuluk ile
24/48/72 saat kenar aralığının keşif amaçlı birleşimleridir. 181 bağlam,
171 hücre-gün×senaryo birleşiminden farklıdır: bir birleşim birden fazla
bileşene bağlı olabilir. Sayımlar bağımsız yangın sayısı veya toplum hata
oranı değildir; 19 örneğin dışına genellenmez.

## İki ayrı sorun

**Gruplama belirsizliği:** 19 örneğin 8'inde dokuz senaryonun yalnız bir
bölümünde ilk hücre/gün eşleşmesi vardır; kalan 11'inde eşleşme her senaryoda
vardır, fakat bileşen üyeliği değişir. Örneğin 21 Ocak 2020, C595_R878 için
500 m'de o gün başlayan aday, 1.000/2.000 m'de önceki gün 23.27 UTC'de
başlayan bileşene bağlanır. 4 Ekim 2019, C596_R878 örneğinde ise 2.000 m
senaryosu ilk zamanı önceki güne ve ilk hücreyi C596_R879'a taşır.
Bu eski izlerdeki iki bağın sırasıyla 533,02 m/10,53 saat ve
1.436,38 m/23,68 saat olduğu 14 Ekim raporunda kayıtlıdır; bugün bu
mesafeler yeniden hesaplanmadı. Eşik seçimi bu örneklerden otomatik çıkarılamaz.

**İlk hücre belirsizliği:** 181 bağlamın 35'inde en erken kayıtlı zaman
iki veya dört farklı hücrede bulunur. Bunlar 19 birimin 5'ine dokunur.
Kayıtlı zaman eşitliği gerçek fiziksel eşzamanlılık veya kesin tutuşma
konumu anlamına gelmez. Çok sayıda tespitin aynı hücrede bulunması da
birden fazla ilk hücre bulunduğu anlamına gelmez; farklı hücre sayılır.

Somut örnek: **5 Ekim 2021, C557_R877**. Dokuz senaryonun tamamında en
erken kayıtlı zaman **23.29 UTC**'dir. Bu zamanda 10 kaynak tespiti,
**C556_R877 ve C557_R877** hücrelerine dağılır. Bileşen toplamı senaryoya
göre 21/22 tespittir. İki hücreyi korumak iki bağımsız yangın kabulü değildir.

## Karara sunulan seçenekler ve seçilen yön

| Yön | Uygulama | Kazanç ve sınırlama |
|---|---|---|
| **A — bütün ilk hücreleri koru (öneri)** | Aynı en erken kayıtlı zamanda bulunan bütün hücreler aynı bileşene bağlı aday kümesi olarak saklanır. Olay kimliği kabul edilirse ortak olay kimliği korunur. | Gözlenen konumları keyfî tek hücreye indirgemez. Bir olayın birden fazla hücre adayı olabilir; olay yakalama sayımı, ağırlıklandırma ve veri ayrımı bunu ayrıca ele almalıdır. |
| **B — ana aday havuzunda yalnız tek ilk hücre** | Çok ilk hücreli bileşenler inceleme kaydında tutulur, ana etiket adayı havuzuna şimdilik alınmaz. Diğer tek hücreli aday varsa o korunur. | Ana havuz daha dar tanımlanır. Sınırda veya geniş alanda gözlenen başlangıçları seçici dışlama riski vardır; il/mevsim/örtü ve olay kapsamı ayrıca denetlenmelidir. |

Her iki yönde de dışlanan/eşleşmeyen örnek **0 yapılmaz**. A yönünde
çok hücreli adaylara doğrudan 1 atanmaz. Gruplama, habitat, kaynak anlamı,
pencere sınırları ve gözlem kabulü ayrıca tamamlanır. Yöntem seçimi
bağımsız doğrulama, eğitim veya nihai birleştirme onayı değildir.

Araştırmacı A'yı seçti. Yeni [sürümlü aday kuralı](../configs/first_cell_candidates_v1.json)
yalnız kayıtlı bütün ilk hücreleri korur; bir gruplama senaryosu seçmez.
181 senaryoya özgü bileşen bağlamının bütün ilk hücreleri **232 aday
satırına** açıldı. Her satırdaki `candidate_component_id` özgün, senaryo
ile nitelenmiş bileşen kimliğidir. İki hücre aynı kimliği taşır; farklı
senaryolar aynı fiziksel olaymış gibi birleştirilmez. 232 satır, 232 veya
181 bağımsız yangın değildir. Bütün hedefler boş; `event_identity_accepted`
ve `event_membership_complete` false kaldı. Bu aday kimlikleri mevcut
eğitim ayrım kapısını sağlayamaz; bu sınır ayrıca test edildi.

İlk hücre seçimi, yukarıdaki yarıçap/zaman gruplama seçimini çözmez.
Tek bir sabit senaryo için yeterli gerekçe henüz yoktur; büyük bileşeni
tek yangın saymak veya dokuz senaryoda uzlaşanı tek başına doğru saymak
kabul edilmez. Belirsizlik listesi ve diğer örnekler korunacaktır.

## Bu 19 örnekte A–B farkı

| Tarih ve örnek hücre | A'da aday eşleşen senaryo /9 | B'de aday eşleşen senaryo /9 |
|---|---:|---:|
| 2021-10-05, C557_R877 | 9 | 0 |
| 2018-09-01, C674_R878 | 9 | 3 |
| 2018-05-26, C675_R877 | 9 | 3 |
| 2023-09-03, C676_R876 | 9 | 3 |

**4 farklı birimde toplam 27 hücre-gün×senaryo birleşimi** B yönünde
bütün aday eşleşmesini kaybeder. Bu 27 bağımsız olay veya silinecek satır
değildir. Beşinci çok ilk hücre bağlamı olan 5 Ağustos 2021, C606_R882'de
eşleşen tek senaryonun tek ilk hücreli ayrı bir bileşeni bulunduğundan
A/B eşleşme sayısı 1/1 kalır. İlk hücre seçeneğinin etkisi ile zincirleme
gruplamanın etkisi bu örnekte de karıştırılmamalıdır.

Tam 19 satır: [karar matrisi](../outputs/reports/dataset/event_cell_decision_v1/20261016T153227Z_54400785/case_decision_matrix.csv).
Dokuz senaryo: [aday sayımı](../outputs/reports/dataset/event_cell_decision_v1/20261016T153227Z_54400785/scenario_impact.csv).
Bu satırlar da etiketsizdir. A/B sütunları başarılı tahmin veya yangın etiketi değildir.

## İnsan incelemesinde beklenen karar

Araştırmacıdan istenen, 5 Ekim örneğinde ilk kaydı iki hücrede tutmanın
hedeflenen günlük hücre riskine uygun olup olmadığını değerlendirmektir.
Verilen karar **A yöntem yönüdür**; fotoğrafa bakıp gerçek tutuşma
yeri, doğru yarıçap veya yangın yokluğu tahmin etmesi istenmez.

A'nın ortak aday kimliği ve aday kimliğinin çözülmüş olay üyeliği yerine
geçememesi kontrol edildi. Gerçek olay kimliği kabul edilirse farklı
hücrelerin eğitim ayrımlarında ayrılmaması ve olay yakalamada çift
sayılmaması ayrıca denetlenecek. Sıradaki bilimsel iş olay gruplama
gerekçesi ve gözlem/negatif protokolüdür. 2024 karşılaştırması ve kapalı
2025 final verisi açılmadı.

## Tekrar üretim ve kayıt

Komut: `python scripts/quality/prepare_event_cell_decision.py`.
Yeni sonuç: `outputs/reports/dataset/event_cell_decision_v1/20261016T153227Z_54400785/`.
13 girdi/beş çıktı hash kapanışı ve CSV/JSON geri okuması geçti.
**18 yeni davranış vakası dahil 67 ilgili test** ve üç dosyada lint/format
kontrolü geçti. Sınananlar: çok bileşenin aynı birimde çift sayılmaması,
tek hücre/tie ayrımı, sol açık–sağ kapalı pencere, etiketli/bozuk girdinin
reddi ve mevcut hedef/son birleştirme kapılarıdır. Tüm depo testleri bu
aşamada çalıştırılmış sayılmaz.

CSV boş hedefinin diskteki sayısal NaN türü ile bellekteki None türü
ayrılarak yalnız hedef dışı alanlar birebir karşılaştırıldı; hedefin
boşluğu ayrıca zorunlu kılındı. Önceki geliştirme dizinleri korundu;
güncel kanıt yukarıdaki son sonuçtur. Ağ ve bulut işi başlatılmadı.

Readback SHA-256:
`84ed43250e05a8023bbcc51ecf57978e9b3709de35070698a98eefa3ce1e6abf`.
Kapanış SHA-256:
`1a8ba2ce82b55f2a911bf6d87e8b6bb9fc83e8727c4b1f897887c603889edcfd`.

`daily_observation_status=unknown`, `negative_label_permitted=false`
korundu; gerçek etiket, gerçek model fit ve nihai birleştirme yapılmadı.
