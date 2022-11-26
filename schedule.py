from datetime import datetime, timedelta
from utils import duration, load_co2_measures, next_datetime_with_time, total_duration


def schedule(*, ready_by, charge_time, plug_in_time, off_peak_start, off_peak_end):
    """
    Schedule the charge of a vehicule :
    Optimizes for charging during a single off-peak window,
    and secondarily at times where carbon intensity is low.

    Keyword Arguments:
        ready_by: The time the car must be charged by as a "HH:MM" string
        charge_time: Integer representing the number of minutes the car needs to charge
        plug_in_time: an isoformat string representing the datetime the car was plugged in
        off_peak_start: The start of the off-peak window as a "HH:MM" string
        off_peak_end: The end of the off-peak window as a "HH:MM" string
    Returns:
        A charging schedule in the form of a list of pairs of datetimes.
        Each pair represents the start and end of a period where should charge.
        The charge periods are sorted chronologically,
        but successive periods that could make a large continuous periods are not merged.
    """
    plug_in_datetime = datetime.fromisoformat(plug_in_time)
    charge_time = timedelta(minutes=charge_time)
    ready_by_datetime = next_datetime_with_time(plug_in_datetime, ready_by)

    if ready_by_datetime - plug_in_datetime <= charge_time:
        return [(plug_in_datetime, ready_by_datetime)]

    off_peak_periods, peak_periods = off_peak_and_peak_periods(
        plug_in_datetime, ready_by_datetime, off_peak_start, off_peak_end
    )

    off_peak_periods_duration = total_duration(off_peak_periods)

    co2_measures = load_co2_measures()

    if charge_time <= off_peak_periods_duration:
        charging_periods = optimize_co2(
            periods=off_peak_periods,
            charge_time=charge_time,
            co2_measures=co2_measures,
        )
    else:
        remaining_charge_timedelta = charge_time - off_peak_periods_duration
        charging_periods = [
            *off_peak_periods,
            *optimize_co2(
                periods=peak_periods,
                charge_time=remaining_charge_timedelta,
                co2_measures=co2_measures,
            ),
        ]

    return simplify_periods(charging_periods)


def off_peak_and_peak_periods(plug_in, ready_by, off_peak_start, off_peak_end):
    """
    Find the off-peak and peak periods between a plugin and "ready by" datetime
    for a single off-peak window

    Arguments:
        plug_in: datetime of the plugin
        ready_by: datetime the car must be ready by
        off_peak_start: Start of off-peak window as a "HH:MM" string
        off_peak_end: End of off-peak window as a "HH:MM" string

    Returns:
        Two lists of off-peak periods and peak periods.
    """
    next_off_peak_start = next_datetime_with_time(plug_in, off_peak_start)
    next_off_peak_end = next_datetime_with_time(plug_in, off_peak_end)

    if next_off_peak_start == next_off_peak_end:
        off_peak_periods = []
        peak_periods = [(plug_in, ready_by)]
    elif next_off_peak_start < next_off_peak_end:
        if next_off_peak_start < ready_by:
            if next_off_peak_end < ready_by:
                off_peak_periods = [(next_off_peak_start, next_off_peak_end)]
                peak_periods = [
                    (plug_in, next_off_peak_start),
                    (next_off_peak_end, ready_by),
                ]
            else:
                off_peak_periods = [(next_off_peak_start, ready_by)]
                peak_periods = [(plug_in, next_off_peak_start)]
        else:
            off_peak_periods = []
            peak_periods = [(plug_in, ready_by)]
    else:
        if next_off_peak_start < ready_by:
            off_peak_periods = [
                (plug_in, next_off_peak_end),
                (next_off_peak_start, ready_by),
            ]
            peak_periods = [(next_off_peak_end, next_off_peak_start)]
        else:
            if next_off_peak_end < ready_by:
                off_peak_periods = [
                    (plug_in, next_off_peak_end),
                ]
                peak_periods = [(next_off_peak_end, ready_by)]
            else:
                off_peak_periods = [(plug_in, ready_by)]
                peak_periods = [(plug_in, ready_by)]
    return off_peak_periods, peak_periods


def optimize_co2(*, periods, charge_time, co2_measures):
    """
    Spread a charging time over given periods in order to minimize co2 emission.

    Keyword Arguments:
        periods: The periods available for charging.
        charge_time: The charging time as a timedelta.
        co2_measures: A list of co2 readings

    Return:
        A list of charging periods
    """
    if total_duration(periods) <= charge_time:
        return periods

    shift_to_forecast = timedelta(weeks=1)
    co2_forecasts = [
        {
            "from": max(co2["from"] + shift_to_forecast, period_from),
            "to": min(co2["to"] + shift_to_forecast, period_to),
            "forecast": co2["intensity"],
        }
        for co2 in co2_measures
        for period_from, period_to in periods
        if co2["from"] + shift_to_forecast <= period_to
        and co2["to"] + shift_to_forecast >= period_from
    ]
    sorted_co2_forecasts = sorted(co2_forecasts, key=lambda co2: co2["forecast"])

    remaining_charge_timedelta = charge_time
    null_timedelta = timedelta(0)
    charging_periods = []
    for co2 in sorted_co2_forecasts:
        if remaining_charge_timedelta <= null_timedelta:
            break

        co2_period = (co2["from"], co2["to"])
        if duration(co2_period) < remaining_charge_timedelta:
            charging_periods.append(co2_period)
        else:
            charging_periods.append(
                (co2["from"], co2["from"] + remaining_charge_timedelta)
            )

        remaining_charge_timedelta = remaining_charge_timedelta - duration(co2_period)

    return simplify_periods(charging_periods)


def simplify_periods(periods):
    """
    Makes a list of periods easier to understand by sorting them
    """
    return sorted(periods, key=lambda p: p[0])


if __name__ == "__main__":
    print(
        schedule(
            ready_by="07:00",
            charge_time=300,
            plug_in_time="2019-10-04T18:42:12+00:00",
            off_peak_start="00:30",
            off_peak_end="07:30",
        )
    )
