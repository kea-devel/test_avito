import json
import logging
import asyncio
import pandas as pd
from core.cli import parse_arguments
from core.fetcher import fetch_online_html, load_offline_html, AvitoBlockException
from core.parser import parse_avito_html, parse_avito_json_data, get_json_from_script
from core.transform import process_and_filter_data, generate_error_row

logger = logging.getLogger(__name__)

async def main():
    args = parse_arguments()
    all_raw_data = []
    failed_skus = []
    
    # Определяем, какой файл конфигурации читать
    config_path = args.offline_config if args.offline_config else args.online_config
    
    logger.info(f"Чтение файла конфигурации: {config_path}")
    
    with open(config_path, "r", encoding="utf-8") as f:
        tasks = json.load(f)
        
    # ---- offline (-f tasks.json) ----
    if args.offline_config:
        logger.info("Запущен offline режим (парсинг локальных файлов)")
        for task in tasks:
            sku = task.get("sku")
            file_path = task.get("file")
            query = f"Offline-файл: {file_path}"
            
            if not file_path:
                logger.error(f"Для артикула {sku} не указан путь к файлу ('file') в JSON.")
                failed_skus.append(generate_error_row(sku, query, "ошибка: не указан файл"))
                continue
                
            try:
                html_content = await load_offline_html(file_path)

                #Так как это оффлайн поиск, можно получить json из html-файла и работать с ним. 
                data_json = get_json_from_script(html_content)
                items = parse_avito_json_data(data_json,sku,query)
                
                # items = parse_avito_html(html_content, sku, query)
                if not items:
                    failed_skus.append(generate_error_row(sku, query, "не найдено"))
                else:
                    all_raw_data.extend(items)
            except Exception as e:
                logger.error(f"Ошибка оффлайн обработки артикула {sku}: {e}")
                failed_skus.append(generate_error_row(sku, query, f"ошибка: {str(e)}"))

    # ---- online (-o tasks.json) ----
    elif args.online_config:
        logger.info("Запущен ОНЛАЙН режим")
        for task in tasks:
            sku = task.get("sku")
            query = f"Oline поиск SKU: {sku}"
            
            try:
                html_content = await fetch_online_html(sku)

                with open("html_page.html", "w", encoding="utf-8") as file:
                    file.write(html_content)
                
                items = parse_avito_html(html_content, sku, query)
                if not items:
                    failed_skus.append(generate_error_row(sku, query, "не найдено"))
                else:
                    all_raw_data.extend(items)
                    
            except AvitoBlockException:
                print("\n" + "!"*75 + 
                      f"\n[АНТИ-ФРОД БЛОКИРОВКА]: Живой запрос для артикула {sku} заблокирован."
                      "\nРекомендуется скачать HTML выдачи вручную и запустить оффлайн-режим:"
                      "\nuv run main.py -f tasks.json"
                      "\nили без uv"
                      "\npython main.py -f tasks.json"
                      "\n" + "!"*75 + "\n")
                failed_skus.append(generate_error_row(sku, query, "ошибка: заблокировано защитой Avito"))
            except Exception as e:
                failed_skus.append(generate_error_row(sku, query, f"ошибка сети/UI: {str(e)}"))

    # ---- Обрабатываем в Pandas и сохраняем в excel ----
    final_df = process_and_filter_data(all_raw_data)
    
    if failed_skus:
        error_df = pd.DataFrame(failed_skus)
        final_df = pd.concat([final_df, error_df], ignore_index=True)

    if not final_df.empty:
        output_file = "result.xlsx"
        columns_order = [
            "искомый артикул", "поисковый запрос", "заголовок", "цена",
            "город или регион", "состояние товара", "ссылку на объявление",
            "место по цене", "дата и время проверки"
        ]
        final_df = final_df.reindex(columns=columns_order)
        final_df.to_excel(output_file, index=False)
        logger.info(f"Пайплайн завершен. Создан файл: {output_file}")
    else:
        logger.warning("Нет данных для записи в Excel.")

if __name__ == "__main__":
    asyncio.run(main())
