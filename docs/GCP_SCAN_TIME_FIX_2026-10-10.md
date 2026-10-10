# Tarama zamanı çözümleme hatası — 10 Ekim 2026

Sonraki gerçek kaynak denemesi 203 scan ve native hücre sayımlarında geçti.
[Kabul kaydı ve V3 uzun devam adımları](GCP_SOURCE_AWARE_V3_2026-10-10.md)
ayrı belgededir; aşağıdaki hazırlık ve ilk kontrol sınırları tarihsel kayıttır.

## Gerçek kaynakta yeniden üretilen hata

`SNPP:2022252.2230` için alınan ağ kapalı kontrol JSON'u 2.824 bayt;
SHA-256 `528f74b8091232a8e54ed598b20d5acedec89e1ee07401eacbacb3b3c65476a5`.
Kontrol betiği, snapshot helper'ı, Eylül 2022 planı ve güvenli alan kimlikleri
yerelde eşleştirildi. Dosya 10 Ekim 01:33:45 UTC'de (04:33 Türkiye) üretildi.
Kullanıcı indirme sonrasında VM'nin Stopped olduğunu teyit etti; canlı API
sorgusu yapılmadı. Orijinal dosya korunup ayrı `scan_replay_readback.json`
kabul kaydı yazıldı.

Dondurulmuş `audit_l2_observation_timing.py` içindeki `source_scans`,
184. satırda `ValueError` üretti. Başlangıç zamanlarının 203 satırından
202'si kesirli saniye, biri tam saniye. Varsayılan Pandas çözümleme bu
karışık hassasiyeti okuyamadı. Bitiş ve orta zamanların varsayılan çözümlemesi
geçti. Üç sütunun açık ISO çözümlemesi ham geolocation dosyasından özgün
TAI93 dönüşümüyle elde edilen zamanlarla **nanosaniyesine kadar** eşleşti.
Üretim girdilerinin işlem öncesi/sonrası hash'leri aynı; indirme ve üretim
yazımı sıfır. Önceki sentetik hipotez bu gerçek kaynakta yeniden üretildi.

Bu bulgu güncel kaynaktaki hata noktasını belirler. İlk tarihsel oturumun
serbest exception metni kaydedilmediği için o exception nesnesi doğrudan
karşılaştırılamaz. Bu JSON tam scan/hücre fonksiyonunun başarıyla bittiğini,
başka hata olmayacağını veya 14 aylık sonuçların yeni yerel kabulünü kanıtlamaz.
Önceki [snapshot incelemesinde](GCP_V2_FAILURE_2026-10-10.md) kaydedilmiş
disk/RAM rezervi tükenmesi görülmedi; kaynak boyutları planla eşleşmişti.

## Dar kapsamlı çözüm ve kabul sınırı

`scripts/cloud/verify_gcp_scan_iso_adapter.py` içinde hazırlanan adapter,
yalnız hash ile doğrulanmış özgün scan modülünün çalışma anındaki Pandas
isim alanını kısa süreyle sarar. Üç scan UTC sütununda tam olarak
`to_datetime(series, utc=True)` çağrısını açık `format="ISO8601"` ve
`errors="raise"` ile çözümler. UTC ve en fazla dokuz kesir basamağı şeması
zorunludur. Saniye yuvarlama, hata yutma, `NaT` üretme veya başka timezone
kabulü yoktur. Özgün fonksiyonun ham zamanlarla nanosaniye eşitlik kontrolü,
scan sırası/kalitesi, kaynak hash'leri ve hücre sayımları aynen çalışır.

Adapter bütün Pandas kütüphanesini değiştirmez. Özgün kaynak dosyası ve kod
nesnesi hash/yoluyla doğrulanır; dosya yazılmaz. Başarı veya hatada modülün
Pandas isim alanı geri yüklenir. Bu bir çalışma zamanı davranış değişikliğidir;
raporda `runtime_parser_adapter_applied=true` olarak açıkça belirtilir.
Kaynak dosyalarının değişmemesi, yürütme davranışının değişmediği iddiasına
dönüştürülmez. Henüz üretim paketine veya checkpoint'e uygulanmadı.

