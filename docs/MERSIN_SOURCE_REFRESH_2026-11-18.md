# Mersin kaynak sürümü ve yayın kimliği kontrolü — 18 Kasım 2026

Gülnar–Silifke vaka incelemesinden sonra, kamuya açık arşivde yeni
başlangıç/koordinat açıklaması yayımlanıp yayımlanmadığı kontrol edildi.
Zenodo, Crossref ve Europe PMC'nin doğrudan API yanıtları yerelde saklandı.
Bu çalışma yayın kimliği ve arşiv sürümünü doğrular. Kaynak kaydının
bulunması, arşivdeki bütün alanların hedefimiz için bilimsel kabulü sağlamaz.

## Doğrulanan kayıtlar

| Kaynak | Bu kontrolde gözlenen |
|---|---|
| Zenodo kaydı 21455927 | HTTP 200, sürüm 1.0.0 |
| Zenodo sürüm listesi | Tek kayıt, aynı sürüm kimliği |
| Yayımlanan dosya | Tek ZIP; MD5 özeti yerel arşivle eşleşiyor |
| Crossref DOI kaydı | HTTP 200, DOI 10.1177/00368504261495731 |
| Europe PMC DOI araması | Tek yayın kaydı, MED 42859945; PMC tam metin kimliği yok |
| Yayınevi HTML ve XML | İki erişim de HTTP 403 |

Yerel arşivin MD5 özeti `2a46ebed6ef6318298c21ba3f892f864`.
SHA-256 `21bb776f1c4a4d96b25c15e72da2730eb0a4ca6472451c9f7f7a3dfb4246ae8a`.
Sürüm listesindeki tek kaydın dosyasıyla aynı bytes/hash korunuyor.
Zenodo'nun latest bağlantısı HTTP 301 verdi; sürüm listesi doğrudan
HTTP 200 yanıtıyla denetlendi. Bu kontrol tarihinde yeni ZIP sürümü yok.
[Zenodo kayıt API'si](https://zenodo.org/api/records/21455927),
[sürüm listesi](https://zenodo.org/api/records/21455927/versions).

Crossref ve Europe PMC, yayının başlığını *Early wildfire escalation
prediction with temporal validation and statistical benchmarking in a
mediterranean region* olarak eşleştiriyor. Yayınevi metni alınamadığı
için yöntem bölümündeki konum veya saat açıklaması doğrulanmış sayılmadı.
Europe PMC'nin açık erişim işareti ile Crossref lisans metadatası farklı
bilgiler taşıyor; bu kontrolde erişim durumu ödeme gereksinimine çevrilmedi.
[Crossref kaydı](https://api.crossref.org/works/10.1177/00368504261495731),
[Europe PMC DOI sorgusu](https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1177/00368504261495731&format=json).

## Verinin kullanım amacı ve proje kabulü

Zenodo açıklaması arşivi, mevcut yangınların son alanının en az 10 ha'ya
büyümesini tahmin eden çalışmanın yeniden üretim paketi olarak tanımlıyor.
Olay günü meteorolojisi ve son yanan alan, bu çalışmanın alanları arasında.
Bizim çalışmamızdaki sonraki 24 saatte yeni yangın olayı hedefinin
başlangıç ve gözlem koşulları ayrıca denetleniyor. Paket açıklaması,
iki arşiv koordinatının özgün tutuşma/yayılma rollerini çözmüyor.
[Arşiv açıklaması](https://zenodo.org/api/records/21455927).

Gülnar vaka incelemesinde şu durum kaydedildi.

| Kabul konusu | Mevcut kanıt |
|---|---|
| Kaynağın varlığı ve yerel bytes | Doğrulandı |
| İki koordinatın olay öncesi örtüsü | İki tarihte görüntü ve araştırmacı ön notları kayıtlı |
| Bildirilen sabah saatlerinin hedef günü | Sekiz senaryoda 7 Eylül |
| İki arşiv satırının özgün olay kimliği | Açık |
| Gerçek tutuşma koordinatı ve başlangıç/yayılma rolü | Açık |
| Dört ilde olay kapsamı ve model değerlendirme dayanağı | Açık |

Bu vakadaki başlangıç rolünün çözümü, özgün olay kimliği veya koordinatın
nasıl üretildiğini açıklayan ek kaynak bilgisine bağlı. Mevcut kamu
paketinin sürüm kontrolü tamamlandı. Birinci aşamanın sonraki işi, kalan
vaka ve bölge kanıtlarını kabul koşullarıyla birlikte uzlaştırmak.
Günlük gözlem `unknown`, negatif etiket izni `false`; etiket kabulü açık.

## Yeniden üretim

`python scripts/quality/audit_mersin_source_refresh.py` üç API erişim
makbuzu ve başarılı metaveri yanıtlarını hash ile doğrular. Yerel ZIP'in
MD5 ve SHA-256 değerleri, DOI kimliği, sürüm sayısı ve iki yayın dizininin
DOI uyumu kontrol edildi. JSON geri okuması ve Ruff geçti. Bu değişiklik
metaveri doğrulamasıdır; yeni bilimsel model deneyi yürütülmedi.

Yerel makbuz
`outputs/reports/dataset/mersin_source_refresh_audit_v1/20261118T203146Z_ece21f37/readback.json`.
SHA-256 `dc1b442c716966f26d012ed4512d831c855abea353833bc7604165084abfe338`.
