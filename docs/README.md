# Belge dizini ve proje mimarisi

Güncelleme: 16 Ekim 2026. Güncel ilerleme, bilimsel yöntem, işlem rehberi ve
tarihsel kayıtların görevleri aşağıda ayrılmıştır. TÜBİTAK belirli bir Git
klasör şeması zorunlu kılmaz; bu düzen araştırmanın izlenebilirliği için seçilmiştir.

## Temel belgeler

| Belge | Sorumluluk |
|---|---|
| [STATUS.md](STATUS.md) | En son tarihli ilerleme, kanıt sınırları ve sıradaki iş |
| [İlk hücre karar seçenekleri](EVENT_FIRST_CELL_OPTIONS_2026-10-16.md) | 19 duyarlı örnekte bütün ilk hücreleri koruma/yalnız tek ilk hücre seçenekleri, gerçek aday kapsamı farkı ve araştırmacının beklenen kararı |
| [Hazırlık envanteri ve kabul bağımlılıkları](PREPARATION_INVENTORY_2026-10-16.md) | Hazır adaylar/eksik etiket ayrımı, güncel dosya varlığı ve metadata kontrolü, kurum yanıtlarının sınırı ve kalan işler |
| [Alt grup hata raporu hazırlığı](SUBGROUP_REPORT_2026-10-16.md) | İl/mevsim/nominal destek paydaları, boş/belirsiz grup korumaları, gerçek etiketsiz pilot ve ayrı sentetik skorlar |
| [Sınıf ağırlığı ve kalibrasyon planı](IMBALANCE_CALIBRATION_PLAN_2026-10-16.md) | Aday karşılaştırmalar, seçilen hazırlık yönü ve açık takvim uygunluğu, kaynaklar ve sentetik ağırlık/rol kontrolleri |
| [Deney hazırlık kaydı](EXPERIMENT_RECORD_2026-10-16.md) | Dosya/kod/ayar ve sentetik ayrım kimlikleri, diskten geri kontrol, kapalı kabul alanları ve gerçek deney sınırı |
| [Fold içi ön işleme](FOLD_PREPROCESSING_2026-10-16.md) | Yalnız eğitimden öğrenilen medyan/ölçek, boş sütun seçenekleri, anahtar/şema korumaları ve sentetik prova |
| [Değerlendirme hesap ve ayrım çekirdeği](EVALUATION_CORE_2026-10-16.md) | AP kararı, eşlenik anahtarlar, eğitim içi zaman/olay/blok kontrolü, belirsiz alarm muhasebesi ve yalnız sentetik sınama |
| [Olay verisi alım kontrolü](REFERENCE_INTAKE_2026-10-15.md) | 19 alanlı şema, kimlik/tarih/CRS/kaynak incelemesi, değersiz hata tanıları ve 12 kamu kaydında kabul sınırı |
| [Gözlem koşullarının alt grup etkisi](PROTOCOL_SELECTION_REVIEW_2026-10-15.md) | Aynı 156 amaçlı birimde il/mevsim/örtü/yıl paydaları, eşlenik seçim farkları ve politika kabul sınırı |
| [Bağımsız referans erişimi ve doğrulama hazırlığı](INDEPENDENT_REFERENCE_PLAN_2026-10-15.md) | Gerçek OGM/EFFIS kaynakları, 12 bağlam kaydının sınırları, boş olay/kapsam şablonları ve gönderilmemiş kurumsal talep |
| [OGM talebi gönderim rehberi](research/OGM_SUBMISSION_GUIDE_2026-10-15.md) | Araştırmacının kurumsal kayıt yolu kararı, doğrulanan CİMER kanalı ve kişisel gönderim adımları |
| [Gözlem protokolünün saat/kalite kanıtı](OBSERVATION_PROTOCOL_EVIDENCE_2026-10-15.md) | 156 birimde zaman boşlukları, 624 dilim, termal pencere karşılaştırması, seçilmemiş protokol kesimleri ve beş saat grafiği |
| [Tamamlanan 156 birimlik gözlem yöntem pilotu](OBSERVATION_PILOT_RESULTS_2026-10-15.md) | 98 çiftin tamamlanması, kaynak/geometri geri kontrolü, alan-zaman tanıları ve araştırmacı inceleme örnekleri |
| [Yerel pilot kuyruğu ve zamanla aktarım azaltma](OBSERVATION_PILOT_QUEUE_2026-10-15.md) | Sabit 156 birim, 292 kaynakta native zaman tanığı, 98 gerekli geometri çifti, özel giriş ve devam kontrolü |
| [İlk çekirdek çiftinin mekânsal/zaman tanısı](OBSERVATION_CORE_SPATIAL_2026-10-15.md) | Gerçek piksel/QA ve tarama uzlaştırması, yaklaşık alan geri okuması, açıklamalı görsel ve tek çift kabul sınırı |
| [CloudFront uyumluluğu ve gerçek teşhis](OBSERVATION_CORE_CDN_2026-10-15.md) | İki gerçek 303 kaydı, tarayıcı kaynak izi, tam CMR nesnesine kimliksiz CDN adımı ve yeni tek çift planı |
| [Devam kontrolü ve başlık erişim teşhisi](OBSERVATION_CORE_ACCESS_PROBE_2026-10-15.md) | Korunan tek çift, cache başarısını uzak erişimden ayıran iki başlık/120 saniye teşhisi ve özel giriş adımı |
| [Tek çiftte güvenli ValueError teşhisi](OBSERVATION_CORE_DIAGNOSTICS_2026-10-15.md) | İki gerçek tekrar, sabit kontrol kodları, URI normalizasyon regresyonu ve güncel plan komutu |
| [Tek çiftte HTTP 303 düzeltmesi](OBSERVATION_CORE_REDIRECT_FIX_2026-10-15.md) | Gerçek hata kanıtı, aynı CMR S3 nesnesine kimliksiz ayrı oturum, 152 ilgili test ve yeni özel giriş planı |
| [Sınırlı ham kaynak kontrolü](OBSERVATION_CORE_TRANSFER_2026-10-15.md) | Tek çift/191 MB, özel terminal girişi, disk/süre/checkpoint korumaları ve eski gerçek yerel çiftte başlık okuyucu sınaması |
| [Gözlem çekirdeğinin NASA katalog kontrolü](OBSERVATION_CORE_CATALOGUE_2026-10-15.md) | 584 tam kimlik/sürüm ve metadata eşleşmesi, ham içerik/erişim sınırı ve S-NPP kaynak sürekliliği duyurusu |
| [Gözlem pilotu genişletme planı](OBSERVATION_EXPANSION_2026-10-15.md) | Dört il kesişimleri, 12 sabit eğitim günü/156 yöntem vakası, korunmuş kontenjan boşlukları ve tekilleştirilmiş kaynak baytı karşılaştırması |
| [Tarama alanı, zamanı ve kalite pilotu](SCAN_AREA_TIME_2026-10-15.md) | Üç eğitim hücresinde ham taramayla bağlı yaklaşık alan/zaman/QA, sensör-yörünge birleşimi ve 1/6/12 saat ayrımlı tekrar alanları |
| [Gözlem desteğinin mekânsal yorumu](OBSERVATION_SUPPORT_2026-10-15.md) | Sekiz eğitim granülünde günlük/tek granül/tekrar alanı, kara-bulut çakışmasının sınırı ve önerilen negatif aday araştırma protokolü |
| [Denetlenmiş eğitim adayı inceleme sürümü](DATASET_INSPECTION_RELEASE_2026-10-14.md) | Tam takvim geri okuması, 181 arka plan adayında gözlem taraması, 400 satırlık özellik önizlemesi ve açık etiket kabul koşulları |
| [19 duyarlı örneğin kaynak/zincir incelemesi](SENSITIVE_PILOT_TRACE_2026-10-14.md) | Eşleşmesiz senaryolar dahil 181 küme bağlamı, 35 kaynak noktası, ilk zaman/hücre değişimi ve yönsüz tanık yollar |
| [Olay/etiket protokolü inceleme seçenekleri](LABEL_PROTOCOL_REVIEW_2026-10-14.md) | 400 örnekte dokuz senaryo, 19 duyarlı örnek, ayrı arka plan incelemesi ve nihai birleştirme öncesi kullanıcı onayı |
| [Sabit 400 örnekte komşu gün denetimi](WINDOW_PILOT_2026-10-14.md) | 883 günlük kaynak, iki sınır örneği, 16 eksik paket kümesi, korunan tabaka/ağırlık ve yeni önceki gün tanığı |
| [Komşu günlerle hedef pencere kontrolü](OBSERVATION_WINDOWS_2026-10-14.md) | 11 amaçlı pencerede 23 eğitim günü, iki komşu pencerede aynı belirsiz merkez, kaynak boşlukları ve dönem sınırı |
| [Tamamen su sınıflı hücrelerin kapsam kararı](WATER_SCOPE_2026-10-14.md) | Araştırmacının A seçeneği, 10 hücrelik dışlama, 727 karışık hücrenin korunması, sürümlü filtre ve gerçek eğitim etkisi |
| [400 örnekte gözlem kanıtı](OBSERVATION_PILOT_REVIEW_2026-10-14.md) / [İnsan değerlendirme rehberi](OBSERVATION_HUMAN_REVIEW_2026-10-14.md) | Alan/zaman/bulut ayrımı, ham taramada gece yarısı tanığı, altı örnek ve araştırmacı/danışman için açık kararlar |
| [Öncelikli dokuz vakanın bağlantı/kaynak incelemesi](PRIORITY_EVENT_TRACE_2026-10-14.md) | 100 farklı tespitte graf tanıkları, uzun zincir, önceki yakın Type=2 ve eksik dönem bağlamı; etiket kararı açık |
| [Olay/ilk hücre karar protokolü](EVENT_DECISION_PROTOCOL_2026-10-14.md) | 53 varyantın 11 örtüşme grubunda duyarlılığı, hedef günü değişen dokuz öncelikli vaka ve altı açık kabul başlığı |
| [Yangın sınırlarıyla coğrafi karşılaştırma](PERIMETER_REFERENCE_REVIEW_2026-10-14.md) | 2021 filtreli EFFIS sınırları, 21 varyant/24 bağlantı, eksen/zaman kontrolü, bağımsızlık ve ilk nokta belirsizliği |
| [Kurumsal kayıtlarla ilk vaka incelemesi](REFERENCE_CONTEXT_REVIEW_2026-10-14.md) | İki canlı resmî kaynak, 10 küme adayına bölgesel bağlam, çoklu başlangıç ve kesin kimlik eşleşmesi sınırı |
| [Etiket kanıtı inceleme paketi](LABEL_EVIDENCE_REVIEW_2026-10-14.md) | 53 amaçlı olay-senaryo vakasının gözlem bağlantıları ve 400 hücre-günlük ayrı pilot; kararlar/etiketler boş |
| [Uydu gözlem denetim tabloları](OBSERVATION_TABLES_2026-10-14.md) | 72 ayda aynı hücre/tarih anahtarlı ayrı uydu tanıları; 5.798 eksik ürün satırı, etiket ve model girdisi yasağı |
| [Tam eğitim adayı kalite incelemesi](DATASET_QUALITY_REVIEW_2026-10-14.md) | 72 ay/6.351.709 hücre-gün kapanışı, sütun bazlı eksikler, kaynak günlerinin hedef pencere incelemesi ve açık altı bilimsel karar |
| [Eğitim özelliklerinin toplu birleştirilmesi](DATASET_TRAINING_JOIN_2026-10-14.md) | Tamamlanan uydu native denetimi sonrası 72 eğitim ayındaki 27 aday özelliğin yerel hazırlanması; etiket ve dönem sınırları |
| [Uydu ürün teslimi ve native kontrol](GCP_PRODUCT_DELIVERY_2026-10-14.md) | 199 kompakt ürünün 1,28 GB hash doğrulamalı yerel teslimi ve tamamlanan 71 ay/2.158 günlük native kontrol |
| [14 Ekim V7 ilerleme ve final kontrolü](GCP_V7_PROGRESS_2026-10-14.md) | Yerel log/katalog kabulü: 70 tam ay/59 uygun kısmi gün; iki eksik kaynak günü ve bilimsel payload kabul sınırı |
| [PROJECT.md](PROJECT.md) | Bilimsel kapsam, zaman, etiket ve veri ayrımı sözleşmesi |
| [ROADMAP.md](ROADMAP.md) | Aşamalar ve kabul ölçütleri |
| [Araştırma planı](research/RESEARCH_PLAN.md) | Araştırma sorusu, deney tasarımı ve açık konular |
| [12 Ekim literatür incelemesi](research/LITERATURE_REVIEW_2026-10-12.md) | Yakın Türkiye/Akdeniz çalışmaları, görev ayrımı ve savunulabilir katkı önerisi |
| [Literatür kimlik denetimi](research/LITERATURE_IDENTITY_AUDIT_2026-10-12.md) / [Makine okunur denetim](research/literature_identity_audit_2026-10-12.json) | 34 kaydın başlık/yazar/DOI veya kurum eşleşmesi; yayın durumu düzeltmeleri ve kanıt sınırları |
| [Literatür kaynak sicili](research/literature_sources_2026-10-12.json) / [Arama kaydı](research/literature_search_log_2026-10-12.json) | 34 seçilmiş kayıt, yayın/erişim düzeyi, arama yöntemi ve sınırları |
| [Makale yönü deney protokolü](research/ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md) | Etiket denetimi, dört hipotez, ayrım/ölçüt ve kabul kapıları; öneri |
| [Danışman literatür özeti](research/ADVISOR_LITERATURE_BRIEF_2026-10-12.md) | Görüşmede kullanılabilecek kısa karşılaştırma ve açık araştırma kararları |
| [Kanıt dizini](research/EVIDENCE_REGISTER.md) | İddiaların rapor ve veri dayanakları |
| [2209-A hazırlığı](research/2209A_PREPARATION.md) | Çağrı, başvuru hazırlığı ve danışmanla değerlendirilecek içerik |
| [Araç kullanım kaydı](research/AI_USE.md) | Üretken yapay zekâ katkısı ve beyan hazırlığı |
| [Araştırma günlüğü](../Diary/README.md) | Günlük işlem ve karar kayıtları |
| [Betik rehberi](../scripts/README.md) | Çalıştırılabilir işlem adımları |
| [Belge ve mimari incelemesi](DOCUMENTATION_REVIEW_2026-10-09.md) | Editoryal kapsam, bütünlük kontrolleri ve mimari sınırlar |
| [Arazi ve bitki örtüsü hazırlığı](LANDSCAPE_PREPARATION_2026-10-09.md) | Statik aday özellikler, geçmiş görüntü örneği ve açık kalite konuları |
| [Bitki örtüsü mevsim karşılaştırması](VEGETATION_WINDOW_REVIEW_2026-10-09.md) | 16/30/60 günlük destek, görüntü yaşı ve günlük geçmişe göre seçim örneği |
| [Veri setine geçiş planı](DATASET_READINESS_2026-10-10.md) | Hazır parçalar, özellik anlamları, bitki örtüsü ölçekleme ve nihai etiket/birleştirme ölçütleri |
| [Özellik birleştirme denemesi](FEATURE_JOIN_PILOT_2026-10-10.md) | Tek eğitim gününde 27 aday, ayrı kalite/provenance, anahtar ve geçmiş zaman kontrolleri |
| [Hedef kabul hazırlığı ve gün geçişleri](TARGET_ADMISSION_REVIEW_2026-10-10.md) | Dört eğitim günü, dokuz keşif kataloğu, kapalı etiket kapısı ve zaman/split sınırları |
| [Habitat–destek ve zor vaka paketi](DECISION_REVIEW_2026-10-10.md) | Tam kapsam envanteri, 33 habitat/53 olay-senaryo örneği ve kaynakla bağlı inceleme formu |
| [Veri seti kabul taslağı](DATASET_ACCEPTANCE_CONTRACT_2026-10-10.md) | Anahtar, eksik değer, etiket kanıtı, veri ayrımı ve son manifest kabul koşulları |
| [Parçalı özellik kaydı ve okuyucu](FEATURE_PARTITION_PILOT_2026-10-10.md) | Dört günün günlük feature/kalite parçaları, hash/anahtar manifesti ve kapalı dönem kontrolü |
| [Tam aylık aday özellik geri okuması](FEATURE_MONTH_READBACK_2026-10-12.md) | Ocak/Ağustos 2018 bütün takvim günleri, 179.738 hücre-gün, kaynak eşitliği ve aday kabul sınırı |
| [Veri setine geçiş hazırlığı](DATASET_PREPARATION_RUNBOOK_2026-10-12.md) | Veri sözlüğü, kaynak/teslim planı, devam eden toplu giriş, hedef eşleştirme ve son aday kabul komutları |
| [Bütün hücrelerde bitki örtüsü denemesi](VEGETATION_FULL_GRID_2026-10-10.md) | 2.899 hücre, iki geçmiş pencere, ham integral geri okuması ve checkpoint tekrar kullanımı |
| [Ağustos 2018 günlük bitki örtüsü adayları](VEGETATION_MONTH_2018_08_2026-10-10.md) | Beş haftalık kesim, 179.738 günlük aday satır, iki geri okuma ve erişim sınırları |
| [Bitki örtüsü eğitim dönemi kuyruğu](VEGETATION_PERIOD_QUEUE_2026-10-10.md) | 72 aylık plan, tek yazar, kaynak/disk/süre kontrolleri ve doğrulanmış yeniden kullanım |
| [Bitki örtüsü kış–yaz tam grid incelemesi](VEGETATION_TRAINING_SUPPORT_2026-10-10.md) | İki eğitim ayında 342.082 aday, destek eksikliği, görüntü yaşı ve tekrar geri okuma |
| [Bitki örtüsü otomatik toplu hazırlığı](VEGETATION_TRAINING_AUTORUN_2026-10-10.md) | Dört saatlik alt kuyrukların otomatik devamı, toplam süre sınırı, canlı kabul ve yerel süreç koşulu |
| [Bitki örtüsü ISO teşhisi ve V2 devam](VEGETATION_ISO_RESUME_2026-10-10.md) | Gerçek karışık zaman hatası, scoped parser kabulü, dondurulmuş ürünler ve yeni sınırlı çalışma |
| [Bitki örtüsü duruşu ve kota kontrolü](VEGETATION_QUOTA_CHECK_2026-10-10.md) | 22 ayın korunması, 91/92 son kesim checkpoint'i, bağlantı kontrolü ve güncel EE kısıtlı mod |
| [Bakım duruşu](VEGETATION_MAINTENANCE_PAUSE_2026-10-11.md) / [Bakım sonrası devam](VEGETATION_MAINTENANCE_RESUME_2026-10-11.md) | 45 ayın hash koruması, kontrollü yerel duruş ve aynı süre sınırıyla yeni çağrı |
| [12 Ekim VPN duruşu](VEGETATION_VPN_PAUSE_2026-10-12.md) | 62 ayın korunması, kapanmayan istek alt sürecinin sonlandırılması ve manuel devam koşulu |
| [12 Ekim VPN sonrası devam](VEGETATION_VPN_RESUME_2026-10-12.md) | 199 korunmuş kaynak ve 169 kısmi JSON kontrolü, bağlantı ve aynı süreyle yeni çağrı |
| [Eğitim bitki örtüsü tamamlanması](VEGETATION_TRAINING_COMPLETE_2026-10-12.md) | 72 ay, final süreç/kilit durumu, 229 dosya bütünlüğü ve kabul sınırları |
| [Habitat kapsamı ön incelemesi](HABITAT_REVIEW_2026-10-10.md) | 2.899 hücrede örtü bileşimi, alan paydaları ve 15 keşif eşiği; uygunluk kararı verilmeden değerlendirme |
| [Olay gruplaması geri okuması](EVENT_GROUPING_REVIEW_2026-10-10.md) | 30.295 eğitim adayında dokuz grafiğin geri okuması; zincirleme, ilk hücre ve dönem sınırı denetimi |
| [Kaynak ertelemeli oturum kapanışı](GCP_CONTINUATION_FAILURE_2026-10-09.md) | RuntimeError bildirimi, uzak ilerleme ve güvenli teşhis arşivi toplama |
| [V2 güvenli tanı ve devam](GCP_SOURCE_AWARE_V2_2026-10-09.md) | Drive raporu çapraz kontrolü, değişmeyen checkpoint kuralları ve yeniden deneme adımları |
| [V2 erken kapanış ve teşhis](GCP_V2_FAILURE_2026-10-10.md) | Eylül 2022 çocuk hatası, son bildirilen 14 tam ay ve kimlik bağlı salt okunur snapshot toplama |
| [Tarama zamanı hatası ve dar düzeltme](GCP_SCAN_TIME_FIX_2026-10-10.md) | Gerçek kaynakta tarih çözümleme ValueError'ı, nanosaniye karşılaştırması ve salt okunur parser kabul denemesi |
| [13 saatlik V4 devam hazırlığı](GCP_THIRTEEN_HOUR_CONTINUATION_2026-10-10.md) | Kabul edilmiş V3 durumundan geçiş, 13 saat STOP ayarı ve süre rezervleri |
| [V4 hata denetimi ve 18 saatlik V5](GCP_EIGHTEEN_HOUR_CONTINUATION_2026-10-11.md) | 40 ayın günlük/katalog kontrolü, incelenmiş tanı koruma ve sınırlı ReadTimeout denemesi |
| [Drive tanısı ve V6 devamı](GCP_DRIVE_RESUME_V6_2026-10-12.md) | 31 hazır ZIP'in rapor geri okuması, exact V5 geçişi, yalnız metadata GET için sınırlı tekrar ve 18 saatlik başlatma |
| [V6 Haziran 2018 kaynak hatası](GCP_V6_FAILURE_2026-10-13.md) | 65 aylık final günlük/katalog kabulü, altı gerçek geolocation kontrol hatası ve exact final bağlı salt okunur tanı |
| [İki eksik günle V7 devamı](GCP_SOURCE_RESUME_V7_2026-10-13.md) | İkinci tanı/22 ZIP hash envanteri, exact V6 arşiv geçişi ve 18 saatlik üç aşamalı devam |
| [V7 Drive OAuth kurtarma](GCP_DRIVE_AUTH_RECOVERY_2026-10-13.md) | Başlangıç token HTTP 400, eski progress ayrımı, aynı klasörlü izin yenileme ve özel VM kurulumu |
| [Doğrulanmış parser ile V3 devam](GCP_SOURCE_AWARE_V3_2026-10-10.md) | Gerçek kaynakta tam scan kabulü, açık çalışma zamanı provenance'ı, incelenmiş tanı arşivi ve uzun oturuma dönüş |

