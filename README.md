My solution to this [coding challenge](https://ev-energy.notion.site/Backend-Engineer-Coding-challenge-7db6c863e76a4c75984b625e0e0670e8).
It consists in optimizing the charging schedule of an electric vehicle with regard to cost and CO2 emission.

# Rationale

My goal was to provide a working solution to the exposed problem while spending limited time on it.
The program should produce an adequate schedule event if some optimization are missing.

The code optimizes for readability over generality and extensibility.

I have prioritized the implementation of the carbon intensity optimization over "car warming" as it makes more sense for a product in green tech and affects all users.
However, if both were implemented, I think the car warming would take precedence in the scheduler, as it is a cost-related optimization.

The the program should handle different timezones.

# Improvements

## Car warming

The "car warming" optimization could be activated by the end user, and by a simple boolean in the schedule function.

After optimizing for off-peak charging and before optimizing for co2 during the peak period, the schedule would allocate a period of up to one hour just before the "ready by" time.

## Multiple off-peak periods

We could represent all of peak time windows in the day as a list like this `[('00:00', '05:00), ('15:00', '16:00'), ('22:00', '00:00')]`.

The calculation of the off-peak periods for multiple window can be based the on calculation for a single window already implemented.

## Merge sucessive periods

The `simplify_periods` function should merge periods that make up a larger continuous period in addition to sorting them.
