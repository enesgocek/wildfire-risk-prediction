# V7 uzak ilerleme kontrolü — 14 Ekim 2026

## Amaç ve yöntem

OAuth kurtarma sonrası devam eden V7 üretiminin aşama ve hata durumunu
izlemek. Kaynak, kullanıcının VM SSH'den paylaştığı launcher kuyruğu ve
seçilmiş progress alanlarıdır; bağımsız canlı VM sorgusu yapılmadı.
Kaynakta gözlem saati yoktur; oturum hızı veya bitiş saati hesaplanmadı.

## Bildirilen ilerleme

İlk 14 Ekim bildiriminde durum running/remaining_months, 178 işlenmiş
çift ve bu çağrıda yeniden doğrulanmış 30 tam ay vardı. Ardından gelen
bildirimde aynı V7 kimliği ve süre sınırıyla 364 çift ve 66 tam ay görüldü.
İki bildirim arasında 186 çift artışı vardır; bu zaman bazlı hız değildir.

| Alan | Son kullanıcı çıktısı |
|---|---|
| Durum / aşama | running / remaining_months |
| Aktif üretim ayı | Nisan 2018 |
| Son görünür gün kapanışları | 5 ve 6 Nisan 2018 |
| Çağrı içinde işlenmiş çift | 364 |
| Çağrı içinde doğrulanmış tam ay | 66 |
| Hata / failed month / failed phase | None / None / None |
| Wrapper SHA-256 | 37a4c4c904b49cac1bb4bc690b485fea19b41e922f24002526ca5ad9d6d0bc3b |
| Google STOP sınırı | 2026-10-14T13:35:01.727602Z / 14 Ekim 16:35 Türkiye |

Önceki 65 tam aylık uzak günlük/katalog kapsamına göre toplam bir tam
ay artışı bildiriliyor. Son seçilmiş çıktıda existing_months listesi
yoktur; eklenen ayın kimliği bu kayıtla bağımsız doğrulanmadı. 66 ay,
72 aylık nominal eğitim takviminin %91,7'sidir. V7'nin 70 tam aylık
işlenebilir hedefine dört ay kalır; iki ertelenen ay ayrıca kısmi kapsamdır.

## Sınırlamalar ve sonraki adım

Yeni tam-ay sayısı uzak üretici bildirimi olarak tutulur; yerel bilimsel
ürün baytlarının kabulü yapılmadı. Gözlem unknown ve negatif etiket false
koşulları değişmedi. 13 Haziran 2018 ve 31 Aralık 2023 kaynak uyuşmazlığı
nedeniyle ertelenmiştir; 70 ay ve iki kısmi ayın 59 uygun günü bitse bile
full_training_complete false kalır. Tam eğitim/etiket/model kabulü değildir.

Başlatma komutu tekrarlanmadan aynı çağrı takip edilir. Oturum bittiğinde
final/progress/launcher kanıtları geri okunur; tamamlanma veya yeni hata
yalnız VM Stop durumundan çıkarılmaz. Yeni kod, paket, kaynak silme veya
bulut işi bu rapor için uygulanmadı.

## Sonraki uzak bildirim: 67 tam ay

Kullanıcı aynı V7 kimliği ve STOP sınırıyla running/remaining_months,
529 işlenmiş çift ve 67 tam ay bildirdi; üç hata alanı None. Önceki
66 ay/364 çift bildirimine göre bir ay ve 165 çift artışı vardır.
Aktif ay Mart 2018; görünür kapanışlar 7, 11, 12 ve 13 Mart. Paralel
gün kapanışları sıralı değildir; bu kesitten 1–13 Mart'ın tamamının
kapandığı sonucu çıkarılmaz. Nisan'dan Mart üretimine geçildiği görülür.

67/72 nominal ay (%93,1); V7'nin 70 tam aylık işlenebilir hedefine üç
ay kalır. İki ertelenen ay ve 59 uygun kısmi günün final kontrolü ayrıdır.
Gözlem saati ve existing_months listesi paylaşılmadı; hız, kesin bitiş
ve yeni ay kimliği için bağımsız doğrulama yapılmadı. Kaynak kullanıcı
uzak çıktısıdır; yeni yerel bilimsel ürün kabulü yoktur. Önceki 66 aylık
kayıt tarihli ara bulgu olarak korunur; aynı çağrı yeniden başlatılmaz.

## Sonraki uzak bildirim: 69 tam ay

