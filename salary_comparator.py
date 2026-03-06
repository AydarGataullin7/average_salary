from __future__ import print_function
import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable

MOSCOW_AREA_ID = 4
SJ_RESULTS_PER_PAGE = 100
HH_SEARCH_PERIOD_DAYS = 30
HH_AREA_ID = 1

SALARY_DIVIDER = 2
SALARY_FROM_ONLY_COEFFICIENT = 1.2
SALARY_TO_ONLY_COEFFICIENT = 0.8


def calculate_salary_from_parts(salary_from, salary_to):
    if salary_from and salary_to:
        return (salary_from + salary_to) / SALARY_DIVIDER
    if salary_from:
        return salary_from * SALARY_FROM_ONLY_COEFFICIENT
    if salary_to:
        return salary_to * SALARY_TO_ONLY_COEFFICIENT
    return None


def predict_rub_salary(salary):
    if not salary:
        return None

    if salary.get('currency') != 'RUR':
        return None

    return calculate_salary_from_parts(
        salary.get('from'),
        salary.get('to')
    )


def predict_rub_salary_for_superJob(vacancy):
    if vacancy.get('currency') != 'rub':
        return None

    return calculate_salary_from_parts(
        vacancy.get('payment_from'),
        vacancy.get('payment_to')
    )


def fetch_sj_language_stats(language, api_key_sj):
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": api_key_sj}
    params = {
        "keyword": f"Программист {language}",
        "town": MOSCOW_AREA_ID,
        "count": SJ_RESULTS_PER_PAGE
    }

    page = 0
    salaries = []
    total_found = 0
    has_more = True

    while has_more:
        params['page'] = page
        response = requests.get(url, headers=headers, params=params)
        data = response.json()

        if page == 0:
            total_found = data['total']

        for vacancy in data["objects"]:
            salary = predict_rub_salary_for_superJob(vacancy)
            if salary:
                salaries.append(salary)

        has_more = data['more']
        page += 1

    processed = len(salaries)
    if processed:
        average_salary = int(sum(salaries) / processed)
    else:
        average_salary = None

    return {
        'total_found': total_found,
        'vacancies_processed': processed,
        'average_salary': average_salary
    }


def fetch_hh_language_stats(language):
    base_url = "https://api.hh.ru/vacancies"
    params = {
        'text': f"Программист {language}",
        'search_field': 'name',
        'period': HH_SEARCH_PERIOD_DAYS,
        'area': HH_AREA_ID
    }

    page = 0
    pages_number = 1
    salaries = []
    total_found = 0

    while page < pages_number:
        params['page'] = page
        response = requests.get(base_url, params=params)
        data = response.json()

        if page == 0:
            total_found = data['found']
            pages_number = data['pages']

        for vacancy in data['items']:
            salary = predict_rub_salary(vacancy['salary'])
            if salary:
                salaries.append(salary)

        page += 1

    processed = len(salaries)
    if processed:
        average_salary = int(sum(salaries) / processed)
    else:
        average_salary = None

    return {
        'vacancies_found': total_found,
        'vacancies_processed': processed,
        'average_salary': average_salary
    }


def get_sj_stats(languages, api_key_sj):
    sj_language_stats = {}
    for language in languages:
        sj_language_stats[language] = fetch_sj_language_stats(
            language, api_key_sj)
    return sj_language_stats


def get_hh_stats(languages):
    hh_language_stats = {}
    for language in languages:
        hh_language_stats[language] = fetch_hh_language_stats(language)
    return hh_language_stats


def build_table(stats, title, found_key, processed_key, salary_key):
    table_data = [('Язык программирования', 'Вакансий найдено',
                   'Вакансий обработано', 'Средняя зарплата')]
    for lang, data in stats.items():
        table_data.append((
            lang,
            data[found_key],
            data[processed_key],
            data[salary_key]
        ))
    return AsciiTable(table_data, title)


def main():
    load_dotenv()
    api_key_sj = os.getenv("API_KEY_SJ")
    languages = ["Python", "Java", "JavaScript", "C++", "C#", "PHP", "Go",
                 "Ruby", "Swift", "TypeScript"]

    sj_stats = get_sj_stats(languages, api_key_sj)
    hh_stats = get_hh_stats(languages)

    sj_table = build_table(sj_stats, 'SuperJob Moscow',
                           'total_found', 'vacancies_processed', 'average_salary')
    hh_table = build_table(hh_stats, 'HeadHunter Moscow',
                           'vacancies_found', 'vacancies_processed', 'average_salary')

    print(sj_table.table)
    print()
    print(hh_table.table)


if __name__ == '__main__':
    main()
