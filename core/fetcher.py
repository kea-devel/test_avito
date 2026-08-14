import logging
import os
import random
from playwright.async_api import async_playwright
from core.settings import AVITO_BASE_URL, SELECTORS

logger = logging.getLogger(__name__)

class AvitoBlockException(Exception):
    """Исключение при обнаружении капчи или блокировок (403, 429)."""
    pass

async def load_offline_html(file_path: str) -> str:
    logger.info(f"Инициализация Playwright для артикула: {file_path}")
    logger.error(f"Ошибка получения дааных: {file_path}")
    """Читаем HTML-файла с диска."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Локальный HTML-файл отсутствует: {file_path}")
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

async def fetch_online_html(sku: str) -> str:
    """
    Открываем Avito в браузере Chromium, вбиваем артикул,
    выставляем фильтр 'Новое' и забираем финальный отрендеренный DOM.
    """   
    async with async_playwright() as p:
        # headless=False иначе, скорей всего, будет бан
        browser = await p.chromium.launch(
            headless=False,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-infobars",
                "--window-size=1920,1080"
            ]
        )
        context = await browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        try:
            # Открываем главную страницу (с выставленным регионом)
            await page.goto(AVITO_BASE_URL, wait_until="domcontentloaded", timeout=20000)

            await page.wait_for_timeout(5000)

            # Вводим артикул и жмем enter
            await page.wait_for_selector(SELECTORS["search_input"])
            await page.locator(SELECTORS["search_input"]).press_sequentially(str(sku), delay=random.randint(80, 120))
            await page.wait_for_timeout(random.randint(300,700))            
            await page.locator(SELECTORS["search_input"]).press("Enter")

            await page.wait_for_timeout(random.randint(1000,1300))

            # Выставляем фильтр "Новое"
            new_checkbox = page.locator(SELECTORS["filter_new_checkbox"])        
            await new_checkbox.click()

            # Немного даем времени что бы все подгрузилось
            await page.wait_for_timeout(1400)

            # Забираем код страницы
            html_content = await page.content()
                
            return html_content

        except Exception as err:
            logger.error(f"Ошибка. Нас поймали =(")
            raise err
        finally:
            await browser.close()
