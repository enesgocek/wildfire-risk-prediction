# Aralık üretiminin erken kapanışı ve teşhis

**Sonuç arşivi geldi ve doğrulandı:** 20 tam çift bilimsel kontrolden
geçti; 14 yarım görev kaldı. RAM/disk örnekleri rezerv ihlali göstermiyor.
Yeni adım [mevcut ham dosyalarla sınırlı yerel teşhis](GCP_RETAINED_SOURCE_PROBE_2026-10-09.md).
Aşağıdaki arşiv toplama adımları tamamlandı, tekrarlanmamalı.

Kaydedilen VM günlükleri `ValueError`, `failed_checkpoints_retained`,
`failed_month=2023-12`, `Guest poweroff requested: True` gösteriyor.
VM 8 Ekim 21:50:46–9 Ekim 00:20:16 Türkiye saati arasında çalışmış.
Google'ın sınırı 9 Ekim 05:50:39: kapanış sekiz saat sınırından önce olmuş.
Hangi kontrolün hata verdiği bu sürümde kayda geçmemiş.
`pair_publication` son ana süreç aşaması; eşzamanlı çocuk hatasının
kesin yerini kanıtlamıyor. Kaynak/ağ/Drive/bilimsel kontrol ayrımı açık.

VM kaydına göre Temmuz–Kasım 2023 beş tam ay, Aralık 1–26 kapalı;
648 yeni çift, 10 eski çift yeniden kullanılmış. Yeni aylara yerel bağımsız
bilimsel kabul verilmedi. İki durum JSON'u aynı; analiz
`outputs/gcp_acceleration/diagnosis_2026-10-09/user_log_analysis.json`.
Teşhis öncesi VM'nin Stopped olduğunu teyit ettim.

## Tek dosyalık, kısa teşhis açılışı

Eski üretim başlatma komutunu çalıştırmadan aşağıdaki adımları uygula.
Makine tipi ve sekiz saatlik sınır aynı kalır.

1. Compute Engine → `wildfire-cpu-pilot` → **Start → SSH**.
2. SSH → **Upload File** ile yalnız şu dosyayı yükle:
   `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\diagnosis_2026-10-09\collect_gcp_acceleration_failure.py`
3. **VM SSH terminalinde** bu tek bloğu çalıştır:

```bash
if printf '%s  %s\n' \
  '0afd6e7618ec7d1d32da7d43458429faf4b0a951876e69d5e993215dfb648f31' \
  "$HOME/collect_gcp_acceleration_failure.py" | sha256sum --check; then
  timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
    ~/collect_gcp_acceleration_failure.py
fi
```

4. `Evidence collected` gelirse SSH → **Download File** ile:
   `/home/enesnuhgocek1/gcp_acceleration_failure_2026-10-09.zip`
5. ZIP'i yerelde `C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\received\`
   klasörüne koy. İndirme sonrası Compute Engine'den **Stop** uygula.
   Araç kendisi VM'yi kapatmaz. `Collection check failed` veya başka hata
   gelirse yalnız terminal çıktısını paylaş; üretimi başlatma ve VM'yi durdur.

Araç özel bağlantı JSON'unu/parolaları/tokenları okumaz. Ağ isteği, NASA ham
indirmesi ve üretim klasörüne yazma yapmaz. Donmuş iki paketi hash ile
kontrol eder; çalışan üretimle çakışmayı mevcut kilitle engeller. Mevcut
metadata arşivini, kalan native çıktıları, kaynakların sadece boyut
envanterini, kaynak örnekleme CSV'sini ve filtrelenmiş günlüğü ayrı ZIP'e
alır. Kayıtları silmez, var olan teşhis arşivinin üzerine yazmaz. En fazla
150 MB dosya toplar; 180 saniye komut sınırı vardır. Paket/controller/gate
hash'leri ve bilimsel doğrulama kuralları aynı kalır.

## Yerel doğrulama

Ruff kontrolü geçti. Gerçek donmuş paketler ve önceki üretimden native
ürünlerle 7 test geçti. Üretim dosyalarının hash'leri değişmedi; raw ve özel
bağlantı okuması testte engellendi. Metadata arşivinin tüm orijinal baytları
(eşleşmeyen katalog kayıtları dahil) korunuyor. Sınır dışı görev, uyuşmayan
durum kayıtları, değişmiş paket, dosya üzerine yazma ve boyut sınırı
reddediliyor. Windows symlink oluşturma yetkisi olmadığı için bu teste
ait gerçek symlink senaryosu atlandı; kodda symlink reddi mevcut.
Linux iş kilidi bu Windows oturumunda işletim sistemi düzeyinde sınanmadı.

Bu ZIP geldiğinde önce kalan çift/gün çıktıları ve kaynak boyutları
incelenecek. Kesin nedeni saptamadan eski komutla uzun oturum açılmayacak.
