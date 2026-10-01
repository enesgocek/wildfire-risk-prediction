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
- **Arazi örtüsü ve yükseklik verileri:** geçmiş yıllara uygun kaynak seçimi ve topografya.

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

Python ortamı, deney takibi ve Earth Engine erişimi hazır. Dört ilin çalışma
alanı ve yaklaşık 25 km² büyüklüğünde 2.899 grid hücresi oluşturuldu. Copernicus
2017 arazi örtüsü için hücre bazında sınıf oranları çıkarıldı; kaynağın modelde
kullanımı ve uygunluk eşiği henüz kesinleşmedi. FIRMS S-NPP ve
NOAA-20 arşivleri (2018–2024) kontrol edildi; iki uydudan 33.255 geçici aday tespit
kaynak kimlikleriyle ortak tabloda toplandı. Gözlem boşlukları ve örnek
yanmış alanlar inceleniyor. Yangın olayları,
eğitim etiketleri ve model henüz hazırlanmadı.

## Kurulum

Python 3.12 ve uv ile:

```bash
uv sync --locked
uv run --locked pytest
```

Windows için kurulum betiği: `scripts/setup.ps1`.

Ayrıntılar için [proje rehberi](docs/PROJECT.md) ve
[yol haritası](docs/ROADMAP.md).

## Klasör düzeni

- `scripts/`: çalıştırılabilir betikler; [işlem sırası ve komutlar](scripts/README.md).
- `src/`: ortak Python kodu; `configs/`: proje ayarları; `tests/`: otomatik kontroller.
- `data/`: coğrafi veriler, ham kaynaklar ve ara tablolar.
- `outputs/`: raporlar, görseller ve deney kayıtları.
- `docs/`: proje rehberi ve yol haritası; `Diary/`: günlük çalışma kayıtları.
