# Eğitim dönemi aday özellik birleştirmesi — 14 Ekim 2026

## Amaç ve mevcut aşama

Uydu kompakt ürünlerinin 71 ay/2.158 uygun günlük yerel denetimi
tamamlandıktan sonra meteoroloji, arazi örtüsü, topografya ve bitki
örtüsü adaylarını ortak hücre–tahmin zamanı anahtarlarında birleştirmek.
Kullanıcının devam talimatıyla yalnız mevcut yerel kaynaklar kullanılır.
Yeni VM/Earth Engine işi, kaynak indirmesi veya model eğitimi açılmadı.

Birleştirme **14 Ekim 16:32 Türkiye**'de başladı. Seçim 2018–2023'ün
72 ayıdır; ilk kontrolde 72 ay seçilmiş, Ocak 2018 yeniden doğrulanmış,
hata alanı boş ve stderr sıfır bayttır. Kalan çalışma henüz tamamlanmış
olarak sunulmaz. Tek aday yazıcı kilidi ve çocuk süreçlerin ağ engeli,
10 GiB disk rezervi ve iki saatlik yürütme sınırı kullanılır. Başlangıçta
yerel boş disk yaklaşık 101,8 GiB'dir. Bilgisayar açık/uyanık kalmalıdır;
VM'nin son kullanıcı teyidi Stop durumudur.

## Kaynak planı ve kapsam

Yeni plan, tamamlanan bitki örtüsü supervisor'ının 72 aylık kabul
referansını ve önceden kabul edilmiş Ocak/Ağustos 2018'in iki aday
ayını tanıdı. İki aday ay yeniden üretilmez; bayt ve kaynak denetiminden
geçerek kullanılır. Diğer 70 ay mevcut betiğin `--build-missing`
seçeneğiyle seri hazırlanır; tamamlanan aylar ayrı raporlarla korunur.

Takvim 2.191 gün × 2.899 hücre = **6.351.709 aday hücre-gün**;
11 meteoroloji, yedi arazi örtüsü, beş topografya, dört NDVI/NDMI
olmak üzere **27 aday özellik** içerir. Bu hedef satır sayısıdır;
tamamlanmış birleştirme veya etiketli örneklem sayısı değildir.
Eksikler NaN olarak korunur; imputasyon yapılmaz. Kalite/kaynak
alanları aday model girdilerinden ayrıdır.

Uydu kaynağı eksik 13 Haziran 2018 ve 31 Aralık 2023 için özellik
takvimi korunabilir; bu, o günlerin etiketinin hazır olduğu anlamına
gelmez. Etiket ve geçmiş pencere etkileri ayrı kabul edilmeden bu
günler yangınsız sayılmaz veya eğitim örneklemine otomatik alınmaz.
`unknown`, `negative_label_permitted=false`, `labels_created=false`
ve `model_ready=false` korunur. 2024 özellik CSV'leri bu eğitim işi
tarafından okunmaz; 2025 final testi kapalı kalır.

## Kanıtların birbirinden ayrılması

Mevcut hazırlık betiği teslim envanterinde tarihsel V5 günlük/katalog
raporunu kullanır; buradaki **40 ay**, o eski raporun kapsamıdır.
Yeni üretim kaybı veya güncel uydu kabul sayacı değildir. Bu sürümün
planı veya önceki kabul kayıtları elle değiştirilmedi. Güncel uydu
kabulü [14 Ekim ürün raporundaki](GCP_PRODUCT_DELIVERY_2026-10-14.md)
71 ay/2.158 günlük native final kanıtına ayrıca bağlanır; Temmuz 2023
ayrı referansıyla toplam 70 tam ay ve iki kısmi ayın 59 günü vardır.
Birleştirme henüz uydu gözlem tablolarını veya ikili hedefleri eklemez.

Hazırlık ve devam/kalite davranış kontrolleri:
`tests/test_dataset_batch_cli.py` ve `tests/test_dataset_preparation.py`,
**41 passed**. İlk test çağrısında olmayan `test_dataset_batch.py`
dosya adı kullanıldığı için test toplanmadı; doğru iki dosyayla kontrol
tamamlandı. Bilimsel kod değiştirilmedi ve yeni test başarısı eski
üretim deneyine atfedilmedi.

## Çalışma kayıtları

- Plan: `outputs/reports/dataset/preparation_v1/20261014T132932Z_48373e98/plan.json`.
  SHA-256: `2167f5c015197e17df70a7e166a97572f0fd3d946a50cd01bf6c0908589573b6`.
- Plan geri okuması: aynı dizinde `readback.json`; 72 kaynak/iki aday
  referansı, sıfır ağ isteği, etiketsiz aday durumu.
- Çağrı: `outputs/reports/dataset/training_join_2026-10-14/launch.json`;
  stdout/stderr aynı dizindedir.
- Canlı aday sonuçları:
  `outputs/reports/dataset/candidate_batch_v1/20261014T133201Z_5e5c4a28/progress.json`.

İki saat tamamlanma garantisi değildir. Süre/disk/hata duruşunda bitmiş
aylar korunur; sonraki plan bu sonuç dizinini hash ile devralabilir.
İş tamamlanınca sonuç indeksinin tam 72 aylık takvimi ve kaynak/anahtar/
eksik değerleri `prepare_dataset.py audit --require-complete-calendar`
ile geri okunacaktır. Bu son adım 16:36 Türkiye'de tek seferlik yerel
devam süreci olarak bağlandı: batch başarıyla tamamlanır ve kilit
kalkarsa güncel indeksin hash'i alınarak denetim başlar. İki saatlik
bekleme ve 600 saniyelik son denetim sınırı vardır; eksik/hatalı batch
tam kabul edilmez. Sonuç aynı çağrı dizininde `final_audit_handoff.json`
olarak yazılır. Bu bir zamanlanmış görev veya bildirim değildir.
Bundan sonra olay, habitat, gözlem/negatif ve
dönem sınırı kararları bilimsel gerekçeleriyle sonuçlandırılmalıdır.
Tam özellik takvimi tek başına model eğitimi izni değildir.
