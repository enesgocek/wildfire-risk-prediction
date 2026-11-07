# Araştırma yol haritası

Güncelleme: 4 Kasım 2026. Takvim, veri erişimi ve doğrulama sonuçlarına göre
ilerler. Aşağıdaki aşamalar kabul ölçütleridir; tamamlanmış sonuç veya
kesin süre taahhüdü değildir. Güncel durum [STATUS.md](STATUS.md) içindedir.

| Sıra | Aşama | Geçiş koşulu |
|---|---|---|
| 1 | Eğitim döneminin kaynak ve gözlem tanılarını hazırlama | Çıktı bütünlüğü, kaynak kimliği, eksik gün/ay ve geri okuma raporları |
| 2 | Olay kataloğu ve etiket politikası | Olay tanımı, Type değerlendirmesi, gözlem yeterliliği ve belirsiz kayıt stratejisi |
| 3 | Model veri seti | Zamana uygun özellikler, veri sözlüğü, split/manifest ve olay sızıntısı denetimi |
| 4 | Temel karşılaştırmalar | FWI uygunluğu ve tabular modeller; aynı protokolde PR-AUC ve kalibrasyon |
| 5 | Hata analizi ve model seçimi | İl/mevsim değerlendirmesi, özellik katkısı ve eşik seçimi yalnız eğitim/doğrulamada |
| 6 | Dondurma ve final test | Model/özellik/eşik/ortam sürümleri sabit; 2025 bağımsız değerlendirme |
| 7 | Günlük karar destek prototipi | Veri erişilebilirliği, zaman damgası, eksiklik gösterimi ve uygulama denetimi |

## Paralel hazırlık

Literatür karşılaştırması, veri kabul gerekçeleri ve risk planı, bitirme
araştırmasının ihtiyaçlarına göre hazırlanır. 4 Kasım kararıyla TÜBİTAK
başvurusu planlanmıyor; eski [başvuru hazırlığı](research/2209A_PREPARATION.md)
tarihsel kayıttır. Bilimsel kabul ölçütleri başvuru takviminden bağımsızdır.
Güncel yöntem işi, yeni kurumsal talep açmadan PU uygulanabilirliğini
incelemektir; [altı veri tamamlama paketinin](DATASET_COMPLETION_PLAN_2026-11-04.md)
kabul kapıları korunur.

## Kapsam sınırları

Ana hedef dört il ve 24 saattir. 72 saat/7 gün ufukları, dış ülke verisi,
uydu temsilleri ve ek ürünler, veri uygunluğu ve karşılaştırmalı yarar
gösterildiğinde değerlendirilecek seçeneklerdir. Bu seçenekler için henüz
ek üretim veya deney başlatılmamıştır. Power BI tarihsel inceleme fikri
uygulama kapsamı kesinleşmeden zorunlu teslim olarak sunulmaz.

## Tarihsel plan

Başlangıçta hazırlanmış ayrıntılı haftalık plan [ROADMAP_INITIAL.md](ROADMAP_INITIAL.md)
dosyasında korunur. Oradaki eski il önerileri, yaklaşık süreler ve negatif
etiket örnekleri güncel bilimsel protokolün yerine geçmez. Belirleyici kapsam
[PROJECT.md](PROJECT.md), araştırma soruları [araştırma planındadır](research/RESEARCH_PLAN.md).
