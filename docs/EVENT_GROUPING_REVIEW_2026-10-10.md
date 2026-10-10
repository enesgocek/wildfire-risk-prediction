# Olay gruplaması geri okuması — 10 Ekim 2026

## Amaç ve kapsam

Modelin hedefi, sonraki 24 saatte yeni bir olayın ilk aktif uydu tespitidir.
Tek yangının tekrar gözlenmesi ayrı olaylara çevrilmemelidir. Bununla birlikte,
yakın tespitlerin zincirleme bağlanması farklı yangınları birleştirebilir.
Mevcut gruplama çıktıları, nihai olay kuralı seçilmeden ayrı kodla yeniden denetlendi.

Ortak aday kaynakta 2018–2024 için 33.255 tespit bulunuyor. Bu incelemede yalnız
2018–2023 eğitimindeki **30.295 aday** kullanıldı; 2024'ün 2.960 kaydı grafikten
çıkarıldı. Ortak dosyanın tarihleri ayrım için okundu, doğrulama kayıtlarıyla
senaryo seçimi yapılmadı. 2025 final testi açılmadı.

Kaynak daha önce Type=0, nominal/yüksek güven koşullarıyla seçilmiştir.
Aşağıdaki ilk zaman, bu **seçilmiş aday kümesinin** ilk tespitidir; bütün uydu
tespitlerinin ilk zamanı, doğrulanmış tutuşma veya bağımsız yangın kimliği değildir.
NASA Type teknik teyidi, habitat kararı ve güvenilir negatif politikası açık kalır.

## Yöntem

Yeni ortak kod `src/wildfire_risk_prediction/event_review.py`, giriş noktası
`scripts/firms/review_event_grouping.py` içindedir. Önce özgün aday tablo hash'i
kontrol edilir. Tespit kimliği, hücre, sensör ve zaman alanları eski atamalarla
eşleştirilir; her kayıt bir kez korunur. Eksik/tekrarlı kimlik, değişen aday
seçimi veya eğitim dışı tarih reddedilir.

500/1.000/2.000 metre ile 24/48/72 saat için dokuz bağlantı grafiği yeniden
kurulur. Coğrafi kutu yalnız hızlı aday aramasıdır; son mesafe WGS84 geodesic
hesabıyla doğrulanır. Arama, 20–40 boylam ve 30–45 enlem pilot zarfını kabul
eder; başka bölgelere sessizce genellenmez. Mekânsal bağlantı önbelleği, tespit
kimliği/koordinat/zaman hash'ine ve mesafe ayarına bağlıdır.

Yeniden hesaplanan bileşenlerle kayıtlı kümelerin iki yönlü bire bir eşleşmesi
kontrol edilir. Yalnız küme sayısının eşit olması yeterli kabul edilmez. Bağlantı
sayısı ve en büyük küme sayımı da eski raporla karşılaştırılır. Kabul edilmiş
atamalar veya raporlar değiştirilmez; yeni inceleme CSV'leri ayrı dizine yazılır.

Her kümede ilk/son zaman, ilk andaki bütün hücreler, sensör/hücre sayıları,
süre ve ilk tespit noktasına en uzak üyenin mesafesi tutulur. Aynı ilk zaman
birden çok hücreye denk gelirse ayrı inceleme işareti verilir. Kimlikle seçilen
`canonical_first_grid_id` yalnız tekrarlanabilir bir referanstır; nihai hedef
hücresi olarak kullanılamaz. Sonradan görülen bütün küme hücreleri ilk andaki
pozitif hücreler sayılmaz.

Süre bağlantı aralığını veya ilk noktaya mesafe bağlantı yarıçapını aştığında
zincirleme inceleme işareti verilir. İşaret, gerçek yangının hatalı gruplandığı
anlamına gelmez; süren/büyüyen yangınlar da böyle görünebilir. Otomatik bölme,
silme veya yeni olay ilanı yapılmadı.

## Gerçek sonuçlar

Dokuz senaryonun tamamı özgün atamalarla eşleşti. Sayılar doğrulanmış yangın
sayısı olarak değil, keşif amaçlı bileşen sayısı olarak raporlanır:

| Mesafe / zaman aralığı | Küme | Süre incelemesi | Mekânsal zincir incelemesi | İlk anda birden çok hücre |
|---|---:|---:|---:|---:|
| 500 m / 24 h | 8.485 | 140 | 467 | 172 |
| 500 m / 48 h | 8.227 | 97 | 472 | 164 |
| 500 m / 72 h | 7.975 | 84 | 480 | 155 |
| 1.000 m / 24 h | 7.478 | 161 | 191 | 192 |
| 1.000 m / 48 h | 7.186 | 131 | 209 | 184 |
| 1.000 m / 72 h | 6.849 | 137 | 229 | 168 |
| 2.000 m / 24 h | 7.006 | 197 | 134 | 192 |
| 2.000 m / 48 h | 6.573 | 165 | 157 | 178 |
| 2.000 m / 72 h | 6.089 | 195 | 174 | 151 |