## Klasör sorumlulukları

Ortak kütüphane `src/`, görev bazlı giriş noktaları `scripts/`, açık ayarlar
`configs/`, otomatik kontroller `tests/` altındadır. Ham/ara/işlenmiş veri
`data/`; rapor, görsel, model deneyi, bulut paketi ve kabul kayıtları
`outputs/` altındadır. Günlükler `Diary/`, kalıcı açıklamalar `docs/` içinde tutulur.

Mevcut bulut betikleri paket üretimi ve bağımsız yürütme için script modülleri
arasında bağımlılıklar içerir. Bu yapı tamamlanmış katı bir katmanlı mimari
olarak sunulmaz. Canlı paketler dondurulmuşken dosya taşıma veya ortak kodu
çıkarma yapılmaz; sonraki refaktör paket/CLI/checkpoint uyumluluğuyla sınanır.

## Yeni dosya kuralları

- Kararlı yöntem belgesi açıklayıcı bir ad taşır; belirli deney raporu tarihle adlandırılır.
- Aynı sonuç farklı özetlerde tekrar hesaplanmaz; ayrıntı bir raporda, bağlantı diğerlerindedir.
- Yeni günlük yeni tarihe yazılır; geçmiş çalışma ve sonradan yapılan editoryal düzenleme ayrıdır.
- Rapor amaç, veri kapsamı, yöntem, bulgu, kontrol, sınırlama ve sonraki adımı içerir.
- Makine çıktısının özgün baytları korunur. Düzeltme yeni sürüm/raporla yapılır.
- Komutlar, dosya yolları, hash'ler ve kaynak kimlikleri dil düzenlemesinde değiştirilmez.
- Büyük veriler, OAuth dosyaları, `.env` ve kişisel belgeler Git'e alınmaz.
- Geçici doğrulama çıktıları `outputs/` altında ilgili işe ait dizinde tutulur.

