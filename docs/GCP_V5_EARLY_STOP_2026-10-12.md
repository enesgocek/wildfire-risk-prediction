# V5 erken kapanış ön incelemesi — 12 Ekim 2026

Kaynak, kullanıcının Cloud Shell `instances describe` çıktısıdır; bağımsız
canlı API/Drive erişimi veya yeni ürün kabulü yapılmadı.

VM TERMINATED. `maxRunDuration.seconds=64800` **18 saati** doğrular;
sekiz saat 28.800 saniyedir. Eski sekiz saatlik ayar nedeniyle kapanmış
olduğu açıklaması bu çıktıyla desteklenmez.

- Başlangıç: 11 Ekim 19:55:53,535 UTC / 22:55:53 Türkiye.
- Duruş: 11 Ekim 21:52:49,231 UTC / **12 Ekim 00:52:49 Türkiye**.
- Çalışma: **1:56:55,696**.
- Kayıtlı Google sınırı: 12 Ekim 13:55:48,352457 UTC / 16:55:48 Türkiye.
- Sınırdan önce duruş: **16:02:59,121457**; normal süre rezervi kapanışı değil.

Kapanış nedeni henüz bilinmiyor. Hata, erken bitiş veya başka bir duruş
günlük olmadan ayrıştırılamaz. Son SSH bildiriminde 56:31 elapsed, 26 ay
geri okunmuş, yeni çift sıfır ve hata None idi. Bu snapshot daha sonra
hata oluşmadığını kanıtlamaz; önceki 40 ayın günlük/katalog kabulü korunur.

Kanıt `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/early_stop_user_readback_20261012.json`.
SHA-256 `3c99fc34c964027d4223fc780483f0f5523d77296636b8fbe8d39c17a80616da`.
Bu yeni tarihli bulgu önceki 11 Ekim başlangıç raporunu değiştirmez.

## Sonraki adım

VM yalnız günlük almak için Start yapılır; mevcut V5 üretim komutu tekrar
çalıştırılmaz. SSH'de V5 launcher kuyruğu ve seçilmiş progress alanları
okunur. Çıktı alınınca VM tekrar Stop yapılır. Nedene uygun devam ancak
tanılar incelendikten sonra hazırlanır. Runtime/STOP/billing ayarı bu yerel
incelemede değiştirilmedi; yeni bulut işi başlatılmadı.
