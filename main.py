import io
import pandas as pd
import requests
import time
from bs4 import BeautifulSoup
import datetime
from models import SpimexTradingResults
from database import Session, Base, engine

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
                if int(link.split("oil_xls_")[1][:4]) < 2025:
                    return reports
                reports.append(link)
            except Exception as e:
                print(e)

    return reports


def process_report(url):
    """Скачиваем отчет по ссылке в ОЗУ, затем записываем данные в датафрейм"""
    response = requests.get(BASE_URL + url)
    response.raise_for_status()

    report_date = url.split("oil_xls_")[1][:8]
    report_date = datetime.date(int(report_date[:4]), int(report_date[4:6]), int(report_date[6:]))
    print(f"Processing report: {report_date}")

    data = io.BytesIO(response.content)

    start_marker = "Единица измерения: Метрическая тонна"
    end_marker = "Итого:"
    skiprows = None

    with pd.ExcelFile(data) as xls:
        for sheet_name in xls.sheet_names:
            sheet_data = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            try:
                start_row = sheet_data[sheet_data.eq(start_marker).any(axis=1)].index[0]
                skiprows = start_row + 2
                break
            except IndexError:
                continue

    if skiprows is None:
        raise ValueError("Кривой файл excel")

    report_df = pd.read_excel(data, skiprows=skiprows)

    end_row = report_df[report_df.eq(end_marker).any(axis=1)].index[0]
    report_df = report_df.iloc[:end_row]

    report_df = report_df.drop(report_df.columns[0], axis=1)

    report_df = report_df[report_df.iloc[:, -1] != "-"]

    return report_df, report_date


def write_to_db(dataframe, report_date):
    """Пишем отчет в базу данных"""
    print(f"Writing to DB: {report_date}")
    records = []

    for _, row in dataframe.iterrows():

        try:
            exchange_product_id = str(row.iloc[0]).strip()
            exchange_product_name = str(row.iloc[1]).strip()
            delivery_basis_name = str(row.iloc[2]).strip()

            oil_id = exchange_product_id[:4]
            delivery_basis_id = exchange_product_id[4:7]
            delivery_type_id = exchange_product_id[-1]

            try:
                volume_value = int(row.iloc[3]) if pd.notna(row.iloc[3]) else None
            except ValueError:
                volume_value = None

            try:
                total_value = float(row.iloc[4]) if pd.notna(row.iloc[4]) else None
            except ValueError:
                total_value = None

            try:
                count_value = int(row.iloc[-1]) if pd.notna(row.iloc[-1]) else None
            except ValueError:
                count_value = None

            record = SpimexTradingResults(
                exchange_product_id=exchange_product_id,
                exchange_product_name=exchange_product_name,
                oil_id=oil_id,
                delivery_basis_id=delivery_basis_id,
                delivery_basis_name=delivery_basis_name,
                delivery_type_id=delivery_type_id,
                volume=volume_value,
                total=total_value,
                count=count_value,
                date=report_date
            )

            records.append(record)

        except IndexError as e:
            print(f"Ошибка при обработке строки: {e}")
            continue

    session = Session()
    session.add_all(records)
    session.commit()
    session.close()


if __name__ == "__main__":
    start_time = time.time()
    Base.metadata.create_all(bind=engine)
    reports = get_reports()
    for report in reports:
        df, date = process_report(report)
        write_to_db(df, date)

    finish_time = time.time() - start_time
    print(f"Время выполнения: {finish_time} сек.")