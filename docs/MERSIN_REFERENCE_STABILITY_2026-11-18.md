# Mersin referanslarında hücre ve hedef günü duyarlılığı — 18 Kasım 2026

2018–2023 döneminde tek merkez hücresi ve geçici saat bağlantısı bulunan
479 arşiv kaydı birlikte incelendi. Türkiye saati ve UTC yorumlarının
ürettiği hedef günleri karşılaştırıldı. Kayıtlı noktanın EPSG:6933
düzlemindeki 250 m ve 1 km çevrelerinin atanmış hücrede kalması sınandı.
Bu yarıçaplar önceki konum duyarlılığı incelemelerinden alındı. Gerçek
ölçüm hata sınırları kaynakta açıklanmıyor.

| Kontrol | Sağlayan kayıt / incelenen kayıt |
|---|---:|
| İki saat yorumunda hedef günü aynı | 458 / 479 |
| 250 m çevrenin tamamı atanmış hücrede | 391 / 479 |
| 1 km çevrenin tamamı atanmış hücrede | 184 / 479 |
| Hedef günü aynı ve 250 m çevre hücrede | 375 / 479 |
| Hedef günü aynı ve 1 km çevre hücrede | 174 / 479 |

375 kayıtlık birlikte sağlama grubunda 293 kayıt 1 ha altı, 82 kayıt
en az 1 ha son alan bildiriyor. 174 kayıtlık grupta sayılar 139 ve 35.
Son alan, yangının geçiş anındaki büyüklüğünü belirlemiyor. Yıl ve
alan grubu sayımları makbuzda ayrıca tutuldu. Önceki 485 noktalık yalnız
coğrafi incelemenin paydası bu 479 saat bağlantılı kayıtla farklıdır.

## WF1487 örneğinde saat yorumunun etkisi

Arşiv tarihi 17 Ağustos 2021, bildirilen saat 00.30. İncelediğimiz gerçek
uydu taraması 16 Ağustos 23.16.14 UTC'de başlıyor.

| Kaynak saatinin yorumu | Bildirilen zamanın UTC karşılığı | Hedef günü | Taramanın bildirilen zamana göre yeri |
|---|---|---|---|
| Türkiye saati | 16 Ağustos 21.30 | 16 Ağustos | Yaklaşık 106 dakika sonra |
| UTC | 17 Ağustos 00.30 | 17 Ağustos | Yaklaşık 74 dakika önce |

Bu noktanın 1 km çevresi tek hücrede kalıyor. Saat varsayımı hem
hedef günü hem gözlemin olaydan önce/sonra yorumunu değiştiriyor.
Önceki [gerçek piksel bulgusu](MERSIN_POINT_RESULT_2026-11-18.md)
Türkiye saati varsayımına bağlı olarak geçerli. Bu inceleme bütün
arşivin saat standardını belirlemiyor.

## Kaynak açıklaması ve devam sınırı

Paketin README, release notes, veri lisansı ve veri sözlüğü tekrar okundu.
Coğrafi tablo açıklaması, kayıtları betimleyici coğrafi/yıllık şekiller
için azaltılmış bir tablo olarak tanımlıyor. `coordinate_qc_pass` bölgesel
makullük aralığını gösteriyor. Ölçüm hassasiyeti veya tutuşma konumunun
nasıl elde edildiği açıklanmıyor. İki CSV'nin yayımlanan alanlarında
söndürülme/kontrol altına alınma zamanı yok. Saat dilimi belirtilmiyor.

375 ve 174 kayıtlık sonuçlar tanısal inceleme gruplarıdır. Tekilleştirme,
iki tablo arasındaki geçici bağlantı, başlangıç örtüsü ve kayıt kapsamı
konuları ayrıca açık. Birinci aşamada sonraki iş, bu grupları mevcut
olay kimliği ve yerel örtü kanıtlarıyla uzlaştırmak. Günlük gözlem `unknown`,
negatif etiket izni `false`, etiket kabulü açık.

## Kontroller ve yeniden üretim

`python scripts/quality/audit_mersin_reference_stability.py` kaynak hash'lerini
doğrular. 958 çevre kontrolü, noktanın hücre sınırına en kısa uzaklığıyla
ayrıca karşılaştırıldı ve tamamı uyuştu. En yakın eşik mesafesi 0,379 m.
Bu sayı fiziksel konum doğruluğunu göstermez. 54 ilgili test ve Ruff geçti.

Yerel makbuz
`outputs/reports/dataset/mersin_reference_stability_v1/20261118T134919Z_c9750a10/readback.json`.
SHA-256 `2b3413aa2957f0bc926fd99d1d634974cfa25d3921edcceb25624a757dd2b604`.
