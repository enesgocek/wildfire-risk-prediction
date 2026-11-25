# Aşama geçiş değerlendirmesi ve sonraki somut iş — 25 Kasım 2026

## Karar dosyasının sonucu

Birinci aşamanın **deneysel teknik hazırlığı ve yerel prototipe geçişi
tamamlandı**. Bunun dayanağı araştırmacının 23 Kasım açık A kararı ve
tamamlanmış veri/model/arayüz çalışmalarındadır; bu belgede yeni bir onay
verilmiş sayılmaz. [Kayıtlı çalışma yönü](RESEARCH_TRANSITION_DECISION_2026-11-23.md).
Ana 24 saatlik yeni orman/çalılık yangını hedefinin bilimsel kabulü ise
tamamlanmadı. Önceki sohbetlerde tek başına “hâlâ birinci aşamadayız”
denmesi bu iki durumu yeterince açıklamıyordu. Teknik geçiş kararı tekrar
sorulmayacak; açık bilimsel koşullar da tamamlanmış gibi gösterilmeyecek.

| Çıktı/iddia | Güncel sonuç | Gereken sonraki dayanak |
|---|---|---|
| Deneysel özellikler ve ayrı S/U inceleme paketi | Hazır: 44.082 anahtar, 822 hücre, 27 alan | Yeni kapsam açılırsa yeni sürüm; nihai etiketli tablo sayılmaz |
| Sabit yöntemle kaynak-bağlam günlük sıralaması | 2018–2021 öğrenmesi ve incelenmiş 2022 sonuçları var | Başka yıla/örnekleme aktarım ayrıca sınanabilir |
| Haritalı araştırma prototipi ve rapor | Teknik teslim mevcut | Okul biçimi ve nihai sunum düzeni ayrıca uyarlanır |
| Gerçek yeni orman/çalılık olayının kabulü | Açık | Konum/zaman/yerel örtü ve olay tanımının gerekçeli protokolü |
| PU varsayımlarından gerçek yangın riskine aktarım | Gösterilmiş değil | Seçim/gürültü varsayımlarının gerekçesi ve yeterli sınama |
| Gerçek yangın AP/olasılık başarımı | Gösterilmiş değil | Uygun hedef referansı ve değerlendirme örneklemi |

Ana hedef korunur; tamamlanmış sonuç, koşullu kaynak-bağlam sıralaması
araştırmasıdır. Kırmızı/sarı/yeşil veya yüzde kullanmamak bilimsel açıkları
ortadan kaldırmıyor. S/U yöntemini incelemek için her kaydın kusursuz olması
istenmiyor; araştırma varsayımları ile doğrulanmış bilgi ayrı tutuluyor.

## Yeni kaynak incelemesinin bu karara etkisi

[92 kayıtlık pilot](MESOGEOS_REFERENCE_RESULTS_2026-11-25.md) ve
[32 farklı kaydın incelemesi](MESOGEOS_CANDIDATE_REVIEW_2026-11-25.md)
tamamlandı. 32 durumda beş kaynak kaydı iki saat/dokuz yakın geçmiş
ayarında ve hedef gününde kararlı koşullu öneri verdi. Bu az sayıdaki
öneri, tek başına dört ilde olay kabulünü, gözlem yokluğunu veya PU
varsayımlarını doğrulamıyor. Mesogeos'un uydu kökeni bağımsız saha
doğrulaması yerine konulamaz. Beş öneri eski ana S/U'ya eklenmedi.

Bu nedenle aynı kaynağı tekrar indirmek, aynı 2022 alt kesitlerini
çoğaltmak veya daha iyi çıkan küçük model aramak bu geçiş dosyasının
önerisi değildir. Yeni işin yanıtlayacağı soru baştan belli olmalıdır.

## Bu devamda tamamlanan teknik hazırlık

Sekiz önceki tamamlanma makbuzu güncel SHA-256 ile eşleşti: deneysel S/U,
ana model koşusu, FWI karşılaştırması, kaynak örtüşmesi, Mesogeos pilot
denetimi, 32 kayıt hazırlığı/denetimi ve eski özellik dizini. Dokuz mevcut
`ranker.json` dosyasının hash'i ana model makbuzuyla eşleşti. Modeller
yüklenmedi, tahmin yapılmadı. 15 dinamik alan sırası makbuzdan sabitlendi.
Bu kimlik kontrolü eski bütün deneylerin veya beş nihai veri parçasının
yeniden denetlenmesi değildir; eski test sayıları güncel test diye yazılmadı.

Yalnız donmuş metadata dizininde özellik günleri:

| Yıl | Özellik günü |
|---|---:|
| 2018 | 365 |
| 2019 | 365 |
| 2020 | 366 |
| 2021 | 365 |
| 2022 | 365 |
| 2023 | 365 |
| 2024 | Bu dizinde yok |

