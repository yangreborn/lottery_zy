from lottery.zones import get_zones


def test_new_format_zones_passthrough():
    rc = {"zones": [{"key": "main", "label": "号码", "min": 1, "max": 80, "count": 20,
                     "pick_min": 1, "pick_max": 10}]}
    zones = get_zones(rc)
    assert len(zones) == 1
    assert zones[0]["key"] == "main"
    assert zones[0]["pick_max"] == 10


def test_legacy_red_blue_converted():
    rc = {"red": {"count": 6, "min": 1, "max": 33},
          "blue": {"count": 1, "min": 1, "max": 16}}
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red", "blue"]
    assert zones[0]["count"] == 6 and zones[0]["min"] == 1 and zones[0]["max"] == 33
    assert zones[0]["label"] == "红球" and zones[1]["label"] == "蓝球"


def test_legacy_single_red_only():
    rc = {"red": {"count": 5, "min": 1, "max": 35}}
    zones = get_zones(rc)
    assert [z["key"] for z in zones] == ["red"]


def test_empty():
    assert get_zones({}) == []
