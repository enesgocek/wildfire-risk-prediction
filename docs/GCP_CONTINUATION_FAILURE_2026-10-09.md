# Kaynak ertelemeli oturumun kapanışı ve inceleme paketi

Kayıt tarihi: 9 Ekim 2026. Kanıt, kullanıcı tarafından paylaşılan Cloud Shell
instance sorgusu ve VM launcher/progress çıktısıdır. Yeni sonuç arşivi henüz
yerelde bağımsız bilimsel geri okumadan geçmedi.

## Kapanma ve ilerleme

VM 10:39:32,307–18:13:05,417 UTC arasında 7:33:33,110 çalıştı. Türkiye
saatiyle 13:39:32–21:13:05. Google sınırı 18:39:24,369866 UTC idi.
Sınırdan 26:18,953 önce kapanma ilk incelemede süre rezerviyle uyumlu
görünüyordu. Son günlük, bunun normal rezerv duruşu olarak raporlanmadığını gösterdi:

- `status=failed_checkpoints_retained`, `error_type=RuntimeError`.
- `failed_month=2022-11`, kaydedilmiş son aşama `pair_publication`.
- `Guest poweroff requested: True`; ardından güvenli hata sınıfı bildirimi.

`failed_phase`, telemetride son kaydedilmiş aşamadır; tek başına hatanın kesin
satırını veya Drive/NASA kaynaklı olduğunu kanıtlamaz. Ayrıntı arşivinden
yerel ürünler, varsa çocuk hata kaydı ve kaynak ölçümleri incelenecek.

Uzak progress 12 tam ay listeliyor: Aralık 2022–Kasım 2023. Bu, nominal
72 eğitim ayının 12'sidir; tam eğitim/etiket veri seti anlamına gelmez.
Kasım 2022 ilk 8 gün ve Aralık 2023 ilk 30 gün de kayıtlıdır. Oturumun
250 günlük listesi Aralık 2022, Ocak–Haziran 2023, Kasım 2022 1–8 ve
Aralık 2023 1–30 tarihlerinden oluşuyor. Önceki Temmuz–Kasım 2023 günleri
bu oturum sayacına dahil değil. Yeni çift sayacı 1.989, yeniden kullanılan 10.
Sayaçlar uzak bildirimdir; bağımsız yerel kabul yapılmadı. 31 Aralık ve iki
SNPP kaynağı ertelenmiş; tam eğitim false, gözlem unknown, negatif izin false.

Paylaşılan metin SHA-256:
`4bf57a1448433960adc4a875e5fc232773c85b8e836a30e8ff4eeb2c19d40908`.
Yerel özet: `outputs/gcp_acceleration/continuation_failure_2026-10-09/remote_summary.json`.

## İnceleme aracı

Yeni `scripts/cloud/collect_gcp_source_aware_failure.py`, önceki kabul edilmiş
forensic araçtan ayrı oluşturuldu. Orijinal collector, continuation wrapper,
controller ve bilimsel paket değişmedi. Arşiv başarısız Kasım planını,
filtrelenmiş progress/log, kaynak ölçümleri ve kalan native/pair/day çıktılarını
içerir; tamamlanmış bütün ayların sonuç arşivi değildir.

Orijinal/controller manifest ve üye hash'leri, continuation wrapper ve kamuya
açık kaynak erteleme registry hash'i doğrulanır. Üç ilerleme özeti eşleşmelidir.
Mevcut iş kilidi paylaşılmış/nonblocking olarak alınır; aktif üretim varsa
arşivleme reddedilir. Symlink, görev kimliği, boyut, üzerine yazma ve ZIP CRC
kontrolleri vardır. Toplam genişletilmiş çıktı sınırı 150 MB'dır.

Ham uydu dosyalarının içerikleri ve OAuth bağlantıları okunmaz. Bilinen
günlük satırları ile yalnız mühürlü koddan çıkarılmış literal hata kontrol
adları aktarılır; bilinmeyen hata metni `CLASS_ONLY` olur. Arşiv progress'i
güvenli alanlara daraltılmış görünümdür, kaynak dosyanın bütün baytları değildir.
İzinli arşiv üyelerinin SHA-256 değerleri capture manifestinde tutulur.

12 yeni test geçti: gerçek native çıktı/hash geri okuması ve değişmeme,
ham/özel dosyaya erişmeme, doğru launcher kullanımı, serbest hata metninin
dışlanması; wrapper/registry/özet uyuşmazlığı, üzerine yazma, boyut ve kaynak
politikası reddi. Ruff kod ve biçim kontrolleri başarılı. Linux kilidi önceki
forensic aracın aynı uygulamasıdır; yeni araç henüz gerçek VM'de çalıştırılmadı.

## Kullanıcı adımları

1. Yalnız bu yeni dosyayı hazırla:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_2026-10-09\collect_gcp_source_aware_failure.py`.
2. VM Start → SSH; Upload File ile ev dizinine yükle. Üretimi başlatma.
3. SSH terminalinde:

```bash
if printf '%s  %s\n' \
  '8e0419b0f4060a3cdec9c167efa08054fd34c60ef9d290d43a6e038f9fa32e0d' \
  "$HOME/collect_gcp_source_aware_failure.py" | sha256sum --check; then
  ~/wildfire-gcp-work/.venv/bin/python ~/collect_gcp_source_aware_failure.py
