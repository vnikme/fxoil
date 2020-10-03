import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import pandas as pd
import datetime
import math


def to_float(s):
    return float(s.replace(',', '.'))


def process_currency(root, db):
    code = root.attrib['ID']
    currency = 'usd'
    if currency not in db:
        db[currency] = {}
    for child in root:
        ds = child.attrib['Date']
        day, month, year = ds.split('.')
        ds = '-'.join([year, month, day])           # конвертируем из формата day.month.year в year-month-day (iso format)
        nominal = 1.0
        value = 0.0
        for item in child:
            if item.tag == 'Nominal':
                nominal = to_float(item.text)
            elif item.tag == 'Value':
                value = to_float(item.text)
        db[currency][ds] = value / nominal


def process_one_file(path, db):
    data = open(path, 'rt').read()
    root = ET.fromstring(data)
    process_currency(root, db)


def iterate_dates(start, end):
    curr_date = start
    for i in range((end - start).days):
        yield curr_date
        curr_date += datetime.timedelta(days = 1)


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
            values.append([dt.isoformat(), price])
            continue
        while current_date + datetime.timedelta(days = 1) != dt:        # добавляем предыдущее значение для тех дней, где оно отсутствует
            current_date += datetime.timedelta(days = 1)
            values.append([current_date.isoformat(), values[-1][1]])
        current_date = dt
        values.append([dt.isoformat(), price])
    return pd.DataFrame(values, columns = ['date', 'oil'])


def read_data(fix_inflation):
    cpi = pd.read_csv('inflation.csv')
    db = {}
    process_one_file("usdrub.xml", db)
    oils = pd.read_csv('brent-daily_csv.csv')
    oils = fill_holidays(oils)
    oils = oils[oils['date'] >= '2000']
    values = []
    mult_usd, mult_rub, cpi_usd, cpi_rub = 1.0, 1.0, 1.0, 1.0
    i = 0
    for curr_date in iterate_dates(datetime.date(2000, 1, 1), datetime.date(2020, 1, 1)):
        if fix_inflation and curr_date.month == 1 and curr_date.day == 1:
            cpi_rub = (1 + cpi[(cpi['LOCATION'] == 'RUS') & (cpi['TIME'] == curr_date.year)].mean()['Value'] / 100)**(1/365)
            cpi_usd = (1 + cpi[(cpi['LOCATION'] == 'USA') & (cpi['TIME'] == curr_date.year)].mean()['Value'] / 100)**(1/365)
        dt = curr_date.isoformat()
        if dt not in db['usd']:                                     # текущая дата отсутствует, берём данные за предыдущий день
            usd = values[-1][1] * cpi_usd / cpi_rub                 # +1, т. к. первый столбец это дата
        else:
            usd = db['usd'][dt] * mult_usd / mult_rub               # корректируем на накопленную инфляцию
        oil = oils.iloc[i]['oil'] / mult_usd
        mult_rub *= cpi_rub
        mult_usd *= cpi_usd
        values.append([dt, usd, oil])
        i += 1
    print(mult_rub, mult_usd)
    return pd.DataFrame(values, columns = ['date', 'usd', 'oil'])



def correlations(fix_inflation):
    data = read_data(fix_inflation)
    corrs = []
    for year in range(2000, 2020):
        for month in range(1): #, 13):
            #pattern = str(year) + '-' + ('%02d' % month)
            pattern = str(year)
            corr = float(data[data.date.str.match(pattern)].corr()['usd']['oil'])
            corrs.append(corr)
            print('%s: %.03f' % (pattern, corr))
    print(data.corr())


def rub_price(fix_inflation):
    data = read_data(fix_inflation)
    oil_rub = data['usd'] * data['oil']
    data.insert(len(data.columns), 'oilrub', oil_rub)
    print(oil_rub.describe())
    mean = float(oil_rub.mean())
    std = float(oil_rub.std())
    print(mean, std)
    print(data[data['oilrub'] > mean + std * 3])
    print(data[data['oilrub'] < mean - std * 2])
    plt.plot(oil_rub)
    plt.plot([mean + std * 3 for _ in range(len(oil_rub))])
    plt.plot([mean - std * 3 for _ in range(len(oil_rub))])
    plt.show()


def main():
    correlations(True)
    rub_price(True)


if __name__ == '__main__':
    main()

