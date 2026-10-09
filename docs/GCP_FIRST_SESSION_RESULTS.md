# İlk uzun oturumun günlük denetimi — 8 Ekim 2026

İndirilen gcp_production_session_logs.tar.gz dosyasını received
klasörüne koydum ve indirme sonrası VM'yi tekrar Stop yaptığımı teyit ettim.
Arşiv 4.451 bayt; SHA256
`3f22eb6cc3e478f6897764537d2dd7e5be281e20208639565eecb76e58af0840`.
Üç düzenli üye yalnızca progress.json, launcher.log ve supervisor.log;
güvenli sınırlarla bellekte okundu, tar dosyaları diske çıkarılmadı.

Orijinal manifest SHA ve 11 paket üyesi doğrulandı. Son çalışma bloğunda
hata yok; eski RuntimeError/exit 1 önceki başarısız oturuma ait. Son çıkış
0 ve Guest poweroff requested True. Progress paused_at_runtime_reserve.
Bu, kayıtları koruyan normal süre rezervi duruşudur; bütün dönem tamamlanmadı.

| Ölçü | Kanıtlanan günlük/katalog sonucu |
|---|---|
| Yeni tam aylar | 2023-08, 2023-09 |
| Daha önce hazır | 2023-07 |
| Tam günlük kayıt | 75: Ağustos 31, Eylül 30, Ekim 14 |
| Kaydedilmiş çift | 673, reused 0 |
| Tam günlere ait çift | 663 |
| 15 Ekim'de kaydedilmiş çift | 10/10; günlük birleşim/kapanış bekliyor |
| Tamamlanmamış ay | 69, Ekim dahil |
| Henüz işlenmemiş nominal çift | 17.768 |
| VM çalışma süresi | 7:15:49,624 |
| Çift / VM saati | 92,651 |

Son günlük gün listesi orijinal katalog günlerinin ardışık prefix'i; bütün
Pair saved/verified kimlikleri tekil ve katalogda mevcut. 663+10=673;
tam gün/ay logları progress ile birebir. 15 Ekim çiftleri sonraki başlangıçta
Drive'dan geçerli completion/ürün geri okuması başarılıysa yeniden indirilmez;
günlük birleştirme hâlâ yapılmalıdır. Gözlem unknown, negatif izin false.

Paylaşılan Cloud Shell çıktısı başlangıç 7 Ekim 23:55:37,862, duruş 8 Ekim
07:11:27,486 Türkiye saati. Google sınırı 07:55:30,424; rezervli duruş ile uyumlu.
Aynı hız kalan çiftlerde sürseydi yaklaşık 191,77 aktif saat senaryosu;
yıl/kaynak boyutu farkı, restore ve son birleştirme nedeniyle bitiş garantisi değil.
Ayların gerçek ayrı süresi günlüklerde timestamp bulunmadığından ölçülemedi.

Rapor: `outputs/gcp_production_diagnosis/session_2026-10-08/session_log_verification.json`.
Bu denetim **günlük ve katalog tutarlılığıdır**. Yeni Drive API isteği veya
bilimsel sonuç ZIP'lerinin bağımsız yerel geri okuması yapılmış değildir.
Sıradaki adım mevcut yerel manifest/sonuç ZIP'lerini ve 15 Ekim'in kaydedilmiş
çıktılarını tek arşivle almak; ham NASA dosyaları ve özel bağlantı dışarı alınmaz.

Kısa kontrol açılışında SSH'de mevcut çıktılardan arşiv oluşturma:

```bash
tar -czf ~/gcp_production_first_session_results.tar.gz \
  -C ~/wildfire-gcp-production-v1 \
  progress.json \
  months/2023-08/manifest.zip \
  months/2023-08/month_results.zip \
  months/2023-09/manifest.zip \
  months/2023-09/month_results.zip \
  months/2023-10/manifest.zip \
  months/2023-10/daily_archives \
  days/2023-10-15/inputs
```

