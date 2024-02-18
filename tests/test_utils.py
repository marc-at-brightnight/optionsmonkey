from optionsmonkey.utils import get_fridays_date
import datetime as dt


def test_get_next_fridays_date():
    date = get_fridays_date()

    assert date.weekday() == 4
    assert date > dt.datetime.now()

    date = get_fridays_date(weeks_until=1)

    assert date.weekday() == 4
    assert date > dt.datetime.now() + dt.timedelta(days=7)

    date = get_fridays_date(weeks_until=2)

    assert date.weekday() == 4
    assert date > dt.datetime.now() + dt.timedelta(days=14)
