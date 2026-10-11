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

## Gerçek arşiv kontrolü ve salt okunur tanı hazırlığı

Kullanıcı arşivi aktardı ve VM'nin Stopped durumunu teyit etti. Gelen dosya
`outputs/gcp_acceleration/received/gcp_v5_failure_20261011T234521Z.tar.gz`,
91.896 bayt; SHA-256 `e7a08fcb89397ffe71eb288540741f6e04c230ef0f05dcdc8f5e9a2c8bb77fc1`.
Yalnız beş beklenen normal üye var; link, yinelenen yol ve kapsam dışı
üyelere izin verilmeden, toplam açılmış boyut 317.748 bayt olarak okundu.
Üç final dosyası aynı: `b9c5de20486ae2ddebc0db2696a9625a219f19d0d38656d1cf5b6fadf00c1249`.
Orijinal bilimsel paket, controller ve V5 kimlikleri yerelde eşleşti.

`verify_gcp_v5_failure.py`, incelenmiş final baytlarını sabitler; eski V3
kabulünden yalnız hata durumu ve wrapper kimliğini kontrollü normalleştirerek
takvim, katalog ve bilimsel politika kontrollerini yeniden kullanır. Bu,
üretim durumu dosyalarını değiştirmez. Sonuçlar:

- 40 tam ay: Ağustos 2020–Kasım 2023; Temmuz 2020 tam kapanmamış.
- 156 yeni çift satırı ve 17 yeni günlük commit; Temmuz 1–17.
- Temmuz 18'de 8 nominal çiftin 5'i kaydedilmiş; günlük commit yok.
- Aralık 1–30, yalnız durumdaki 30 eski gün; bu oturumda yeni üretim sayılmadı.
- 2.696 kaynak örneği; en az 11,356 GiB boş disk / 113,181 GiB kullanılabilir RAM;
  üst ve çocuk süreçler RSS zirvesi 11,048 GiB. Örneklenmiş rezerv ihlali yok.
- CPU ortalaması %7,212; eski ay geri okuması dahil, ham işlem hızı ölçüsü değil.

Yerel rapor `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/failure_readback.json`;
SHA-256 `b98cad5bff82fed84e1ff17f1ff234da1de074606986211e453f903129158daa`.
Arşivde uzak ürün ZIP'leri veya etkilenen Drive ID yok. Bu kabul günlük/katalog
ve örneklenmiş kaynak kullanımı içindir; yeni bilimsel ürün bayt kabulü değildir.

### Hazırlanan tanı

Tek dosya `scripts/cloud/diagnose_gcp_v5_drive_publication.py`; yükleme kopyası
`outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/package/diagnose_gcp_v5_drive_publication.py`.
SHA-256 `f55bce3cf40b19dba59231335292c8038ca9000586e872eb75f0194bce96fb32`.
Mevcut, hash kontrollü HTTP helper'ını kullanır. Üç final, V5 ve donmuş paketler
eşleşmeden, üretim kilidi alınmadan Drive isteği yapmaz. Son parent tanısını
kapalı şemayla, kalan çocuk tanılarını yalnız incelenmiş sınıf/hash bilgileriyle
okur. Retained task kimlikleri donmuş Temmuz kataloğuyla karşılaştırılır.

Drive istekleri GET ile sınırlandırılır; OAuth token yenilemesi normal token
uç noktasındaki POST'tur. Klasör erişimi/kota/listing ve kalan yerel pair ZIP'leri
için mevcut completion/payload geri okunur. Kimlik, içerik hash'i, tam bayt,
etiket politikası farklıysa durur. Payload olup completion yoksa tamamlandı
sayılmaz; hiçbir nesne oluşturulmaz, düzeltilmez veya silinmez. Final özetler,
aday ZIP'ler ve tanı dosyalarının hash'leri işlem sonunda aynı olmalıdır.

Tanı 230 saniye iç sınır, 300 saniye dış `timeout` ile çalıştırılır. Yalnız yeni
tarihli küçük JSON raporu yazar; üretim/ham işleme ve poweroff çağrısı yoktur.
VM kısa tanı için açılıp rapor indirilince tekrar Stop yapılır. Tanı başarılı
olsa bile tarihsel 404'ün kesin nedenini veya otomatik devam güvenliğini tek
başına kanıtlamaz; devam sürümü sonuç incelendikten sonra değerlendirilir.

25 yeni davranış/güvenlik kontrolü, 36 mevcut Drive store kontrolü ve 51
ilgili manifest/controller regresyon testi geçti; lint/format geçti. Son
regresyon çağrısında kapsam dışındaki tam eski ay bilimsel geri okuma testi
seçilmedi; bu çağrı tüm test deposunun kabulü değildir. İlk geniş çağrı TEMP
erişim hataları ve uzun eski ürün kontrolü nedeniyle kesildi; başarılı kabul
sayısına katılmadı. İlk test çağrısında sistem Python'unda pytest/ruff yoktu;
projenin .venv'i kullanıldı. Sandbox TEMP erişim hataları çalışma alanındaki
izole test dizinleriyle giderildi; canlı kod/paketler buna göre değiştirilmedi.

Hazırlık kaydı `outputs/gcp_acceleration/source_aware_v5_18h_2026-10-11/drive_probe_prepared_20261012.json`;
SHA-256 `1b2620496053bb8ef314a158cb38710d03a175e1d4f6b4e55687c60ee12c2320`.

VM Start ve yalnız tanı dosyasının SSH Upload File ile home'a aktarılmasından sonra:

```bash
if printf '%s  %s\n' \
  'f55bce3cf40b19dba59231335292c8038ca9000586e872eb75f0194bce96fb32' \
  "$HOME/diagnose_gcp_v5_drive_publication.py" | sha256sum --check; then
  timeout 300s ~/wildfire-gcp-work/.venv/bin/python \
    ~/diagnose_gcp_v5_drive_publication.py
fi
```

Yazdırılan yeni JSON indirilip `outputs/gcp_acceleration/received/` altına
aktarılır; VM tekrar Stop yapılır. OAuth JSON'u yeniden yüklenmez veya paylaşılmaz.
