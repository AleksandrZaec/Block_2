import io
import pandas as pd
import requests
from datetime import datetime
import time
from bs4 import BeautifulSoup
from database import Session, BaseModel, engine
from models import SpimexTradingResult
import numpy as np

BASE_URL = "https://spimex.com"
RESULTS_URL = "https://spimex.com/markets/oil_products/trades/results/"


def get_reports():
    """Получаем все ссылки на отчеты с сайта с 2023 года"""
    response = requests.get(RESULTS_URL)
    soup = BeautifulSoup(response.text, "lxml")
    pages = soup.find("div", {"class": "bx-pagination"}).find_all("a")
    number_of_pages = int(pages[-2].find("span").text)

    reports = []
    for page in range(1, number_of_pages + 1):
        print(f"Processing page: {page}")
        url = f"{RESULTS_URL}?page=page-{page}"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, "lxml")
        links = soup.find_all("a", {"class": "accordeon-inner__item-title link xls"}, limit=10)
        links = [link['href'] for link in links]
        for link in links:
            try:
                if int(link.split("oil_xls_")[1][:4]) < 2023:
                    return reports
                reports.append(link)
            except Exception as e:
                print(e)

    return reports


def process_report(url):
    """Скачиваем отчет по ссылке в ОЗУ, затем записываем данные в датафрейм"""
    response = requests.get(BASE_URL + url)
    response.raise_for_status()

    report_date_str = url.split("oil_xls_")[1][:8]
    report_date = datetime.strptime(report_date_str, '%Y%m%d').date()
    print(f"Processing report: {report_date}")

    data = io.BytesIO(response.content)

    xls = pd.ExcelFile(data)
    sheet_name = 'TRADE_SUMMARY' if 'TRADE_SUMMARY' in xls.sheet_names else xls.sheet_names[0]
    df = pd.read_excel(data, sheet_name=sheet_name, header=None)
    start_row = df[df[1].str.contains('Единица измерения: Метрическая тонна', na=False)].index[0] + 2
    headers = df.iloc[start_row].values
    df = pd.read_excel(data, sheet_name=sheet_name, header=start_row + 1)
    df = df[df.iloc[:, -1] != "-"]
    df = df.dropna(subset=[df.columns[0], df.columns[1], df.columns[2]])
    numeric_cols = [3, 4, -1]
    for col in numeric_cols:
        df[df.columns[col]] = df[df.columns[col]].replace("-", np.nan)

    return df, report_date


def write_to_db(dataframe, report_date):
    """Пишем отчет в базу данных"""
    print(f"Writing to DB: {report_date}")
    records = []

    for _, row in dataframe.iterrows():
        try:
            volume = int(row.iloc[3]) if pd.notna(row.iloc[3]) else None
            total = int(row.iloc[4]) if pd.notna(row.iloc[4]) else None
            count = int(row.iloc[-1]) if pd.notna(row.iloc[-1]) else None

            exchange_product_id = str(row.iloc[0])
            oil_id = exchange_product_id[:4]
            delivery_basis_id = exchange_product_id[4:7] if len(exchange_product_id) >= 7 else None
            delivery_type_id = exchange_product_id[-1] if len(exchange_product_id) >= 1 else None

            records.append(SpimexTradingResult(
                exchange_product_id=exchange_product_id,
                exchange_product_name=str(row.iloc[1]),
                oil_id=oil_id,
                delivery_basis_id=delivery_basis_id,
                delivery_basis_name=str(row.iloc[2]),
                delivery_type_id=delivery_type_id,
                volume=volume,
                total=total,
                count=count,
                date=report_date
            ))
        except Exception as e:
            print(f"Error processing row: {row}. Error: {e}")
            continue

    try:
        session = Session()
        session.add_all(records)
        session.commit()
    except Exception as e:
        session.rollback()
        print(f"Error committing to DB: {e}")
    finally:
        session.close()


if __name__ == "__main__":
    start_time = time.time()
    BaseModel.metadata.create_all(bind=engine)
    reports = get_reports()
    for report in reports:
        try:
            df, date = process_report(report)
            write_to_db(df, date)
        except Exception as e:
            print(f"Error processing report {report}: {e}")
            continue

    finish_time = time.time() - start_time
    print(f"Total time: {finish_time} seconds")