## Teknik belgeler

Tarihli raporların performans, maliyet ve durum ifadeleri kendi ölçüm anlarına
aittir. Eski kurulum rehberi çalıştırılmadan önce güncel devam rehberi kontrol edilir.

- [Yaklaşık gözlem alanının sınır hassasiyeti — 5 Ekim 2026](AREA_BOUNDARY_SENSITIVITY_2026-10-05.md)
- [Hesap ızgarasının çözünürlük ve başlangıç konumu — 5 Ekim 2026](AREA_GRID_SENSITIVITY_2026-10-05.md)
- [Google Cloud kredisiyle hızlandırma — 5 Ekim 2026](CLOUD_CREDIT_OPTIONS_2026-10-05.md)
- [İki sensörlü bir günün Colab denemesi](COLAB_DAY_PILOT.md)
- [Drive'da küçük sonuçların kalıcı saklanması — 5 Ekim 2026](COLAB_DRIVE_STORAGE.md)
- [Temmuz 2023 aylık Colab işi](COLAB_MONTH_2023_07.md)
- [Temmuz 2023 aylık sonuç denetimi](COLAB_MONTH_RESULTS_2023_07.md)
- [Tek uydu geçişiyle ücretsiz bulut denemesi](COLAB_PILOT.md)
- [Colab yaz kontrolü — seçilen B kapsamı](COLAB_SUMMER_CONTROL.md)
- [B yaz kontrolü sonucu — 5 Ekim 2026](COLAB_SUMMER_RESULTS_2026-10-05.md)
- [FIRMS gözlem kapsamı — eğitim dönemi ön incelemesi](FIRMS_OBSERVATION_COVERAGE.md)
- [Doğrulanmış yeni hatla sekiz saatlik üretim](GCP_ACCELERATED_PRODUCTION_2026-10-08.md)
- [N2 ve örtüşen işlem hattıyla hızlandırma deneyi](GCP_ACCELERATION_2026-10-08.md)
- [Aralık üretiminin erken kapanışı ve teşhis](GCP_ACCELERATION_FAILURE_2026-10-09.md)
- [Gerçek hızlandırma sonucu — 8 Ekim 2026](GCP_ACCELERATION_RESULTS_2026-10-08.md)
- [Ücretsiz deneme için CPU kapasite sorgusu](GCP_CPU_PREFLIGHT.md)
- [Drive ZIP türü düzeltmesi — 6 Ekim 2026](GCP_DRIVE_MIME_REPAIR.md)
- [Google Drive kalıcılık kontrolü — VM kapalıyken hazırlık](GCP_DRIVE_PROOF.md)
- [Drive kalıcılık kontrolünün sonucu — 6 Ekim 2026](GCP_DRIVE_PROOF_RESULTS.md)
- [GCP iş sonu: sonuçları koru, kaynakları kaldır, faturalandırmayı kapat](GCP_FINAL_CLEANUP.md)
- [İlk uzun oturumun günlük denetimi — 8 Ekim 2026](GCP_FIRST_SESSION_RESULTS.md)
- [Gerçek geolocation girdisinin adını toplama](GCP_GEOLOCATION_HEADER_CAPTURE_2026-10-09.md)
- [İlk Drive manifest kaydının teşhisi — 7 Ekim 2026](GCP_MANIFEST_DIAGNOSIS.md)
- [GCP: bir ve iki işçi karşılaştırması](GCP_PARALLEL_BENCHMARK.md)
- [Mevcut VM'de iki saatlik paralellik ölçümü](GCP_PARALLEL_TUNING_2026-10-08.md)
- [8 Ekim 2026 — Gerçek VM paralellik ölçümü](GCP_PARALLEL_TUNING_RESULTS_2026-10-08.md)
- [GCP üzerinde ilk kaynak doğrulama denemesi](GCP_PORTABILITY_PILOT.md)
- [Uzun GCP üretimine geçiş — 6 Ekim 2026](GCP_PRODUCTION_READINESS.md)
- [Tam eğitim dönemi: GCP çalıştırma rehberi — 6 Ekim 2026](GCP_PRODUCTION_RUN.md)
- [Kalan ham dosyalarla sınırlı yerel teşhis](GCP_RETAINED_SOURCE_PROBE_2026-10-09.md)
- [31 Aralık kaynağını beklemeye alarak üretime devam](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md)
- [Kalan eğitim aylarının süre senaryosu — 6 Ekim 2026](GCP_TIME_PLANNING_2026-10-06.md)
- [Piksel geometrisi ve veri hacmi — 4 Ekim 2026](GEOMETRY_DIAGNOSIS_2026-10-04.md)
- [Daha küçük uydu işleme kapsamı — 6 Ekim 2026](L2_SAMPLING_FEASIBILITY_2026-10-06.md)
- [Uydu verisini sınırlı diskle işleme seçenekleri — 4 Ekim 2026](L2_STORAGE_OPTIONS_2026-10-04.md)
- [Uydu gözlem alanı — yöntem ve doğrulama kaydı](OBSERVATION_AREA_METHOD.md)
- [Tarama kalitesi ve zaman boşlukları — 5 Ekim 2026](OBSERVATION_TIMING_2026-10-05.md)
- [Veri hazırlama kalite incelemesi — 2 Ekim 2026](QUALITY_REVIEW_2026-10-02.md)
- [EGE VE AKDENİZ ORMAN YANGINI ERKEN UYARI SİSTEMİ](ROADMAP_INITIAL.md)
- [Kısa proje durum raporu — 9 Ekim 2026](STATUS_HISTORY_2026-10-09.md)
- [Yaz kontrolü için kapsam seçenekleri — 5 Ekim 2026](SUMMER_CONTROL_OPTIONS_2026-10-05.md)
- [Meteoroloji kullanım kuralı — weather_model_v1](WEATHER_POLICY.md)
- [İş yükü ve büyük gruplara geçiş — 5 Ekim 2026](WORKLOAD_PLAN_2026-10-05.md)
