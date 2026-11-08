# İlk tespit merkezi ile yaklaşık piksel çevresinin karşılaştırması — 8 Kasım 2026

Urla kıyı tespitinde merkez sınıfı ile çevre farklıydı. Bu farkın başka adaylarda görülüp görülmediği, aynı CORINE 2018 rasterında iki örneklemle denetlendi. Önceki yöntem pilotu 25 noktayı ve 21 hücre-gün inceleme birimini içeriyor. Açık olay incelemesi 2021'deki Aydıncık ve Urla vakalarından 46 farklı ilk noktayı içeriyor. İki örneklem amaçlı seçildi. Nokta sayıları bağımsız yangın sayısı veya proje geneli hata oranı olarak yorumlanamaz.

## Yöntem

Her FIRMS merkezinde, bildirilen `scan` ve `track` boyutlarıyla EPSG:3035 düzleminde 0–179 derece arasında birer derece aralıklı dikdörtgenler kuruldu. Yerel şekil veya yönelim bilinmediği için bu işlem yönelim duyarlılığını gösterir. Merkez konum hatası, gerçek VIIRS köşeleri ve haritanın tarihsel doğruluğu ölçülmedi. Her dikdörtgendeki 100 m raster hücrelerinin kesişim alanı, tüm dikdörtgen alanına bölündü. 311/312/313/322/323/324 kodları önceki incelemedeki haritalanmış orman/çalılık grubudur. %1, %10 ve %50 kesimleri tanımlayıcı karşılaştırma için kullanıldı.

Pilot noktaların daha önce ölçülen, yerel VIIRS merkezleriyle yaklaşık olarak kurulmuş poligonları ayrıca korundu. Bu poligonlar için [önceki CORINE alan denetiminden](CORINE_SUPPORT_REVIEW_2026-11-04.md) gelen ölçüler ayrı sütunda kullanıldı. Açık olay noktalarının bu türden bir yerel poligonu yok.

## Bulgular

| İnceleme grubu | Orman/çalılık kodunda merkez | Bütün yönelimlerde en az %1 | Bütün yönelimlerde en az %10 | Bütün yönelimlerde en az %50 | %50 sonucu yönelime göre değişen |
|---|---:|---:|---:|---:|---:|
| Yöntem pilotu | 2/25 | 6/25 | 5/25 | 2/25 | 0/25 |
| Aydıncık–Pembecik | 27/34 | 34/34 | 32/34 | 26/34 | 3/34 |
| Urla–Karaburun | 11/12 | 12/12 | 12/12 | 12/12 | 0/12 |

- **Yöntem pilotu.** Önceki poligonlarda %50'ye ulaşan iki nokta var. Toplam sayı merkez kontrolüyle aynı olsa da iki noktanın sonucu değişiyor. C'nin merkezi doğal çayır, önceki poligonun **%78,0'ı** orman kodunda. R03'ün merkezi sklerofil örtü, önceki poligonun **%36,9'u** orman/çalılık kodunda. Nominal yönelimler C'de **%74,8–78,8**, R03'te **%30,1–35,5** verdi. Pilotun 25 noktasında bu üç betimsel kesim için nominal yönelimlerle önceki poligon aynı tarafta kaldı. Bu sonuç gerçek piksel geometrisini doğrulamaz.
- **Aydıncık.** Merkezde orman/çalılık kodu bulunmayan yedi noktanın tamamında, her yönelim en az %1 kesişim verdi. Üç noktada %50 sonucu yöne göre değişiyor. Bunlardan C640_R864'teki nokta, son yangın sınırı dışında kalan ayrı ilk hücrenin tek üyesi. Kesişim **%29,5–51,9** arasında. Diğer iki nokta C641_R864'te ve aralıkları **%45,0–61,7** ile **%43,7–61,4**.
- **Urla.** Deniz kodlu merkezde aynı harita kullanılarak yapılan bu eş alan düzlemi hesabı, **%51,6–52,7** orman/çalılık ve **%47,3–48,4** deniz verdi. Farklı tarihlerdeki görüntülerde bulunan daha düşük kara payı ayrı kanıttır. [Urla kıyı denetimi](URLA_COASTAL_DETECTION_2026-11-08.md).

## Veri setine aktarılacak inceleme bilgisi

Merkez kodu, yaklaşık alan payı, yönelim aralığı ve varsa tarihli görüntü kanıtı ayrı tutulabilir. Yönelim duyarlı Aydıncık noktaları ile ters yönde sonuç veren C ve R03, bir sonraki örtü değerlendirmesi için belirgin örneklerdir. C ve R03'ün harita sonucunun karşıt çıkması, yalnız toplam kabul sayısına bakmanın aday kimliğindeki değişimi gizleyebileceğini gösterir. Kıyı ve karışık örtü kayıtları ortak aday bağını korur. Hücre uygunluğu, yerel örtü, bağımsız olay kanıtı ve günlük gözlem ayrı aşamalardır. Bu hesap bir örtü eşiği, örnek dışlama, PU pozitif kabulü veya eğitim onayı oluşturmaz.

## Doğrulama

Yerel çıktı `outputs/reports/dataset/candidate_center_footprint_v1/20261107T235952Z_cbc4f2b3/readback.json`, SHA-256 `159771b79506df43bdedf5f4004ecf3d6003384600c84fe4ba055fd8bfd21394`. Kaynak özetleri, 71 noktanın kimliği, örneklem ayrımı ve kapalı etiket alanları kontrol edildi. 12.780 dikdörtgen ayrıca trigonometrik köşeler ve exactextract hücre kapsamı ile hesaplandı. Nokta bazında sınıf payı aralığı uçlarındaki en büyük mutlak fark **1,50 × 10⁻⁸**. İki hesap aynı CORINE rasterına dayanır. İlgili 65 test geçti.
