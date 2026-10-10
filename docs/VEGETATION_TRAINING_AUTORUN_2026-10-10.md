# Eğitim aylarının otomatik toplu hazırlığı

Kayıt tarihi: 10 Ekim 2026. Kullanıcı kalan bitki örtüsü eğitim aylarının
tek tek sohbet onayı beklenmeden hazırlanmasını istedi. Aylık bilimsel kayıt
birimi korunur; yürütme ve süre sonunda devam otomatikleşir.

## Çalıştırma ve sınırlar

İlk çağrı Mart 2019'da karışık ISO saniye hassasiyetinin çözümlemesi nedeniyle
durdu. Dondurulmuş verileri/kaynakları değiştirmeden runtime parser
kimliği ekleyen [V2 devam](VEGETATION_ISO_RESUME_2026-10-10.md) 10 Ekim
14:45 Türkiye saati civarında başlatıldı. Aşağıdaki V1 komutu tarihsel
ilk çağrıdır; yeni devam için V2/proof rehberi kullanılır. Çalışan işin
yanına ikinci kuyruk başlatılmaz.

```powershell
.\.venv\Scripts\python.exe scripts/landcover/run_vegetation_training.py --start 2018-01 --end 2023-12 --hours 24 --batch-minutes 240 --min-free-gib 10
```

Seçili kapsam 72 eğitim ayıdır. Şubat ve Ağustos 2018 önceden hazırlanmıştır;
diğer 70 ay henüz tamamlanmış sayılmaz. Aylar sıralı çalışır; aynı anda tek ay
ve en fazla iki Earth Engine isteği vardır. Her ay, ham integraller ve günlük
tablo bağımsız geri okumasından sonra kabul listesine girer. Dosya varlığı
tek başına kabul değildir. Mevcut aylar doğrulanarak yeniden kullanılır.

Alt kuyruğun dört saatlik sınırı dolarsa mevcut dosyalar korunur ve aynı
aralık için yeni alt kuyruk otomatik başlar. Böylece sonraki aya veya süre
sonrasına geçmek için her seferinde sohbet mesajı gerekmez. Bütçe sınırında
kesilen son grup yeniden gerekebilir; sıfır tekrar maliyeti iddia edilmez.

Toplam çağrı sınırı 24 saattir; bitiş süresi garantisi değildir. Kod en fazla
48 saat ve 24 alt kuyruk kabul eder; mevcut çağrı 24 saatle sınırlıdır. Kaynak
hatası, disk rezervi sınırı, kullanıcı kesintisi veya kod/grid/ortam değişikliği
otomatik tekrar edilmez. En az 10 GiB disk rezervi ay başında kontrol edilir.
Boş disk alanı diğer uygulamalara karşı ayrılmış bir kota değildir.

Bu yerel Python sürecidir; GCP VM'deki yangın gözlem kuyruğundan bağımsızdır.
VM'nin makine, süre, kapanma veya faturalandırma ayarlarını değiştirmez.
Bilgisayar açık ve uyanık olmalıdır. Tarayıcı sekmesine bağlı değildir;
bilgisayar kapanırsa veya uykuya geçerse kesintisiz çalışma garantisi yoktur.
İşletim sisteminin uyku/güç ayarları otomatik değiştirilmez.

## 10 Ekim başlatma kaydı

Toplu çağrı 10 Ekim 2026 yaklaşık 01:38 Türkiye saatinde başladı:
`training_2018_2023_20261010_26d6769c`. Kod commit'i `edb8d6f`.
Son yetkili yerel süreç kontrolünde üst süreç ve hazırlık çocukları canlı;
Ocak 2018'in ilk kesiminde 54/92 ham grup kaydedilmişti. Seçili 72 ayın
bu yeni çağrıdaki kabul listesi henüz boş; daha önce kabul edilmiş Şubat ve
Ağustos kayıtlarının silindiği anlamına gelmez. Toplam 24 saat sınırı yaklaşık
11 Ekim 01:38 Türkiye saatine karşılık gelir; tamamlanma garantisi değildir.

Kısıtlı araç ortamındaki ilk süreç sorgusu dışarıda başlatılmış süreçleri
göremedi ve yanlış yokluk izlenimi verdi. Yetkili salt okunur CIM sorgusu
aynı işin canlılığını doğruladı; ikinci iş başlatılmadı, kilitler kaldırılmadı.
Yerel denetim: aynı iş dizininde `process_inspection_001.json`.

