from bs4 import BeautifulSoup
import lxml

import requests
import json

START_URL = 'https://fix-price.ru/personal'
PERSONAL_INFO_URL = 'https://fix-price.ru/personal/#profile'
FAVORITE_PRODUCTS_URL = 'https://fix-price.ru/personal/#favorites'
PROMOTIONS_URL = 'https://fix-price.ru/personal/'
AUTH_URL = 'https://fix-price.ru/ajax/auth_user.php'


def get_auth(start_url, auth_url, login, password):
    """
    Open session and login
    """

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, "
                      "like Gecko) Chrome/73.0.3683.103 Safari/537.36 OPR/60.0.3255.69"})

    form_data = dict(
        AUTH_FORM='Y',
        TYPE='AUTH',
        backurl='/personal/',
        login=login.strip(),
        password=password.strip()
    )
    #
    session.get(start_url)
    login = session.post(auth_url, data=form_data, timeout=15)

    return session


def get_personal_data(session, url):
    r = session.get(url)

    soup = BeautifulSoup(r.text, 'lxml')

    surname = soup.find(attrs={'name': 'LAST_NAME'}).get('value')
    name = soup.find(attrs={'name': 'NAME'}).get('value')
    second_name = soup.find(attrs={'name': 'SECOND_NAME'}).get('value')
    birthday = soup.find(attrs={'name': 'PERSONAL_BIRTHDAY'}).get('value')
    email = soup.find(attrs={'placeholder': '*EMAIL'}).get('value')

    gender = soup.find(attrs={'name': 'PERSONAL_GENDER'}, checked='checked').get('value')
    if gender == 'F':
        gender = 'Женский'
    else:
        gender = 'Мужской'

    state = soup.find(attrs={'name': "PERSONAL_STATE"}).find_next(selected=True).text
    city = soup.find(attrs={'name': "PERSONAL_CITY"}).find_next(selected=True).text
    card_number = soup.find(attrs={'class': 'personal-card__number'}).text
    print(soup.find(attrs={'class': 'personal-card__number'}))

    personal_data = {
        'имя': name,
        'фамилия': surname,
        'отчество': second_name,
        'дата рождения': birthday,
        'почта': email,
        'пол': gender,
        'регион': state,
        'город': city,
        'номер карты': card_number
    }

    return personal_data


def get_favorite_product(session, url):
    products_data = []

    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')

    try:
        products_catalog = soup.find('div', attrs={'id': 'catalog_sect_cont'}).find_all('div', attrs={
            'class': 'main-list__card-item'})
        for product in products_catalog:
            product_name = product.find('a', attrs={'class': 'product-card__title'}).text.strip()
            link = 'https://fix-price.ru' + product.find('a', attrs={'class': 'product-card__title'}).get('href')
            price = product.find('span', attrs={'class': 'badge-price-value'}).get('data-price') + ' руб'

            product_data = {
                'Название': product_name,
                'Ссылка': link,
                'Цена': price
            }

            products_data.append(product_data)
    except:
        products_data = None
    return products_data


def get_promotions(session, url):
    r = session.get(url)
    soup = BeautifulSoup(r.text, 'lxml')
    try:
        user_points_active = soup.find(attrs={'class': 'client-points__active'}).text
        user_points_inactive = soup.find(attrs={'class': 'inactive-points'}).text.strip('+')
    except:
        user_points_active = None
        user_points_inactive = None

    user_point = dict(point_active=user_points_active, point_inactive=user_points_inactive)
    promotions_list = []
    try:
        action_cards = soup.find_all(attrs={'class': 'action-block__item'})
        for action_card in action_cards:
            name = action_card.find(attrs={'class', 'action-card__desc-title'}).text.strip()
            description = action_card.find(attrs={'class': 'action-card__info'}).find('div').text.strip()

            action_items = {
                'Название': name,
                'Описание': description,
            }
            promotions_list.append(action_items)
    except:
        promotions_list = None
    return user_point, promotions_list


def generate_user_data(personal_data, favorite_products, promotions):
    user_data = personal_data
    user_data['активные балы'] = promotions[0]['point_active']
    user_data['неактивные баллы'] = promotions[0]['point_inactive']
    user_data['избранные товары'] = favorite_products
    user_data['акции'] = promotions[1]
    return user_data


def write_json(item):
    dump = json.dumps(item, indent=4, sort_keys=False, ensure_ascii=False)
    with open('Резултат.json', 'w', encoding='utf8') as file:
        file.write(dump)
        file.close()


if __name__ == '__main__':
    login = input('Введите адрес электронной почты или номер телефона в формате: +7xxx xxx xxxx: ')
    password = input('Введите пароль: ')

    session = get_auth(START_URL, AUTH_URL, login, password)
    personal_data = get_personal_data(session, PERSONAL_INFO_URL)
    favorite_products = get_favorite_product(session, FAVORITE_PRODUCTS_URL)
    promotions = get_promotions(session, PROMOTIONS_URL)

    user_data = generate_user_data(personal_data, favorite_products, promotions)
    write_json(user_data)
