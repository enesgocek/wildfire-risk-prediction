# Belge dizini ve proje mimarisi

Güncelleme: 10 Ekim 2026. Güncel ilerleme, bilimsel yöntem, işlem rehberi ve
tarihsel kayıtların görevleri aşağıda ayrılmıştır. TÜBİTAK belirli bir Git
klasör şeması zorunlu kılmaz; bu düzen araştırmanın izlenebilirliği için seçilmiştir.

## Temel belgeler

| Belge | Sorumluluk |
|---|---|
| [STATUS.md](STATUS.md) | En son tarihli ilerleme, kanıt sınırları ve sıradaki iş |
| [PROJECT.md](PROJECT.md) | Bilimsel kapsam, zaman, etiket ve veri ayrımı sözleşmesi |
| [ROADMAP.md](ROADMAP.md) | Aşamalar ve kabul ölçütleri |
| [Araştırma planı](research/RESEARCH_PLAN.md) | Araştırma sorusu, deney tasarımı ve açık konular |
| [Kanıt dizini](research/EVIDENCE_REGISTER.md) | İddiaların rapor ve veri dayanakları |
| [2209-A hazırlığı](research/2209A_PREPARATION.md) | Çağrı, başvuru hazırlığı ve danışmanla değerlendirilecek içerik |
| [Araç kullanım kaydı](research/AI_USE.md) | Üretken yapay zekâ katkısı ve beyan hazırlığı |
| [Araştırma günlüğü](../Diary/README.md) | Günlük işlem ve karar kayıtları |
| [Betik rehberi](../scripts/README.md) | Çalıştırılabilir işlem adımları |
| [Belge ve mimari incelemesi](DOCUMENTATION_REVIEW_2026-10-09.md) | Editoryal kapsam, bütünlük kontrolleri ve mimari sınırlar |
| [Arazi ve bitki örtüsü hazırlığı](LANDSCAPE_PREPARATION_2026-10-09.md) | Statik aday özellikler, geçmiş görüntü örneği ve açık kalite konuları |
| [Bitki örtüsü mevsim karşılaştırması](VEGETATION_WINDOW_REVIEW_2026-10-09.md) | 16/30/60 günlük destek, görüntü yaşı ve günlük geçmişe göre seçim örneği |
| [Veri setine geçiş planı](DATASET_READINESS_2026-10-10.md) | Hazır parçalar, özellik anlamları, bitki örtüsü ölçekleme ve nihai etiket/birleştirme ölçütleri |
| [Bütün hücrelerde bitki örtüsü denemesi](VEGETATION_FULL_GRID_2026-10-10.md) | 2.899 hücre, iki geçmiş pencere, ham integral geri okuması ve checkpoint tekrar kullanımı |
| [Ağustos 2018 günlük bitki örtüsü adayları](VEGETATION_MONTH_2018_08_2026-10-10.md) | Beş haftalık kesim, 179.738 günlük aday satır, iki geri okuma ve erişim sınırları |
| [Kaynak ertelemeli oturum kapanışı](GCP_CONTINUATION_FAILURE_2026-10-09.md) | RuntimeError bildirimi, uzak ilerleme ve güvenli teşhis arşivi toplama |
| [V2 güvenli tanı ve devam](GCP_SOURCE_AWARE_V2_2026-10-09.md) | Drive raporu çapraz kontrolü, değişmeyen checkpoint kuralları ve yeniden deneme adımları |

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
