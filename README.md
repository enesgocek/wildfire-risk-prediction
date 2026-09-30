# Orman Yangını Risk Tahmini

Antalya, Muğla, İzmir ve Mersin'de önümüzdeki 24 saat içinde yangın oluşma riskini
hesaplamayı amaçlayan bir bitirme projesi.

Meteorolojik veriler, uydu görüntüleri ve arazi özellikleri bir araya getirilerek
5 × 5 km alanlar için yangın olasılığı üretilecek. Sonuçların bir harita üzerinden
sunulması ve risk üzerinde etkili faktörlerin incelenmesi hedefleniyor.

## Kapsam

Çalışma, dört ildeki orman ve diğer uygun bitki örtüsü alanlarını kapsıyor.
Yangın etiketleri NASA FIRMS VIIRS kayıtlarından oluşturulacak; aynı yangına ait
tekrarlı tespitler tek olay altında toplanacak. İlk uydu tespiti, gerçek yangın
başlangıç zamanını yaklaşık olarak temsil ediyor.

Başlıca veri kaynakları:

- **NASA FIRMS VIIRS:** aktif yangın tespitleri.
- **ERA5-Land:** tarihsel meteorolojik veriler.
- **Sentinel-2:** bitki örtüsü ve nem göstergeleri.
- **ESA WorldCover ve yükseklik verileri:** arazi örtüsü ve topografya.

Türkiye verisinin yeterliliğine göre İtalya ve benzer Akdeniz iklimine sahip
ülkelerden ek eğitim verisi de değerlendirilebilir.

## Modelleme ve değerlendirme

İlk modeller Random Forest ve XGBoost olacak; FWI bağımsız bir karşılaştırma
ölçütü olarak kullanılacak. Uydu görüntülerinden elde edilen temsillerin katkısı,
temel modellerin sonuçları değerlendirildikten sonra araştırılacak.

Veri ayrımı: **2018–2023 eğitim**, **2024 doğrulama**, **2025 final test**.
Final test, model ve parametre seçiminden ayrı tutulacak. Özellikler tahmin anında
bilinebilen verilerden üretilecek. Başarı, PR-AUC ve olasılık kalibrasyonu başta
olmak üzere yangın riskine uygun ölçütlerle değerlendirilecek.

## Mevcut durum

Python ortamı, proje yapılandırması, deney takibi ve temel kontroller hazır.
Veri toplama ve model eğitimi henüz başlamadı.

## Kurulum

Python 3.12 ve uv ile:

```bash
uv sync --locked
uv run --locked pytest
```

Windows için kurulum betiği: `scripts/setup.ps1`.

Ayrıntılar için [proje rehberi](docs/PROJECT.md) ve
[yol haritası](docs/ROADMAP.md).
