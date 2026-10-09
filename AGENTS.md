# Proje çalışma kuralları

Bu depo, Antalya, Muğla, İzmir ve Mersin için 24 saatlik yangın riski üzerine
bir bitirme araştırmasıdır. TÜBİTAK 2209-A başvurusu, bitirme projesi danışmanıyla
hazırlanması planlanan bir sonraki aşamadır; destek alınmış veya başvuru yapılmış değildir.

## Önce okunacak belgeler

- `docs/STATUS.md`: tarihli güncel durum ve açık konular.
- `docs/PROJECT.md`: bilimsel kapsam, zaman sözleşmesi ve veri ayrımı.
- `docs/research/RESEARCH_PLAN.md`: araştırma soruları ve aşama kabul ölçütleri.
- `docs/research/2209A_PREPARATION.md`: başvuru hazırlığı, kaynaklar ve açık kararlar.
- `docs/README.md`: belge dizini ve dosya yerleşim kuralları.

## Bilimsel doğruluk ve kanıt

- Gerçekleştirilen çalışma, önerilen çalışma ve yorum ayrı belirtilir. Başarı,
  finansman, danışman onayı, bağımsız doğrulama veya yayın kabulü uydurulmaz.
- FIRMS tespit sayısı bağımsız yangın sayısı değildir. İlk uydu tespiti gerçek
  tutuşma zamanı değildir. Eksik gözlem otomatik olarak negatif etikete çevrilmez.
- `daily_observation_status=unknown` ve `negative_label_permitted=false`
  koşulları, bilimsel gerekçe ve doğrulanmış yeni protokol olmadan değiştirilmez.
- Eğitim 2018–2023, doğrulama 2024, kapalı final test 2025'tir. Tahmin anında
  bilinmeyen veriler girdiye alınmaz; ERA5-Land geriye dönük yeniden analizdir.
- Bir sonucun kaynağı açık olmalıdır: yerel denetim raporu, uzak iş günlüğü,
  manuel bildirim veya literatür. Uzak günlük tek başına yerel kabul değildir.
- Sayısal iddialarda dönem, birim, örneklem ve sınırlama yazılır. İyileştirme
  oranı yalnız ölçüldüğü karşılaştırmaya atfedilir. Eski test sayısı güncel sayılmaz.

## Yazım ve kayıt

- Türkçe, açık ve profesyonel araştırma dili kullanılır. Günlüklerde amaç,
  işlem, bulgu, sınırlama ve sonraki adım yer alır. Sohbet talep/yanıt dökümü yazılmaz.
- Günlükte birinci tekil kişi araştırma kararı veya gerçekten yapılan manuel
  iş için kullanılabilir. Otomatik hesaplamalar ve doğrulamalar yöntemleriyle anlatılır.
- Yapay zekâ kullanımını gizleme veya tüm işleri kişisel olarak yapılmış gösterme
  amacıyla kayıt değiştirilmez. Katkı kapsamı `docs/research/AI_USE.md` içinde tutulur;
  resmî beyan danışman ve araştırmacı tarafından başvuru öncesinde kontrol edilir.
- Yeni sonuçlar ilgili rapora, güncel özet STATUS'a, günün çalışması Diary'a yazılır.
  PROJECT'in tarihsel bölümüne yeni uzun oturum günlükleri eklenmez.
- Önceki tarihlerdeki bulgular sonradan elde edilen sonuçlarla sessizce değiştirilmez.
  Editoryal düzenleme tarihi ile deney tarihi birbirine karıştırılmaz.

## Mimari ve dosya bütünlüğü

- `src/` ortak Python kütüphanesi, `scripts/` görev bazlı komutlar,
  `configs/` açık yapılandırmalar, `tests/` davranış kontrolleri içindir.
- `data/` veri, `outputs/` üretilmiş rapor/deney/paket alanıdır; büyük veri ve
  kimlik bilgileri Git'e eklenmez. Yeni üst düzey klasör yalnız gerçek gereksinimle açılır.
- Canlı bulut paketleri, dosya yolları, checkpoint anahtarları ve hash ile bağlı
  bilimsel kod, belge düzenlemesi nedeniyle değiştirilmez. Refaktör ayrı değişikliktir;
  paket yeniden üretimi, uyumluluk ve gerekli testlerle değerlendirilir.
- Kabul edilmiş ZIP/JSON/CSV/manifestler elle düzeltilmez; yeni sonuç yeni sürümle üretilir.
- `.env`, OAuth bağlantıları, tokenlar ve kişisel belgeler içerik taramasında yazdırılmaz.
- Anlamlı değişikliğe uygun kontrol çalıştırılır; yalnız metin düzenlemesi için
  bilimsel üretim veya bulut işi yeniden başlatılmaz.

## GitHub güncelleme tercihi — 10 Ekim 2026

Kullanıcı, her önemli proje değişikliği ve güncellemesinin sonunda uygun
kontrollerden sonra commit ve normal GitHub push yapılmasını açıkça yetkilendirdi.
Her push öncesinde aday/staged dosyalar gizlilik açısından denetlenir: kimlik
bilgileri, OAuth bağlantıları, token/parola, kişisel belgeler, ham/ara veri,
çıktı arşivleri ve büyük ikili dosyalar gönderilmez. `.gitignore` tek başına
yeterli sayılmaz; Git index içeriği ayrıca kontrol edilir. Bulgu varsa
giderilmeden push yapılmaz. Kod/dokümantasyon ve küçük açık yapılandırmalar
izlenebilir commit'lerle gönderilir; force-push veya geçmiş silme yapılmaz.
Bu kalıcı tercih zamanlanmış görev ya da bulut işi başlatma yetkisi değildir.
Gönderim hedefi `https://github.com/enesgocek/wildfire-risk-prediction`, mevcut
`main` dalıdır. Kullanıcı 10 Ekim'de bu deponun kendisine ait olduğunu ve
kontrol edilmiş kod/rapor commit'lerinin gönderimini ayrıca açıkça teyit etti.
Standart içerik kontrolü: `python scripts/quality/check_git_privacy.py --scope staged`.
Otomatik kontrol bütün olası sızıntıları kanıtlamaz; staged diff, dosya listesi
ve boyut incelemesiyle birlikte uygulanır. Kimlik bilgisi bulguları değerleri
yazdırılmadan yalnız dosya/kural/satır bilgisiyle raporlanır.

## Bulut ve maliyet sınırı

Free Trial dışına çıkılmaması ve kişisel ödeme oluşmaması temel çalışma sınırıdır.
Güncel oturumun süre/Stop ayarı ve checkpoint düzeni korunur. Stop işlemi kaynak
silme olarak raporlanmaz. Tam kaynak kaldırma, doğrulanmış sonuçların korunmasıyla
birlikte `docs/GCP_FINAL_CLEANUP.md` planına göre yürütülür. Bu dosya yeni bir
bulut işi, ücretli yükseltme, kaynak silme veya dış iletişim yetkisi vermez.
