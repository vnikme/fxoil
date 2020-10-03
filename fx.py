import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import pandas as pd
import datetime


currency_codes = [('usd', 'R01235'), ('gbp', 'R01035'), ('eur', 'R01239'), ('tkr', 'R01700'), ('jpy', 'R01820')]
currencies = [x[0] for x in currency_codes]
code2currency = {code: currency for currency, code in currency_codes}
currency2code = {currency: code for currency, code in currency_codes}


def to_float(s):
    return float(s.replace(',', '.'))


def process_currency(root, db):
    code = root.attrib['ID']
    currency = code2currency[code]
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


def read_data():
    db = {}
    for curr in currency2code:
        process_one_file(curr + "rub.xml", db)
    values = []
    for curr_date in iterate_dates(datetime.date(2000, 1, 1), datetime.date(2020, 10, 1)):
        dt = curr_date.isoformat()
        items = []
        for j in range(len(currencies)):
            currency = currencies[j]
            if dt not in db[currency]:              # текущая дата отсутствует, берём данные за предыдущий день
                items.append(values[-1][j + 1])     # +1, т. к. первый столбец это дата
            else:
                items.append(db[currency][dt])      # иначе берём данные по текущей валюте за текущую дату
                if curr_date.year < 2005 and currency == 'tkr':
                    items[-1] *= 1000000                # учитываем деноминацию турецкой лиры 2005 года
        values.append([dt] + items + [1.0])
        #print(values, currencies)
        #exit(1)
    return pd.DataFrame(values, columns = ['date'] + currencies + ['rur'])



def best_in_week(start, end):
    best, value = 'rur', 1.0
    for curr in currencies:
        val = end[curr] / start[curr]               # сравниваем курс на начало этой и начало следующей недели
        if val > value:                             # выбираем максимум
            best, value = curr, val
    return best, value


def plot_best_in_week():
    data = read_data()
    dist = {}
    color_map = {'rur': 'red', 'usd': 'blue', 'gbp': 'green', 'eur': 'yellow', 'jpy': 'orange', 'tkr': 'black'}
    plots = {curr: ([], []) for curr in currencies + ['rur']}               # здесь будем хранить номера дней, когда данная валюта была лучшей, и соответствующие дельты
    for i in range(len(data) - 7):
        best, value = best_in_week(data.iloc[i], data.iloc[i + 7])
        dist[best] = dist.get(best, 0) + 1
        plots[best][0].append(i)
        plots[best][1].append(value - 1)
    print(dist)
    for curr in currencies + ['rur']:                                       # отрисовываем каждую из валют
        plt.scatter(plots[curr][0], plots[curr][1], c=color_map[curr], label=curr)
    plt.legend()
    plt.show()


def max_possible_growth_day(values1, values2):
    value = 1.0
    for c in currencies:
        delta = values2[c] / values1[c]
        if delta > value:
            value = delta
    return value


def max_possible_growth_period(data):
    value = 1.0
    for i in range(1, len(data)):
        value *= max_possible_growth_day(data.iloc[i - 1], data.iloc[i])
    return value


def speculate():
    data = read_data()
    growth = [max_possible_growth_period(data.iloc[i : i + 30]) for i in range(len(data) - 30)]
    for i in range(len(growth)):
        if growth[i] < 1.4:                         # с этим параметром можно поиграться
            continue
        print(data.iloc[i]['date'], growth[i])      # выводим даты, в которые можно было больше всего заработать (обратите внимание, это, в основном, кризисы)
    plt.plot(growth)
    plt.show()


def renorm_data(data):
    means = data.mean()
    usd = float(means['usd'])
    for curr in means.index:
        means[curr] = usd / means[curr]
    sums = None
    for curr in means.index:
        if sums is None:
            sums = data[curr].copy()
        else:
            sums = sums + data[curr]
    for curr in means.index:
        data[curr] /= sums
    return data


def correlations():
    data = read_data()
    data = renorm_data(data)
    for year in range(2000, 2021):
        print(year)
        print(data[data.date.str.match(str(year))].corr())
        print("")
    """
    Данная функция печатает все корреляции по всем годам относительно корзины валют.
    Наблюдения:
     1. usd часто коррелирует с jpy
     2. rur редко коррелирует с gbp, часто коррелирует с tkr.
     3. 2001 - год, когда tkr имеет отрицательную корреляцию со всеми валютами.
     4. 2016 - год, когда gbp имеет отрицательную корреляцию со всеми валютами, кроме tkr.

     П. 3 и 4 - вероятно, все перекладывались из этих валют в другие в эти года.
    """


def main():
    plot_best_in_week()
    speculate()
    correlations()


if __name__ == '__main__':
    main()