## İzleme ve kesinti sonrası devam

10 Ekim yaklaşık 02:45 Türkiye saati durum kaydı: süreç canlı, `running`;
Mayıs 2018 hazırlanıyor. Yeni çağrıda Ocak–Nisan kabul edilmiş; önceki
Ağustos ile toplam beş tam ay ve 67 kalan ay var. Yerel gözlem
`progress_inspection_002.json` içinde. Ocak/Mart'ın 21,09/23,20 dakikalık
hazırlama ölçümlerinden kalan dönem için kaba tahmin 24–28 ek saat;
bütün dönem garantisi değildir. Bu hızda 24 saatlik çağrı sınırına tamamlanma
öncesinde ulaşılabilir; sonraki devam çağrısı mevcut dosyaları yeniden kullanır.

Her çağrı ayrı `job_id` ile
`outputs/reports/landscape/training_supervisor_v1/<job_id>/progress.json`
yazar. `current_month`, `verified_months`, `active_batch_report`, toplam
süre ve çalışma durumu canlı güncellenir. Alt oturumların ayrı raporları ve
hash'leri korunur. Terminal çıktısı aylık hazırlık ve kabul geçişlerini gösterir;
ham Earth Engine grup logları alt kuyruğun rapor dizinindedir.

İlerleme dosyasının `running` olması tek başına canlı süreç kanıtı değildir;
kaydedilen `pid` ile süreç durumu ve güncel log birlikte incelenir. Toplu iş
kilidi ve mevcut aylık kuyruk kilidi eşzamanlı ikinci çalışmayı reddeder.
Zorla kapatma sonrası kilitler otomatik silinmez: hem üst süreç hem çocuk
süreçlerin bittiği doğrulanmadan yeniden başlatma yapılmaz.

Normal bütçe/kapanış sonunda kilitler bırakılır. Devam için aynı eğitim
aralığı yeni `job_id` ile çağrılır; doğrulanmış aylık dosyalar yeniden üretilmez.
`selected_training_range_verified`, yalnız bitki örtüsünün seçili aralığını
belirtir; yangın tanıları, nihai etiket tablosu veya model eğitimi anlamına gelmez.

## Doğrulama ve gizlilik

Üst süreç, üretim kodu/grid/ortam kilidi hash'lerini ve beş paket sürümünü
başlangıçta kaydeder, alt oturumdan ve aylık kabulden önce karşılaştırır.
Ortam değişkenleri veya kimlik bilgileri rapora alınmaz. Kabul listesi
ay başına tek kayıt tutar; yeniden kullanım toplamı şişirmez. Başarısız
hazırlık tam aralık başarısı olarak kaydedilmez.

Otomatik süre devamı, disk/hata/kesinti duruşu, toplam süre/alt kuyruk sayısı,
kaynak değişimi, kapsam dışı ay ve eksik kabul durumları dahil **74 ilgili test
geçti**. Ruff ve biçim denetimleri geçti. Gerçek Ağustos yeniden kullanım
denemesi yeni üst süreçte geçti: 179.738 satır, bir seçili ay, 11,328 saniye,
veri isteği yapılmadan mevcut manifest/tablo hash'leri korunmuş halde.
Deneme: `outputs/reports/landscape/training_supervisor_v1/offline_august_supervisor_20261010/`.
Bu test tamamlanmış 72 aylık çalışma veya saha doğrulaması değildir.

Ham/ara veriler, ortam kimlik bilgileri ve makine raporları Git dışında kalır.
Kod ve açık yöntem/durum raporları gizlilik denetimi sonrası normal push ile
yayımlanır. Yerel arka plan süreci sohbet mesajı veya zamanlanmış bildirim
oluşturmaz; ilerleme sonraki kontrolde gerçek dosya ve süreçten okunur.

Haftalık kesim, sekiz günlük saklama ve ayrı 30/60 günlük pencereler korunur.
Geçmiş erişim zamanı bilinmiyor; aday özellikler operasyonel uygunluk onayı
değildir. `negative_label_permitted=false` ve kapalı 2025 final test korunur.
