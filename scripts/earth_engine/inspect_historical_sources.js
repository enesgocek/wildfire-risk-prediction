// Tarihsel kaynak incelemesi; kesin yangın etiketi veya model girdisi değildir.
// Vaka kimliğini değiştirerek aynı yöntemi diğer eğitim örneklerine uygula.
var caseId = 'H06';
var reviewCases = {
    "H01": {
        "coordinates": [
            26.93221,
            38.73095
        ],
        "candidateTime": "2018-04-23T00:30:00+00:00",
        "firstLaterStatic": "2019-05-16T00:06:00+00:00",
        "anchorDetectionId": "SNPP_815579_3922",
        "category": "later_only"
    },
    "H02": {
        "coordinates": [
            26.91908,
            38.78931
        ],
        "candidateTime": "2018-10-19T10:56:00+00:00",
        "firstLaterStatic": "2018-12-12T00:11:00+00:00",
        "anchorDetectionId": "SNPP_815579_32141",
        "category": "later_only"
    },
    "H03": {
        "coordinates": [
            27.06561,
            38.82114
        ],
        "candidateTime": "2018-04-06T00:49:00+00:00",
        "firstLaterStatic": "2019-06-19T23:59:00+00:00",
        "anchorDetectionId": "SNPP_815579_3073",
        "category": "later_only"
    },
    "H04": {
        "coordinates": [
            27.21594,
            38.42831
        ],
        "candidateTime": "2018-04-13T00:18:00+00:00",
        "firstLaterStatic": "2018-04-29T23:08:00+00:00",
        "anchorDetectionId": "SNPP_815579_3395",
        "category": "prior_static"
    },
    "H05": {
        "coordinates": [
            33.73007,
            36.26247
        ],
        "candidateTime": "2018-04-03T22:56:00+00:00",
        "firstLaterStatic": "2018-04-13T23:09:00+00:00",
        "anchorDetectionId": "N20_815590_158",
        "category": "prior_static"
    },
    "H06": {
        "coordinates": [
            30.44355,
            37.25166
        ],
        "candidateTime": "2018-04-21T00:18:00+00:00",
        "firstLaterStatic": "2018-04-24T00:12:00+00:00",
        "anchorDetectionId": "N20_815590_1070",
        "category": "prior_static"
    }
};
if (!reviewCases[caseId]) { throw new Error('Bilinmeyen vaka: ' + caseId); }
var selectedCase = reviewCases[caseId];
print('İncelenen vaka (eleme kararı değildir):', selectedCase);
var point = ee.Geometry.Point(selectedCase.coordinates);
var area = point.buffer(800).bounds();
// Kalite seçimi tespit çevresinde; geniş alan yalnızca bağlamdır.
var qualityArea = point.buffer(100);
var candidateTime = ee.Date(selectedCase.candidateTime);

function prepare(image) {
    var scl = image.select('SCL');

    // Bulut, gölge, bozuk piksel, kar ve belirsiz sınıfları gizle.
    var clear = scl.neq(0)
        .and(scl.neq(1))
        .and(scl.neq(3))
        .and(scl.neq(7))
        .and(scl.neq(8))
        .and(scl.neq(9))
        .and(scl.neq(10))
        .and(scl.neq(11));

    var fraction = clear.unmask(0, false).reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: area,
        crs: scl.projection(),
        scale: 20,
        maxPixels: 1000000
    }).get('SCL');

    var coreFraction = clear.unmask(0, false).reduceRegion({
        reducer: ee.Reducer.mean(),
        geometry: qualityArea,
        crs: scl.projection(),
        scale: 20,
        maxPixels: 1000000
    }).get('SCL');

    return image.updateMask(clear)
        .set('review_clear_fraction', fraction)
        .set('review_core_clear_fraction', coreFraction);
}

