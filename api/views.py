import datetime, re
from rest_framework.response import Response
from rest_framework.decorators import api_view
from api.decorators import expect_datetime
from api.utils import datetime_to_str
from api.algorithms import WorldPopulationRankCalculator
from dateutil.relativedelta import relativedelta



# FIXME: temporary hack until WorldPopulationRankCalculator has been completely cleaned up
wprCalculator = WorldPopulationRankCalculator()
wprCalculator.readCSV()



@api_view(['GET'])
def list_countries(request):
    """ Returns a list of all countries in the statistical dataset.
    """

    return Response({'countries': WorldPopulationRankCalculator.REGIONS})


@api_view(['GET'])
@expect_datetime('dob')
def wprank_today(request, dob, sex, country):
    """ Calculates the world population rank of a person with the given date of birth, sex and country of origin as of today.

    The world population rank is defined as the position of someone's birthday when compared to the entire world population ordered by date of birth decreasing. That is, the last person born is assigned rank #1.

    Today's date is always based on the current time in the timezone UTC.

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, all)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)

    Examples:
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/today/: calculates the person's world population rank today
    """
    today = datetime.datetime.utcnow()
    rank = wprCalculator.worldPopulationRankByDate(sex, country, dob, today)
    return Response({"rank": rank, 'dob': datetime_to_str(dob), 'sex': sex, 'country': country})


@api_view(['GET'])
@expect_datetime('dob')
@expect_datetime('date')
def wprank_by_date(request, dob, sex, country, date):
    """ Calculates the world population rank of a person with the given date of birth, sex and country of origin on a certain date.

    The world population rank is defined as the position of someone's birthday when compared to the entire world population ordered by date of birth decreasing. That is, the last person born is assigned rank #1.

    The historical date must lie past the person's date of birth, but may well be in the future.

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, unisex)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)
       * date: the date on which to calculate the rank in format YYYY-MM-DD

    Examples:
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/on/2000-01-01/: calculates the person's world population rank at the turn of the century
    """
    rank = wprCalculator.worldPopulationRankByDate(sex, country, dob, date)
    return Response({"rank": rank, 'dob': datetime_to_str(dob), 'sex': sex, 'country': country, 'date': datetime_to_str(date)})


@api_view(['GET'])
@expect_datetime('dob')
def wprank_by_age(request, dob, sex, country, age):
    """ Calculates the world population rank of a person with the given date of birth, sex and country of origin on a certain date as expressed by the person's age.

    The world population rank is defined as the position of someone's birthday when compared to the entire world population ordered by date of birth decreasing. That is, the last person born is assigned rank #1.

    Based on the date of birth and the given age, a calculation date is computed. This date may lie in the future (by specifying an age the person hasn't reached yet). Then the world population rank of the person on that day is calculated.

    The age can be given as a simple number, in which case it is assumed to be days since birth. Alternatively, the age can be specified in years, months and days, using the format "##y##m##d", e.g. "18y1m5d" to denote the day one month and five days after the 18th birthday. All three values are optional (or may be zero), but at least one of them must be given.

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, unisex)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)
       * age: the time interval after the person's birth at which to calculate the world population rank, either given in days (e.g. '1000') or in a combination of years, months and days (e.g. '3y6m9d')

    Examples:
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/age/100/: calculates the world population rank a hundred days after the person's birth
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/age/6m/: calculates the world population rank when the person was six months old
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/age/25y1d/: calculates the world population rank one day after the person's 25th birthday
    """
    age_delta = _parse_timeframe(age)
    rank = wprCalculator.worldPopulationRankByDate(sex, country, dob, dob + age_delta)
    return Response({"rank": rank, 'dob': datetime_to_str(dob), 'sex': sex, 'country': country, 'age': age})


