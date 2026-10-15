# Gözlem koşullarının pilot örnek dağılımına etkisi

Tarih: 15 Ekim 2026. Durum: aynı yöntem pilotunda çevrimdışı alt grup
incelemesi tamamlandı. Bir gözlem/etiket politikası seçilmedi.

## Amaç ve kapsam

Kurumsal olay kaydı yanıtını beklerken, farklı nominal gözlem koşullarının
hangi örnekleri dışarıda bıraktığı incelendi. Girdi, önceki
[saat ve kalite kanıtının](OBSERVATION_PROTOCOL_EVIDENCE_2026-10-15.md)
değişmeyen 156 amaçlı hücre-günüdür: 117 farklı hücre, 12 farklı tarih,
2018/2021/2023 eğitim yılları. Dört il, dört takvim mevsimi ve altı örtü
grubu yöntem tanısında korunur. Bir hücre birden çok günde bulunabilir;
156 birim bağımsız örnek veya rastgele seçilmiş popülasyon değildir.
Su/kentsel tanı örneklerinin korunması model kapsamına kabul edildikleri
anlamına gelmez. Mevcut su kapsam kararı değiştirilmedi.

Günlük nominal kara alanı, en az 12 saat ayrımlı tekrar alanı ve dört
altı saatlik UTC diliminin ortak alanı, AOI ile kesilmiş aynı hücre alanına
bölünür. Önceki açıklayıcı 0,50/0,80/0,90/0,95/0,99 kesimleri aynen
korundu. Bunlar yangın yokluğu veya bulutsuz sürekli gözlem kuralları
değildir. Yeni eşik ya da konum/zaman toleransı seçilmedi.

## Ölçülen seçim farkı

**Yalnız açıklayıcı %95 alan kesiminde**, aynı 156 birimin sayıları:

| Takvim mevsimi | Pilot paydası | Günlük alanı geçen | 12 saat tekrarı geçen | Dört dilim ortak alanını geçen |
|---|---:|---:|---:|---:|
| İlkbahar | 42 | 37 | 25 | 0 |
| Yaz | 40 | 39 | 35 | 13 |
| Sonbahar | 43 | 40 | 29 | 0 |
| Kış | 31 | 15 | 11 | 1 |
| Toplam | 156 | 131 | 100 | 14 |

Dört dilim koşulunun tuttuğu 14 birimin 13'ü yazdadır; bu pilotta
ilkbahar ve sonbahardan hiç birim kalmaz. Bu sonuç o mevsimlerin bütün
bölgede gözlenemediğini veya yaz etiketlerinin daha doğru olduğunu
kanıtlamaz. Az sayıdaki amaçlı tarihin ve konumların etkisi ayrı
değerlendirilmelidir. Koşulu yalnız örnek sayısına göre seçmek hem
gözlem boşluğunu hem seçilim sorununu gözden kaçırabilir.

Termal merkez tanığı olmayan **96 amaçlı birimin** il karşılaştırması;
her ilde payda 24 hücre-gün, aynı açıklayıcı %95 kesim:

| İl | Günlük alanı geçen | 12 saat tekrarı geçen | Dört dilim ortak alanını geçen |
|---|---:|---:|---:|
| Antalya | 22 | 16 | 2 |
| Muğla | 13 | 8 | 4 |
| İzmir | 17 | 9 | 3 |
| Mersin | 20 | 16 | 0 |

"Termal merkez tanığı yok" yangın yokluğu etiketi değildir. Bu sayılar
illerin tüm dönem gözlem kalitesi veya yangın riski sıralaması değildir.
İl/termal grup çapraz tablosu, marjinal il toplamlarından ayrı tutulur.
Örtü ve yıl gruplarında da payda, kalan/dışlanan birim, farklı hücre ve
tarih sayısı kaydedilir. Örneğin orman/çalı tanı grubunun 75 biriminden
günlük/tekrar/dört dilim kesimlerini sırasıyla 67/49/8 birim geçer;
bu grup için de negatif etiket kabulü yapılmaz.

## Yöntem ve korumalar

