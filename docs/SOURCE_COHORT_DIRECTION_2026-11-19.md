# Mersin kaynak havuzu: ölçülen kapsam ve yöntem seçeneği — 19 Kasım 2026

Bu devamın amacı, açık kaynak aramasını belirsiz süre uzatmak yerine mevcut
arşivle yapılabilecek bir sonraki yöntemi somutlaştırmak. **Birinci aşama
tamamlanmadı.** Aşağıdaki sayılar etiket veya gerçek yangın sayısı değil;
aynı yayımlanmış arşivin 2018–2022 dönemindeki 424 kaynak satırına aittir.
2023 kalibrasyon, 2024 karşılaştırma ve 2025 final değerleri hesaba alınmadı.

## Tamamlanan iş ve sonuç

Daha önce yalnız kimlik/yılla dondurulan 424 satırın tamamı korundu. İlk
10 satırlık sonuçtan bağımsız kontrol örneklemi değiştirilmedi. Yeni tablo,
bu örneklemin yerine geçen bir değerlendirme örneklemi değildir. Coğrafi ve
saat dosyalarındaki anonim kimlikler ortak olay anahtarı sayılmadı; tarih,
yıl, ilçe ve nihai alanın tekil birleşimi yalnız geçici bağlantı olarak
kullanıldı. Nihai alan model girdisi veya örnek seçme ölçütü yapılmadı.

| Kontrol | Kaynak satırı | Anlamı ve sınırı |
|---|---:|---|
| Dondurulmuş 2018–2022 havuzu | 424 | Yıllara göre 71 / 90 / 84 / 88 / 91; bağımsız yangın envanteri değil |
| Yayımlanan koordinat QC alanı geçiyor | 422 | Kaynak alanı; gerçek başlangıç konumu doğrulaması değil |
| Nokta Mersin içinde ve tek proje hücresinde | 403 | En yakın hücreye zorlama yok; kaynak konumunun rolü bilinmiyor |
| Saat tablosuyla tekil geçici imza bağlantısı | 418 | Fiziksel olay eşitliği veya saat standardı doğrulanmıyor |
| UTC ve Türkiye saati yorumları aynı 24 saatlik pencereye düşüyor | 402 | Saatin ilk uydu tespiti olduğu doğrulanmıyor |
| Tek hücre + tekil bağlantı + iki yorumda aynı fit penceresi | 381 | Yalnız metadata aktarılabilirliği; L veya Y uygunluğu değil |
| WF1538'in önceki dışarıda tutma kararı ayrıca korununca | 380 | Karar geri alınmadı; hiçbir satıra L atanmadı |

424 satırın birbirini dışlayan tanı grupları: **21** tek hücreye
aktarılamıyor; kalanlarda **6** tekil saat bağlantısı yok ve **16** iki saat
yorumunda farklı günlere düşüyor. **381** satır metadata bakımından
aktarılabilir; bunlardan WF1538 ayrıca atamasız tutuluyor. 21+6+16+381=424.
Bu sıralı tanı, eksikleri silmek veya kabul edilmiş bir eleme kuralı değildir.

Somut örnek: WF1198'in bildirilen tarihi 29 Mayıs 2018. İki saat yorumu
hedef penceresinin başlangıcını 28 veya 29 Mayıs UTC yapıyor. Uydu sonucu
hangisine uyuyor diye saat seçilmedi. İki olasılık birlikte saklandı.
İlk uydu tespitinin gerçek zamanı bu kaynak saatinden üretilmedi.

380 satır **374 farklı koşullu hücre-gün** veriyor. Beş hücre-gün birden
fazla kaynak satırı taşıyor; bu ne aynı fiziksel yangın olduklarını ne de
ayrı yangın olduklarını kanıtlar. Kayıtlar birleştirilmedi/silinmedi. Kaynak
konumunun anlamı ve toplam hata sınırı, olay birimi, kayıt kapsamı, yerel
orman/çalılık bağlamı ve ilk uydu tespitiyle zaman ilişkisi açık kalıyor.

## Bu devamda yeni görsel kaynaklardan ne elde edildi?