İnceleme sütunları örtüşebilir; toplanarak farklı küme sayısı elde edilemez.
500 m/24 h senaryosunda en uzun küme 312,95 saat (yaklaşık 13,04 gün).
İlk noktadan en uzak üye 20,129 km; bu değer küme çapı veya yangın çevresi
değildir. 2.000 m/72 h senaryosunun en uzun süresi 1.236,217 saat
(yaklaşık 51,51 gün). Bağlantı aralığı, kümenin toplam süresini sınırlamaz.
Dolayısıyla yalnız bu parametreleri değiştirmek, doğru olay kimliğini kanıtlamaz.

1.000 m/72 h ve 2.000 m/72 h senaryolarında birer eğitim içi takvim yılı
sınırını geçen küme var. 2023–2024 ayrımındaki bağların tam denetimi yapılmadı;
2024 grafiğe dahil edilmedi. Başlangıç/bitiş bağlamı eksikliği işaretleri,
seçilen bağlantı aralığı kadar dönem kenarını kapsar; bütün gözlem boşluklarını
ve AOI dışındaki yangın devamını ölçmez.

## Hedef penceresi ve kabul sınırı

Kayıtlı sözleşme `(T,T+24 saat]`. Tam 00:00 UTC tespiti önceki günün sağ
sınırına atanır; aynı gün 00:00 UTC tahmini için yeni tespit sayılmaz.
Katalogdaki `candidate_prediction_timestamp_utc` yalnız bu zaman eşleştirmesini
gösterir. 2018 başında hedef 2017'nin son gününe düşerse dönem kenarı işareti
korunur; 2017 özellik tablosu okunmaz veya model satırı oluşturulmaz.

Her küme `exploratory_cluster_only`, negatif etiket izni `false` olarak kaldı.
`confirmed_event_count=null`, `scenario_selected=null`,
`daily_observation_status=unknown`, `labels_created=false`.
İleri tarihteki tespitler eski bileşenleri birleştirebildiği için bu yöntem
dondurulmuş çevrimdışı katalog denemesidir; değişmez çevrimiçi olay kimliği
veya tahmin anında kullanılabilecek bir özellik değildir.

## Kontrol ve kayıt

Çıktı `outputs/reports/events/review_v1/20261010T001137Z_320433ed/` içinde:
dokuz inceleme CSV'si, kaynak/çıktı/kod hash'lerini tutan `review.json` ve
ayrı ilk-tespit/hedef-penceresi kontrolü `independent_readback.json`.

- Özgün aday tablo SHA-256: `37ebb8e1f204b28faf2da21661ff6b0f8e9125c25876b7966df3ae9aea7551c5`.
- İnceleme JSON SHA-256: `61de3f798bb1462baf4f1d65bebc72539cef47467d5590baeec498951dc94d7e`.

56 ilgili test geçti; bunların 20'si yeni olay denetimine aittir. Yanlış
bölme/birleştirme, kaynak uyuşmazlığı, gelecek/test tarihleri, iki sensör,
sıralama değişimi, gece yarısı ve yıl sınırı kontrol edildi. Zaman aritmetiği
NumPy/Pandas uyarılarını hata kabul eden denemede geçti. Gerçek kataloglar
CSV'den geri okundu; ayrıca özgün atama/zamanlardan ilk an, ilk hücre listesi,
sayım ve `(T,T+24 saat]` koşulu yeniden denetlendi. Bu hesaplar bağımsız
yangın olayının saha doğrulaması değildir.

Bitki örtüsü işi değişmedi. 10 Ekim 03:14 Türkiye saati süreç sorgusunda
üst süreç canlı, Mayıs kabul edilmiş ve Haziran hazırlanıyor. Önceki Ağustos
kabulüyle altı eğitim ayı kayıtlı; bu olay denetimi yeni EO isteği oluşturmadı.

## Sonraki adım

Uzun zincirler, ilk anda çok hücreli örnekler ve kalıcı sıcak kaynak yakınlığı
için gerekçeli vaka incelemesi gerekir. Örnekler bu işaretlerden seçildiğinde
temsil edici yangın örneklemi oldukları iddia edilmez. Olay kimliği, ilk hücre
politikası ve dönem kenarı dışlama kuralları dondurulduktan sonra doğrulama
sınırı kontrolüne ve nihai etikete geçilebilir. Bu sırada bağımsız özellik
birleştirme/eksiklik/sızıntı denetimi geliştirilebilir; unknown günler sıfır
etikete çevrilmez.