Kullanıcı aynı V7 hash'i ve `2026-10-14T13:35:01.727602Z` STOP sınırıyla
running/remaining_months, 840 çift ve 69 tam ay bildirdi; hata alanları
None. Önceki 67 ay/529 çift bildirimine göre iki ay ve 311 çift artışı
var. Aktif ay Ocak 2018; görünür kapanışlar 18, 21, 22, 23 ve 24 Ocak.
Bu kesit bütün önceki günlerin tek tek kapanış kanıtı değildir.

Asıl hedef 72 ayın tamamıdır. 69/72 nominal tam ay (%95,8); mevcut kaynak
sorunlarıyla erişilebilir 70 tam aylık ara hedefe bir ay kalır. Haziran
2018 ve Aralık 2023'teki iki eksik gün çözülmeden bu aylar tam sayılamaz.
Ara hedefte iki kısmi ayın 59 uygun gününün final kontrolü de gereklidir.
Henüz son durum veya full_training_complete kabulü yoktur.

Kaynak kullanıcı uzak çıktısıdır; existing_months listesi ve gözlem saati
yoktur. Yeni ay kimlikleri, yerel bilimsel ürün baytları veya kesin bitiş
zamanı ayrıca doğrulanmadı. Aynı çağrı takip edilir; Stop bildirimi tek
başına tamamlanma kanıtı sayılmaz. Önceki ara bulgular korunur.

## Uzak final bildirimi: işlenebilir kapsam tamamlandı

Kullanıcı Cloud Shell çıktısı TERMINATED/64800 saniye/STOP gösteriyor.
Başlangıç 13 Ekim 19:35:07.144 UTC, duruş 14 Ekim 01:18:17.528 UTC
(Türkiye 22:35:07 / 04:18:17); süre 5 saat 43 dakika 10 saniye.
14 Ekim 13:35:01.727602 UTC üst sınırına ulaşılmamış. İlk duruş
bildirimi tek başına nedeni ayırmıyordu; sonraki final geri okuması:

- Status `processable_months_verified_source_resolution_pending`,
  phase remaining_months, doğru V7 hash'i ve 862 işlenmiş çift.
- Tam ay sayısı 70; Haziran uygun günleri 29/29, Aralık 30/30.
- Hata/failed month/failed phase None; full_training_complete false.
- İki deferred gün/ay değişmedi. İki final summary, progress ile eşit.
- 31 Ocak gün kapanışı, aylık nominal tanı tamamlanması ve guest
  poweroff isteği launcher'da görülüyor.

Bu çıktı işlenebilir bölüm tamamlandığında beklenen sözleşmeyle uyumlu;
erken kapanış yeni hata veya süre sınırına atfedilmedi. Asıl hedef 72 ay;
13 Haziran 2018 ve 31 Aralık 2023 çözülene kadar 70 tam ay ve iki kısmi
ay olarak raporlanır. Bunlar uydu tanı/işleme çıktılarıdır; nihai etiket,
model veya yerel bilimsel ürün bayt kabulü değildir. Yeni uzun üretim
başlatılmaz; kalan iki gün için kaynak çözümü ayrıca araştırılacaktır.

Kanıt kullanıcı seçilmiş alan geri okumasıdır. Tam existing_months
listesi ve dosya baytları henüz alınmadı; bağımsız VM sorgusu yok.
`outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/remote_final_user_readback_20261014.json`,
SHA-256 `a18bdb8a55870ea53e7d745da44e0ff15f3cf5f54dd0c573df9207db8405eea6`.

## Sonraki adım: yalnız public final arşivi

VM SSH'de üretim betiği çalıştırılmadan şu arşiv oluşturulur. Beş explicit
public dosya alınır; private bağlantı, token, giriş dosyası veya ham veri
arşivlenmez. VM kapalıysa yalnız indirme için kısa Start gerekir.

```bash
archive="$HOME/gcp_v7_final_$(date -u +%Y%m%dT%H%M%SZ)_logs.tar.gz"
if tar -czf "$archive" \
  -C "$HOME/wildfire-gcp-production-v1" \
  progress.json acceleration_run_summary.json continuation_summary.json \
  resource_samples.csv \
  -C "$HOME" gcp_source_aware_launcher_v7.log; then
  sha256sum "$archive"
  printf 'Download: %s\n' "$archive"
fi
```

SSH Download File ile yazdırılan yol indirilir; yerelde
`outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/received/`
klasörüne konur ve VM Stop yapılır. Arşiv yeni kayıt olarak korunacak;
summary eşitliği, ay kimlikleri, 59 uygun gün, protokol/manifest/hash
kimlikleri ve kaynak örnekleri yerelde geri okunacaktır. Bu log arşivi
bilimsel payload baytlarının tamamını içermez; ayrı kabul sınırı korunur.

