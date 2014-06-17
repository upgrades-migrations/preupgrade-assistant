# -*- coding: utf-8 -*-
from datetime import timedelta

LANG = "en"

# Singular and plural forms of time units in your language.
unit_names = dict(en = {"year" : ("year", "years"),
                        "month" : ("month", "months"),
                        "week" : ("week", "weeks"),
                        "day" : ("day", "days"),
                        "hour" : ("hour", "hours"),
                        "minute" : ("minute", "minutes"),
                        "second" : ("second", "seconds")})

num_repr = dict(en = {1 : "one",
                      2 : "two",
                      3 : "three",
                      4 : "four",
                      5 : "five",
                      6 : "six",
                      7 : "seven",
                      8 : "eight",
                      9 : "nine",
                      10 : "ten",
                      11 : "eleven",
                      12 : "twelve"})

def amount_to_str(amount):
    if amount in num_repr[LANG]:
        return num_repr[LANG][amount]
    return str(amount)

def seconds_in_units(seconds):
    """
    Returns a tuple containing the most appropriate unit for the
    number of seconds supplied and the value in that units form.

        >>> seconds_in_units(7700)
        (2, 'hour')
    """
    unit_limits = [("year", 365 * 24 * 3600),
                   ("month", 30 * 24 * 3600),
                   ("week", 7 * 24 * 3600),
                   ("day", 24 * 3600),
                   ("hour", 3600),
                   ("minute", 60),
                   ('second', 1)]
    result = []
    if seconds == 0:
        return [(0, 'second')]
    for unit_name, limit in unit_limits:
        if seconds >= limit:
            #amount = int(round(float(seconds) / limit))
            result.append((seconds / limit, unit_name))
            seconds = seconds % limit
    return result

def stringify(td):
    """
    Converts a timedelta into a nicely readable string.

        >>> td = timedelta(days = 77, seconds = 5)
        >>> print readable_timedelta(td)
        two months
    """
    seconds = td.days * 3600 * 24 + td.seconds
    stringified = seconds_in_units(seconds)

    # Localize it.
    processed = []
    for s in stringified:
        #i18n_amount = amount_to_str(amount, unit_name)
        amount, unit_name = s
        i18n_amount = str(amount)
        i18n_unit = unit_names[LANG][unit_name][1]
        if amount == 1:
            i18n_unit = unit_names[LANG][unit_name][0]
        processed.append("%s %s" % (i18n_amount, i18n_unit))
    return ' '.join(processed)


def test(td, s):
    try:
        assert stringify(td) == s
    except AssertionError:
        print 'ERROR', stringify(td), '!=', s


def main():
    global LANG
    LANG = "en"
    test(timedelta(weeks=7, days=3), '1 month 3 weeks 1 day')
    test(timedelta(weeks=1), '1 week')
    test(timedelta(days=1000), '2 years 9 months')
    test(timedelta(days=400), '1 year 1 month 5 days')
    test(timedelta(days=4), '4 days')
    test(timedelta(seconds=2000), '33 minutes 20 seconds')
    test(timedelta(seconds=9888), '2 hours 44 minutes 48 seconds')
    test(timedelta(seconds=99), '1 minute 39 seconds')
    test(timedelta(seconds=45), '45 seconds')
    test(timedelta(), '0 seconds')
    test(timedelta(seconds=1), '1 second')

if __name__ == "__main__":
    main()