@api_view(['GET'])
@expect_datetime('dob')
def wprank_ago(request, dob, sex, country, offset):
    """ Calculates the world population rank of a person with the given date of birth, sex and country of origin on a certain date as expressed by an offset relative to today.

    The world population rank is defined as the position of someone's birthday when compared to the entire world population ordered by date of birth decreasing. That is, the last person born is assigned rank #1.

    Based on today's date (the current date in UTC) and the offset parameter, a calculation date is computed. Then the world population rank of the person on that day is calculated.

    The offset parameter can be given as a simple number, in which case it is assumed to be days before today. Alternatively, the offset parameter can be specified in years, months and days, using the format "##y##m##d", e.g. "8y1m5d" to denote the day eight years, one month and five days ago. All three values are optional (or may be zero), but at least one of them must be given.

    Specifying a date before the person's birth (i.e. giving a higher value than the person's age as an offset) will result in an error.

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, unisex)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)
       * offset: the time interval after the person's birth at which to calculate the world population rank, either given in days (e.g. '1000') or in a combination of years, months and days (e.g. '3y6m9d')

    Examples:
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/ago/100/: calculates the world population rank a hundred days ago
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/ago/6m/: calculates the world population rank six months ago
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/ago/1y2m3d/: calculates the world population rank one year, two months and three days ago
    """
    today = datetime.datetime.utcnow()
    before_delta = _parse_timeframe(offset)
    rank = wprCalculator.worldPopulationRankByDate(sex, country, dob, today - before_delta)
    return Response({"rank": rank, 'dob': datetime_to_str(dob), 'sex': sex, 'country': country, 'offset': offset})


@api_view(['GET'])
@expect_datetime('dob')
def wprank_by_rank(request, dob, sex, country, rank):
    """ Calculates the day on which a person with the given date of birth, sex and country of origin has reached (or will reach) a certain world population rank.

    The world population rank is defined as the position of someone's birthday when compared to the entire world population ordered by date of birth decreasing. That is, the last person born is assigned rank #1.

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, unisex)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)
       * rank: the rank to calculate the date for

    Examples:
       * /api/1.0/wp-rank/1952-03-11/male/United%20Kingdom/ranked/1000000000/: calculates the day on which the person became the one billionth inhabitant
    """
    # TODO: validate rank and return error message if not int
    date = wprCalculator.dateByWorldPopulationRank(sex, country, dob, int(rank))
    return Response({'dob': datetime_to_str(dob), 'sex': sex, 'country': country, 'rank': rank, 'date_on_rank': datetime_to_str(date)})


@api_view(['GET'])
@expect_datetime('dob')
def life_expectancy(request, dob, sex, country):
    """ Calculates the remaining life expectancy of a person with the given date of birth, sex and country.

    The result is given in a decimal number of years as of today (UTC).

    Parameters:
       * dob: the person's date of birth (format: YYYY-MM-DD)
       * sex: the person's sex (valid values: male, female, unisex)
       * country: the person's country of origin (valid values: see /meta/countries, use 'WORLD' for all)

    Examples:
       * /api/1.0/life-expectancy/1952-03-11/male/United%20Kingdom/: calculates the remaining life expectancy of the given person
    """
    return Response({'dob': datetime_to_str(dob), 'sex': sex, 'country': country, 'life_expectancy': 12.34})



TIMEFRAME_REGEX = re.compile(r'^(?:(?P<years>\d+)y)?(?:(?P<months>\d+)m)?(?:(?P<days>\d+)d)?$')
def _parse_timeframe(val):
    if val.isdigit():
        return relativedelta(days=int(val))
    else:
        re_result = TIMEFRAME_REGEX.match(val)
        if re_result and re_result.lastindex:   # lastindex is None (and has_any_match therefore False) if all three optional groups were left off
            years, months, days = (int(x) if x else 0 for x in re_result.groups())
            return relativedelta(years=years, months=months, days=days)

    from rest_framework.exceptions import ParseError
    raise ParseError(detail='Invalid offset format, please use integer to indicate days or ##y##m##d')  # TODO: improve message
