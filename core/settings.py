import logging

# Логирование
LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)

# URL для поиска в целевом регионе (Москва и МО)
AVITO_BASE_URL = "https://avito.ru/moskva_i_mo"


SELECTORS = {
    # Интерфейс поиска
    "search_input": 'input[data-marker="search-form/suggest/input"]',
    "search_button": 'button[data-marker="search-form/submit-button"]',
    "filter_new_checkbox": 'label[data-marker="params[110056]/option(418153)"]', 
    "apply_filters_button": 'button[data-marker="search-filters/submit-button"]',
    
    # Карточка объявления и её внутренности
    "items_block": 'div[data-marker="catalog-serp"]',
    "item_card": 'div[data-marker="item"]',
    "title_link": 'a[data-marker="item-title"]',
    "price": 'meta[itemprop="price"]',
    "location": 'div[data-marker="item-location"]',
    "condition": 'div[data-marker="iva-item/2969"]', 
}