Yeni araç mevcut iki ham dosyayı ve referansları okur; önceki gerçek replay
JSON'unun hash'ini doğrular. Aynı girdi hash'leriyle özgün fonksiyonu adapter
altında çalıştırır. Yeni indirme, kimlik bilgisi okuma, Drive erişimi, kaynak
yönetimi veya üretimi sürdürme yoktur. Ağ/DNS engeli, mevcut iş kilidi,
6 GiB adres alanı sınırı ve yeni JSON adı korunur. Nihai kabul; üç sütunda
203'er satırın çözülmesi, özgün native hücre sayımlarının eşleşmesi, tüm
girdi hash'lerinin aynı kalması ve isim alanının geri yüklenmesiyle mümkündür.

## Yerel kontroller

14 yeni adapter kontrolü dahil **76 ilgili test geçti**. Yerel küçük fixture'da
hash'i gerçek dondurulmuş kodla aynı `source_scans` fonksiyonu değiştirilmeden
çalıştırıldı: karışık başlangıç zamanı önce ValueError verdi; adapter ile
bütün özgün guard'lar ve sıfır seçilmiş merkezlerin sayımı geçti. Başka
kontrollerde yanlış sensor mode ve mikro saniyelik ham zaman uyuşmazlığı
özgün guard'lar tarafından reddedildi. İsim alanı geri yüklendi, fixture
dosyalarının bütün baytları aynı kaldı. Ek olarak UTC dışı/eksik/çok hassas
zaman, yanlış çağrı, değişmiş helper/kaynak/evidence reddi test edildi.
Ruff geçti. Fixture kontrollü küçük bir örnektir; gerçek 203 scan kaynağının
adapter ile tam denemesi henüz yapılmadı. Canlı bitki örtüsü kaynakları,
kuyruk, bilimsel paketler, registry ve kabul edilmiş sonuçlar değişmedi.

## Son kısa VM kontrolü

1. VM Start ve SSH. Üretim komutunu çalıştırma.
2. Yalnız yeni dosyayı Upload File ile ev dizinine yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\continuation_failure_v2_2026-10-10\verify_gcp_scan_iso_adapter.py`.
   Önceki iki kontrol helper'ı ve VM'de üretilen replay JSON'u kalmalıdır.
3. SSH'de çalıştır; en fazla dört dakika boyunca Download satırını bekle:

```bash
if printf '%s  %s\n' \
  'e729c56aced66feb6b3a461773c7d694e43d4f35b586d6060f8cabceee968a39' \
  "$HOME/verify_gcp_scan_iso_adapter.py" | sha256sum --check; then
  timeout 240s ~/wildfire-gcp-work/.venv/bin/python \
    ~/verify_gcp_scan_iso_adapter.py
fi
```

4. `Download:` satırındaki `gcp_scan_iso_adapter_proof_<UTC>.json` dosyasını
   aynı `continuation_failure_v2_2026-10-10/received/` klasörüne indir.
5. VM Stop. Araç otomatik kapatmaz veya üretimi başlatmaz. Timeout/hata
   olursa kısa terminal çıktısı paylaşılır ve VM yine Stop yapılır.

`passed_single_retained_source` ve JSON'un yerel çapraz kontrolü geçerse,
adapter kimliğini açık kaydeden sürümlü devam paketi hazırlanacak. Önceki
tam aylar tekrar hesaplanmadan doğrulanarak kullanılacak; kısmi kaynaklar ve
eski hata kayıtları korunacak. 31 Aralık 2023 ertelemesi, negatif etiket
yasağı ve `daily_observation_status=unknown` değişmeyecek. Bu kısa deneme
tam dönem bitişi veya uzun oturumda bütün hata türlerinin çözümü değildir.
