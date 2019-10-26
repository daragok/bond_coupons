import datetime
from decimal import Decimal
from functools import reduce

import pandas as pd

import utils

TO_PERCENT = 100
DAYS_PER_YEAR = 365


class Bond:
    def __init__(self, name, face_value, coupon, coupon_days, first_coupon_date, maturity_date):
        self.name = name
        self.face_value = Decimal(face_value)
        self.coupon = Decimal(coupon)
        self.coupon_days = coupon_days
        self.first_coupon_date = first_coupon_date
        self.maturity_date = maturity_date

    def __repr__(self):
        return f"{self.__class__.__name__}({','.join([f'{k}={repr(v)}' for k, v in self.__dict__.items()])})"

    def __mul__(self, other):
        if isinstance(other, int):
            return Bond(self.name + f'*{other}', self.face_value * other, self.coupon * other, self.coupon_days,
                        self.first_coupon_date, self.maturity_date)
        raise TypeError

    def __rmul__(self, other):
        return self * other

    @property
    def coupon_rate(self):
        """ Coupon rate is relative to the face value, per year """
        return self.coupon_per_year / self.face_value

    @property
    def coupon_per_year(self):
        return self.coupon * DAYS_PER_YEAR / self.coupon_days

    @property
    def coupon_rate_pretty(self):
        return f"{round(self.coupon_rate * TO_PERCENT, 2)}%"

    @property
    def coupon_payments(self):
        dates = []
        coupon_date = self.first_coupon_date
        while coupon_date <= self.maturity_date:
            dates.append((coupon_date, self.coupon))
            coupon_date += datetime.timedelta(self.coupon_days)
        df = pd.DataFrame(data=dates, columns=('date', self.name))
        df['date'] = pd.to_datetime(df['date'])
        df.set_index('date', inplace=True)
        return df

    @property
    def n(self):
        n = 0
        coupon_date = self.first_coupon_date
        while coupon_date <= self.maturity_date:
            coupon_date += datetime.timedelta(self.coupon_days)
            n += 1
        return n


class BondDeal:
    def __init__(self, bond, price):
        self.bond = bond
        self.price = Decimal(price)

    @property
    def current_yield(self):
        return self.bond.coupon_per_year / self.price

    @property
    def yield_to_maturity(self):
        return (utils.secant(self._yield_to_maturity_function, Decimal('0.000001'), Decimal('1'), 100)
                * DAYS_PER_YEAR / self.bond.coupon_days)

    @property
    def yield_to_maturity_pretty(self):
        return f"{round(self.yield_to_maturity * TO_PERCENT, 2)}%"

    def _yield_to_maturity_function(self, ytm):
        return (self.bond.coupon * ((1 - 1 / (1 + ytm) ** self.bond.n) / ytm)
                + self.bond.face_value / (1 + ytm) ** self.bond.n
                - self.price)


class BondCollection:
    def __init__(self, *bonds):
        self.bonds = bonds

    def print_all_coupons(self):
        dfs = [b.coupon_payments for b in self.bonds]
        # merge all into one dataframe
        merged = reduce(lambda left, right: pd.merge(left, right, on='date', how='outer', sort=True), dfs)
        # make a total column
        merged['total'] = merged.sum(axis=1)
        # with precise dates for each payment
        # print(merged['total'])

        # totaled by month
        grouped = merged.resample('M').sum().sum(axis=1)
        # reformat month date to be pretty
        grouped.index = grouped.index.strftime('%Y/%m')
        # drop zero rows
        grouped = grouped[grouped != 0]
        print("Coupons by month excluding 0s")
        print(grouped)


if __name__ == '__main__':
    ofz_29012 = Bond(name='OFZ_29012',
                     face_value=1000,
                     coupon=Decimal('39.59'),
                     coupon_days=182,
                     first_coupon_date=datetime.date(2019, 11, 20),
                     maturity_date=datetime.date(2022, 11, 16))
    ofz_26220 = Bond(name='OFZ_26220',
                     face_value=1000,
                     coupon=Decimal('36.9'),
                     coupon_days=182,
                     first_coupon_date=datetime.date(2019, 12, 11),
                     maturity_date=datetime.date(2022, 12, 7))

    bonds_collection = BondCollection(10 * ofz_29012,
                                      15 * ofz_26220,
                                      )
    bonds_collection.print_all_coupons()