function showWindow(label, start, end, latest, shown) {
    var collection = ee.ImageCollection(
        'COPERNICUS/S2_SR_HARMONIZED'
    )
        .filterBounds(area)
        .filterDate(start, end);

    print(label + ' — kaynak görüntü sayısı:', collection.size());

    var usable = collection.map(prepare)
        .filter(ee.Filter.gte('review_core_clear_fraction', 0.90))
        .sort('system:time_start', !latest);

    var count = usable.size().getInfo();
    print(label + ' — 100 metre çevresi en az %90 açık görüntü:', count);

    if (count === 0) {
        print(label + ': uygun görüntü bulunamadı; sonuç çıkarma.');
        return;
    }

    var image = ee.Image(usable.first());
    var date = image.date().format('YYYY-MM-dd HH:mm').getInfo();

    print(label + ' — seçilen tarih (UTC):', date);
    print(label + ' — görüntü kimliği:', image.id());
    print(label + ' — 100 metre çevresi açık alan oranı:',
        image.get('review_core_clear_fraction'));
    print(label + ' — geniş bağlam alanı açık alan oranı:',
        image.get('review_clear_fraction'));

    Map.addLayer(
        image.clip(area),
        { bands: ['B4', 'B3', 'B2'], min: 0, max: 3000 },
        label + ' | ' + date,
        shown
    );
    return image;
}

// Adaydan önceki en yakın uygun görüntü.
var beforeImage = showWindow(
    caseId + ' — adaydan önce',
    candidateTime.advance(-90, 'day'),
    candidateTime,
    true,
    true
);

// Adaydan sonraki ilk uygun görüntü.
var afterImage = showWindow(
    caseId + ' — adaydan sonra',
    candidateTime,
    candidateTime.advance(45, 'day'),
    false,
    false
);

// İlk sonraki sabit kayıt tarihinden itibaren uygun görüntü.
showWindow(
    caseId + ' — sonraki sabit kayıt dönemi',
    ee.Date(selectedCase.firstLaterStatic),
    ee.Date(selectedCase.firstLaterStatic).advance(46, 'day'),
    false,
    false
);

// Soru 1: 2017 referans örtüsü. Harita sınıfı kesin yer gerçeği değildir.
var landcover = ee.Image(ee.ImageCollection(
    'COPERNICUS/Landcover/100m/Proba-V-C3/Global'
).filterDate('2017-01-01', '2018-01-01').first());
var lcProjection = landcover.select('discrete_classification').projection();
print(caseId + ' — 2017 nokta örtü kaydı (100m kaynak pikseli):',
    landcover.select(['discrete_classification', 'tree-coverfraction',
        'shrub-coverfraction', 'grass-coverfraction', 'urban-coverfraction'])
    .sample({region: point, projection: lcProjection, geometries: false}).first());
Map.addLayer(landcover.select('tree-coverfraction').clip(area),
    {min: 0, max: 100, palette: ['fff7ec', 'a1d99b', '006d2c']},
    caseId + ' — 2017 ağaç örtüsü (%)', false);

// Soru 1 ve 2: yakın kızılötesi, bitki indeksi ve değişim.
if (beforeImage && afterImage) {
    Map.addLayer(beforeImage.clip(area),
        {bands: ['B8', 'B4', 'B3'], min: 0, max: 4000},
        caseId + ' — ÖNCE kızılötesi (bitki genellikle kırmızı)', false);
    Map.addLayer(afterImage.clip(area),
        {bands: ['B8', 'B4', 'B3'], min: 0, max: 4000},
        caseId + ' — SONRA kızılötesi (bitki genellikle kırmızı)', false);
    var beforeNDVI = beforeImage.normalizedDifference(['B8', 'B4']);
    var afterNDVI = afterImage.normalizedDifference(['B8', 'B4']);
    var ndviCommon = beforeNDVI.mask().and(afterNDVI.mask());
    var beforeNBR = beforeImage.normalizedDifference(['B8A', 'B12']);
    var afterNBR = afterImage.normalizedDifference(['B8A', 'B12']);
    var nbrCommon = beforeNBR.mask().and(afterNBR.mask());
    var indices = beforeNDVI.updateMask(ndviCommon).rename('NDVI_before')
        .addBands(afterNDVI.updateMask(ndviCommon).rename('NDVI_after'))
        .addBands(beforeNBR.updateMask(nbrCommon).rename('NBR_before'))
        .addBands(afterNBR.updateMask(nbrCommon).rename('NBR_after'));
    print(caseId + ' — ortak geçerli piksellerde indeks medyanları (100m çevre):',
        indices.reduceRegion({reducer: ee.Reducer.median(), geometry: qualityArea,
            scale: 20, crs: beforeImage.select('B8A').projection(), maxPixels: 100000}));
    var change = beforeNBR.subtract(afterNBR).updateMask(nbrCommon);
    Map.addLayer(change.clip(area),
        {min: -0.5, max: 0.5, palette: ['2166ac', 'f7f7f7', 'b2182b']},
        caseId + ' — NBR değişimi: önce eksi sonra (yangın etiketi değil)', false);
    print('İndeks yorumu:',
        'Seçilen tarihler ve mevsim etkisi ayrıca değerlendirilir. NDVI/NBR değişimi tek başına yanma kanıtı değildir.');
}

