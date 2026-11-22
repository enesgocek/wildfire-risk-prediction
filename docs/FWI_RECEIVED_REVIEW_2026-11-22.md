# Teslim edilen FWI dosyasının yerel incelemesi

22 Kasım 2026. Kullanıcının indirdiği özgün dosyanın başlığı ve sınırlı
sayısal kalitesi incelendi. Dosya korunuyor; bu sonuç zaman eşleştirme,
model girdisi, yangın etiketi veya birinci aşama kabulü değildir.

## Gerçekte kontrol edilen dosya

`data/raw/external/cems_fwi_pilot_v1/ff72cf1a14e9faea5681118fe8888717.nc`

- Boyut: 100.424 bayt; gerçek NetCDF4/HDF kapsayıcısı.
- SHA-256: `e6b57e8ecbd5836f141eb6d0cbd17dc283d6569bb194c5496861d4ba8e5f5a8e`.
- Değişken: `fwinx`, parametre 260540; dosyanın uzun adı Canadian
  Forest Service tanımlı Forest Fire Weather Index, birimi `Numeric`.
  Parametre kodunun bağımsız parametre kataloğu doğrulaması yapılmış sayılmadı.
- 1–30 Haziran 2022 için 30 bant; 49 × 21 nokta, 0,25° aralık.
  Nokta merkezleri 25–37° doğu / 35–40° kuzey arasında.
  Hücre kenarı sınırları 24,875–37,125° / 34,875–40,125°.
- Rasterio CRS alanı `None`; CF derece eksenleri ve GRIB `regular_ll`
  başlığı tutarlı. EPSG kodu atanmadı veya yeniden projeksiyon yapılmadı.
  Bu ızgara projenin 5 km fiziksel çözünürlüğü değildir.
- İstenen sistem 4.1 idi; dosya başlığında bu sürümü bağımsız doğrulayan
  açık bir sürüm alanı bulunmadı. Form tercihi dosya içi sürüm kanıtı sayılmadı.

## Sayısal kalite sonucu

Yalnız bu Haziran 2022 dosyasının değerleri okundu; 2023–2025 açılmadı.
30 günlük CSV'nin tamamında günde 873 sonlu ve 156 işaretli eksik nokta var.

| Ölçüm | Sonuç |
|---|---:|
| İncelenen nokta-gün | 30.870 |
| Sonlu, maskelenmemiş değer | 26.190 |
| Sağlayıcı maskesiyle eksik | 4.680 |
| Maskelenmemiş NaN/sonsuz değer | 0 |
| Negatif değer | 0 |
| En küçük / büyük değer | 1,7722 × 10⁻⁹ / 100,115234375 |