`protocol_selection.describe_selection`, aynı hücre/tarih kimliklerinde
her kesimi karşılaştırır. Bir yöntem çiftinde ikisinin tuttuğu, yalnız
solun/sağın tuttuğu ve ikisinin de dışladığı dört grup toplamı payda ile
uzlaştırılır. Birbirinden farklı örnek kümelerinin oranları doğruluk
iyileştirmesi gibi karşılaştırılmaz. Gerçek %95 toplamında günlük ile
tekrar koşulu arasında 31, tekrar ile dört dilim arasında 86 birim farkı
vardır; bunlar yanlış etiket veya kaçırılan yangın sayıları değildir.

Eksik/uyuşmayan mevsim, tekrarlı hücre-gün, kapalı dönem tarihi, doldurulmuş
hedef, açılmış kabul bayrağı, belirsiz boolean, geçersiz alan payı ve
termal grup/zaman tanığı uyuşmazlığı reddedilir. Alanlarda 1'i çok küçük
aşan sayısal yuvarlama için 1e-8 tolerans vardır; kayıtlar kırpılmaz ve
eşik karşılaştırması değiştirilmez. Kaynak dosyalar güncellenmedi.

Bu işte önceki yedi çıktının ve rapor/kapanışının güncel hash'leri
doğrulandı. Miras alınan 562 ham/ara girdinin tamamı tekrar açılmadı;
önceki teknik kabulün yerini aldığı iddia edilmez. Yeni işin 11 bağlı
girdisi işlem sonunda tekrar hash ile kontrol edildi. Ağ/bulut işi ve
ham dizi okuması yok; 2024/2025 açılmadı.

## Çıktılar ve doğrulama

Dizin: `outputs/reports/dataset/protocol_selection_v1/20261015T194012Z_72ade129/`.

- `unit_descriptive_screens.csv`: 156 birim × beş kesim = 780 satır;
  üç koşul ayrı bayrak, hedefler boş ve kabul kapıları kapalı.
- `stratum_screen_counts.csv`: 420 grup/koşul satırı; farklı paydalar açık.
- `paired_screen_counts.csv`: aynı gruplarda 420 eşlenik karşılaştırma satırı.
- `province_selection.png`: termal tanığı olmayan 96 birimin il grafiği;
  araçla görsel kontrol edildi, araştırmacı/uzman onayı değildir.
- `input_manifest.json`: 11 bağlı girdi; beş çıktının hash'leri readback içinde.

Readback SHA-256:
`e19de33e0db98948369c971a6d4d9966caf208574df73ad3059e8b26a6159242`.
Kapanış SHA-256:
`859c5005a94858f7344d7bfb2b04544a28dcb76aa415d588d9e9b05e0c1822f2`.
Önceki rapordaki beş kesimin iki termal gruptaki sayıları yeni
tablodan birebir uzlaştırıldı. **25 yeni davranış vakası dahil 53 ilgili
test**, Deprecation/Future uyarıları hata sayılarak geçti; üç Python
dosyasında lint/format kontrolü uygulandı.

## Sonraki adım ve karar sınırı

İller ve mevsimler arasında aynı koşulun farklı örnekleri tutması,
kurumsal kayıtlarla doğrulama planına açık kapsam/temsil kontrolü
eklenmesini gerektirir. Bağımsız kayıt gelirse onun gerçek kapsamı ve
zaman/konum belirsizliği incelenerek karşılaştırılabilir alt küme
belirlenecek; bu rapor bir eşleştirme toleransı veya nihai politika seçmez.
Yanıt beklerken veri alım ve belirsizlik kontrolleri hazırlanabilir.

Araştırmacının bakabileceği somut dosya `province_selection.png`'dir.
Beklenen inceleme il bazındaki aynı paydada koşulların tuttuğu birimlerin
değişimini görmektir; bu aşamada yangın/yangın yokluğu kararı istenmez.
`daily_observation_status=unknown`, `negative_label_permitted=false`, boş
hedefler, `model_ready=false` ve nihai birleştirme onayı gerekliliği korunur.
