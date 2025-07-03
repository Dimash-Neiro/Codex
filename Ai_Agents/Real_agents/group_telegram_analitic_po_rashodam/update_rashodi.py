import requests
import pandas as pd
import numpy as np
from pandas.io.json import json_normalize

data_rashod = requests.get('http://31.31.202.35:9000/?rashod_b')

rashod = pd.read_json(data_rashod.text)['test']
total = json_normalize(data=rashod[0])
n = 0
for i in rashod.index:
    n += 1
    if i == 0:
        continue
    norm = json_normalize(data=rashod[i])
    total = pd.concat([total, norm])
rashod = total
rashod.index = np.arange(len(rashod))
rashod = rashod[rashod['Операция'] != '']
rashod = rashod[rashod['Сумма'] != '']
rashod['Сумма'] = rashod['Сумма'].apply(lambda x: int(x.split(',')[0]))


def kategor_rashoda(s):
    if 'Перевод денег в другие отделения' in s:
        return 'Перевод денег в другие отделения'
    elif 'Выдача зарплаты' in s:
        return 'Выдача зарплаты'
    elif 'Комиссия за банковские операции' in s:
        return 'Комиссия за банковские операции'
    elif 'Заправка принтера' in s:
        return 'Заправка принтера'
    elif 'Покупка канцтоваров' in s:
        return 'Покупка канцтоваров'
    elif 'Рабочая техника' in s:
        return 'Рабочая техника'
    elif 'Налоги' in s:
        return 'Налоги'
    elif 'Оплата рекламы' in s:
        return 'Реклама'
    elif 'Коммунальные услуги' in s:
        return 'Коммунальные услуги'
    elif 'Оплата интернета' in s:
        return 'Оплата интернета'
    elif 'Охрана' in s:
        return 'Охрана'
    elif 'Дорожные' in s:
        return 'Дорожные'
    elif 'Пополнение баланса на рабочий' in s:
        return 'Пополнение баланса на рабочий'
    elif 'Ремонт товаров' in s:
        return 'Ремонт товаров'
    elif 'Аренда помещения' in s:
        return 'Аренда помещения'
    elif 'Программное обеспечение' in s:
        return 'Программное обеспечение'
    elif 'Хоз. товары' in s:
        return 'Хоз. товары'
    elif 'Покупка оборудования' in s:
        return 'Покупка оборудования'
    elif 'Корректировочные расходы' in s:
        return 'Корректировочные расходы'
    elif 'Юридические и консалтинговые услуги' in s:
        return 'Юридические и консалтинговые услуги'
    elif 'Услуги уборщицы, электрика, сантехника' in s:
        return 'Услуги уборщицы, электрика, сантехника'
    elif 'Выемка' in s:
        return 'Выемка'
    elif 'Возврат долга' in s:
        return 'Возврат долга'
    elif 'Продукты питания' in s:
        return 'Продукты питания'
    elif 'Чистка и ремонт ювелирных изделий' in s:
        return 'Чистка и ремонт ювелирных изделий'
    elif 'dddd' in s:
        return 'dddd'
    elif 'За уборку' in s:
        return 'Услуги уборщицы, электрика, сантехника'
    elif 'Выдача средств из кассы учредителю' in s:
        return 'Выдача средств из кассы учредителю'
    elif 'Перевод с расчетного счета в кассу' in s:
        return 'Перевод с расчетного счета в кассу'
    elif 'Обучение' in s:
        return 'Обучение'
    elif 'Хоз. нужды' in s:
        return 'Хоз. товары'
    elif 'Перевод в другое отделение' in s:
        return 'Перевод денег в другие отделения'
    elif 'Ремонт телефонов' in s:
        return 'Ремонт телефонов'
    elif 'Комиссия банка' in s:
        return 'Комиссия за банковские операции'
    elif 'Реклама' in s:
        return 'Реклама'
    elif 'Открытие нового отделения' in s:
        return 'Открытие нового отделения'
    elif 'Комиссия Банка' in s:
        return 'Комиссия за банковские операции'

    elif 'Ремонт залогов' in s:
        return 'Ремонт залогов'
    elif 'Административный расход' in s:
        return 'Административный расход'
    elif 'Новые типы расходов' in s:
        return 'Новые типы расходов'
    elif 'Оплата кредитов' in s:
        return 'Оплата кредитов'
    elif 'Налоги по зарплатам' in s:
        return 'Налоги по зарплатам'
    elif 'Подоходный налог' in s:
        return 'Подоходный налог'
    elif 'Покупка воды' in s:
        return 'Покупка воды'
    elif 'Корректировочное списание' in s:
        return 'Корректировочное списание'
    elif '% за рассрочку банку' in s:
        return '% за рассрочку банку'
    elif 'Выдача денежных средств из кассы сотруднику' in s:
        return 'Выдача денежных средств из кассы сотруднику'
    elif 'Банк' in s:
        return 'Банк'
    elif 'Freedom Life (-15%) страховка' in s:
        return 'Freedom Life (-15%) страховка'
    elif 'Коммисия Kaspi' in s:
        return 'Коммисия Kaspi'
    elif 'Прочие расходы' in s:
        return 'Прочие расходы'

    return 'Неизвестно'


