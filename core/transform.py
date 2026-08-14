import logging
import pandas as pd

logger = logging.getLogger(__name__)

def process_and_filter_data(raw_data: list[dict]) -> pd.DataFrame:
    """Используем pandas для очистки цен, дедупликация и топ-5."""
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)
    
    df = df.dropna(subset=["цена"])
    df["цена"] = pd.to_numeric(df["цена"], errors="coerce")
    df = df.dropna(subset=["цена"])
    df["цена"] = df["цена"].astype(int)

    df = df.drop_duplicates(subset=["искомый артикул", "item_id"])

    df = df.sort_values(by=["искомый артикул", "цена"], ascending=[True, True])

    df["место по цене"] = df.groupby("искомый артикул").cumcount() + 1
    df = df[df["место по цене"] <= 5]

    if "item_id" in df.columns:
        df = df.drop(columns=["item_id"])

    return df

def generate_error_row(sku: str, query: str, status: str) -> dict:
    """Формирует строчку-индикатор ошибки или отсутствия данных для Excel."""
    from datetime import datetime
    return {
        "искомый артикул": sku,
        "поисковый запрос": query,
        "заголовок": status,
        "цена": None,
        "город или регион": None,
        "состояние товара": None,
        "ссылку на объявление": None,
        "место по цене": None,
        "дата и время проверки": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
