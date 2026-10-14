# Kurumsal kayıtlarla ilk vaka incelemesi — 14 Ekim 2026

## Amaç ve yöntem

[Örnek inceleme paketinden](LABEL_EVIDENCE_REVIEW_2026-10-14.md) sonra,
2021 büyük yangın adayları için harici kurumsal kayıt araması yapıldı.
Bu çalışma etiket doğruluğu ölçümü veya tamamlanmış uzman incelemesi değildir.
Kaynak anlatımı, yerel uydu kümesi ve araştırma yorumu ayrı tutuldu.

Antalya Valiliği ve Orman Genel Müdürlüğünün iki resmî HTML sayfası,
14 Ekim 2026'da canlı HTTPS isteğiyle alındı. İlk varsayılan istemci isteği
HTTP 500 verdi; açık araştırma User-Agent bilgisiyle sonraki istek başarılı
oldu. En fazla 3 MB/sayfa ve 25 saniye/istek sınırı kullanıldı. Çerez veya
kimlik bilgisi gönderilmedi; bulut hesabına erişilmedi. Ham sayfalar yalnız
yerel çıktı alanında, URL/tarih/HTTP durumu/boyut/SHA-256 kaydıyla tutuldu.

Kaynakların ilgili açıklamaları okunup küçük bir
[kaynak siciline](research/label_reference_sources_2026-10-14.json) kaydedildi.
Görünür metindeki tarih/yer anahtarları kodla ayrıca kontrol edildi.
Bu anahtar kontrolü tek başına anlamsal doğruluk veya bağımsızlık kanıtı değildir.
Kurumsal anlatımın sensör ve bildirim kökeni denetlenmediği için tam bağımsız
ground truth olduğu ileri sürülmedi. İki resmî açıklama birbirinden bağımsız
iki saha gözlemi olarak sayılmadı.

## Kaynakta bulunan bilgi ve çıkarım sınırı

**Valilik kaydı:** 28 Temmuz 2021 tarihli açıklama Manavgat'ta dört ayrı
başlangıç yeri bildirir: Yeniköy, Sarılar, Baraj bölgesi ve Gebece. Bir
başlangıç için 12:05 saatini verir; metinde saat dilimi açık değildir.
[Antalya Valiliği, özgün açıklama](https://www.antalya.gov.tr/manavgatta-4-ayri-noktada-orman-yangini-cikti).

Bu anlatım, bölgedeki bütün uydu tespitlerinin tek bir tutuşmadan gelmesi
varsayımına karşı inceleme gerekçesidir. Belirli kümenin yanlış birleştiğini
tek başına kanıtlamaz; dört koordinat veya grid/olay eşlemesi sağlamaz.
Kaydı kullanarak kümeler otomatik dörde bölünmedi, bir kümeye yangın kimliği
atanmadı ve uydu tespiti gecikmesi hesaplanmadı.

**OGM kaydı:** 13 Ağustos 2021 açıklaması 28 Temmuz–12 Ağustos dönemindeki
yangınlar için toplu kontrol altına alma bilgisidir.
[Orman Genel Müdürlüğü, özgün açıklama](https://www.ogm.gov.tr/tr/haberler/tum-orman-yanginlari-kontrol-altinda).
Bu bilgi tekil bir kümenin son aktif tespitini, tam sönme saatini veya ertesi
günün yangınsızlığını belirlemez. Uydu serisinin sonunu bu tarihe kırpma veya
negatif gözlem üretme işlemi yapılmadı.

## Yerel vaka bağlantısı

Önceki seçkide 28 Temmuz 2021 ilk tespitli, başlangıç koordinatları bağlam
aramasında incelenmiş 10 olay-senaryo adayı belirlendi. Kimlikleri açıkça
sicile yazıldı; seçim yeni bir temsili örnekleme değildir. Bu 10 adayda
sekiz farklı üyelik örüntüsü bulunur. Bunlar **10 doğrulanmış yangın veya
aynı yangının sekiz doğrulanmış sürümü değildir**.

Yeni `candidate_context_links.csv`, yerel ilk/son tespit, tespit sayısı,
bütün ilk hücreler, üyelik hash'i ve kaynak URL'sini birlikte tutar.
Bağlantının durumu yalnız `candidate_regional_context_only` olur.
`exact_event_identity_proven=false`, `first_cell_identity_proven=false`;
`ignition_timestamp_utc` ve `target` boştur. İlk hücreler kaybedilmedi.

Bu seçkide ilk uydu tespitleri 28 Temmuz 10:11–23:22 UTC, küme tespit
sayıları 1.307–5.304 aralığındadır. Bunlar yerel seçilmiş küme sayımlarıdır;
kurumsal kayıttaki başlangıçlara birebir karşılık veya hata oranı değildir.
Sadece tek tarih/mesafe eşiği ya da tespit sayısıyla olay tanımı seçilmedi.

## Doğrulanamadığı için kullanılmayan kaynaklar

- OGM Muğla duyurusunda PDF adı bulundu; ilgili indirme bağlantısı HTML'de
  doğrulanamadı. PDF'nin içeriği okunmuş veya kabul edilmiş sayılmadı.
  [Duyuru](https://www.ogm.gov.tr/muglaobm/duyurular/2021-yili-orman-yanginlari-degerlendirme-raporu-430).
- EMSR527 arama adayı, resmî sayfada Yunanistan aktivasyonu olduğundan
  Türkiye vakaları için reddedildi. Aktivasyon kimliği tahmin edilerek
  veri indirilmedi. [Resmî aktivasyon sayfası](https://mapping.emergency.copernicus.eu/activations/EMSR527/).

## Geri okuma, test ve sıradaki karar

İki sayfanın toplam 497.044 baytı ve vaka bağlantı CSV'si dosyadan hash ile
kontrol edildi. Önceki altı inceleme çıktısı ve 22 donmuş bulut girdisi aynı.
Önceki formdaki 453 birimin tamamı hâlâ `not_reviewed` durumundadır;
kurumsal bağlam eklenmesi insan incelemesi tamamlandı olarak gösterilmez.
55 ilgili test ve lint/format geçti: bağlam/etiket ayrımı, değişmiş içerik,
eğitim kapsamı, kayıt kimlikleri, görünür metin, indirme sınırı/izinli URL,
uçtan uca kaynak makbuzu ve boş hedef kontrol edildi.

Yerel sonuç dizini:
`outputs/reports/dataset/reference_context_v1/20261014T154819Z_113615fa/`.
`readback.json` SHA-256:
`fcca0e13511584f8d45f73887302ba840ee82f4d0d403a6a63b772c78a0de351`.
Kaynak makbuzları bu rapordadır; ham HTML Git'e eklenmez.
Kapanış `completion_readback.json` SHA-256:
`a7732b2b6ed3be67b1eae4c91ea81c6b1ac08232125f43cc6ef3ff60102d194e`.

Sıradaki ihtiyaç, özellikle bu bölgesel adaylar için olay bazlı koordinat/
yanmış alan sınırı ve zaman bilgisi olan referanslarla coğrafi karşılık
kurmaktır. Yangın sonrası yanık alan da tek başına 24 saatlik başlangıç
etiketini doğrulamaz. Temsili pilotta yangınsızlık referansı ve hedef
penceresinin gözlem yeterliliği ayrı çözülmelidir. Kaynak yetersizse sonuç
belirsiz kalır; gözlem unknown, pozitif/negatif kapıları kapalı, model_ready
false korunur. Bu işlem 2024 ve 2025'i açmadı; model veya bulut işi başlamadı.
