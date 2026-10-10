# Hedef kabul hazırlığı ve gün geçişleri — 10 Ekim 2026

## Çalışan işler sürerken bağımsız kontrol

Çalışma mevcut yerel dosyalarla ve ağ bağlantıları engellenerek yapıldı.
Yeni indirme, uzun kuyruk veya model eğitimi başlatılmadı. Canlı GCP ve
bitki örtüsü kodları değiştirilmedi. Eski ürün ve kabul raporları korunarak
yeni denetimler `outputs/reports/dataset/` altında ayrı dizinlere yazıldı.

## Özellik birleştirmesinde gün geçişleri

[İlk birleştirme](FEATURE_JOIN_PILOT_2026-10-10.md) 1 Ağustos 2018'i
kapsıyordu. Aynı kaynak kabul ve sütun sözleşmesi 8, 9 ve 31 Ağustos'ta
ayrıca çalıştırıldı. Destekli satırlarda sırasıyla 8 Ağustos kesimi/sıfır
gün yaş, aynı kesim/bir gün yaş ve 29 Ağustos kesimi/iki gün yaş kullanılır.
Desteksiz hücreye kesim veya değer uydurulmaz.

| Gün | Hücre-gün | 30 günlük destek | 60 günlük destek |
|---|---:|---:|---:|
| 1 Ağustos — önceki kabul | 2.899 | 2.896 | 2.896 |
| 8 Ağustos — kesim günü | 2.899 | 2.896 | 2.896 |
| 9 Ağustos — ertesi gün | 2.899 | 2.896 | 2.896 |
| 31 Ağustos — ay sonu | 2.899 | 2.894 | 2.896 |

Dört günde toplam 11.596 farklı hücre-gün ve her satırda 27 aday özellik
geri okundu. Son gün kısa pencerenin beş eksik hücresi, uzun pencerenin
üç eksik hücresinden bağımsız korundu. Bu, bütün ay veya bütün dönem
birleştirmesi değildir; aday sütunlar nihai model seçimi değildir.

Yeni raporlar `outputs/reports/dataset/feature_join_v1/` altında:

- `20261010T120945Z_c66a13c1/readback.json` (8 Ağustos), SHA-256
  `e413d28fbb2da46524f0a11ea022766be5d71976d423681fdeb226a76f496519`.
- `20261010T120947Z_b843472f/readback.json` (9 Ağustos), SHA-256
  `007887f69e0eafe580f4e83043f0bddf2c1a6257d02da101c0695620aaf3c778`.
- `20261010T120949Z_b9f7fdfa/readback.json` (31 Ağustos), SHA-256
  `7b2e544a9e8ce1789c5623adaf18d1eb16abcf2a8d52c74217edba35e11006e0`.

## Etiket kabulünde mevcut kapılar

Yeni `target_admission.py` şu anki bilimsel durumu kodla ifade eder.
Bu bir kabul edilmiş etiketleme yöntemi değildir; mevcut etiket kabulünü
kapalı tutan sürümlü bir denetimdir. Çağıranın `observed=true` benzeri
işareti veya sıfır olay eşleşmesi kapıyı açamaz. İleride gerekçeli kabul
sağlanırsa yeni sürüm/kanıt kaydı gerekir.

| Bekleyen karar/kanıt | Mevcut durum | Etikete etkisi |
|---|---|---|
| Kaynak Type anlamı ve üretim sürümü | Teknik teyit açık | Seçilmiş adaylar kesin yangın doğrusu sayılmaz |
| Nihai olay tanımı | Keşif kümeleri; senaryo seçilmedi | Küme kimliği nihai olay kimliği değildir |
| İlk hücre politikası | İlk anda çok hücreli örnekler açık | Canonical hücre otomatik hedef hücresi seçilmez |
| Habitat kapsamı | Ön inceleme; nihai karar yok | Bütün hücreler otomatik orman kabul edilmez |
| Negatif gözlem politikası | unknown; izin false | Tespit yokluğu veya eksik gözlem 0'a çevrilmez |

Bu sürüm hem 0 hem 1 hedef atamalarını reddeder; nullable hedef alanı
yalnız boş kalabilir. Bu geçici kabul engeli, araştırma hedefinden
vazgeçildiği veya ileride pozitif etiket üretilemeyeceği anlamına gelmez.
Kalan uydu işleri bu bilimsel kapıların her birini kendiliğinden kapatmaz.

## Zaman ve veri ayrımı kontrolü

Hedef `(T,T+24 saat]`; tam gece yarısı tespiti önceki T'ye düşer. Bir
nanosaniye sonrası yeni günlük pencereye düşer. UTC biçimi ve nanosaniye
aritmetiği açık kontrol edilir. 2018 öncesine düşen T veya dahil sağ ucu
2024'e ulaşan eğitim penceresi inceleme işareti alır. Sağ ucun sınırla
eşit olması da önemlidir; hedef penceresi o anı içerir.

Bu işaret otomatik dışlama/embargo kararı değildir. Dönem kenarı kuralı
henüz seçilmedi; kayıt görünür tutulur. 2024/2025 tespitleri bu denetimde
okunmaz. Önerilen olay kimlikleri için train/validation arasında ortak
`event_id` reddeden kontrol de eklendi; bu kontrol sentetik örneklerde
sınandı, gerçek nihai olay kimlikleri henüz yok. Final test kimlik
girdisi bu yardımcıda da reddedilir.

## Gerçek katalog geri okuması ve sınırı

Önceki [olay gruplaması kabulünün](EVENT_GROUPING_REVIEW_2026-10-10.md)
SHA-256 kimliği doğrulandı; dokuz CSV mevcut kayıtlı hash'leriyle okundu.
Her senaryoda bütün kümeler ve ilk hücre listeleri korundu; 0/1 ataması
sıfır, seçilen senaryo null kaldı. Her senaryoda bir eğitim penceresi
sınır incelemesi var. Dokuz senaryo örtüşür; bu sayı dokuz farklı olay
veya doğrulanmış yangın sayısı olarak toplanamaz.

Kabul raporu:
`outputs/reports/dataset/target_admission_v1/20261010T121239Z_ce73888e/readback.json`;
SHA-256 `3e597acd1c8349c2fc486eefe785d469b6e93b75e98e0a72fb085a670a989e01`.
15 girdi/kod dosyasının hash'i değişmedi. Yeni CSV'lerden hedefin boşluğu,
küme/ilk hücre eşitliği ve ilk tespitin sağdan kapalı 24 saat penceresine
aitliği ayrı geri okundu. Ham uydu veya bağlantı grafiği yeniden hesaplanmadı.

16 yeni kontrol dahil **54 ilgili test** geçti; deprecation uyarıları hata
sayıldı. Ruff/biçim kontrolü geçti. Testler gece yarısı/nanosaniye,
dönem kenarı, kapalı test, sahte izin, sıfır eşleşme ve split ortak olayını
sınar. Bunlar bilimsel olay/saha doğrulaması değildir.

```powershell
.\.venv\Scripts\python.exe scripts/quality/audit_target_admission.py
```

Sonraki araştırma işi, kayıtlı zincir/ilk hücre örneklerini gerekçeli vaka
incelemesiyle değerlendirmek ve uzman/yardımcı kaynak teyidi kapsamını
belirlemektir. Nihai etiket üretimi bu kabulleri bekler; özellik hazırlığı
ve oturum sonuçlarının geri okuması bağımsız sürdürülebilir.
