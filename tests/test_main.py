from main import float_price


def test_float_price():
    res = float_price("68.554 €")
    assert res == 68554