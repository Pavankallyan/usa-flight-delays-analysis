"""Walk through the bundled 100k-row flight-delay sample with src/analysis.

Prints an on-time summary, the delay-cause breakdown, the worst time of
day to fly, the busiest routes, and the per-year trend — all computed from
the real sample in DataSets/.

Run from the repo root:

    python examples/delay_explorer.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src import analysis as a


def main() -> None:
    df = a.load_sample()
    print(f"Flights analysed: {len(df):,}")
    print(f"Years covered: {sorted(df['Year'].unique())}")
    print(f"Carriers: {df['UniqueCarrier'].nunique()}")
    print(f"Cancelled: {df['Cancelled'].mean():.1%}")
    print(f"On-time rate (operated flights, <15 min delay): {a.on_time_rate(df):.1%}")
    print()

    print("Delay minutes by cause:")
    for cause, minutes in a.delay_cause_totals(df).items():
        print(f"  {cause:<20} {minutes:>10,.0f}")
    print()

    print("Delayed flights by primary cause:")
    for cause, count in a.primary_cause_counts(df).items():
        print(f"  {cause:<15} {count:>6,}")
    print()

    rates = a.delayed_rate_by_time_of_day(df)
    print("Delay rate by time of day:")
    for tod, rate in rates.sort_values(ascending=False).items():
        print(f"  {tod:<10} {rate:.1%}")
    print()

    print("Busiest routes (delay rate, mean delay):")
    for route, row in a.route_stats(df, top_n=5).iterrows():
        print(
            f"  {route:<8} {int(row['flights']):>4} flights, "
            f"delayed {row['delayed_rate']:.1%}, "
            f"mean {row['mean_delay_minutes']:+.1f} min"
        )
    print()

    print("Yearly trend (delay rate, mean delay):")
    for year, row in a.yearly_trend(df).iterrows():
        print(
            f"  {year}: {int(row['flights']):>6,} flights, "
            f"cancelled {row['cancelled_rate']:.1%}, "
            f"delayed {row['delayed_rate']:.1%}, "
            f"mean {row['mean_delay_minutes']:+.1f} min"
        )


if __name__ == "__main__":
    main()
