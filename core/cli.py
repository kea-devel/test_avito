import argparse
import os

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Парсер Avito: короткие флаги -o (онлайн) и -f (оффлайн)."
    )
        
    group = parser.add_mutually_exclusive_group(required=True)
    
    group.add_argument(
        "-o", 
        dest="online_config",
        metavar="CONFIG_JSON",
        help="Запустить живой ОНЛАЙН поиск по SKU из указанного JSON файла."
    )
    
    group.add_argument(
        "-f", 
        dest="offline_config",
        metavar="CONFIG_JSON",
        help="Запустить ОФФЛАЙН парсинг локальных HTML файлов из указанного JSON файла."
    )
    
    args = parser.parse_args()
    
    # Проверяем существование файла конфигурации
    target_file = args.online_config or args.offline_config
    if not os.path.exists(target_file):
        parser.error(f"Указанный файл конфигурации не найден: {target_file}")
        
    return args