Bu komut yeni üretim veya ham indirme başlatmaz. Mevcut dosyaları arşivler;
tar hata verirse eksik arşiv doğrulanmış sonuç sayılmaz. Download File ile
arşiv alınır, VM tekrar Stop yapılır. Sonraki yerel doğrulama orijinal donmuş
metadata/çift/gün/ay kurallarını kullanacak; dosyalar gelmeden başarı ilan edilmez.
Kod/paket/VM kapasitesi değiştirilmedi, yeni Git push yapılmadı.

## Bağımsız bilimsel geri okuma tamamlandı

Sonuç arşivi 72.039.268 bayt; SHA256
`1801d0275ae82b6bb98fe7e3caff7ba7e3758c32ae481ecb9ad6e1ed7f769c33`.
120 düzenli üye, toplam genişletilmiş boyut 130.877.559 bayt. Beklenen
dosya listesiyle birebir; link, yol kaçışı, yabancı dosya, tekrar ve boyut
sınırları denetlendi. İkinci indirme sonrası da VM Stop teyit ettim.

Yeni salt okunur doğrulayıcı orijinal paket/metadata SHA'larını kontrol ederek
donmuş bilimsel kodu kullandı. Ağustos 556, Eylül 522, Ekim 552 kaynak UMM'i
katalog ürün/kimlik/zaman/byte/checksum bilgileriyle doğrulandı. Aylık receipt,
gün takvimi, scope/worker/payload SHA, nested gün ZIP'leri ve unmatched kayıt
listeleri geçti. 75 günün her birinde 2.899 grid kimliği, alan/oran sınırları,
native merkez sayımlarının toplamları, tarama zamanları ve bağımsız zaman
aralığı birleşimleri, kaynak/alan journal bağlantıları kontrol edildi.

15 Ekim'in 10 checkpoint'i ve dokuzar bilimsel ürünü dosya hash'i ve orijinal
native compare_pair ile geri okundu. GeoPackage katmanlarının geçerliliği,
CRS/grid kimlikleri ve alanların CSV'yle eşleşmesi geçti. Bütün 673 çiftin
75 günlük özeti ve 10 pending-gün çifti mevcut kapsamı tam açıklıyor.
15 Ekim günlük union/Drive daily completion hâlâ yapılmış sayılmaz.

Doğrulayıcı `scripts/cloud/verify_gcp_production_session_results.py`;
7 anlamlı archive/altered-completion testi ve Ruff kod/biçim kontrolü geçti.
Gerçek veri denetimi yaklaşık 129,89 saniyede tamamlandı. Rapor:
`outputs/gcp_production_diagnosis/session_2026-10-08/scientific_readback/scientific_readback_report.json`.
Durum independent_first_session_result_readback_passed.

Sınırlar: bu yerel ürün geri okumasıdır; yeni canlı Drive API bağımsız
readback'i değil. Tamamlanmış 75 günün union geometrisi pair journal'lardan
baştan hesaplanmadı; sayısal/zaman/kaynak kontrolleri yapıldı. Ham uydu
verisi yeniden indirilmedi veya işlenmedi. Etiket unknown/negative false.

15 Ekim'in on kaydındaki performans örneği: toplam kaynak 1.833.823.856 bayt,
işçi elapsed_seconds 33,31–85,74 saniye, ortalama 63,11 saniye; peak RSS
0,555–0,680 GiB. Bu tek günün on çifti bütün dönem bellek/hız üst sınırı
değildir; elapsed indirme/işleme aşamalarını ayrı ayırmıyor. CPU örneği ve
bu metrikler mevcut VM'de paralellik/dalga/seri kayıt ölçümünü öncelemeyi
destekliyor; daha büyük VM için gerçek hız kazancı henüz kanıtlanmadı.
Yeni kapasite/işçi paketi başlatılmadan güncel deneme kredisinin doğrulanması planlandı. Donmuş üretim paketi ve mevcut sonuçlar değiştirilmedi; push yok.