12 Haziran nominal bandında bir değer 100'ün üzerinde. Bu otomatik hata
veya yüzde olasılık değildir: sağlayıcının ayrıntılı değişken tablosu
FWI'yi üst sınırı olmayan bir endeks olarak tanımlar. Aynı kılavuzun genel
girişinde 0–100 ifadesi bulunsa da bu, kırpma kuralı yapılmadı.
[CEMS tarihsel ürün kullanıcı kılavuzu](https://confluence.ecmwf.int/spaces/CEMS/pages/340779714/User+Guide+for+Fire+danger+indices+historical+data+from+the+Copernicus+Emergency+Management+Service).

Eksikler sıfıra çevrilmedi. Eksik noktaların hepsinin deniz olduğu veya
maske geometrisinin her gün aynı kaldığı ayrıca sınanmadı; eşit sayılar
geometrik eşitlik kanıtı değildir.

## Açık kalan zaman konusu ve somut örnek

Dosyadaki `valid_time` günleri 00:00 UTC gösterirken kendi uzun adı
`initial time of forecast`, standart adı `forecast_reference_time`.
Ayrı bir tahmin adımı/forcing zaman aralığı açık değil. Dolayısıyla
1 Haziran 00:00 kaydını, o anda bilinen 1 Haziran günlük tehlikesi diye
bağlamadık. Yerel öğlen koşullarını içeren aynı gün alanının sabahki
tahmine eklenmesi gelecek bilgi sızıntısı yaratabilir.

Resmî kılavuz, tarihsel ürünü ERA5 tarihsel simülasyonlarındaki hava
tahminleriyle hesaplanan ve yerel öğlen koşullarını temsil eden bir
ürün olarak açıklar. Bu nedenle dosyadaki `fc` işareti tek başına yanlış
ürün indirildiğini göstermez; operasyonel erişimi de kanıtlamaz.
[CEMS yöntem ve zaman açıklaması](https://confluence.ecmwf.int/spaces/CEMS/pages/340779714/User+Guide+for+Fire+danger+indices+historical+data+from+the+Copernicus+Emergency+Management+Service).

ECMWF, yerel zamanlı alanlarda forcing saatlerini saklamak için GRIB2
şablonları geliştirdiğini açıklıyor. Özgün GRIB başlığı, NetCDF'e dönüşümde
görünmeyen zaman alanlarını sağlayabilir. Bu bir beklentidir; eldeki dosya
için doğrulanmış sonuç değildir. Makalenin 2022 operasyonel arşiv başlangıcı,
bu Haziran 2022 tarihsel dosyasının erişim tarihi gibi kullanılmadı.
[ECMWF: Fire can now be found on MARS](https://www.ecmwf.int/en/newsletter/173/news/fire-can-now-be-found-mars).

## Sonraki küçük edinim

Yeni yıl veya geniş arşiv yerine, aynı isteğin **yalnız 1 Haziran 2022
ve GRIB biçimindeki** eş dosyasını incelemek öneriliyor. Bu bir aylık
NetCDF'in yanlış olduğu anlamına gelmez; amaç özgün saat başlığını görmek.

[EWDS indirme formunda](https://ewds.climate.copernicus.eu/datasets/cems-fire-historical-v1?tab=download)
Reanalysis / yalnız Fire weather index / Consolidated dataset / 4.1 /
2022 / June / yalnız day 01; kuzey 40, güney 35, batı 25, doğu 37;
0.25x0.25 interpolated; **Data format: GRIB** seçilmeli.
Özgün `.grib` dosyası aynı yerel klasöre konmalı; NetCDF silinmemeli.
Portalın farklı kısıt/uyarı vermesi durumunda boyut veya dönem otomatik
genişletilmeyecek. Kimlik bilgisi veya oturum URL'si paylaşılmamalı.

Başlık okuyucusu `scripts/quality/inspect_fwi_grib_header.py` hazır;
gerçek GRIB henüz gelmedi veya çalıştırılmadı. Okuyucu yalnız kapsayıcı
ve GRIB metadata'sını kaydeder, raster değer dizisini okumaz. GRIB başlığı
da yayımlanma/edinim saatini veya tüm forcing aralığını açıklamayabilir.
Belge ve dosya bulguları görülmeden otomatik T−1 kuralı kabul edilmez.
Bu tek edinim üç bilimsel geçiş konusunun tamamını çözme garantisi değildir.

## Makbuzlar ve teknik doğrulama

Yollar `outputs/reports/dataset/` altında; çıktılar elle değiştirilmedi.

- Başlık: `fwi_reference_metadata_v1/20261122T164628Z_846e19fc/readback.json`;
  SHA-256 `63006cb114152f3501b52465411930632771eed3032b6860399438e0d60be955`.
- Sayısal kalite: `fwi_received_quality_v1/20261122T165059Z_42a37e1b/readback.json`;
  SHA-256 `a66cdd0f6cdcdd74e1d195a6285eb73d003f775a2e59c6de7667a93ac476bc13`.
- Günlük tablo SHA-256:
  `ec4882df72bfd77c6cc084bee57f3e7ea9249efeda7a725aaba8c18db73bf579`.

Dört bağlı girdi, günlük çıktı ve iki üreticinin hash'leri geri okumada
eşleşti. Dört yeni test, dört önceki CF-zaman testi ve hedef/nihai
birleştirme korumalarıyla toplam **36 test** geçti; dört yeni Python
dosyası Ruff kod/biçim kontrolünden geçti. GRIB imza testleri sentetik
kapsayıcı testidir; gerçek GRIB çözümleme başarısı değildir.

21 Kasım edinim hazırlığı ve o tarihteki “dosya yok” kaydı tarihsel
olarak korundu. Yeni kalite kapsamı ayrı
`configs/fwi_delivery_quality_review_v1.json` ile bağlı. Yeni model,
özellik tablosu, gerçek Y/L, risk rengi veya nihai birleştirme üretilmedi.
