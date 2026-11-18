# Salur'da başlangıç hücresi ve sonraki küme birleşmesi — 19 Kasım 2026

Salur, başlangıç işareti ve saat açıklaması bulunan güçlü bir bağımsız
kaynak örneği. Bu çalışmada, işaret çevresindeki tespitlerin dokuz sabit
gruplamada hangi başlangıç hücrelerine bağlandığı incelendi. Çalışma,
tek vaka üzerinde yöntem tanısıdır. Kaynak işaretinin özgün ölçüm
hassasiyeti, gerçek yangın kimliği ve nihai etiket kabulü açık.
[Önceki kaynak ve konum denetimi](SALUR_START_MARKER_2026-11-08.md).

## Sabit başlangıç kanıtı ve arama kapsamı

İki konum çözümünün 1 km çevresinde aynı 11 katalog tespiti bulundu.
Hepsi 28 Temmuz 2021 hedef penceresinde ve işaretin proje hücresinde.
İlk yerel tespit 10.12 UTC, kaynakta bildirilen başlangıç 08.58 UTC.
1 km, katalog karşılaştırması için duyarlılık ölçeği. Tutuşma konumu
için ölçülmüş hata sınırı değil. Tespitler ayrı ayrı yangın sayılmadı.

Özgün katalogdan 2018–2023 eğitim kapsamındaki 30.295 aday satırı
seçildi. Dokuz sabit atama dosyasının anahtarları, hücreleri, sensörleri
ve zamanları bu kaynakla uzlaştırıldı. Yerel 11 kaydın her senaryoda
tek tam bileşende olduğu görüldü. Bileşen üyelik hash'leri ve ilk
hücreler, önceki katalog raporlarıyla ayrı geri okundu. Ortak ham
dosyanın 2024 satırları analize alınmadı; 2025'e erişilmedi.

## Yeni bulgu

| Mesafe / zaman boşluğu | Tam bileşendeki tespit sayısı | Tam bileşenin ilk UTC zamanı | Salur hücresi ilk kümede mi? | Hedef gün sonunda bağlı tespit sayısı |
|---|---:|---|---|---:|
| 500 m / 24 saat | 3.578 | 28 Temmuz 10.12 | Evet | 338 |
| 500 m / 48 saat | 3.596 | 28 Temmuz 10.12 | Evet | 338 |
| 500 m / 72 saat | 3.604 | 28 Temmuz 10.12 | Evet | 338 |
| 1 km / 24 saat | 3.708 | 28 Temmuz 10.12 | Evet | 395 |
| 1 km / 48 saat | 3.710 | 28 Temmuz 10.12 | Evet | 395 |
| 1 km / 72 saat | 3.710 | 28 Temmuz 10.12 | Evet | 395 |
| 2 km / 24 saat | 5.303 | 28 Temmuz 10.12 | Evet | 399 |
| 2 km / 48 saat | 5.303 | 28 Temmuz 10.12 | Evet | 399 |
| 2 km / 72 saat | 5.304 | 28 Temmuz 10.11 | Hayır | 399 |

Tam bileşenler 6 Ağustos'a kadar sonraki kayıtlar içeriyor. Tablodaki
sayılar yangın sayısı veya bağımsız örnek sayısı değil. Dokuz satır
birbirleriyle büyük ölçüde aynı tespitleri içeriyor.

En geniş ayarda başlangıca dönüşen `N20_815590_134676`, Salur
işaretinden **25.761 m** uzakta. Bu tek satır, 2 km / 48 saat
bileşeninde yok. 2 km / 72 saat bileşenine, ilk uygun doğrudan
komşusu `N20_815590_137950` üzerinden katılabiliyor. Komşu kaydı
**30 Temmuz 11.14 UTC**, kenar mesafesi **1.933,4 m**, zaman
boşluğu **49 saat 03 dakika**. Bu kenar 48 saat koşulunu aşarken
72 saat koşulunu karşılıyor.

## Bağlantının zamanla kanıtlanması

Yalnız belirlenen zamana kadar gelen kayıtlarla aynı bileşenin grafiği
yeniden kuruldu. Bu işlem üretim etiketi veya seçilmiş yeni kural değil.

1. İlk yerel tespit anında 500 m ayarlarında Salur'a bağlı bir tespit
   ve tek ilk hücre var. 1 km ayarlarında 74, 2 km ayarlarında 75
   aynı zamandaki bağlı tespit ve dört ilk hücre var.
2. Hedef pencerenin sonunda, **29 Temmuz 00.00 UTC** kesiminde,
   dokuz ayarda da Salur'a bağlı bileşenin ilk zamanı 10.12 ve ilk
   hücreleri aynı dört hücre. Salur hücresi bu dördün içinde.
3. En geniş ayarda, ilk uygun kenardan bir nanosaniye önce Salur'a
   bağlı 2.486 tespit var; ilk zaman 10.12 ve aynı dört hücre.
4. **30 Temmuz 11.14 UTC** anının bütün kayıtları eklendiğinde
   2.564 tespit var; ilk zaman 10.11 ve tek ilk hücre uzak kaydın
   `C610_R877` hücresi. Salur'un `C605_R879` hücresi ilk kümeden çıkıyor.

