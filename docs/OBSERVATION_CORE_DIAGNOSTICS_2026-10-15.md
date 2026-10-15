# Tek çift tekrarında ValueError ve güvenli teşhis — 15 Ekim 2026

Dar HTTP 303 düzeltmesinden sonraki iki gerçek deneme de
`bounded_file_transfer` aşamasında **ValueError** ile durdu. Bu hata önceki
303 kaydıyla aynı kabul edilmedi. Eski kayıtta durduran guard bilgisi
olmadığından kesin neden henüz belirlenmiş değildir.

## Yerel kanıt

Çalışma dizinleri:

- `outputs/reports/dataset/observation_core_native_v1/20261015T002236Z_8bec4d91/`
- `outputs/reports/dataset/observation_core_native_v1/20261015T002317Z_3a8832df/`

İki `failure.json` baytı aynıdır: aktarım fazı, ValueError ve null HTTP
durumu. SHA-256:
`9cb769f505f78657a32c4df27082c2c632303451c54e246277c19d0eb7241753`.
İki `launcher_receipt.json` SHA-256:
`cc9d11b7d3ac17dede310798918535f47d71bbe2e700165201048df85bd62c4c`.
İncelenen ham önbellekte dosya yoktur. Kimlik bilgisi, imzalı URL veya
özel hata metni saklanmamış. Bunlar parola hatası ya da kaynak yokluğu
kanıtı değildir. İlk tasarımın hata ayrıntısını fazla kısıtlaması, tanı
için yetersiz kayıt bırakmıştır; kesin neden tahminle doldurulmadı.

## Yapılan değişiklik

Serbest hata metni yerine projedeki sabit guard mesajları açık izin
listesiyle kısa kodlara bağlandı. Örnekler: `signed_object_key`,
`signed_endpoint_or_key`, `signed_parameters`, `final_response_url`,
`response_encoding`, `response_length`, `historical_sha256`. Bilinmeyen
mesaj `unclassified` kalır. Terminal yalnız izinli `Kontrol kodu:` değerini gösterir.

Yerel rapor yalnız kaynak rolü, ilk/son sayısal HTTP durumu, beklenen/
görülen Content-Length baytı, hedefin aws/giriş/diğer/eksik sınıfı ve
imza alanlarının varlığı/istek eşdeğerliği boolean tanılarını tutabilir.
Bu alanlar ad/tür/değer filtresinden geçer. Tam host/yol/Location,
imza/token/çerez/kullanıcı bilgisi, serbest gövde veya traceback kaydedilmez.

Bağımsız regresyon denemesinde `%7E` ve `~` gibi aynı URI değerinin HTTP
kütüphanesince normalleştirilmesinin eski birebir metin karşılaştırmasında
yanlış redde yol açabildiği gösterildi. Karşılaştırma aynı HTTPS host,
443/default port, çözümlenmiş yol ve aynı sorgu anahtar/değerleri üzerinden
düzeltildi. Başka nesne veya değişen imza kabul edilmez. Aynı CMR bucket/
nesne, ayrı kimliksiz S3 oturumu ve tek yönlendirme koşulları korunur.

**Bu yerel URI bulgusu iki gerçek ValueError'ın kesin nedeni sayılmadı.**
Önceki guard/Location saklanmadığından nedensellik yeni canlı tanıyla
değerlendirilecek. Boyut, SHA/checksum, disk veya native eşleşme koşulları
gevşetilmedi.

## Kontroller ve yeni plan

Yedi yeni davranış testi dahil **44 aktarım testi/159 ilgili test** geçti;
deprecation ve future uyarıları hata sayıldı. Keyfi özel mesajın rapor/
terminale geçmemesi, yapısal tanı filtresi, URI normalizasyonu, farklı
nesne/imza/port reddi, boyut tanısı ve en güncel tamamlanmış planın ayrıca
doğrulanması sınandı. Dört Python dosyasında lint/format geçti.

Yeni plan **117 giriş/iki çıktı** hash kapanışından geçti; **22 donmuş
üretim girdisi** korundu. Eski kabul edilmiş native okuyucu tanığı
tekrarlandı; yeni çiftin indirme başarısı değildir. Tek çift
`SNPP:2018045.0000`, 191.244.528 bayt, 900 saniye, bir işçi, 2 GB plan
önbelleği ve 20 GB boş disk sınırları değişmedi. Yeni ham indirme,
bulut işi, model/etiket veya eğitim dışı veri erişimi başlatılmadı.

Dizin:
`outputs/reports/dataset/observation_core_transfer_v1/20261015T002822Z_d2ec68a3/`.
`native_plan.json` SHA-256:
`8cec32a4b634f958e7a3dab163f8194eae2a86c184c44c5761a3e685c864db8b`.
`readback.json` SHA-256:
`7384cd89ec7d51ec2d04d9bdd8afac91f00ed8b9748152644dbbb3367e753a21`.
`completion_readback.json` SHA-256:
`186352078aff3d2b35fbaab0399daf9c8933f0c3f1099448520c564624bd6e45`.

Özel yerel PowerShell'de yeni komut:

```powershell
.\.venv\Scripts\python.exe scripts\firms\run_observation_core_pair.py --latest-plan --run-one --prompt-login
```

`--latest-plan` en güncel tamamlanmış hazırlığı seçer; kaynak/kod/hash ve
kapsam kapıları girişten önce ayrıca doğrulanır. Eski plana sessiz geri
düşme yoktur. Kimlik bilgileri saklanmadığı için gizli istemde yeniden
giriş gerekir. Yalnız Kontrol kodu veya PASS satırı paylaşılır; yerel
güvenli rapor ayrıca okunur. Gerçek tekrarın sonucu henüz açık; unknown,
kapalı negatif izni, boş hedefler ve nihai birleştirme kapısı korunur.
