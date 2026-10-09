# Gerçek geolocation girdisinin adını toplama

**9 Ekim sonuç:** başlık arşivi geldi; 5.007 bayt / tek JSON, CRC/hash
kontrolleri geçti. 34 kalan çiftin 32'si eşleşti. SNPP:2023365.0106 ve
SNPP:2023365.1048 için yangın başlığı seçili geolocation dosyasından
farklı işleme sürümünü istiyor. Tam adlar ve güncel arşiv sorgu sonuçları
[devam rehberinde](GCP_SOURCE_AWARE_CONTINUATION_2026-10-09.md).
31 Aralık'ı eksik bırakarak diğer aylara devam etmeyi onayladım;
bilimsel kontrol korunuyor. **Aşağıdaki başlık toplama işlemi tamamlandı,
yeniden çalıştırılması gerekmiyor.**

Yerel ham kaynak teşhisi ZIP'i 799 bayt; yalnız `probe_summary.json` içeriyor.
CRC ve controller/original/teşhis/Aralık planı hash kimlikleri eşleşti.
ZIP SHA256 `c2bdb82a94ead1730b55e79e6ea03d6d459bc4dadda24cdc68d2349abbd74e24`.
SNPP:2023365.0106 yerel yeniden denemesi 6,562 saniyede `ValueError`:
`Not the actual geolocation input` verdi. Donmuş `child_audit → inspect →
validate_pair → require` zinciri kaydedilmiş. Önceki üretimin genel hatası
ile aynı görevde somut kaynak eşleştirme kusuru yeniden üretildi; eski
çağrının kaybolmuş exception nesnesi birebir geri getirilmiş sayılmıyor.

Seçili nominal çiftin dosyaları:

- Fire: `VNP14IMG.A2023365.0106.002.2023365085734.nc`
- Geo: `VNP03IMG.A2023365.0106.002.2024006061118.nc`

Bu tarihler işlemenin farklı zamanda yapıldığını gösterir, tek başına
yanlış eşleşme kanıtı değildir. Başlıktaki `VNP03IMG`/`VJ103IMG` veya
`InputPointer` doğrulaması esas alınacak. Önceki araç beklenen gerçek
dosya adını rapora eklememiş; bu eksik bilgi için küçük bir başlık
arşivi gerekiyor. Tam dosya adı farklı mı, aynı ad farklı biçimde mi
belirtilmiş, başlık okunmadan seçilemiyor. Geolocation kaynak kontrolü
kaldırılmıyor, ay/gün veya başarısız çift atlanmıyor.

## Hızlı başlık okuması

VM kapalıysa **Start → SSH**. Uzun üretim komutunu çalıştırma.
**Upload File** ile yalnız şu dosyayı yükle:

`C:\PROJELERIM\wildfire-risk-prediction\outputs\gcp_acceleration\diagnosis_2026-10-09\collect_gcp_geolocation_headers.py`

**VM SSH terminalinde**:

```bash
if printf '%s  %s\n' \
  '4aebb1f297eaac69848881639294b0d6999f7e0e6bb519d47b374e689892f8ca' \
  "$HOME/collect_gcp_geolocation_headers.py" | sha256sum --check; then
  timeout 180s ~/wildfire-gcp-work/.venv/bin/python \
    ~/collect_gcp_geolocation_headers.py
fi
```

`HEADER REPORT COMPLETE` ve `Download:` gelirse SSH → **Download File**:

`/home/enesnuhgocek1/gcp_geolocation_headers_2026-10-09.zip`

Yerelde `outputs/gcp_acceleration/received/` klasörüne koy; indirme
sonrası **VM → Stop**. Araç VM'yi kendisi kapatmaz. Başlık toplama
başarısız olursa yalnız terminal çıktısını paylaş ve VM'yi durdur.

Önceki iki teşhis Python dosyası aynı hash ile VM ev dizininde kalmalı.
Bu araç bütün kalan 34 görevin ilgili başlık alanlarını tek seferde
alır. Ham indirme, login, piksel `.read()` veya native ürün yeniden
hesaplaması yok; kaynakların boyut/mtime bilgisi okuma öncesi/sonrası
aynı olmalı. Soket bağlantısı engellenir. İş kilidi ve paket/plan hash
kontrolleri aynı. Bytecode ve üretim klasörüne yazım yok. Yalnız NASA
geolocation dosya adları, referans biçimi/kimlik eşleşme bayrakları,
bilinen hata kontrolü ve hash'ler ayrı, en fazla 1 MB rapora alınır.
Diğer başlık alanları veya bağlantı bilgileri rapora eklenmez.

Araç/sınırlı başlık testleri ile mevcut eşleştirme kontrolleri birlikte
23 testten geçti; Ruff geçti. Gerçek VM başlık okuması tamamlandı.
Rapor geldiğinde eksik kaynak kaydı, güvenli çocuk hata günlüğü ve
checkpoint devamı ayrı bir araçta hazırlandı. Üretim paketi ve hazır-kayıt
değiştirilmedi.

Başlık ve gerçek girdinin kaynak kayıtları için:
[NASA VIIRS fire file specification](https://ladsweb.modaps.eosdis.nasa.gov/filespec/VIIRS/1/VNP14),
[CMR producer granule ID search](https://cmr.earthdata.nasa.gov/search/site/docs/search/api.html).
