# Hesap ızgarasının çözünürlük ve başlangıç konumu — 5 Ekim 2026

14 Ocak 2019'un mevcut sekiz geçişli yaklaşık nominal yangınsız kara birleşimi
50/100/200 koordinat metrelik sabit EPSG:6933 ızgaralarına aktarıldı. Her
çözünürlükte başlangıç (0,0), yarım hücre doğu, yarım hücre kuzey ve iki
yönde yarım hücre kaydırılarak 12 senaryo karşılaştırıldı. Modelin 5 km'lik
2.899 hücresi ve kaynak dosyaları aynı kaldı. Yeni indirme, 2024/2025 okuması,
üretim çözünürlüğü veya etiket seçimi yapılmadı.

## Yöntem ve karşılaştırma alanı

İnce hücrenin merkezi mevcut yaklaşık gözlem poligonunun içinde veya tam
sınırındaysa hücre gözlenmiş sınıfına örneklenir. İnce hücrenin analiz/AOI
parçasıyla kesişen gerçek alanı ağırlık olarak kullanılır. Payda her senaryoda
aynı vektör alanıdır; payda da merkez sayımıyla yaklaşık hesaplanmaz.
Komşu 5 km hücrelerin parçaları birlikte kullanılır. Böylece sınırın öbür
yanındaki ince hücre merkezi kaybolmaz; her analiz hücresinde farklı
bir ızgara başlangıcı oluşturulmaz.

AOI dışındaki kaynak bilgisi bilinmediğinden ortak karşılaştırma alanı AOI
sınırından 300 koordinat metresi içeridedir. En büyük ince hücrenin yarım
köşegeninden daha geniş bu mesafe, karşılaştırılan parçaların dışındaki
bilinmeyen merkezleri ayırır. AOI delikleri korunur. Alan 59.334,656 km²;
1.392,458 km² kenar şeridi karşılaştırma dışında. Vektör referans alanı
35.291,648 km² ve oran %59,479. 51 hücrede iç karşılaştırma alanı kalmadı;
bu hücreler raporda tutuldu, oranları boş bırakıldı. Bu sayı gözlemsiz veya
negatif yangın örneği sayısı değildir. Önceki 100 m sınır tanısıyla payda
aynı olmadığından iki çalışmanın toplam oranları doğrudan karşılaştırılmaz.

## Sonuç

Tablodaki oran farkı dört başlangıç konumunun aynı hücrede ürettiği en büyük
ve en küçük kapsam oranları arasındaki farktır. Yüzde puanı kullanılır;
örneğin %60 ile %60,2 arasında 0,2 yüzde puanı vardır.

| Hesap çözünürlüğü | Hücrelerin %95'inde başlangıç farkı en fazla | Toplam alanın başlangıçlar arası açıklığı |
|---|---:|---:|
| 50 m | 0,203 yüzde puanı | 0,739 km² |
| 100 m | 0,580 yüzde puanı | 2,712 km² |
| 200 m | 1,639 yüzde puanı | 11,628 km² |

Vektör referansla karşılaştırıldığında dört başlangıçtaki hücre başına mutlak
oran hatasının 95. yüzdeliği 50 m için 0,081–0,083, 100 m için 0,239–0,254,
200 m için 0,702–0,737 yüzde puanı. Bu, yaklaşık kaynak poligona göre hesap
farkıdır; gerçek uydu gözlem hatası değildir. Toplamdaki artı/eksi farkların
birbirini götürmesi hücre bazındaki farkları gizleyebileceği için mutlak
hücre hataları ve başlangıç aralıkları ayrıca kaydedildi.

Küçük, düzensiz AOI parçaları daha hassas: C537_R875 hücresinin iç
karşılaştırma parçası yaklaşık 0,020 km². 200 m senaryolarında kapsam
oranının başlangıç açıklığı yaklaşık 99,65 yüzde puanı. Bu hücre otomatik
elenmedi; minimum alan veya negatif etiket eşiği seçilmedi. Ek geometrik
grupta 1.925 dikdörtgen karşılaştırma parçasının 95. yüzdelik başlangıç
farkı 50/100/200 m için yaklaşık 0,140/0,408/1,232 yüzde puanı.

50 m hesabı bu örnekte daha kararlı. Daha ince hesap ızgarası kaynağa yeni
uydu detayı eklemez. Tek kış günü; sonuç yıl, mevsim, sensör geometrisi veya
üretim yöntemi için genel doğruluk onayı değildir. Doğrudan doğal VIIRS
dizileri yeniden örneklenmedi; resmî fiziksel ayak izi konusu açık kalıyor.

## Denetim ve sonraki adım

19 yeni test boş/tam gözlemi, AOI deliğini, komşu hücreyi, dar parçayı,
negatif koordinatı, sınır üyeliğini, farklı başlangıçları ve bellek sınırını
sınadı. Tam kümede 257 test geçti; kod/biçim denetimi başarılı.

Bağımsız doğrulayıcı 2.899 hücrenin tüm sütunlarını, 12 senaryonun toplam ve
istatistiklerini, vektör paydalarını ve kaynak SHA256 özetlerini geri okudu.
Altı seçilmiş kontrol, tek tek merkez noktaları ve seçilmiş karelerin
birleşimiyle yeniden hesaplandı; en büyük alan farkı 0,00000006 m² altında.
Günlük gözlem `unknown`, negatif etiket izni `false` kaldı.

Yerel çıktılar `outputs/reports/observation_coverage/` altında:

- `area_grid_sensitivity_2019-01-14.json/.csv`: 12 senaryo, bütün hücreler.
- `area_grid_sensitivity_readback.json`: bağımsız kontroller ve geometrik grup.

CSV yaklaşık 1,45 MB; büyük ham arşiv indirilmedi. Sırada eğitim örneklerinde
tarama kalitesi ve gözlem zaman boşlukları var. Bu incelemeler ve daha geniş
eğitim örnekleri sonrasında üretim yöntemi/eşik seçenekleri kullanıcıya
sunulacak; bu aşamada yöntem kararı verilmedi.
