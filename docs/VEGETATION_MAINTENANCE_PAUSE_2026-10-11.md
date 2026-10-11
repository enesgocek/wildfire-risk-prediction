# Bilgisayar bakımı için bitki örtüsü duruşu — 11 Ekim 2026

Kullanıcı bilgisayar bakımı için yerel bitki örtüsü kuyruğunun kontrollü
durdurulmasını ve yalnız daha sonra açıkça "başlat" dediğinde devamını istedi.
Otomatik yeniden başlatma veya zamanlayıcı kurulmadı. VM işi değiştirilmedi.

## Kontrollü duruş ve süreç kontrolü

Yeni yerel job `training_iso_v2_power_resume_20261011_bb85a275` durduruldu.
Gerçek Windows süreç ağacı launcher 6424, supervisor 33832 ve hazırlık
çocukları 26336/34012 olarak doğrulandı. İzole konsol listesi yalnız bu iş
ve sinyal yardımcısını içerdi; kontrollü CTRL_C_EVENT gönderildi. Mevcut
KeyboardInterrupt/final progress/kilit cleanup yolları kullanıldı; donmuş
bilimsel kaynaklar değiştirilmedi. Sinyalden hemen sonraki ilk gözlem hâlâ
running idi; cleanup tamamlanmadan duruş başarısı ilan edilmedi.

Final kayıt **18:26:43,686223 UTC / 21:26:43 Türkiye**:
`interrupted_checkpoints_retained`. Aktif batch aynı durumda, hata alanı yok.
Gerçek Windows tekrar sorgusunda launcher/supervisor/çocukları kalmadı.
İki yazıcı kilidi mevcut cleanup ile kalktı; elle silinmedi.

## Korunan veri

**45 ay**, Ocak 2018–Eylül 2021, doğrulanmış listede kaldı. Bu ayların
135 manifest/günlük tablo/readback dosyası ve 13 runtime pin'i, toplam
**148 dosya**, duruş öncesi ve sonrası aynı hash'lerle geri okundu.
Ekim 2021 tamamlanmadı; mevcut 276 ham JSON dosyası ayrıca envantere alındı.
Dosya bulunması tek başına bilimsel grup/ay kabulü değildir. Tamamlanmamış
isteğin yeniden çalışması gerekebilir; geçerli checkpoint'ler korunur.

Kanıt dizini:
`outputs/reports/landscape/maintenance_pause_v1/20261011T182521Z/`.
Final progress ve batch özgün baytları burada ayrı kopyalarla korundu.
`pause_readback.json` SHA-256:
`2c216e13e8c80d717a3c8cb63921803cb7325160c1e1c5a7f7e9a9b4db4e9623`.
`partial_cache_readback.json` Ekim ham dosya kimliklerini içerir; SHA-256:
`e677b7e27fe8e07c5ea7ad50bcbe5ebafbf1b8bc884bfda3a8d65c70c528209e`.

## Devam koşulu

Bakım bitince kullanıcı açıkça başlatmayı istemeden kuyruk çalıştırılmaz.
Sonraki başlangıçta süreç/kilit yokluğu, korunan dosya ve parser proof
kimlikleri, disk ve bağlantı kontrol edilir. Eski job/progress üzerine
yazılmaz; yeni job ile aynı bilimsel kapsamdan devam edilir. Bu duruş
bilgisayar açılınca otomatik çalışma yetkisi vermez. Kimlik bilgileri
raporlanmadı; Free Trial, billing, Earth Engine tier ve VM değiştirilmedi.
