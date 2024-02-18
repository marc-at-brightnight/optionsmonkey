import datetime as dt


def get_fridays_date(weeks_until: int = 0) -> dt.date:

    current_date = dt.datetime.now()

    days_until_friday = 4 - current_date.weekday() + 7
    datetime = current_date + dt.timedelta(days=days_until_friday + weeks_until * 7)

    return datetime.date()
