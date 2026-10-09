# Orman Yangını Risk Tahmini

Antalya, Muğla, İzmir ve Mersin'de, sonraki 24 saat içinde yeni bir yangın
olayının ilk uydu tespitine ilişkin olasılığı modellemeyi amaçlayan bitirme
araştırmasıdır. Çalışma, meteoroloji, uydu gözlemleri ve arazi özelliklerini
yaklaşık 25 km² hücreler üzerinde birleştirir. İlk uydu tespiti gerçek tutuşma
zamanının doğrudan ölçümü değildir.

## Araştırma durumu

9 Ekim 2026 itibarıyla coğrafi altyapı ve 2018–2024 meteoroloji hazırlığı
tamamlanmıştır. Uydu gözlem tanılarının eğitim dönemi boyunca işlenmesi
sürmektedir. Nihai olay kataloğu, negatif etiket politikası, model veri seti
ve eğitilmiş model henüz tamamlanmamıştır. Güncel ilerleme ve kanıt sınırları
[durum raporunda](docs/STATUS.md) tutulur.

2209-A başvurusunun bitirme projesi danışmanıyla hazırlanması planlanmaktadır.
Bu depo henüz TÜBİTAK destekli veya kabul edilmiş bir proje olarak sunulmaz.

## Kapsam ve değerlendirme

- Pilot: Antalya, Muğla, İzmir, Mersin; 2.899 coğrafi hücre.
- Temel kaynaklar: NASA FIRMS VIIRS, ERA5-Land, bitki örtüsü ve arazi verileri.
- Veri ayrımı: **2018–2023 eğitim**, **2024 doğrulama**, **2025 kapalı final test**.
- Tahmin: 00:00 UTC'de, sonraki 24 saat için yeni olayın ilk aktif tespiti.
- Model karşılaştırmaları: FWI uygunluğu, Random Forest ve XGBoost; ek yöntemler
  temel karşılaştırmaların sonuçlarına göre değerlendirilir.
- Değerlendirme: PR-AUC, olasılık kalibrasyonu, olay yakalama ve yanlış alarm yükü.

Eksik uydu gözlemi yangın yokluğu olarak etiketlenmez. Mevcut ERA5-Land tablosu
geriye dönük yeniden analiz verisidir; canlı tahmin anındaki erişilebilirliği
henüz doğrulanmamıştır. Bilimsel sözleşme [proje rehberindedir](docs/PROJECT.md).

## Belgeler

- [Belge dizini ve mimari](docs/README.md)
- [Güncel durum](docs/STATUS.md) · [Aşamalı yol haritası](docs/ROADMAP.md)
- [Araştırma planı](docs/research/RESEARCH_PLAN.md) · [Kanıt dizini](docs/research/EVIDENCE_REGISTER.md)
- [2209-A hazırlığı](docs/research/2209A_PREPARATION.md)
- [Araştırma günlüğü](Diary/README.md) · [Araç kullanım kaydı](docs/research/AI_USE.md)
- [Betikler ve komutlar](scripts/README.md)

## Kurulum

Python 3.12 ve uv ile:

```bash
uv sync --locked
uv run --locked pytest
```

Windows kurulumu: `scripts/setup.ps1`. Büyük kaynak verileri, bulut sonuçları
ve özel bağlantı dosyaları depoya dahil değildir. Gerçek dosya gerektiren
kontrollerin kapsamı ilgili test ve işlem raporunda belirtilir.

## Klasör düzeni

| Konum | Sorumluluk |
|---|---|
| `src/` | Ortak Python kütüphanesi |
| `scripts/` | Görev bazlı hazırlama, yürütme ve doğrulama komutları |
| `configs/` | Gizli bilgi içermeyen proje ve işlem yapılandırmaları |
| `tests/` | Davranış, veri sözleşmesi ve hata senaryosu kontrolleri |
| `data/` | Kaynak, ara ve modelleme verileri |
| `outputs/` | Üretilmiş raporlar, deneyler, görseller, paketler ve doğrulama çıktıları |
| `docs/` | Yöntem, uygulama, sonuç ve başvuru hazırlığı belgeleri |
| `Diary/` | Tarihli araştırma kayıtları |

Yeni katkılarda [çalışma kuralları](AGENTS.md) uygulanır. Paket kimlikleri ve
checkpoint yolları, belge düzenlemesi gerekçesiyle değiştirilmez.

Önemli güncellemeler, gerekli kontrollerden sonra commit edilip GitHub'a
gönderilir. Her gönderimden önce dosya listesi/diff incelemesi ve
`python scripts/quality/check_git_privacy.py --scope staged` kontrolü uygulanır.
Kontrol bulguları gizli değeri yazdırmaz. Ham veri, özel bağlantılar ve sonuç
arşivleri gönderilmez; otomatik tarama tek başına bütün gizlilik risklerinin
bulunmadığını kanıtlamaz.