fi
```

4. Başarılı `Evidence collected` ve `Download` satırı sonrası SSH Download File:
   `/home/enesnuhgocek1/gcp_source_aware_failure_2026-10-09.zip`.
5. Arşivi yerelde şu dizine koy:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_2026-10-09\received\`.
6. İndirme tamamlanınca VM tekrar Stop. Hata varsa kısa hata satırını paylaş;
   başka klasörleri veya özel JSON'ları arşivleme.

Arşiv gelince paket bütünlüğü, kalan görevlerin bilimsel geri okuması,
CPU/RAM/disk ölçümleri ve hata kaydı değerlendirilecek. Temel hata nedeni
belirlenmeden yeni uzun oturum veya checkpoint silme önerilmiyor.

## İndirilen arşivin yerel denetimi

Arşiv 55.049.295 bayt; SHA-256
`74273df994a005372be4c3916c569a8670fde801d1816e60bed78b6a0841d260`.
64 üye, 58.591.742 bayt genişletilmiş içerik. CRC, izinli üye adları,
tekrar/boyut sınırları, capture hash'leri, orijinal/controller kimlikleri ve
kaynak erteleme registry hash'i geçti. Kasım 2022 kaynak planı orijinal
katalog/metadata sözleşmesiyle geri okundu; plan SHA-256
`eef25617a86cd9f5ab41def17d50975f6d4cb521a517a1317a7c696931fb5858`.

29 görev kaldı. İçindeki 19 tamamlanmış pair ZIP'in tamamı donmuş native
`restore_pair` kontrolünden geçti. Diğer 10 görevde tam ZIP yok; dokuzunda
kısmi audit/merkez çıktısı var. Bir görevde geolocation dosyası mevcut
değil; bu stat bilgisi indirme hatasının kesin nedeni değildir, kapanmada
kesilmiş başka bir iş de olabilir. Ham dosyalar arşivde olmadığı için
kaynak baytları yeniden hesaplanmadı. Tamamlanmamış beş gün 9–13 Kasım.
Arşivde `continuation_failure.json` bulunmadı. Kesin tarihsel exception hâlâ
belirlenmedi; Drive veya NASA hatası olarak ilan edilmedi.

12.018 kaynak örneğinde en az 12,9 GiB boş disk ve 111,6 GiB kullanılabilir
RAM, en fazla yaklaşık 11,6 GiB süreç ağacı RSS ölçüldü. Kaydedilen dört GiB
rezerv ihlali yok. Örnekleme bütün anları, çocuk virtual-memory sınırını
veya işletim sistemi olaylarını kanıtlamaz. Kaynak yetersizliği gösterilmedi.

Kontrol ağ erişimi Python audit hook ile engellenerek ikinci kez tekrarlandı;
aynı 19 çıktı geçti. Yeni doğrulayıcı `scripts/cloud/verify_gcp_source_aware_failure.py`.
Rapor `outputs/gcp_acceleration/continuation_failure_2026-10-09/readback_network_blocked/failure_readback.json`.
Bu arşivde tamamlanan 12 ayın bütün sonuçları bulunmadığı için bu aylar
bağımsız yerel kabul edilmiş sayılmadı. VM'nin indirme sonrası yeniden Stop
yapıldığı kullanıcı tarafından teyit edildi; araçla VM'ye müdahale yapılmadı.

## Sıradaki salt okunur Drive kontrolü

Yeni `diagnose_gcp_continuation_publication.py`, mevcut orijinal yardımcıları
hash doğrulamasıyla yükler ve iş kilidini alır. OAuth yenileme, güncel kota,
scope içi nesne listesi, Kasım manifesti ve kalan 19 yerel ZIP'in uzak payload/
completion eşleşmesini okur. Drive nesnesi yükleme, silme, onarma veya üretim
başlatma yok; yalnız yeni public teşhis JSON'u ev dizinine yazılır.
OAuth token yenilemesi auth endpoint POST kullanır; Drive nesne işlemleri
GET ile sınırlandırılır. Başarılı güncel erişim, geçmiş hatanın nedenini
kanıtlamaz. İç süre sınırı 230 saniyedir; hata ayrıntısı yalnız izinli HTTP
kodu/neden sınıflarıyla gösterilir. Eski HTTP response metni kaydedilmediği
için geçmişteki hata doğrudan geri getirilemez.

Yeni kontrol/geri okuma için 10 test geçti; bozuk completion/payload reddi,
eksik payload, orphan ayrımı, Drive POST/PATCH/PUT/DELETE reddi, değiştirilmiş
yardımcının yüklenmemesi ve gizli hata metninin dışlanması sınandı. Ruff başarılı.
Gerçek VM Drive teşhisi henüz yapılmadı; yeni uzun oturum başlatılmadı.

1. VM Start → SSH; şu yeni dosyayı Upload File ile yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_2026-10-09\diagnose_gcp_continuation_publication.py`.
2. SSH terminalinde:

```bash
if printf '%s  %s\n' \
  '7a3195ebcef67057de1b449197bd463611759994bc7b969c95a2cd17365678f2' \
  "$HOME/diagnose_gcp_continuation_publication.py" | sha256sum --check; then
  timeout 240s ~/wildfire-gcp-work/.venv/bin/python ~/diagnose_gcp_continuation_publication.py
fi
```

3. `Download` satırında belirtilen dosyayı indir:
   `/home/enesnuhgocek1/gcp_continuation_publication_probe_2026-10-09.json`.
   Aynı `received` klasörüne koy ve VM tekrar Stop.
4. Teşhis aracı setup/dependency hatası verirse kısa çıktı paylaşılır;
   üretim komutu çalıştırılmaz. Mevcut `collect_gcp_source_aware_failure.py`
   ve `diagnose_gcp_production_manifest.py` yardımcılarının hash'leri zorunludur.
