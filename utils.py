from datetime import datetime, timedelta, timezone
import json


def parse_time(time):
    return int(time[:-3]), int(time[-2:])


def parse_co2_timestamp(timestamp):
    return datetime.strptime(timestamp, "%Y-%m-%dT%H:%MZ").replace(tzinfo=timezone.utc)


def next_datetime_with_time(current, time):
    hour, minute = parse_time(time)
    this_time_same_day = current.replace(hour=hour, minute=minute)

    if this_time_same_day <= current:
        return this_time_same_day + timedelta(days=1)

    return this_time_same_day


def duration(period):
    period_from, period_to = period
    return period_to - period_from


def total_duration(periods):
    return sum([duration(period) for period in periods], timedelta())


def load_co2_measures():
    with open("carbon_intensity_json.json") as file:
        return [
            {
                "from": parse_co2_timestamp(co2_object["from"]),
                "to": parse_co2_timestamp(co2_object["to"]),
                "intensity": co2_object["intensity"]["actual"],
            }
            for co2_object in json.load(file)["data"]
        ]
