from __future__ import print_function
import requests
import os
from dotenv import load_dotenv
from terminaltables import AsciiTable


def predict_rub_salary(salary):
    if salary is None:
        return None

    salary_from = salary.get('from')
    salary_to = salary.get('to')

    if salary.get('currency') != 'RUR':
        return None

    if salary_from is not None and salary_to is not None:
        average_salary = (salary_from+salary_to)/2
    elif salary_from is not None:
        average_salary = salary_from * 1.2
    elif salary_to is not None:
        average_salary = salary_to * 0.8
    else:
        return None

    return average_salary


def predict_rub_salary_for_superJob(vacancy):
    salary_from = vacancy.get('payment_from')
    salary_to = vacancy.get('payment_to')

    if vacancy.get('currency') != 'rub':
        return None

    if salary_from is not None and salary_to is not None:
        average_salary = (salary_from+salary_to)/2
    elif salary_from is not None:
        average_salary = salary_from * 1.2
    elif salary_to is not None:
        average_salary = salary_to * 0.8
    else:
        return None
    return average_salary


def make_table_for_sj(languages):
    API_KEY_SJ = os.getenv("API_KEY_SJ")
    url = "https://api.superjob.ru/2.0/vacancies/"
    headers = {"X-Api-App-Id": API_KEY_SJ}
    results_sj = {}

    for language in languages:
        params = {"keyword": f"Программист {language}",
                  "town": 4, "count": 100}

        page = 0
        pages_number = 1
        salaries = []

        while page < pages_number:
            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if page == 0:
                total_found = data['total']
                number_of_pages = 100
                pages_number = (total_found + number_of_pages -
                                1) // number_of_pages

            for vacancy in data["objects"]:
                salary = predict_rub_salary_for_superJob(vacancy)
                if salary is not None:
                    salaries.append(salary)

            page += 1

        processed = len(salaries)
        if processed > 0:
            average_salary = int(sum(salaries)/processed)
        else:
            average_salary = None

        results_sj[language] = {
            'vacancies_processed': processed,
            'average_salary': average_salary,
            'total_found': total_found
        }
    table_data = []
    table_data.append(('Язык программирования', 'Вакансий найдено',
                      'Вакансий обработано', 'Средняя зарплата'))

    for programming_language in results_sj:
        data_for_table = results_sj[programming_language]
        table_data.append((programming_language, data_for_table['total_found'],
                          data_for_table['vacancies_processed'], data_for_table['average_salary']))

    title = 'SuperJob Moscow'
    table_for_sj = AsciiTable(table_data, title)
    return table_for_sj


def make_table_for_hh(languages):
    results = {}

    for language in languages:
        url = f"https://api.hh.ru/vacancies?text=Программист {language}&search_field=name&period=30&area=1"
        page = 0
        pages_number = 1
        salaries = []

        while page < pages_number:
            response = requests.get(url, params={'page': page})
            data = response.json()

            if page == 0:
                pages_number = data['pages']
                total_found = data['found']

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

        results[language] = {
            "vacancies_found": total_found,
            "vacancies_processed": processed,
            "average_salary": average_salary
        }
    table_data = []
    table_data.append(('Язык программирования', 'Вакансий найдено',
                      'Вакансий обработано', 'Средняя зарплата'))

    for programming_language in results:
        data_for_table = results[programming_language]
        table_data.append((programming_language, data_for_table['vacancies_found'],
                          data_for_table['vacancies_processed'], data_for_table['average_salary']))

    title = 'HeadHunter Moscow'
    table_for_hh = AsciiTable(table_data, title)
    return table_for_hh


def main():
    load_dotenv()
    languages = ["Python", "Java", "JavaScript", "C++", "C#", "PHP", "Go",
                 "Ruby", "Swift", "TypeScript"]
    sj_table = make_table_for_sj(languages)
    head_hunter = make_table_for_hh(languages)
    print(sj_table.table)
    print()
    print(head_hunter.table)


if __name__ == '__main__':
    main()
