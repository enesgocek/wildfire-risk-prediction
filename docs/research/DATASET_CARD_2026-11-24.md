# Deneysel S/U veri kartı

24 Kasım 2026. Yerel araştırma ve inceleme sürümü; gerçek yangın etiketli
eğitim veri seti kabulü değildir. Araştırma amacı dört ilde sonraki 24
saatlik yeni orman/çalılık yangınıdır. Bu kart mevcut sürümü tanımlar.

## Birim, kapsam ve kaynaklar

Antalya, Muğla, İzmir ve Mersin için 5 km projeksiyon hücresi ve
00:00 UTC tarih anahtarı kullanılır. Hazırlık havuzundaki 2.889 hücrenin
tam nüfus paneli yerine, kaynak/aday bağlamıyla seçilmiş hücre–ay
takvimlerinden oluşan **44.082 farklı hücre–gün / 822 hücre** vardır.
37.509 satır 2018–2021, 6.573 satır keşif amaçlı 2022 rolündedir.
Bu seçimden genel saha sıklığı veya yangın olasılığı hesaplanamaz.

27 özellik: 11 ERA5-Land meteoroloji özeti, 12 arazi/örtü özeti ve
dört geçmiş NDVI/NDMI özeti. CGLS 2017 ana örtü bağlamı; CORINE 2018
yardımcı incelemedir. Hücrenin örtüsü ile yangın adayının yerel örtüsü
ayrı değerlendirilir. İnsan görsel notları sınırlı örnekler içindir.
Tam alan adları, Türkçe anlamları ve birimler `data/feature_dictionary.json`
içindedir. Kaynak/zaman/kalite izi `data/provenance.csv` içinde korunur.
ERA5-Land geriye dönük yeniden analizdir; canlı tahmin girdisi sayılmaz.

## Üyelik ve belirsizlik

`data/features.csv` yalnız anahtar ve özellikleri içerir. Ayrı
`data/inspection_memberships.csv`, dokuz ayar için S önerilerini ve
inceleme rollerini tutar. Dokuz ayar 500/1.000/2.000 m ile 24/48/72
saat gruplama duyarlılığıdır; ana hedef penceresini 72 saate çevirmez.
1.670 anahtar en az bir S önerisinde, 412 anahtar ayara duyarlıdır.
S sayısı bağımsız yangın veya doğrulanmış pozitif sayısı değildir.
Atamasız U günleri gerçek negatif değildir; eski rastgele U ağırlıkları
bu koşullu takvime taşınmamıştır.

`target` ve `accepted_L_membership` boş,
`daily_observation_status=unknown`, `negative_label_permitted=false`.
İlk uydu tespiti gerçek tutuşma zamanı veya kesin olay kimliği değildir.
Kaynak kayıtlarının zaman/konum/kapsam belirsizlikleri sürmektedir.
Özellik ve üyelik parçaları bu teslimde ayrı dosyalar olarak korunur.

## Eksiklik ve kullanım desteği

41.358 satırda 27 özellik tam; 2.724 satırda en az bir eksik vardır.
Eksikler sıfırla doldurulmaz. 15 dinamik alanla puanlama için ayrıca
önceden tanımlı tam-hücre meteoroloji desteği aranır. Dolu değer,
otomatik olarak tam alan gözlemi demek değildir.

Prototip yalnız iki mevcut 2022 takvimini gösterir: dört-il takvimi
6.573 kayıt / 4.841 puanlanabilir kayıt; ayrı Mersin kaynak takvimi
2.383 / 1.929. İki takvim 245 anahtarda ortak; toplam 8.956 üyelik,
8.711 farklı hücre–gündür. Bunlar 44.082 satırdan farklı inceleme
rolleridir. Dört-il takvimine ayrıca Mersin il filtresi uygulanınca
2.038 kayıt görülür; bu ayrı Mersin takvimiyle aynı seçim değildir.
İl alanları hücrenin il geometrisiyle kesişimidir; örtüşebilir.

## Ayrım, izin ve açık konular

Mevcut küçük deneylerin öğrenmesi 2018–2021, incelenmiş değerlendirmesi
2022'dir. Genel araştırma planındaki 2023 kalibrasyon / 2024 karşılaştırma
/ kapalı 2025 final rolleri bu paket çalışmasında açılmamıştır.
2022 kör final test değildir. Kaynak/uydu üyeliğinden yeni gerçek yangına
aktarımı, seçim/gürültü varsayımları ve yeterli gözlem dayanağı açık kalır.

Yerel teknik paket; etiket kabulü, doğrulanmış AP/olasılık, canlı uyarı
veya tüm hücrelerde risk yayımlama izni sağlamaz. Nihai etiketli birleştirme
ayrı güncel parça denetimi ve rapora bağlı kullanıcı onayı gerektirir.
Paketin hazırlanması veri lisanslarının yeniden dağıtıma izin verdiğinin
incelendiği anlamına gelmez; burada dış veri yayını yapılmamıştır.

Kaynak sürüm: `experimental_SU_inspection_v2/20261123T102954Z_6d6e52c1`;
makbuz SHA-256 `86270dea5d9d12a1764ead780dcfa79166bed60a0977bf712e3df497d84bc366`.
Kaynaklar ve dosya hash'leri yerel teslim manifestinde ayrı listelenir.
Yapay zekâ katkısı [katkı kaydında](AI_USE.md) açıklanır.