Bu, tüm diskin/sağlayıcıların envanteri değildir. Eski birleşik FIRMS
CSV'sinin yalnız tek başlık satırı okundu; dosya boyutu kaydedildi.
2024 tarih dağılımı, aday sayısı, konum/kalite değerleri veya model sonucu
okunmadı. Dosya adındaki 2024, kullanılabilir bir değerlendirme paketi
olduğunun kanıtı sayılmadı. `body_read=false` makbuzda korunur.

## Yeni yöntem önerisi: önce 2024 uygulanabilirliği

**Öneri A:** şimdiye kadar bilimsel değerleri kapalı tutulan 2024'te,
aynı kaynak-bağlam yönteminin ayrı yıl sınamasının hazırlanabilirliğini
incelemek. Yeni yıl erişimi, önceki yalnız 2018–2022 inceleme kapsamından
farklı olduğu için araştırmacı kararı gerekir. Somut kapsam
`configs/2024_source_replication_feasibility_proposal_v1.json` içindedir;
`execute_authorized=false` olarak hazırlandı.

İlk iş en fazla 900 saniye, yerelde ve indirmesizdir. İzin verilirse
2024 katalog alanları, dört il kapsamı ve eski tip/güven kurallarıyla
veri/kalite desteği incelenir; kaynak ve gerekli özellik girdilerinin
hazır/eksik durumu raporlanır. Diğer yıllar tarih metadata'sında süzülmeden
konum/kalite değerleri açılmaz. Bu ilk iş yeni öğrenme, tahmin, S/Y/L,
negatif etiket, kalibrasyon, ücretli kaynak veya nihai birleştirme içermez.
Eksik veri bulunursa sessizce indirme/ücret veya başka kaynak başlatılmaz;
gerekli somut edinim ve hesap kapsamı hazırlanır.

Sonraki olası ayrı yıl sınamasının yöntemi sonuç görülmeden sabitlendi:

- Dokuz ana model ve 15 alan aynı kalır; öğrenme 2018–2021 olarak korunur.
  2022 sonuçlarına göre yeni üretim ayarı veya hiperparametre seçilmez.
- Aynı hücre/ayda kaynak-bağlamlı gün ile atamasız gün karşılaştırılır.
  Genel, 1–3 gün ve önce/sonra kesitleri birlikte raporlanır; eksik desteğe
  sıfır başarı veya gerçek negatif yazılmaz.
- Yeni Mesogeos önerileri yönteme sessizce eklenmez. Kaynak/örtü/başlangıç
  kuralları değişecekse ayrı sürüm ve gerekçe gerekir.
- 2023'ten geçmiş bağlam veya özellik gecikmesi gerekirse bu ilk kapsamın
  dışında kalır. Yıl başı eksik geçmişi sınır incelemesinde tutulur;
  2023 kalibrasyon rolü veya 2025 final kapısı açılmaz.
- 2024 sonucu görülmesi onu ileride kör final diye sunmaya izin vermez.
  2025 final kapalıdır. Mevcut araştırma zaten 2022'yi birçok kez inceledi;
  yeni yıl sınaması, aynı kesitte sonuç aramadan zamansal aktarımı sınayabilir.

**Bu sınamanın yanıtlayacağı soru**, kaynak-bağlam ayrımının ayrı yılda
hazırlanabilir ve sonra tekrarlanabilir olup olmadığıdır. Kaynak/uydu
etiketinden gerçek yangın riskine aktarımı tek başına doğrulamaz. Daha
yüksek 2024 sayısı üç bilimsel kapının otomatik açılması olmayacaktır.

**Alternatif B:** 2024'ü kapalı tutup mevcut onaylı araştırma teslimiyle
çalışmak. Veri/model/prototip/rapor kaybolmaz; ayrı yıl genellemesi
gösterilmemiş kalır. Bu, önceki prototip A kararını tekrar sormak değildir;
karar yalnız yeni bilimsel yıl erişimi ve sınamanın kapsamıdır.

## Zaman ve yürütme durumu

25 Kasım'da 26–29 Kasım karar aralığı henüz geçmedi; tahmini 1 Ocak'a
37 takvim günü var. Teknik kapanış ve bilimsel açıklar bu dosyada
netleştirildi. Ayrı yıl hazırlığının süresi mevcut girdilere bağlı;
900 saniye yalnız ilk uygunluk incelemesinin sınırıdır, tüm 2024 veri
hazırlığının süre vaadi değildir. Şu an yeni yıl erişim kararı yok.

Yeni makbuz: `outputs/reports/dataset/stage_transition_review_v1/20261124T235727Z_04796a5a/readback.json`.
SHA-256: `df45ac450e854a0e1db83f40308b621aed48d36be1fa3405ce8883d0a267446a`.
Üretici `scripts/quality/prepare_stage_transition_review.py`; metadata ve
girdi kapanış kontrolü geçti, Ruff/biçim geçti. Yeni model/yıl sonucu,
veri etiketi, dış iletişim veya nihai birleştirme üretilmedi.
