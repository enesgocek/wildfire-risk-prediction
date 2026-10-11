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

## Sonraki SSH bildirimi — Drive metadata hatası

Kullanıcının yeni SSH çıktısında `failed_checkpoints_retained`, Temmuz 2020,
`pair_publication`, RuntimeError ve `full_training_complete=False` var.
156 yeni kaydedilmiş çift raporlanıyor; görünen son gün commit'i 17 Temmuz.
Tam ay sayısı 40. Bu uzak bildirim yerel ürün kabulü veya Temmuz ayının tam
kapanışı sayılmaz.

Son satırlar `HTTP_DIAGNOSTIC FILE_METADATA 404 notFound`,
`PARENT_FAILURE GOOGLE_HTTP_404 CLASS_ONLY`, `Guest poweroff requested: True`.
Kod incelemesinde HTTP rolü Google Drive dosya metadata isteğine karşılık
gelir; pipeline hata halinde çocukları durdurur, supervisor poweroff ister.
Bu nedenle erken kapanışın iş hatasını izlediği destekleniyor; 18 saat
ayarının yanlışlığı veya başarılı kuyruk tamamlanması desteklenmiyor.

[Google Drive hata rehberinde](https://developers.google.com/workspace/drive/api/guides/handle-errors#404_errors)
404, var olmayan veya bağlantının okuma erişimi bulunmayan kaynağı belirtir.
Bu kayıt tek başına silinme, kota dolması veya geçici görünürlük gecikmesini
ayırt etmez. `IndexedDriveStore.metadata` hem önceki dosyaları okurken hem
yeni dosya oluşturulduktan sonra çağrılır; belirsiz upload sonrası aynı
üretilmiş ID'yi kontrol eden başka yol da aynı HTTP rolünü üretir. Hangi
yolun etkilendiği tam günlük/tanı ve gerekirse salt okunur Drive kontrolü
olmadan kesinleşmez. 404 için kör yeniden üretim veya sınırsız retry eklenmedi.

Kanıt `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/failure_user_readback_20261012.json`;
SHA-256 `e8985c002ca25abc6bed2df27e97f91534479fed2adbcefccc5f65c153deac19`.
Sonraki adım üç final özet, resource CSV ve V5 launcher günlüğünün yeni
arşivini almak, VM'yi Stop yapmak ve yerelde sınırlandırılmış geri okumadır.
Kimlik bağlantısı, tokenlar, kaynak ham verileri ve canlı paketler arşive alınmaz.
