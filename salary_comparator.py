from __future__ import print_function
import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable

load_dotenv()

MOSCOW_AREA_ID = 4
SJ_RESULTS_PER_PAGE = 100
HH_SEARCH_PERIOD_DAYS = 30
HH_AREA_ID = 1

SALARY_DIVIDER = 2
SALARY_FROM_ONLY_COEFFICIENT = 1.2
SALARY_TO_ONLY_COEFFICIENT = 0.8


def calculate_salary_from_parts(salary_from, salary_to):
    if salary_from is not None and salary_to is not None:
        return (salary_from + salary_to) / SALARY_DIVIDER
    elif salary_from is not None:
        return salary_from * SALARY_FROM_ONLY_COEFFICIENT
    elif salary_to is not None:
        return salary_to * SALARY_TO_ONLY_COEFFICIENT
    else:
        return None


def predict_rub_salary(salary):
    if salary is None:
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
            if salary is not None:
                salaries.append(salary)

        has_more = data['more']
        page += 1

    processed = len(salaries)
    if processed > 0:
        average_salary = int(sum(salaries) / processed)
    else:
        average_salary = None

    return {
        'total_found': total_found,
        'vacancies_processed': processed,
        'average_salary': average_salary
    }


def fetch_hh_language_stats(language):
    url = f"https://api.hh.ru/vacancies?text=Программист {language}&search_field=name&period={HH_SEARCH_PERIOD_DAYS}&area={HH_AREA_ID}"
    page = 0
    pages_number = 1
    salaries = []
    total_found = 0

    while page < pages_number:
        response = requests.get(url, params={'page': page})
        data = response.json()

        if page == 0:
            total_found = data['found']
            pages_number = data['pages']

        for vacancy in data['items']:
            salary = predict_rub_salary(vacancy['salary'])
            if salary is not None:
                salaries.append(salary)

        page += 1

    processed = len(salaries)
    if processed > 0:
        average_salary = int(sum(salaries) / processed)
    else:
        average_salary = None

    return {
        'vacancies_found': total_found,
        'vacancies_processed': processed,
        'average_salary': average_salary
    }


def make_table_for_sj(languages, api_key_sj):
    results_sj = {}
    for language in languages:
        results_sj[language] = fetch_sj_language_stats(language, api_key_sj)

    table_data = [('Язык программирования', 'Вакансий найдено',
                   'Вакансий обработано', 'Средняя зарплата')]
    for lang, stats in results_sj.items():
        table_data.append(
            (lang, stats['total_found'], stats['vacancies_processed'], stats['average_salary']))

    return AsciiTable(table_data, 'SuperJob Moscow')


def make_table_for_hh(languages):
    results = {}
    for language in languages:
        results[language] = fetch_hh_language_stats(language)

    table_data = [('Язык программирования', 'Вакансий найдено',
                   'Вакансий обработано', 'Средняя зарплата')]
    for lang, stats in results.items():
        table_data.append(
            (lang, stats['vacancies_found'], stats['vacancies_processed'], stats['average_salary']))

    return AsciiTable(table_data, 'HeadHunter Moscow')


def main():
    api_key_sj = os.getenv("API_KEY_SJ")
    languages = ["Python", "Java", "JavaScript", "C++", "C#", "PHP", "Go",
                 "Ruby", "Swift", "TypeScript"]
    sj_table = make_table_for_sj(languages, api_key_sj)
    head_hunter = make_table_for_hh(languages)
    print(sj_table.table)
    print()
    print(head_hunter.table)


if __name__ == '__main__':
    main()