[Bakanlığın Çile/Menderes duyurusu](https://www.tarimorman.gov.tr/Haber/4674/Mendereste-Yanginin-Ciktigi-An-Ihalarca-Goruntulendi)
yeniden özgün medya açısından incelendi. Alınan HTML'de olay videosu
bağlantısı elde edilmedi; görünen YouTube bağlantısı genel kurum kanalı.
Sayfadaki özgün görsel isteği HTTP 401 döndü. Bu erişim sonucu, belgenin
yanlış veya medyanın kalıcı olarak yok olduğu anlamına gelmiyor. Önceki
üçüncü taraf videonun tarih uyuşmazlığı çözülmedi; özgün video alınmış sayılmadı.

[Orman Mühendisleri Odası saha raporunun](https://www.ormuh.org.tr/files/2025/09/05/2_opbk_yangin_ulkemizin_akdeniz_ve_ege_bolgelerinde_20_temmuz_12_austos_2021_tarihleri_arasnda_meyda.pdf)
20–24. PDF sayfalarındaki erken görüntülerden kullanılabilir yeni başlangıç
kanıtı araştırıldı. Güvercinlik görüntüsündeki telemetri daha okunur hale
getirildi; koordinatın uçak mı yer hedefi mi olduğu, datum ve boylamın
kırpılmış yarımküre işareti doğrulanmadı. Donmuş koşullu koordinat yorumu
proje AOI'sine düşmedi. 22–31 Temmuz 2021 katalog bağlamında önceden
belirlenen 500/1.000/2.000 m çevrelerde eşleşme yok; alan sonuca göre
genişletilmedi. Bu sıfır sonuç yangın yokluğu/negatif etiket yapılmadı.
Armutalan görüntüsündeki koordinat güvenilir okunamadı. Yeni ham indirme,
özel giriş, yazışma veya bulut işi başlatılmadı.

## Araştırmacı kararı için iki somut yön

**A — Kaynak koşullu, hata içerebilen üyelik pilotu taslağı hazırlamak
(öneri).** Mersin'in yukarıdaki 380 kaydını olası bir kaynak havuzu olarak
ele alacak, yayımlanmış merkez hücrelerinin bağımsız başlangıç doğrulaması
olmadan kullanılmasının etkisini açıkça sınayacak ayrı protokol hazırlanır.
374 koşullu hücre-gün otomatik L/Y olmaz. Konum/zaman alternatifleri,
aynı anahtardaki kayıtlar, yerel örtü ve kaynak seçimi ayrı sınanır;
uydu eşleşmesi olanları seçerek pozitif havuz zenginleştirilmez. 43 metadata
sınırı olan kayıt ve WF1538 korunur. İnceleme sonucunda yeterli dayanak
çıkmazsa bu kaynak yolunun kullanılamadığı da kabul edilebilir sonuçtur.

Bu yönün yararı tekil haber aramaları yerine ölçülebilir bir yöntem
sorusuna geçmektir. Bedeli, kaynak noktası/günü hatasının PU'nun öğrenme
varsayımlarını sağlayabileceğini ayrıca gerekçelendirme gereğidir. Kaynak
havuzunun gerçek pozitifçe zenginliği, L/U sınıf koşullu dağılım ilişkisi,
gürültü oranları ve bağımsız değerlendirme dayanağı henüz bilinmiyor.
Hatalı pozitiflere izin veren bir yöntem bu eksikleri kendiliğinden
çözmez. Dört ile genellenebilirlik veya kalibre yangın olasılığı sözü verilmez.

**B — Tekil dış eşleşme ölçütünü korumak.** Salur/Marmaris benzeri
ayrı olay ve konum kanıtı bulunan vakalar için olası L önerisi hazırlanır;
381 sayısının tek başına yeni üyelik gerekçesi olmadığı kabul edilir.
Kaynak anlamı açısından daha temkinlidir; kullanılabilir açık olay
kanıtı gelmezse mevcut az sayıdaki öneriyle bilimsel ilerleme sınırlı kalır.
Mevcut kaynakları yeniden saymak bu bilgi açığını kapatmaz.

Önceki araştırmacı kararları hata içerebilen PU girdisi hazırlığını ve
**tekil** Salur/Marmaris önerilerini kapsıyor. Buradaki A, yayımlanmış
merkeze dayalı daha genel bir kaynak kullanımı yönüdür; önceki kararların
otomatik genellemesi yapılmadı. **Yön seçimi bekleniyor.** Her iki seçenek
de ana 24 saatlik hedefi korur; eğitim, 0/1 etiket, nihai yöntem kabulü
veya birleştirme onayı değildir. Bağımsız değerlendirme açığı sürer.

## Teknik kontrol ve izlenebilirlik

Yeni hazırlayıcı ve mevcut kaynak örnekleyicisinin **29 davranış testi**,
Ruff ve biçim kontrolü geçti. Testler anonim kimlik farkı, tekil olmayan
bağlantı, gece yarısı sağ uç, farklı saat günleri, fit sınırı, dış/QC
konumları, ortak hücre sınırı, WF1538 kararı ve yinelenen hücre-günleri
kapsıyor. Ayrı standart-kütüphane saat hesabı ve mekânsal indeks kesişimi
424 satırın gün/hücre sonuçlarıyla uyuştu; aynı geometri kütüphanelerini
kullanan bu geri okuma bağımsız saha/kurum doğrulaması değildir.

- Üretici: `scripts/quality/prepare_source_cohort_options.py`.
- Sonuç: `outputs/reports/dataset/source_cohort_options_v1/20261119T195538Z_02488a97/readback.json`;
  SHA-256 `849f0ef0ad8af1ed88eac2418ddf5c2026db0910a7a852760b710a8821387a06`.
- Aynı klasörde `closure_verification.json`;
  SHA-256 `76b518232411b4c0b3645be4135b3ca2b900f33ad505b18020d22df29b36c55f`.
- Medya makbuzu: `outputs/reports/dataset/primary_fire_media_v1/20261119T193914Z/intake_closure.json`;
  SHA-256 `9bb16a420df0c93cbe11c1f021b2000da3bdf5765afc9ad033397935d74c8bf5`.
  12 yeni yerel dosya kimliği, eski saha PDF kimliği ve başarısız erişim
  ayrımı saklandı. Görsel okuma asistana ait; insan onayı değil.
- Dondurulmuş kaynak anahtarları, 10'lu örneklem, iki olası L'nin gerçek
  CSV dosyaları/inceleme dizini, 2.048 U ve WF1538 karar makbuzu hash ile
  korundu. Ham veri, rapor çıktısı ve görüntüler Git'e eklenmedi.

Yeni L/etiket: **0**. Bütün 424 kaydın üyeliği `review_unassigned`, hedefi
boş. Günlük gözlem `unknown`; pozitif/negatif izinleri kapalı. Ana veri
ayrımı, kapalı final test, eğitim ve rapora bağlı nihai birleştirme kapısı
değişmedi. Bu teknik paketin tamamlanması birinci aşamanın kabulü değildir.
