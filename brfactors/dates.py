"""Rebalancing date helpers."""
from datetime import timedelta

from bizdays import Calendar, set_option

cal = Calendar.load('ANBIMA')
set_option('mode', 'pandas')


def get_weekday_list(week_day, year, month, end_date):
    # Creates a list of dates from the weekday given in the parameter, adding seven days up to a limit date
    first_date = cal.getdate(week_day, year, month)
    date_list = [first_date]

    while (date_list[-1] + timedelta(7)).date() < end_date:
        date_list.append(date_list[-1] + timedelta(7))

    return date_list
