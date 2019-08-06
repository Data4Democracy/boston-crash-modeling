import geopandas as gpd
from shapely.geometry import Point
from pandas.util.testing import assert_frame_equal
from .. import join_segments_crash


def test_make_rollup():
    """
    Tests total number of crashes per crash location is correctly calculated and
    list of unique crash dates per location is correctly generated
    """
    standardized_crashes = [{
        "id": 1,
        "dateOccurred": "2015-01-01T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "mode": "vehicle"
    }, {
        "id": 1,
        "dateOccurred": "2015-04-15T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "mode": "pedestrian"
    }, {
        "id": 1,
        "dateOccurred": "2015-10-20T00:45:00-05:00",
        "location": {
                "latitude": 42.365,
                "longitude": -71.106
        },
        "address": "GREEN ST & PLEASANT ST",
        "mode": "vehicle"
    }, {
        "id": 2,
        "dateOccurred": "2015-01-01T01:12:00-05:00",
        "location": {
                "latitude": 42.361,
                "longitude": -71.097
        },
        "address": "LANDSDOWNE ST & MASSACHUSETTS AVE",
        "mode": "bike"
    }, {
        "id": 3,
        "dateOccurred": "2015-01-01T01:54:00-05:00",
        "location": {
                "latitude": 42.396,
                "longitude": -71.127
        },
        "address": "LOCKE ST & SHEA RD",
        "mode": "bike"
    }, {
        "id": 3,
        "dateOccurred": "2015-01-01T01:54:00-05:00",
        "location": {
                "latitude": 42.396,
                "longitude": -71.127
        },
        "address": "LOCKE ST & SHEA RD",
        "mode": "vehicle"
    }]

    expected_rollup = gpd.GeoDataFrame()
    expected_rollup["coordinates"] = [
        Point(-71.106, 42.365),
        Point(-71.097, 42.361),
        Point(-71.127, 42.396)]
    expected_rollup["total_crashes"] = [3, 1, 2]
    expected_rollup["pedestrian"] = [1, 0, 0]
    expected_rollup["bike"] = [0, 1, 1]
    expected_rollup["vehicle"] = [2, 0, 1]


    expected_rollup["crash_dates"] = [
        "2015-01-01T00:45:00-05:00,2015-04-15T00:45:00-05:00,2015-10-20T00:45:00-05:00",
        "2015-01-01T01:12:00-05:00",
        "2015-01-01T01:54:00-05:00"
    ]

    results = join_segments_crash.make_crash_rollup(standardized_crashes)

    assert_frame_equal(results, expected_rollup)
