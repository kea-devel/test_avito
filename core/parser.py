import logging
from datetime import datetime
from bs4 import BeautifulSoup
from core.settings import SELECTORS
import json

logger = logging.getLogger(__name__)

def parse_avito_html(html_content: str, sku: str, query: str) -> list[dict]:
    """Парсим HTML"""

    soup = BeautifulSoup(html_content, "html.parser")
    parsed_results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Получаем главный каталог карточек
    catalog = soup.select_one(SELECTORS["items_block"])
    if not catalog:
        return []

    # Получаем первый элемент
    first_item = catalog.find("div", {"data-marker": "item"})
    if not first_item:
        return []

    # Собираем элементы до блока похожих товаров.
    items = [first_item]
    for sibling in first_item.find_next_siblings("div"):
        
        # Если у элемента нет нужного дата-маркера
        if sibling.get("data-marker") != "item":
            h2_tag = sibling.find("h2")
            
            # Проверяем, является ли этот блок окончанием выдачи ("Похоже на то...")
            if h2_tag and "похоже" in h2_tag.get_text().lower():
                break  # Конец выдачи, полностью останавливаем цикл
                
            # Если h2 нет, значит это обычный рекламный блок или баннер
            continue

        # Если элемент имеет data-marker="item", добавляем его в список
        items.append(sibling)

    # Обработка отфильтрованных карточек
    for item in items:
        try:
            # Ссылка и название
            title_tag = item.select_one(SELECTORS["title_link"])
            title = title_tag.get_text(strip=True) if title_tag else "Нет заголовка"
            link = "https://avito.ru" + title_tag["href"] if title_tag else "Нет ссылки"
            
            # ID
            item_id = item.get("data-item-id") or link.split("_")[-1]

            # Цена
            price_tag = item.select_one(SELECTORS["price"])
            price_val = price_tag["content"] if price_tag and price_tag.has_attr("content") else None

            # ЛОкация (Город / район)
            loaction_tag = item.select_one(SELECTORS["location"])
            location = loaction_tag.get_text(strip=True) if loaction_tag else "Не указан"

            # Состояние (перестраховываемся, на случай что фильтр не применился)
            condition_tag = item.select_one(SELECTORS["condition"])
            condition = condition_tag.get_text(strip=True).lower() if condition_tag else "новое"

            parsed_results.append({
                "item_id": item_id,
                "искомый артикул": sku,
                "поисковый запрос": query,
                "заголовок": title,
                "цена": price_val,
                "город или регион": location,
                "состояние товара": condition,
                "ссылку на объявление": link,
                "дата и время проверки": timestamp
            })

        except Exception:
            continue

    return parsed_results

def parse_avito_json_data(json_data: dict, sku: str, query: str) -> list[dict]:
    parsed_results = []
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if not json_data:
        return []

    loader_data = json_data.get("loaderData", {})
    data_block = loader_data.get("data", {})
    catalogs = data_block.get("catalog", {})
    items_list = catalogs.get("items", [])
    
    if not items_list:
        return []

    for item in items_list:
        # встретили элемент-разделитель
        if item.get("type") == "placeholder" and "похоже на то" in item.get("title", "").lower():
            break  # Полностью останавливаем сбор товаров

        # Скипаем рекламу
        if item.get("type") != "item":
            continue

        # Собираем список 
        try:
            item_id = item.get("id")
            title = item.get("title", "Нет заголовка")
            
            uri = item.get("urlPath", item.get("url", ""))
            link = f"https://avito.ru{uri}" if uri else "Нет ссылки"
            
            price_info = item.get("priceDetailed", {})
            price_val = price_info.get("value", None)

            location_info = item.get("location", {})
            location = location_info.get("name", "Не указано")
            
            condition = ""
            iva = item.get("iva", {})
            badge_bars = iva.get("BadgeBarStep", [])
            for badge_info in badge_bars:

                badge_payload = badge_info.get("payload", {})
                badges_list = badge_payload.get("badges", [])
            
                has_target_id = any(badge["id"] == 2969 for badge in badges_list)
                if has_target_id:
                    condition = "Новое"
                    continue

            if not condition:
                continue

            
            parsed_results.append({
                "item_id": str(item_id) if item_id else link.split("_")[-1],
                "искомый артикул": sku,
                "поисковый запрос": query,
                "заголовок": title,
                "цена": price_val,
                "город или регион": location,
                "состояние товара": condition,
                "ссылку на объявление": link,
                "дата и время проверки": timestamp
            })

        except Exception as e:
            logger.error(f"Ошибка обработки JSON: {e}")
            continue

    return parsed_results

def get_json_from_script(html_content: str) -> dict:
    """Извлекаем json из html"""
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Ищем скрипт строго по атрибуту data-mfe-state="true"
    script_tag = soup.find("script", attrs={"data-mfe-state": "true"})
    
    if not script_tag:
        print("Скрипт с данными data-mfe-state='true' не найден.")
        return {}
        
    # Получаем чистый текст из тега
    script_text = script_tag.get_text(strip=True)
    if not script_text:
        print("Тег скрипта пустой.")
        return {}
        
    # Декодируем чистый JSON
    try:
        data = json.loads(script_text)
        return data
    except json.JSONDecodeError as e:
        print(f"Ошибка при чтении JSON из скрипта: {e}")
        return {}

    