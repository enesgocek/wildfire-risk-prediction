# Drive kalıcılık kontrolünün sonucu — 6 Ekim 2026

V2 VM işi Passed verdi. Kullanıcı sonuç JSON'unu ilgili klasöre aktardı ve
VM'yi Stop yaptığını bildirdi. Yerel doğrulayıcı, alınan özet ile hazırlanmış
paket/manifest/ürün byte özetlerini ve ZIP üyeleri/CRC'sini kontrol etti;
`returned_drive_proof_summary_validated` sonucu başarılı.

| Kontrol | Sonuç |
|---|---|
| Ürün | SNPP:2023197.0018, 3.982.961 bayt |
| Kaydetme süreci | PID 1327, 5 bilimsel geri okuma bildirildi |
| Geri yükleme süreci | PID 1336, 1 bilimsel geri okuma bildirildi |
| Tamamlanma öncesi yapay kesinti | Uygulandı; uncommitted ürün tamamlanmış sayılmadı |
| Sonraki süreçte mevcut completion kullanımı | Başarılı bildirildi |
| Depo | Gerçek Drive backend; filesystem_only false |
| Yeni ham veri / üretim ayı | 0 / 0 |
| Negatif etiket izni | false |
| VM | Kullanıcı Stop bildirdi; yerel araç canlı Compute API durumunu okumadı |

Alınan JSON SHA256:
`691547f74d29b1c42a351e8728c054001b269702a6b8f90de4e7c4839d7a93d4`.
Paket SHA256:
`7c0366b82afdf33f6b8c2873cbcd096efc2d1bb8237827cb8f8011504ade393f`.
Manifest SHA256:
`bddfd564a8f6a0f0190e15abecbefd8efb6ca08890930e406bf09bb4b90f2982`.
Ürün SHA256:
`2ac9892aa4c9889b23fed174b7acc0812bd2e2bda549873def562c92757328c9`.

Rapor `outputs/reports/observation_coverage/gcp_drive_returned_proof_v2.json`.
Kaynak JSON/ZIP değiştirilmedi. Özet doğrulayıcıya gerçek hazırlanmış ZIP,
manifest ve payload SHA/CRC kontrolü eklendi; değiştirilmiş paket/manifest/
payload referansı için dört ek koruyucu test ve ilgili 16 test geçti.
Önceki tam test kümesi 467 başarılıydı. Donmuş bilimsel kod/paket değişmedi.

## Bu kapının kanıtlamadığı işler

VM'de Drive'a yazma ve geri indirilmiş ürünün bilimsel denetimi bildirildi;
yerel denetimde remote payload tekrar bağımsız indirilmedi. Rapor bunu
`remote_payload_independently_downloaded: false` olarak ayırır. Ayrı süreç
ve yeni geçici bilimsel çıktı dizinleri kullanıldı; VM Stop/Start sonrası
yeni ortamda resume veya SSH bağlantısı kesilerek çalışma deneyi yapılmadı.
Bu sonuç tam ay/yıl kapasitesi, toplam süre/maliyet veya üretim işçisinin
hazır olduğu anlamına gelmez. Günlük gözlem unknown, negatif izin false.

## Sonraki öneri

VM kapalıyken devam eden iki işçili üretim sarmalayıcısı, tamamlanan çiftleri
Drive'dan yeniden kullanma ve yalnızca tüm çiftleri doğrulanmış günler için
geometrik birleşim hazırlanmalı. İlk önerilen yeni kapsam 1–3 Ağustos 2023:
26 çift/52 kaynak, yaklaşık 4,76 GB yalnızca VM'ye akış. Yerel ham indirme
yok; gerçek tam iş süresi ve günlük ürün boyutu bu kapsamda ölçülmeden aylar
ve 6/8 saatlik gruplar başlatılmamalı. Bu kapsam henüz çalıştırılmadı.
