# Danışman görüşmesi için literatür ve araştırma özeti

12 Ekim 2026. Bitirme çalışması; 2209-A başvurusu hazırlık aşamasında,
destek alınmış değildir. Aşağıdaki araştırma yönü danışman değerlendirmesine
sunulan öneridir; sonuç veya onay değildir.

## Bu proje daha önce yapılmış mı?

Genel yaklaşım yapılmıştır. Türkiye'de FireAId 24 saatlik risk haritası ve
kaynak planlama sunar. Yunanistan'da Apostolakis ve arkadaşları ertesi gün
yangın riskini, Mesogeos araştırması günlük Akdeniz yangın görevlerini ele
alır. Mersin'deki 2026 çalışma ertesi gün yüksek FWI koşulunu modeller;
FWI hedefi yeni yangın olayıyla aynı değildir. Türkiye'de SHAP ve uydu
verisiyle yatkınlık haritaları da yayımlanmıştır.

Birincil dayanaklar: [FireAId](https://www.weforum.org/impact/artificial-intelligence-wildfire-prediction-and-prevention/),
[Apostolakis 2022](https://publications.beyond-eocenter.eu/DISASTERS/Estimating_Next%20Day_s%20Forest%20Fire%20Risk.pdf),
[Mesogeos 2023](https://arxiv.org/abs/2306.05144),
[Mersin FWI 2026](https://www.nature.com/articles/s41598-026-68923-7).

Bu nedenle “ilk yapay zekâ”, “ilk Türkiye uygulaması”, “ilk 24 saat tahmini”
veya “ilk SHAP” iddiası kullanılamaz. İlk uydu tespitini çıkarmak ve eksik
etiketleri dikkate almak da önceki araştırmalarda vardır. Yalnız farklı
model mimarisi ya da harita arayüzü bilimsel katkıyı kanıtlamaz.

## Önerilen araştırma katkısı

Antalya, Muğla, İzmir ve Mersin'in uygun 5 km hücrelerinde, sonraki 24 saatte
**yeni olayın ilk aktif tespiti** hedeflenir. Devam eden yangının tekrar
hotspot'ları ayrılır. Uydu ilk tespiti gerçek tutuşma saati olarak sunulmaz.

Önerilen soru: **Olay tanımı ve gözlem eksikliği, modelin ölçülen başarısını
ve günlük sınırlı uyarı kapasitesindeki yararını ne kadar değiştirir?**

Sınanacak katkılar:

1. Gerekçeli olay/gözlem politikalarını ortak incelenmiş örneklemde
   karşılaştırmak; başarı artışıyla veri kapsamı kaybını birlikte göstermek.
2. Meteorolojiye arazi/örtü ve geçmiş NDVI/NDMI eklenmesinin gerçek
   katkısını aynı ayrım ve kayıtlarla ölçmek.
3. Basit referanslar ile RF/XGBoost'u kalibrasyon ve günlük sabit uyarı
   kapasitesinde olay yakalama/yanlış alarm açısından karşılaştırmak.
4. İl, mevsim ve yıl genellemesini; belirsizlik ve başarısızlıkları raporlamak.

Bu bütünleşik yerel karşılaştırma **olası katkıdır**. Aynı tasarımın hiç
yapılmadığı veya önerinin başarı sağlayacağı henüz kanıtlanmamıştır.
Olumsuz ablation sonuçları da saklanmadan raporlanacaktır.

## Veri ve değerlendirme güvenceleri

2018–2023 eğitim, 2024 doğrulama, 2025 kapalı final testtir. Olaylar ve
yakın hücrelerin sızıntısı denetlenir. Değerlendirmede kabul edilmiş doğal
sınıf oranı korunur; yüksek accuracy tek başarı ölçütü değildir. AP/PR,
Brier, kalibrasyon, olay yakalama, yanlış uyarı ve değerlendirilebilir
alan/gün kapsamı birlikte raporlanır. Uydu coverage eksikliği sıfır etiket
üretemez. ERA5-Land ile geriye dönük deney gerçek zamanlı ürün kanıtı değildir.

En önemli açık konu bağımsız/uzman incelenmiş olay referansı ve negatif
gözlem yeterliliğidir. OGM benzeri kayıtların erişimi/izni araştırılabilir;
elde edilmiş değildir. Aynı uydu ürününün tekrar kontrolü bağımsız saha
doğrulamasına eşit değildir. Bu kapı çözülmezse kapsam kesin yangın
olasılığı yerine gözlenen tespit/etiket belirsizliği araştırmasına daraltılır.

## Görüşmede netleştirilecek kararlar

- Ana hipotez ve makaleye aday katkının kapsamı.
- Bağımsız olay kaynağı, incelemeci ve örnekleme yöntemi.
- Küçük olayların kapsamı, olay gruplaması ve güvenilir negatif koşulları.
- Ölçüt sözleşmesi, gerçekçi uyarı kapasitesi ve çalışma takvimi.

Makale yönü için geçici başlık: **Gözlem ve Olay Tanımındaki Belirsizliğin
24 Saatlik İlk Yangın Tespiti Tahminine Etkisi: Türkiye'nin Dört İlinde
Bir Karşılaştırma**. Bu başlık ürün adını değiştiren karar değildir.

[Ayrıntılı inceleme](LITERATURE_REVIEW_2026-10-12.md),
[34 kayıtlık kaynak sicili](literature_sources_2026-10-12.json) ve
[önerilen deney protokolü](ARTICLE_RESEARCH_PROTOCOL_2026-10-12.md)
eklerde kullanılabilir. Tarama yapılandırılmış kapsam incelemesidir;
Scopus/WoS/TR Dizin üzerinden eksiksiz sistematik derleme değildir.
Makale veya destek kabulü garanti edilmez.
