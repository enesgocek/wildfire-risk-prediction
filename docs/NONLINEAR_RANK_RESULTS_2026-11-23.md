# Sabit XGBoost günlük sıralama deneyi — sonuç ve ayrı denetim

**Sonraki 23 Kasım kalite notu:** Aşağıdaki ilk modeller tam 15
alanlı geniş meteoroloji desteğiyle kuruldu; tam-alan ana profille
öğrenilmiş sayılmamalı. Mevcut meteoroloji kuralına ayrı kalite
uyumu ve aynı tam-alan çiftlerinde kıyas sonradan tamamlandı.
[Yeni sürüm, sonuçlar ve kaynak desteği](DATASET_SUPPORT_AND_WEATHER_REVIEW_2026-11-23.md).
Önceki deney dosyaları ve buradaki tarihsel sayılar korunuyor.

23 Kasım 2026. [Somut A önerisinin](NONLINEAR_RANK_PROPOSAL_2026-11-23.md)
ardından gelen devam talimatı, önerilen kapsamda ilerleme olarak
kaydedildi; kullanıcının harf olarak A yazdığı iddia edilmedi.
Geçmiş öneri dosyasındaki eğitim izni değiştirilmedi; ayrı
`configs/nonlinear_rank_execution_v1.json` oluşturuldu.

## Tamamlanan iş

Resmî Windows x64 XGBoost 3.4.1 wheel'i, önerideki SHA-256
zorunlu tutularak yerel `.venv` içine kuruldu. Proje bağımlılığı ve
`uv.lock` güncellendi; mevcut paket sürümleri yükseltilmedi.
Linux'a özgü NCCL kaydı çapraz platform kilidinde bulunur; Windows
deneyinde kurulmadı veya GPU kullanılmadı. Kurulu 136 paketin
uyumu ve kilidin çevrimdışı tutarlılığı kontrol edildi.

2018–2021 öğrenme / daha önce incelenmiş 2022 değerlendirmesi,
aynı 15 dinamik alan ve dokuz aday gruplama ayarı korundu.
100 ağaç, derinlik 3, hız 0,05 ve önerideki diğer parametreler
değişmeden uygulandı. Aynı hücre–ayda hem aday hem atamasız
tam-girdili gün içeren 938–1.160 grup / 28.068–34.887 satır
kullanıldı. Eksikler doldurulmadı; kimlik, ay ve konum girdiye
alınmadı. Kütüphane uygunluk kodu kaynak adayı var/yoktu;
gerçek Y/L alanları boş kaldı.

Dokuz model sırayla CPU'da tamamlandı. 900 saniyelik dış süreç
sınırı altındaki toplam çocuk süreç süresi **56,27 saniye**;
kurulum bu süreye dahil değil. Her ayarın model, öğrenme satırı,
skor ve kimlik makbuzu ayrı kaydedildi. Yeni parametre araması,
eski modelin yeniden eğitimi veya üretim ayarı seçimi yapılmadı.

## Ölçülen sonuç

Her sayı, aynı hücre ve ay içindeki kaynak/aday günü ile atamasız
günün skor sırasını ölçer. Eşit skora yarım puan verilir. Bu
**yardımcı çift AUC**, yangın AP'si, sınıflandırma doğruluğu veya
olasılık değildir. Aşağıdaki aralıklar dokuz ayrı ayardır; bağımsız
tekrarlar veya güven aralıkları değildir.

| 2022 incelemesi | Sabit eski doğrusal | Yeni XGBoost | Aynı ayarda yeni − eski |
|---|---:|---:|---:|
| Dört il, bütün aynı-hücre/ay çiftleri (5.733–6.406 çift/ayar) | 0,585685–0,595230 | 0,565731–0,609741 | −0,025847 ila +0,020137 |
| Dört il, 1–3 gün aralığı | 0,520107–0,541187 | 0,517364–0,569967 | −0,009300 ila +0,032324 |
| Ayrı Mersin takvimi, 2.329 çift/ayar | 0,522542–0,540575 | 0,553242–0,588235 | +0,029412 ila +0,055818 |
| Ayrı Mersin, 1–3 gün / 440 çift/ayar | 0,450000–0,465909 | 0,498864–0,564773 | +0,048864 ila +0,112500 |

Dört il genelinde yalnız 500 m gruplama ailesinin üç ayarında
artış var; diğer altı ayarda azalma var. Ayrı Mersin genelinde
dokuz ayarda da artış var. Mersin'de kaynak gününden sonraki
günlerle karşılaştırma hâlâ zayıf: yeni 0,482391–0,519462;
önceki günlerde yeni 0,598000–0,660400. Dört ilde sonraki günler
kesiti dokuz ayarın tamamında eski doğrusal modelden daha düşük.
Yalnız genel sayıyla güçlü günlük risk becerisi kabul edilmedi.