## Yerel final arşivi ve katalog geri okuması

Kullanıcı arşivi aktardı ve indirme sonrası VM Stop teyidi verdi.
`gcp_v7_final_20261014T113827Z_logs.tar.gz`, 318.086 bayt;
SHA-256 `61fc0aa9c59c3bb2ca37a01f0f2849907c364775d057aa04cd9dd694716bcb5c`.
Arşiv beş beklenen normal dosyayı içeriyor; yol/bağlantı/tekrar üye ve
30 MB genişleme sınırı kontrol edildi, dosyalar diske açılmadı.

Yeni salt okunur `scripts/cloud/verify_gcp_v7_session_logs.py` ile:

- Üç final JSON eşit; exact 70 eğitim ayı ve 210 çağrı günü doğrulandı.
  Günler Ocak–Mayıs 2018'in 151 günü, Haziran'ın 29 uygun günü ve
  Aralık'ın 30 uygun günüdür. İki ertelenen gün/ay tam kabulden dışlanmış.
- V7/registry, manifest/controller, scan-time adaptörü ve protokol hash'leri,
  gözlem unknown/negatif false/tam eğitim false koşulları eşleşti.
  Üretim paketleri ve 22 korunan girdinin hash'i değişmedi.
- Donmuş pairs.csv içindeki 18.711 nominal kimliğe karşı log denetlendi.
  862 yeni çift satırı, 6 katalogdan çıkarılan yeniden kullanım, 171 gün
  kapanışı ve 64 ay yeniden kullanım satırı tutarlı. Yeni kapanan aylar
  Ocak, Şubat, Mart, Nisan ve Mayıs 2018. 39 gün yalnız state'te bulunuyor:
  önceki Haziran 1–9 ve Aralık'ın 30 günü; yeniden üretim diye sayılmadı.
- Son başarılı çağrı seçildi; öncesindeki yedi prefix satırı sayaçlardan
  dışlandı. Bu prefix eski OAuth hata denemesini ve yeni arşiv receipt
  satırını da içerir. Üç aşama sırası ve tek kapanma isteği geçti.
- 8.463 kaynak örneğinde son üretim süresi 19.839,589 saniye (5:30:39,589).
  En az disk boşluğu 7,46 GiB, kullanılabilir RAM 111,89 GiB; süreç ağacı
  RSS zirvesi 10,95 GiB. Örneklenmiş 4 GiB rezerv ihlali veya sayısal
  anomali yok. Ortalama CPU %9,05; restore/metadata dahil bütün çağrı
  ortalaması olduğundan hesaplama hızlanması veya yeni darboğaz kanıtı sayılmaz.

Tam kontrol socket bağlantıları engellenerek tekrarlandı; ağ/Drive/VM
işlemi yok. Yeni denetleyici ve ortak tarihsel okuyucu için 36 davranış
kontrolü geçti; lint/format geçti. İlk test çağrısının dört dosya testi
sandbox geçici dizin izni nedeniyle kurulamamıştı; yeni ve workspace
içinde bir basetemp ile çözüldü. Arşiv veya accepted sonuçlar değiştirilmedi.

Kabul kaydı
`outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/accepted_final_readback_20261014.json`,
SHA-256 `5e7adb9eab5ba2483717751573271916ef0dff83ec5e2eac213eede2f58a6df0`.
İlk denetim raporu da ayrı korunur; son kayıtta lint düzeltmesi sonrası
denetleyici hash'i kayıtlıdır. Komut:

```powershell
.\.venv\Scripts\python.exe scripts/cloud/verify_gcp_v7_session_logs.py `
  --received outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/received/gcp_v7_final_20261014T113827Z_logs.tar.gz `
  --out outputs/gcp_acceleration/source_aware_v7_session_2026-10-14/new_readback.json
```

Bu yerel log/katalog kapanış kabulüdür. Bilimsel payload/checkpoint
baytları arşivde yok; 39 restore günün ve kullanılan ürünlerin bayt kabulü
ve canlı Drive geri okuması yapılmadı. Asıl 72 aylık hedefte iki kaynak
günü açık kalır. Yeni uzun üretim başlatılmaz ve doğrulanmış bağımsız
sonuç yedeği alınmadan VM diski silinmez; kaynak çözümü ve ürün teslimi
bir sonraki aşamadır.
