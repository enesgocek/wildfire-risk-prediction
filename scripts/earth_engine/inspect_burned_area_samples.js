// Önceki Python görsellerindeki aynı 3×3 hücre pencereleri.
var area2021 = ee.Geometry.Rectangle(
    [31.351608, 36.843495, 31.507070, 36.989850],
    null, false
);

var area2019 = ee.Geometry.Rectangle(
    [26.895015, 38.170892, 27.050478, 38.319837],
    null, false
);

var source = ee.ImageCollection('MODIS/061/MCD64A1');

function inspect(start, end, area, name, shown) {
    var collection = source
        .filterDate(start, end)
        .filterBounds(area);

    print(name + ' — aylık görüntü sayısı:', collection.size());

    var burned = collection.map(function (image) {
        var burnDate = image.select('BurnDate');
        var validData = image.select('QA').bitwiseAnd(2).neq(0);

        return burnDate
            .updateMask(validData)
            .updateMask(burnDate.gt(0))
            .rename('burn_day');
    }).max().clip(area);

    Map.addLayer(
        burned,
        {
            min: 210,
            max: 244,
            palette: ['ffffb2', 'fd8d3c', 'bd0026']
        },
        name + ' — yaklaşık yanma günü',
        shown
    );

    Map.addLayer(
        ee.FeatureCollection([ee.Feature(area)]).style({
            color: '00FFFF',
            fillColor: '00000000',
            width: 2
        }),
        {},
        name + ' — inceleme sınırı',
        shown
    );
}

inspect(
    '2021-07-01', '2021-09-01',
    area2021, '2021 Temmuz–Ağustos', true
);

inspect(
    '2019-08-01', '2019-09-01',
    area2019, '2019 Ağustos', false
);

Map.centerObject(area2019, 12);