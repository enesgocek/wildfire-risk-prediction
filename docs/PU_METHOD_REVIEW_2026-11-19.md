# PU yönteminin bilgi gereksinimleri — 19 Kasım 2026

**Aynı gün sonraki inceleme:** aşağıda yalnız özeti incelendiği belirtilen
Bao 2018 çalışmasının tam metni daha sonra ayrıca kontrol edildi.
Üye düzeyinde sınıflandırma yolu ve kalibrasyon ayrımı
[yeni raporda](PU_MIL_FEASIBILITY_2026-11-19.md). Önceki inceleme kapsamı
bu tarihli ekleme ile geriye dönük değiştirilmedi.

Amaç, birinci aşamadaki açık konuları yeni bir algoritmanın gerçekten
çözüp çözemediğini incelemek. Kaynak taraması ve tam olasılıklı sentetik
karşı örnekler birlikte kullanıldı. Sonuç, bütün PU yöntemlerinin işe
yaramayacağı değildir. Mevcut veriye uygulanabilirliği gösterilmeden bir
yöntemin etiket kabul sorununu çözdüğü söylenemez. Ana araştırma hedefi
ve 8 Kasım kararı korunuyor.

## Yeni birincil çalışma

He, Liang ve Liu'nun *Identifying Labeling Mechanism in Positive–Unlabeled
Learning under Unknown Class Prior* çalışmasının yazarları, başlığı ve
yayın bilgisi PMLR sayfasından doğrulandı. Yayıncı deposundaki 18 sayfalık
PDF indirildi. İlgili yöntem bölümleri metinden, basılı 2121 ve 2124.
sayfalar ayrıca görüntüden incelendi.
[PMLR 337, 2119–2136, UAI 2026](https://proceedings.mlr.press/v337/he26a.html).

Çalışma, sınıf oranı önceden bilinmeden SCAR uyumluluğunu sınamayı
öneriyor. Başlangıçtaki etiketli örneklerin gerçek pozitif olduğu ve
örneklerin bağımsız, aynı dağılımdan geldiği kabul ediliyor. Negatif skor
bileşeninin tanımlanabilirliği, dağılım yaklaşımının doğruluğu ve çoklu
testlerde bağımsızlık veya PRDS koşulu da önemli. Yöntem, belirli
varsayımlar altında ampirik pozitif kümeler ve bootstrap testleri
oluşturuyor. SCAR'ın reddedilmemesi onun doğrulandığı anlamına gelmiyor.
Yayındaki geçerlilik sonuçlarının hata terimleri korunmalı. Bu projede
algoritma uygulanmadı veya başarımı ölçülmedi.

**Projeye ilişkin çıkarım.** Sınıf oranını mutlaka dışarıdan kesin bir
sayı olarak alma şartı koymamalıyız. Yeni yöntemde bu bilgi gereksinimi
başka varsayımlarla ele alınıyor. Buna karşılık başlangıç pozitiflerinin
niteliği ve varsayımların projeye uygunluğu açık kalıyor. Hücrelerin ve
günlerin bağımlılığı nedeniyle makaledeki i.i.d. kabulü, bizim takvime
otomatik taşınamaz. Bu çıkarım yeni bir kabul engeli eklemiyor; kullanılacak
yöntemin kendi gerekçesini istiyor.

## Tam olasılıklı sentetik karşı örnek

`S=1` etiketli kayıt, `Y=1` gerçek pozitif olsun. Negatiflerin pozitif
etiketlenmediği üç ayrı yapay dünyada iki grubun ağırlığı eşit alındı.
Her dünyada gözlenebilir dağılım tam olarak aynı. A'da etiketli kayıt
olasılığı %2, B'de %1.

| Yapay dünya | A gerçek pozitif olasılığı | B gerçek pozitif olasılığı | A/B etiketlenme olasılığı | Toplam pozitif oranı | Yüksek risk |
|---|---:|---:|---|---:|---|
| Sabit seçilme | %4 | %2 | 1/2, 1/2 | %3 | A |
| Özelliğe bağlı, farklı oran | %2,5 | %10 | 4/5, 1/10 | %6,25 | B |
| Özelliğe bağlı, aynı oran | %2,5 | %3,5 | 4/5, 2/7 | %3 | B |

Hesaplar kayan noktalı yaklaştırma yerine tam kesirlerle yapıldı.
`P(X,Y,S)` hücrelerinin toplamı bir. Her dünyanın `P(X,S)` marjinalleri
tam eşit. Birinci ve üçüncü dünyada toplam sınıf oranı da aynı olduğu
halde gerçek risk sıralaması ters. Dolayısıyla serbestçe özelliğe bağlı
seçilme altında, gözlenen kayıt oranı ve hatta toplam sınıf oranı tek
başına gerçek yerel riski belirlemiyor.

Bu örnekler gerçek yangın sıklığı, kayıt doğruluğu veya model deneyi
değildir. Özelliğe bağlı seçilme dünyaları PGPU gibi ek kısıtlarla
dışlanabilir. Bu nedenle karşı örnek makalenin koşullu güvencelerini
çürütmüyor; ek kısıtların neden gerekçelendirilmesi gerektiğini gösteriyor.

## Kaba konum ve yıllık sayılar

Çok örnekli PU öğrenmesi, tek tek üyeler yerine grup etiketleriyle
çalışmayı araştıran gerçek bir yöntem ailesi. Bao, Sakai, Sato ve
Sugiyama'nın 2018 makalesinin yayın kimliği ve özeti kontrol edildi;
tam yöntemi bu incelemede değerlendirilmedi.
[Yayın kaydı ve DOI](https://pubmed.ncbi.nlm.nih.gov/29804041/).

Basit bir karşı örnekte, üç hücrelik bir grupta tam bir pozitif bulunduğu
biliniyor. `(1,0,0)` ve `(0,1,0)` atamaları hem aynı grup etiketini hem
aynı toplamı sağlıyor. Bu bilgiyle bütün üyeler pozitif yapılamaz.
Birden fazla gruptan varsayımlarla öğrenme olasılığı dışlanmıyor; grup
bilgisinin tek başına nokta etiketi olmadığı gösteriliyor.

Ayrıca iki ayrı olay aynı hücre-günde veya iki ayrı hücre-günde olabilir.
Olay sayısı iki iken ikili pozitif hücre-gün sayısı bir veya iki oluyor.
Önceki OGM il-yıl toplamları bu nedenle doğrudan hücre-gün sınıf oranına
çevrilmedi. Gerçek kullanımda idari sınır, orman/çalılık kapsamı, tarih
ve ilk tespit penceresi de uzlaştırılmalı.
[Önceki resmî toplam denetimi](OGM_PROVINCE_YEAR_2026-11-08.md).

## Kabul ve devam kararı

| Yol | Bu incelemenin sonucu | İlerleme için gereken bilgi |
|---|---|---|
| Sınıf oranı bilinmeden SCAR testi | Araştırılabilir; otomatik kabul sağlamıyor | Güvenilir pozitifler, skor bileşeni ve bağımlılık varsayımlarının gerekçesi |
| Grup düzeyinde pozitif–belirsiz öğrenme | Olası yöntem yönü; uygulanabilirlik açık | Gerçek grup kapsamı, grup etiketinin anlamı ve hücre düzeyinde değerlendirme dayanağı |
| Yıllık toplamı doğrudan hücre-gün oranı yapma | Mevcut bilgilerle gerekçelendirilmedi | Sayım birimi, kapsam ve olay–hücre–gün eşlemesi |
| Kayıt sıklığını doğrudan gerçek risk sayma | Serbest seçilmede karşı örnekle belirsiz | Seçilme mekanizmasına ilişkin desteklenebilir kısıtlar |

Sonraki ilerleme yeni kontrol sayısına bağlanmıyor. Öncelik, mevcut
adaylardan bağımsız kaynaklarla başlangıç ve kapsam anlamı kurulabilen
pozitif örneklerin kabul gerekçesini somutlaştırmak. Bu mümkün olmazsa,
ek varsayım veya hedef/iddia değişikliği somut yarar ve sınırlarıyla
araştırmacıya sunulmalı. Önceden reddedilen ayrı katalog hedefi sessizce
plana alınmayacak. Yeni kurumsal talep açılmadı.

Birinci aşama açık. `daily_observation_status=unknown`, pozitif/negatif
etiket izinleri kapalı. Sınıf oranı tahmini, gerçek model eğitimi ve
nihai birleştirme yapılmadı. 2024/2025 verisi okunmadı.

## Yerel yeniden üretim ve kontrol

Komut `python scripts/quality/audit_pu_identifiability.py`.
Kaynak PDF hash'i, tam kesirli ortak dağılımlar ve marjinaller, ters
sıralamalar, grup/sayım örnekleri, mevcut kapalı protokol ve JSON geri
okuması denetlendi. Ruff ve biçim kontrolü geçti. Bu doğrulamalar
gerçek etiket veya model doğrulaması değildir.

PDF `outputs/reports/dataset/pu_method_review_v1/sources/he26a.pdf`.
10.495.659 bayt, SHA-256
`04d34a9bbbf47360e04796a67ec0d6e738b39aad6ec5c378887e0fc1fe36b95a`.

Son çalışma
`outputs/reports/dataset/pu_method_review_v1/20261118T225001Z_357f143d/readback.json`.
SHA-256 `e80edf0756005700d5d9ebfc78a95581410b37668ae1bf3821862e0e150c2485`.
Çalışma kimliği UTC 18 Kasım 22.50; yerel araştırma tarihi Türkiye
saatiyle 19 Kasım 01.50. Kaynak PDF ve çıktılar Git'e eklenmez.