rashod['Категория'] = rashod['Описание'].apply(kategor_rashoda)
# rashod['Должность'] = ''
rashod['Дата'] = pd.to_datetime(rashod['Дата'], format='%d.%m.%Y')

rashod[rashod['Категория'] == 'Неизвестно'].head(60)
rashod_zatrati = rashod[rashod['Операция'] == 'Расход (затраты)']


# print(rashod_zatrati['Отделение'].unique())
# rashod_zatrati[(rashod_zatrati['Отделение'] == 'Спортивный') | (rashod_zatrati['Отделение'] == 'Респ Шым') | (rashod_zatrati['Отделение'] == 'Уалиханова') | (rashod_zatrati['Отделение'] == 'Магаз Шым') & (rashod_zatrati['Дата'] >= pd.to_datetime('01.03.2023', format='%d.%m.%Y'))].sort_values(by='Сумма',ascending=False).head(60)


def dolzhnost(s):
    s = s.lower()
    if 'оценщик' in s:
        return 'Оценщик'
    elif 'директор' in s:
        return 'Директор'
    elif 'колл-центр' in s:
        return 'Колл-центр'
    elif 'аудитор' in s:
        return 'аудитор'
    elif 'бухгалтер' in s:
        return 'Бухгалтерия'
    elif 'smm' in s:
        return 'Smm'
    elif 'роп' in s:
        return 'Роп'
    elif 'hr' in s:
        return 'Hr'
    elif 'отдел обучения' in s:
        return 'Отдел обучения'
    elif 'отдел взыскания' in s:
        return 'Отдел взыскания'
    elif 'ахо' in s:
        return 'Ахо'
    elif 'программист' in s:
        return 'Программист'
    elif 'аналитик' in s:
        return 'Аналитик'
    elif 'e-commerce' in s:
        return '(E-commerce)'
    elif 'видеограф' in s:
        return 'Видеограф'
    elif 'фот' in s:
        return 'Ген. дир.'
    elif 'казначей' in s:
        return 'Казначей'
    elif 'юрист' in s:
        return 'Юрист'
    elif 'loona' in s:
        return 'Магазин Loona'
    elif 'луна' in s:
        return 'Магазин Loona'
    elif 'ddd' in s:
        return 'ddd'
    elif 'ddd' in s:
        return 'ddd'
    elif 'ddd' in s:
        return 'ddd'
    elif 'ddd' in s:
        return 'ddd'

    return 'Неизвестно'


rashod_zatrati['Должность'] = rashod_zatrati['Описание'].apply(dolzhnost)
rashod_zatrati.to_csv('zatrati.csv')