Somut örnek, önceden var olan **1 km/24 saat** ayarıdır; en iyi
model seçimi değildir. Ayrı Mersin'de 2.329 çiftin yeni skorunda
1.346 üstün sıra ve 9 eşitlik var: (1.346 + 9/2) / 2.329 =
0,579863. Eski skor 1.255 üstün sıra / 2.329 = 0,538858.
Yakın 440 çiftte yeni 0,551136, eski 0,461364. Bu kayıtlı günün
başka günden önce sıralanmasını anlatır; o günün gerçek yangın
olduğunu veya başka günün yangınsızlığını kanıtlamaz.

## Veri setine katkı ve açık kalan konu

Günlük ilişkilerin yalnız doğrusal bir modelle sınanması eksikliği
giderildi; doğrusal olmayan tek sabit yöntem farklı kaynakta daha
iyi, uydu adaylarında ise ayara duyarlı sonuç verdi. Bu, yöntem
ve sonuç bölümünde raporlanabilir bir bulgudur. Bir başarı eşiği
veya istatistiksel anlamlılık sonradan icat edilmedi; bağımlı
çiftlerden güven aralığı üretilmedi.

44.082 satırlık incelenebilir deneysel paket değişmedi. S/U üyelik
işaretleri, yeni olay/örtü kanıtı, PU seçimi/gürültüsü ve gerçek
hedef değerlendirmesinin yerine geçmez. 2022 daha önce görülmüş
keşif yılıdır; kör test değildir. Mersin kaynağının konum, saat ve
kayıt kapsamı belirsizliği sürüyor. Çift sayısı bağımsız yangın
sayısı değildir. Yeni Y/L, negatif etiket, 2023–2025 bilimsel
değeri, risk rengi veya nihai etiketli birleştirme yok.

Sıradaki bağımsız iş yeni modeller çoğaltmak değil; veri/yöntem
taslağını bu tamamlanmış bulgularla somutlaştırmaktır.
[Teslimde kullanılabilecek yöntem taslağı](research/DATASET_METHODS_DRAFT_2026-11-23.md)
hazırlandı. Ana yöntemin üç bilimsel geçiş koşulu hâlâ açık;
inceleme paketinin teknik tamamlanması bilimsel kabul sayılmadı.

## Denetim ve tekrar üretim

- Yeni yedi davranış testi dahil **40 ilgili test** geçti;
  beş yeni Python dosyası Ruff kod/biçim kontrolünden geçti.
- Ayrı denetleyici dokuz modeli yeniden yükledi; her birinde
  100 ağaç, CPU, 15 alan ve sabit parametreleri doğruladı.
- Öğrenme satırları bağımsız Kartezyen çift yapımıyla eşleşti;
  2022'deki çift kimlikleri eski doğrusal listeyle birebir aynı.
- İki takvimdeki yeniden tahminler kayıtlı skorlarla tam eşleşti;
  bütün **4.420** zaman/il/hücre sonuç satırı ayrı tamsayı
  üstünlük/eşitlik hesabıyla eşleşti. Denetimde yeni fit yok.
- Yerel SQLite yedeklendi; MLflow'a kaydedilen **252** özet ölçü
  tam olarak geri okundu. Hücre ayrıntıları ayrıca dosyada kaldı.
- Grafik görsel olarak incelendi; bütün ayarlar ve iki takvimin
  genel/yakın gün sonuçları birlikte gösteriliyor.

Üreticiler: `scripts/quality/run_nonlinear_rank_comparison.py`,
`audit_nonlinear_rank_comparison.py`, `close_nonlinear_rank_comparison.py`.
Ortak giriş/koruma: `src/wildfire_risk_prediction/nonlinear_rank.py`.

| Kayıt | `outputs/reports/dataset/` altındaki dizin | `readback.json` SHA-256 |
|---|---|---|
| Deney | `nonlinear_rank_run_v1/20261123T132502Z_6193ac44` | `4b7222cf8d2dff9d3ac8c38f15292fc30366eeec391b83927ff84e23c125dc30` |
| Ayrı denetim | `nonlinear_rank_audit_v1/20261123T132823Z_4615965f` | `7fec3cb7f12f9359a1fad01c01e466222408201bcde33e7842df6cdd197d9566` |
| Kapanış | `nonlinear_rank_closure_v1/20261123T133013Z_64470446` | `f291058ddfbbbcc486bba01e128eae9c53cc600eede33161e74569835a3db466` |

MLflow kimliği `a11924a0827440af824d668706ddadad`; yalnız yerel.
Kapanış dizininde `temporal_summary.csv`, bütün kesitler için
`comparisons.csv` ve `fixed_rank_comparison.png` var. Makbuzların
girdi/üretici/çıktı hash'leri deneyle bağlı; eski dosyalar düzeltilmedi.