Son adımda 78 satır aynı zaman diliminde ekleniyor. Değişimin tek
doğrudan bağlantı tanığı yukarıdaki kenar; sayısal artış yalnız iki
düğümden ibaret değil. İki gerçek yangının birleştiği veya uzak
kaydın yanlış olduğu çıkarılmadı. Kanıtlanan, kayıtların grafik
bağlantısının daha sonra oluştuğu ve geriye dönük ilk hücre atamasını
değiştirdiği. Bu tek başına model girdisinde zaman sızıntısı kanıtı değil.

## Pozitif kabul önerisine katkı

| Koşul | Salur'da mevcut bilgi | Açık sınır |
|---|---|---|
| Bağımsız olay anlatımı | Sunumda başlangıç işareti, saha raporunda saat ve örtü anlatımı | Kaynaklar ortak idari bilgi kullanmış olabilir |
| Bildirilen başlangıcın hedef günü | 28 Temmuz penceresi | Bildirilen saat gerçek tutuşmanın ölçümü olarak doğrulanmadı |
| Yerel uydu eşleşmesi | İki konum çözümünde aynı 11 aday | 1 km olay kimliği veya ölçülmüş konum hatası sağlamıyor |
| İlk hücreye bağlama | Gün sonu kesiminde dokuz ayar aynı dört hücreyi koruyor | Sonraki birleşme tam grafik sonucunu değiştiriyor |
| Orman/çalılık bağlamı | Önceki saha kaynağında genç kızılçam ve maki anlatımı | İşaretin özgün konumu ve nokta örtüsü kabulü açık |
| Değerlendirme kapsamı | Kaynakla incelenmiş tek büyük olay | Dört il, küçük yangınlar ve altı yıl için temsil sağlamıyor |

Pozitif adayın varlığı için bütün günün eksiksiz gözlenmesi yeni bir
önkoşul yapılmadı. Eksik gözlem negatif üretme izni sağlamıyor. Bu
inceleme Salur'u otomatik 0/1 etiketine çevirmiyor.

## Araştırmacıya sunulan yöntem yönü

**A — Önerilen, başlangıç geçmişini koruyan izleme provası.** Zamanları
sırayla ve aynı zamanlı kayıtları birlikte işleyen sınırlı bir yöntem
provası hazırlansın. Sonradan birleşen adayların önceki başlangıç
hipotezleri silinmesin. Birleşme ilişkisi ayrı saklansın. Aynı ilk
zamandaki bütün hücreler ortak aday kimliğine bağlı kalsın. Yeni
görünen aday otomatik yeni fiziksel yangın sayılmasın. Mevcut dokuz
ayar karşılaştırma olarak korunsun; tek vakadan küresel eşik seçilmesin.
Maliyeti, ek izleme kodu ve parçalanma/yeniden görünme kontrolleri.

**B — Gün sonu grafik kesitleriyle daha sınırlı karşılaştırma.** Yalnız
her hedef pencerenin sonuna kadar gelen kayıtlar kullanılarak grafik
incelemesi hazırlansın. Prova daha basit olur. Günler arasında süren
yangınları ve adayların birleşme geçmişini izlemek için ayrıca politika
gerekir. Salur'da gün sonu sonucu kararlı olsa da bu bütün vakalar için
gösterilmiş değil.

Bu seçim bir yöntem hazırlığı yönü olacak. Gerçek yangın kimliği,
güvenilir pozitif küme, PU varsayımları, eğitim ve nihai birleştirme
kabulü ayrı kalacak. Araştırmacı yönü henüz seçmedi. Ana hedef ve
önceki bütün ilk hücreleri birlikte koruma kararı değişmedi.

## Kontroller ve makbuzlar

21 girdi hash'i denetlendi. Dokuz tam bileşen, 18 başlangıç/gün sonu
ve iki kenar sınırı grafiği karşılaştırıldı. Yeni regresyon testi,
ilerideki bir köprünün daha eski ayrı kaydı bağlayıp ilk hücreyi
değiştirmesini ve zaman boşluğu farkını sınadı. İlgili **9 test**,
Ruff ve biçim kontrolü geçti. Hedef alanları boş, etiket izinleri kapalı.

Hesap komutu `python scripts/quality/audit_salur_event_context.py`.
Makbuz
`outputs/reports/dataset/salur_event_context_v1/20261118T230221Z_cab0c9e1/readback.json`.
SHA-256 `89ffb290079ae4167cbf3b577e9787cbbde5092118acaab0d43d704189dad846`.

Görsel komutu `python scripts/quality/plot_salur_event_context.py`.
Son görsel ve makbuz
`outputs/reports/dataset/salur_event_review_v1/20261118T230442Z_2a32435b/`.
Makbuz SHA-256 `c5d89ef9814379350591ceafb6dc5bca339ed48be23d086442e25ed192a5f1e1`.
Görsel çıktı açılarak kontrol edildi. Klasör zamanları UTC 18 Kasım;
çalışma tarihi Türkiye saatiyle 19 Kasım. Birinci aşama açık.
