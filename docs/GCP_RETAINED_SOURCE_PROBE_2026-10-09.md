# Kalan ham dosyalarla sınırlı yerel teşhis

**Teşhis tamamlandı:** SNPP:2023365.0106 yerel kontrolü 6,562 saniyede
gerçek geolocation girdi eşleştirmesinde reddedildi. Bu yönergeyi tekrar
çalıştırma; yeni adım [ilgili başlıkları toplamak](GCP_GEOLOCATION_HEADER_CAPTURE_2026-10-09.md).

İndirilen `gcp_acceleration_failure_2026-10-09.zip` doğrulandı:
54.071.572 bayt, 75 üye, açılmış toplam 63.100.208 bayt.
SHA256 `f157cf60b334d4e815948721670f959ad49f2a350b3b7ff4c090eed07c39db27`.
CRC, tüm yakalama hash'leri, donmuş iki paket kimliği ve Aralık katalog/
UMM kaynak planı kontrolü geçti. 34 görevin 68 ham dosya boyutu doğru.
20 tam çift ZIP'i, donmuş native checkpoint/CSV/geometri/tarama kontrollerini
eksiksiz geçti; 14 görev yarım. Aralık 27–31 günlük kapanışları yok.

3.862 kaynak örneğinde en az 15,355 GiB boş disk / 111,468 GiB
kullanılabilir RAM var; süreç ağacı RSS tepe 11,153 GiB. Örneklerde
4 GiB rezerv ihlali yok. Bu örnekler her anı ve alt süreçlerin 6 GiB adres
alanı sınırını kanıtlamaz. Yarım görevler tek tek veri hatası değildir:
uygulama hata aldığında diğer çalışan çocukları da durdurmuş.

20 tamamlanmış üründe bozuk bilimsel çıktı bulunmadı. Eski çağrının kesin
`ValueError` kontrolü hâlâ bilinmiyor. Drive geri okuma hatası, ağ/login,
çocuk süreç veya yarım ham dosyanın checksum/içerik hatası arasında bu
arşivden kesin seçim yapılamıyor. Tam aylar bu arşivde bulunmadığından
yeni Ekim/Kasım ayları için yerel bağımsız kabul verilmedi.
Makine manuel durum bildirimiyle Stopped.

## Kısa teşhisi çalıştır

Bu aşamada uzun üretim komutunu çalıştırma. VM'deki 14 yarım görev,
yeniden indirme yapmadan tek işçiyle kontrol edilecek. İki boş çıktı
görevi önce gelir; ilk yerel hata bulunursa teşhis durur. Her çocuk
180 saniye, bütün görev döngüsü 900 saniye bütçeyle sınırlı. Bu yeni
teşhis zaman aşımı, eski üretimin hata nedenini kanıtlamaz.

1. VM → **Start → SSH**.
2. **Upload File** ile şu tek Python dosyasını yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\diagnosis_2026-10-09\probe_gcp_retained_sources.py`
3. **VM SSH terminalinde**:

```bash
if printf '%s  %s\n' \
  '2ae1c48c87ce69701189319fb0c981fc1839bd8d263c303bdaecaa5d5d22a787' \
  "$HOME/probe_gcp_retained_sources.py" | sha256sum --check; then
  ~/wildfire-gcp-work/.venv/bin/python ~/probe_gcp_retained_sources.py
fi
```

`Detached local probe PID` gelince işlem SSH'den bağımsız sürer.
Yaklaşık bir dakika sonra ilerlemeyi kontrol et:

```bash
tail -n 15 ~/gcp_local_probe_launcher.log
```

`Download:` görünene kadar birer dakika arayla aynı komutla bak.
`Probe stopped` / `Probe check failed` gelirse çıktıyı paylaş ve VM'yi
durdur; üretime geçme.

4. SSH → **Download File**:
   `/home/enesnuhgocek1/gcp_acceleration_local_probe_2026-10-09.zip`
5. Yerelde `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\received\`
   klasörüne koy ve indirme sonrası **VM → Stop** uygula.
   Teşhis VM'yi kendisi kapatmaz; mevcut Google sekiz saat sınırı aynı kalır.

Önceki yüklediğin `collect_gcp_acceleration_failure.py` dosyası aynı
hash ile VM ev dizininde bulunmalı; tekrar bağlantı JSON'u yüklemek yok.
Paket hash'leri ve Aralık planı hash'i baştan kontrol edilir. Mevcut iş
kilidiyle çalışan üretimle çakışması engellenir. Yeni sonuçlar yalnız
`~/gcp_acceleration_local_probe_2026-10-09/` içine yazılır; üretim
çıktıları ve checkpoint'ler değiştirilmez. Bytecode yazımı kapalı.
Earthdata/OAuth login ve indirme çağrısı yapılmaz; çocukların soket
bağlantıları audit hook ile reddedilir. Parola/bağlantı JSON'u okunmaz.
Gerçek donmuş bilimsel kodun kaynak/CMR checksum, native alan/tarama ve
geometri kontrolleri aynı kalır; hiçbir başarısız kaynak kabul edilmez.

## Yerel kontroller

- Bağımsız gerçek veri geri okuması: 20/20 çift geçti.
- Yeni okuyucu/probe kontrolleri: 6 test geçti, Ruff geçti.
- Testlerde ağ bağlantısı kurulmadan engellendi, yanlış kaynak bilimsel
  aşamaya geçmedi, yalnız ayrı çıktı klasörü kullanıldı ve harici hata
  metni/manifestte olmayan kaynak satırları günlükten çıkarıldı.
- Gerçek Linux ham dosya yeniden denemesi henüz yapılmadı. Sonuç başarılı
  olsa da önceki hatanın kesin nedeni otomatik kanıtlanmış sayılmayacak.

Yerel rapor:
`outputs/gcp_acceleration/diagnosis_2026-10-09/readback/failure_readback.json`.
Okuyucu: `scripts/cloud/verify_gcp_acceleration_failure.py`.
Donmuş üretim/controller ZIP'i ve production_readiness.json değiştirilmedi.
