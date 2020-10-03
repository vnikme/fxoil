import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import math
import datetime


def spikes_and_drops():
    oil = pd.read_csv('brent-daily_csv.csv')
    dates = oil['Date']
    price = oil['Price']
    #plt.plot(oil['Price'])
    #plt.show()
    deltas = pd.DataFrame([[dates[i], math.log10(price[i + 30] / price[i])] for i in range(len(price) - 30)], columns = ['Date', 'Delta'])
    #drops = deltas[deltas['Delta'] > 0.15]
    drops = deltas[deltas['Delta'] < -0.15]
    drop_months = {}
    for _, row in drops.iterrows():
        month = row['Date'][0:7]
        #drop_months[month] = max(drop_months.get(month, 0.0), row['Delta'])
        drop_months[month] = min(drop_months.get(month, 0.0), row['Delta'])
    for month in sorted(drop_months.keys()):
        print(month, drop_months[month])
    #plt.plot(deltas)
    #plt.show()
    """
    1990 11/12 - компенсация производства нефти во время войны в Персидском Заливе
    1991 01 - конец войны в Персидском Заливе
    2000 11 - крах доткомов
    2001 09 - 9/11
    2008 08/09/10/11 - экономический кризис 2008
    2014 11/12 - сланцевая нефть в США
    2015 11/12 - отмена санкций против Ирана в январе 2016
    2020 01/02/03 - covid19

    Видны циклы примерно в 10 лет.
    Про циклы см. https://ru.wikipedia.org/wiki/%D0%A6%D0%B8%D0%BA%D0%BB%D1%8B_%D0%9A%D0%BE%D0%BD%D0%B4%D1%80%D0%B0%D1%82%D1%8C%D0%B5%D0%B2%D0%B0
    """


def from_iso(dt):
    dt = dt.split('-')
    return datetime.date(int(dt[0]), int(dt[1]), int(dt[2]))


def fill_holidays(oil):
    values = []
    dates = oil['Date']
    prices = oil['Price']
    current_date, first_date = None, None
    for _, row in oil.iterrows():
        dt = from_iso(row['Date'])
        price = row['Price']
        if current_date is None:
            current_date = dt
            first_date = dt
            values.append([dt, price])
            continue
        while current_date + datetime.timedelta(days = 1) != dt:        # добавляем предыдущее значение для тех дней, где оно отсутствует
            current_date += datetime.timedelta(days = 1)
            values.append([current_date, values[-1][1]])
        current_date = dt
        values.append([dt, price])
    return pd.DataFrame(values, columns = ['Date', 'Price'])


def max_possible_growth(data):
    value = 1.0
    for i in range(1, len(data)):
        if data[i] > data[i - 1]:
            value *= (data[i] / data[i - 1])
    return value


def speculate():
    oil = pd.read_csv('brent-daily_csv.csv')
    oil = fill_holidays(oil)
    values = list(oil['Price'])
    growth = [max_possible_growth(values[i : i + 30]) for i in range(len(values) - 30)]
    for i in range(len(growth)):
        if growth[i] < 1.8:             # с этим параметром можно поиграться
            continue
        print(oil.iloc[i]['Date'].isoformat(), growth[i])
    plt.plot(growth)
    plt.show()
    


def main():
    spikes_and_drops()
    speculate()


main()

