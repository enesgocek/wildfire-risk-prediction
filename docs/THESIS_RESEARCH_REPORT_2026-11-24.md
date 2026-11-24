# Veri hazırlığı ve günlük sıralama araştırma raporu

24 Kasım 2026. Mevcut veri, yöntem, sonuç ve sınırlamalar 11 sayfalık
okunabilir bir PDF araştırma raporunda birleştirildi. Bu işlem, okulun
biçim şablonuna göre tamamlanmış resmî bitirme teslimi veya ana yangın
hedefinin bilimsel kabulü değildir. Önceki veri ve prototip paketi korunur.

## Kapsam ve somut katkı

Rapor; dört il/5 km/24 saat amacını, 44.082 anahtar ve 27 özellikten oluşan
deneysel paketi, kaynak üyeliği ile gerçek hedef ayrımını, 15 dinamik
alanlı dokuz sabit sıralama modelini ve 2022 keşif sonuçlarını birlikte
açıklar. Genel ve 1–3 gün karşılaştırmaları, kaynak örtüşmesi, düşük ve
yüksek sıralanan örnekler, yerel prototip ve açık bilimsel gereksinimler
aynı metindedir. Desteklenmeyen başarı/olasılık iddiası eklenmedi.

Literatür bölümündeki dört seçili çalışmanın yazar/yayın kimliği ve
kullanılan kapsamı birincil yayın veya yazar ön baskısı kayıtlarından
kontrol edildi: Apostolakis ve arkadaşları, Mesogeos, Next Day Wildfire
Spread ve Kiryo ve arkadaşları. Bu dört kayıt, önceki kapsamlı taramanın
yerine yeni bir sistematik tarama değildir. Çalışmaların deneyleri yeniden
çalıştırılmadı; kaynakların farklı hedef/örneklemlerindeki başarı değerleri
projenin başarısı olarak taşınmadı.

## Sayısal ve görsel kontrol

Tablolar önceki sohbet sayılarından kopyalanmadı. Hash ile sabit kaynak
dosyalar okundu; 44.082 özellik ve üyelik satırında sayım/eksiklik ve boş
Y/L, unknown gözlem, false negatif izin koşulları kontrol edildi.
675 mevcut ölçünün kazanım/eşitlik kredisi aritmetiği geri hesaplandı.
Ana karşılaştırmanın 12 ve kaynak örtüşmesinin altı aralık hücresi dokuz
ayardan ayrı kesir hesabıyla eşleşti. PDF'den çıkarılan sekiz tablonun
126 başlık/veri hücresi kaynak tabloyla ve dört yayın bağlantısı gerçek
PDF hedefleriyle eşleşti. Sayfa sınırları ve bölüm yerleşimleri kontrol edildi.

Son PDF, birlikte gelen Poppler ile 120 DPI'da 11 sayfa görüntüsüne
çevrildi. Her sayfa asistan tarafından ayrı açılıp metin, Türkçe karakter,
tablo, boşluk ve sayfa geçişi bakımından görsel incelendi. Bu, araştırmacının
yangın/örtü etiketi onayı değildir. İnceleme, PDF ve sayfa hash'lerine bağlıdır.

Word için gereken birlikte gelen LibreOffice bu Windows runtime'ında
bulunmadığından doğrulanmamış DOCX teslim edilmedi. PDF, birlikte gelen
Python/ReportLab ile üretildi; kullanıcının masaüstü Office kurulumuna
başvurulmadı. Düzenlenebilir içerik sürümü JSON olarak korunur. PDF kontrolü
eski yerel HTML arayüzünün görsel tarayıcı kontrolü sayılmaz.

## Çıktılar ve makbuzlar

Ana klasör:
`outputs/reports/dataset/thesis_research_report_v1/20261124T192159Z_4f479211`.
Son dosya `Orman_yangini_arastirma_raporu_2026-11-24.pdf`.
Kaynak metin `docs/research/thesis_report_content_2026-11-24.json`;
tablo, içerik ve sayfa inceleme kayıtları çıktı klasöründedir.

Üretim makbuzu SHA-256:
`7ca3f6cb5cafdc0956d94e516bed1d853d8bd5a571d7472abca03251c7353daa`.

PDF SHA-256:
`c9bd87290acd4ee44718dced3df220d3aca6e5cce34038c854576ae02fd02567`.

Ayrı denetim:
`thesis_research_report_audit_v1/20261124T192425Z_ed3be998`.
Makbuz SHA-256:
`f7f5dca86cb83a53603c35efb5ba55db590331308935081375cf36cc30ff1196`.

İlk üretimde yanlış grup adı, sonraki metin denetiminde satır sonu
normalizasyonu, ayrı denetimde tablo sayısı düzeltilmiştir. Başarısız
ara sürümler kabul edilmedi ve korunmuştur. Son kaynak kodunun lint/format
kontrolü geçti. Yeni model, tahmin, veri indirme, kapalı yıl erişimi,
risk sınıfı, etiket veya nihai birleştirme yoktur.

## Açık kalan konu

Bu rapor teslim metninin bilimsel içeriğini kullanılabilir hale getirir;
kaynak sırasının gerçek yeni yangın hedefine aktarımı, kaynak seçimi ve
gözlem desteği açığını çözmez. Nihai etiketli birleştirme için geçerli son
parça denetimi ve rapora bağlı araştırmacı onayı hâlâ yoktur. Okulun
zorunlu biçimi ve kişisel kapak bilgileri uydurulmamıştır. Mevcut yerel
paket yeniden üretilmeden rapor ayrı tamamlayıcı çıktı olarak korunur.
