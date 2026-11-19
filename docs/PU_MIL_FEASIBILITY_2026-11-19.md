# Grup bilgisinden hücreye PU uygulanabilirliği — 19 Kasım 2026

Bu inceleme, önceki PU değerlendirmesinde açık bırakılan Bao ve
arkadaşlarının tam yöntemini ele alır. Yeni yöntem kabulü veya model
eğitimi değildir. Ana 24 saatlik yeni olay hedefi korunur.

## Doğrulanmış kaynak

Han Bao, Tomoya Sakai, Issei Sato ve Masashi Sugiyama, *Convex formulation
of multiple instance learning from positive and unlabeled bags*, Neural
Networks 105, 132–141 (2018), DOI 10.1016/j.neunet.2018.05.001.
[Yayın kimliği](https://pubmed.ncbi.nlm.nih.gov/29804041/) ve
[yazarın yayın listesi](https://t-sakai-kure.github.io/publications) eşleşti.
İncelenen tam metin [arXiv v3](https://arxiv.org/abs/1704.06767v3);
dergi PDF'iyle bayt eşitliği iddiası yok.

**Kaynağın yöntemi.** Pozitif grup en az bir pozitif üye içerir.
PU-SKC doğrudan grup sınıflandırır; 3.3 grup sınıf oranını tahmin eder.
3.4 ayrıca üye düzeyinde bir yol sunar. Bu yolun i.i.d. örnekleme,
ortak sınıf koşullu dağılımlar ve farklı karışım oranları kabulleri var.
Türetilen sınıflandırma eşit test sınıf oranlarını varsayıyor. Dolayısıyla
makalenin yalnız grup çıktısı verdiği söylenemez; sınıflandırma işareti
kalibre edilmiş hücre olasılığı da değildir. PDF s. 10–12 metin ve
görüntüden, Ek A s. 24 devamı metinden incelendi.
[Birincil tam yöntem](https://arxiv.org/html/1704.06767v3).

## Projeye ilişkin çıkarım

Kaba konumlu kaynakları kullanmak bütünüyle dışlanmıyor. Fakat bir
ilçede yangın anlatılması, seçtiğimiz hücre-gün grubunda **yeni olayın
ilk uydu tespitinin** bulunduğunu tek başına göstermiyor. Grup sınırı,
zaman aralığı ve pozitif anlamı önce kaynakla uzlaştırılmalı.

Olay sonrası yangın alanı geriye dönük etiket desteği olarak incelenebilir.
Bu geometrinin tahmin anında bilindiği varsayılamaz. Yeni bir grubun
tahmin birimi yapılması veya hücre sınıflandırıcısına geçilmesi farklı
uygulama tasarımlarıdır. Kullanıcının ana hücre-gün hedefi değiştirilmedi.

Komşu hücrelerin bağımlılığı, aynı olaydan gelen örtüşen gruplar ve grup
büyüklüğüyle değişen örnek ağırlıkları uygulama sırasında ele alınmalı.
Bunlardan otomatik SCAR reddi veya bütün PU yöntemlerinin olanaksızlığı
sonucu çıkarılmadı. Grup oranı tahmini hücre-gün sıklığı yerine konmadı.

## Tam kesirli açıklama örneği

Aşağıdaki dağılımlar bu çalışmada kurulan **yapay örnektir**; yayın
başarımı, yangın sıklığı veya eğitilmiş model çıktısı değildir.
Pozitif/negatif koşullu A/B dağılımları `(4/5,1/5)` ve `(1/5,4/5)`;
iki karışım katsayısı `theta=pi=1/10` alındı. U havuzunda pozitif oranı
bu cebirsel örnekte `1/100`.

| A/B grubu | Eşit sınıf oranlı nüfusta olasılık | %1 pozitif oranlı yapay U nüfusunda olasılık |
|---|---:|---:|
| A | %80 | `4/103`, yaklaşık %3,8835 |
| B | %20 | `1/397`, yaklaşık %0,2519 |

Yoğunluk farkları tam olarak `27/500` ve `−27/500`. A için işaretin
pozitif olması gerçek seyrek nüfusta %50 üstü olasılık demek değil.
Makalenin sınıflandırıcısının %80 döndürdüğü iddia edilmedi. Örnek,
pozitif grup üretimini veya her grupta pozitif bulunmasını simüle etmez;
yalnız iki karışımın cebirini ve nüfus oranının etkisini gösterir.

## Sonuç ve yeniden üretim

Bu yöntem mevcut güvenilir pozitif, seçilme ve değerlendirme konularını
kendiliğinden kapatmıyor. Yeni bir algoritmaya geçiş kararı önerilmedi.
Birinci aşama açık; etiket kapıları kapalı ve gözlem `unknown`.
Yerel 2024/2025 verisi okunmadı; eğitim veya nihai birleştirme yok.

`python scripts/quality/audit_pu_mil_contract.py` PDF kimliğini, tam
kesirli dağılımları/özdeşliği, kapalı kabul durumunu ve JSON geri
okumasını denetler. Kaynak 725.028 bayt; SHA-256
`a32a9d6fdab37aa3aced49dce0a475d9db2290d07dc4fa837aecb02cc1441b60`.

Makbuz:
`outputs/reports/dataset/pu_mil_method_v1/20261119T112841Z_07975786/readback.json`.
SHA-256 `52f57462ea607fdc8d0bcb41fd5c93b420254dff766dc907a7f1004cdec9d857`.
Kaynak ve çıktılar yerel tutulur. Önceki yalnız özet incelemesi kaydı
tarihsel olarak değiştirilmedi.