// Soru 2: native MODIS pikseli; tarih, belirsizlik ve QA birlikte okunur.
function inspectBurnMonth(start, end, label) {
    var collection = ee.ImageCollection('MODIS/061/MCD64A1')
        .filterDate(start, end);
    var count = collection.size().getInfo();
    print(label + ' — aylık görüntü sayısı:', count);
    if (count !== 1) {
        print(label + ': tek aylık görüntü bulunamadı; yorum yapma.');
        return;
    }
    var image = ee.Image(collection.first());
    var nativeProjection = image.select('BurnDate').projection();
    var qa = image.select('QA');
    var valid = qa.bitwiseAnd(2).neq(0);
    var land = qa.bitwiseAnd(1).neq(0);
    var burned = image.select('BurnDate').gt(0)
        .and(image.select('BurnDate').lte(366)).and(valid).and(land);
    var details = image.select(['BurnDate', 'Uncertainty', 'QA', 'FirstDay', 'LastDay'])
        .toInt16()
        // Kaynak maskesi: 0 ise -9999 betiğin eksik veri işaretidir.
        .addBands(image.select('BurnDate').mask().unmask(0, false)
            .rename('BurnDate_source_mask'))
        .addBands(image.select('Uncertainty').mask().unmask(0, false)
            .rename('Uncertainty_source_mask'))
        .addBands(valid.rename('QA_valid'))
        .addBands(land.rename('QA_land'))
        .addBands(qa.bitwiseAnd(4).neq(0).rename('QA_shortened_period'))
        .addBands(qa.rightShift(5).bitwiseAnd(7).rename('QA_special_condition'))
        .toInt16().unmask(-9999, false);
    print(label + ' — ' + caseId + ' noktasının native MODIS pikseli:',
        details.sample({region: point, projection: nativeProjection,
            geometries: false}).first());
    Map.addLayer(burned.selfMask().clip(area), {palette: ['ff9900']},
        label + ' — geçerli yanmış pikseller', false);
}
var candidateMonth = ee.Date.fromYMD(candidateTime.get('year'), candidateTime.get('month'), 1);
for (var monthOffset = 0; monthOffset < 2; monthOffset++) {
    var monthStart = candidateMonth.advance(monthOffset, 'month');
    inspectBurnMonth(monthStart, monthStart.advance(1, 'month'),
        caseId + ' — MODIS ' + monthStart.format('YYYY-MM').getInfo());
}
print('Adayın yıl içindeki gün numarası:', candidateTime.getRelative('day', 'year').add(1));
print('MODIS yorumu:',
    'BurnDate 0 yanmamış sınıfıdır; kaynak maskesi, QA ve özel koşullar ayrıca kontrol edilir. '
    + '-9999 bu betiğin eksik veri işaretidir; yanmamış demek değildir. '
    + 'QA_valid=1, maskeli BurnDate değerini geri getirmez. '
    + 'Yanma bulunmaması küçük yangını dışlamaz; BurnDate yaklaşık tarih verir.');

// Bu çember yalnızca inceleme mesafesidir; uydu piksel sınırı değildir.
Map.addLayer(
    ee.FeatureCollection([ee.Feature(point.buffer(100))]).style({
        color: '00FFFF',
        fillColor: '00000000',
        width: 2
    }),
    {},
    '100 metre inceleme çevresi'
);

Map.centerObject(area, 16);