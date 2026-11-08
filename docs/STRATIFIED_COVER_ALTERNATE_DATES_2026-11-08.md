# Eğitim dönemi örtü pilotunda ikinci tarih — 8 Kasım 2026

24 tespitlik pilotta yerel kalite işaretleri %50'yi aşan dört nokta (H02, H08, H16, H19) ve üç örtü sorusu (H01, H03, H15) ikinci bir olay öncesi tarihte denetlendi. Aynı tespit kimliği ve aynı 250 m çevre korundu. Tahmin kesiminden önceki 30 gün içinde ilk kesitten farklı bir gün seçildi. Katalog sıralaması önce sahne bulut oranı %20 veya altında olanları, ardından daha yakın tarihleri öne aldı. Yedi yeni kesit başarıyla okundu. Önceki görüntüler ve ön görünüm kayıtları korundu. [İlk örneklem](STRATIFIED_COVER_PILOT_2026-11-08.md).

## Görüntü kalitesi

| Nokta | İlk ve ikinci görüntü, UTC | Seçili kalite işareti payı | İki görüntünün ön yorumu |
|---|---|---:|---|
| H02 | 19 ve 14 Ekim 2019 | %81,9 → %0,0 | İkinci görüntü açık. Tarla geometrileri ve açık/parlak merkez şeridi iki tarihte de görülüyor. Yerel örtü karışık. |
| H08 | 7 ve 2 Şubat 2019 | %100,0 → %100,0 | İlk görüntü beyaz bulutla örtülü. İkinci görüntüde bazı yüzeyler görünür, ancak SCL çevrenin tamamını bulut/sirüs sınıflarında işaretliyor. Örtü belirsiz. |
| H16 | 2 Haziran ve 23 Mayıs 2021 | %65,3 → %60,2 | Aynı parlak geometriler ve yollar iki tarihte de görülüyor. Yapılaşma olasılığı güçleniyor. Yüksek SCL işareti sürüyor, yapı türü ve yerel örtü kabulü açık. |
| H19 | 7 ve 2 Eylül 2018 | %52,2 → %42,0 | İkinci tarihte bulut/sirüs sıfır. Gölge, koyu ve sınıflandırılmamış alanlar sürüyor. Görünen yeşil örtüden doğal/yönetilen ayrımı tamamlanmadı. |

Yüzdeler her 250 m çevredeki 20 m SCL piksel merkezlerinin payıdır. Payda noktaya göre 484–493 piksel merkezidir ve iki tarih arasında nokta bazında aynı kaldı. Seçili işaretler bulut, sirüs, gölge, koyu alan, eksik/bozuk veri, sınıflandırılmamış alan ve kar/buzu kapsar. Üç noktada işaret payı azaldı, ikisinde %50'nin altına indi. %50 yalnız ikinci incelemeye öncelik vermek için kullanıldı. [Dört kalite karşılaştırması](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/alternate_dates_20261108T002956Z_0e6d2a99/quality_comparison.png).

## Örtü soruları

- **H01, 19 ve 17 Eylül 2018.** Açık zemin ve yeşil örtü iki tarihte de aynı bölgelerde görünüyor. SCL genel bitki örtüsü oranı %33,9 ve %31,8. Eski haritada yaklaşık piksel çevresinin tamamı orman/çalılık kodunda. Harita ile görüntünün farklı paydaları ve tarihlerinden dolayı bu yüzdeler doğrudan eşitlenmez. Karışık yerel örtü ön notu korunur.
- **H03, 7 ve 2 Kasım 2020.** Düzensiz yeşil örtü her iki tarihte görünür. SCL genel bitki örtüsü oranı %75,8 ve %81,0. Eski haritanın tarım/doğal örtü mozaiği sınıfı, doğal örtünün iç payını vermiyor. İki tarih ağaçlık bağlamı destekliyor. Doğal/yönetilen kullanım ayrımı açık.
- **H15, 15 ve 5 Ekim 2020.** İki görüntüde seçili kalite işareti yok. SCL genel bitki örtüsü %90,4 ve %92,2. Eski haritanın meyvelik kodu ve görüntülerdeki düzenli sınırlar birlikte değerlendirildi. Yoğun yeşil örtü doğal orman kabulü sağlamıyor. Yerel kullanım belirsiz kaldı.

[Üç örtü karşılaştırması](../outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/alternate_dates_20261108T002956Z_0e6d2a99/cover_comparison.png).

## Veri seti için sonuç

İkinci tarih, geçici görüntü engeli ile tekrarlanan karışık yüzey görünümünü ayırmaya yardımcı oldu. H02 karışık, H08 görüntü kalitesiyle sınırlı, H16 olası yapay yüzey ve H19 kalite/örtü belirsizliği olarak ayrı değerlendirildi. Pilotun önceki 24 noktalık dağılımı tarihsel kayıt olarak duruyor. Ek bulgular yalnız bu yedi noktaya aittir. Yorumlar asistanın ön görsel değerlendirmesidir. Araştırmacı görüşü, özellikle H15'te düzenli parsel izlerinin yorumunu güçlendirebilir. Bu yorum olay eşleşmesi için tek başına yeterli olmayacağından ilerleme koşulu yapılmadı.

Sonraki araştırma işi, örtü bağlamı desteklenen örneklerde bağımsız olay kanıtı, ilk uydu zamanının güveni ve önceki tespitlerle devam ilişkisini birlikte sınamaktır. Yedi noktada habitat kabulü açık, hedef boş ve günlük gözlem durumu `unknown`. Pozitif ve negatif etiket izinleri `false`.

## Doğrulama kaydı

Üretici `scripts/quality/compare_stratified_cover_dates.py`. Yerel okuma kaydı `outputs/reports/dataset/stratified_cover_pilot_v1/20261108T002035Z_de57b547/alternate_dates_20261108T002956Z_0e6d2a99/readback.json`. SHA-256 `8a8e384e7de7d0f7ac48856c2d1fc37d0f8d0a05df71e7b93c6b2f20a751ce9a`. 34 dosya özeti, iki görsel, yedi tarih çifti ve 14 SCL ölçümü kaynak rasterlardan yeniden denetlendi. 64 ilgili test geçti.
