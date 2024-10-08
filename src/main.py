import logging
import re
from urllib.parse import urljoin

import requests_cache
from bs4 import BeautifulSoup
from tqdm import tqdm

from configs import configure_argument_parser, configure_logging
from constants import (BASE_DIR, COUNT_STATUS, EXPECTED_STATUS, MAIN_DOC_URL,
                       PEP_URL)
from outputs import control_output
from utils import find_tag, get_response


def pep(session):
    response = get_response(session, PEP_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')
    main_section = find_tag(soup, 'section', attrs={'id': 'numerical-index'})
    tr_tags = main_section.find_all('tr')
    different_status = []
    for tr_tag in tqdm(tr_tags[1:]):
        status_column = find_tag(tr_tag, 'td')
        external_status = status_column.text[1:]
        pep_link = find_tag(tr_tag, 'a')['href']
        url = urljoin(PEP_URL, pep_link)
        response = get_response(session, url)
        if response is None:
            return
        soup = BeautifulSoup(response.text, 'lxml')
        dl_tag = find_tag(
            soup, 'dl', attrs={'class': 'rfc2822 field-list simple'}
        )
        abbr_tag = find_tag(dl_tag, 'abbr',)
        if abbr_tag.string not in EXPECTED_STATUS[external_status]:
            different_status.append(
                '''
                Несовпадающие статусы:
                {url}
                Статус в карточке: {status}
                Ожидаемые статусы: {expect_status}
                '''.format(
                    url=url, status=abbr_tag.string,
                    expect_status=EXPECTED_STATUS[external_status]
                )
            )
        COUNT_STATUS[abbr_tag.string] += 1
    logging.info('\n'.join(different_status))
    results = [('Статус', 'Количество')]
    results.extend(COUNT_STATUS.items())
    results.append(('Total', sum(COUNT_STATUS.values())))
    return results


def whats_new(session):
    whats_new_url = urljoin(MAIN_DOC_URL, 'whatsnew/')
    response = get_response(session, whats_new_url)
    if response is None:
        return
    soup = BeautifulSoup(response.text, features='lxml')
    main_div = find_tag(soup, 'section', attrs={'id': 'what-s-new-in-python'})
    div_with_ul = find_tag(main_div, 'div', attrs={'class': 'toctree-wrapper'})
    sections_by_python = div_with_ul.find_all(
        'li', attrs={'class': 'toctree-l1'}
    )

    results = [('Ссылка на статью', 'Заголовок', 'Редактор, автор')]

    for section in tqdm(sections_by_python):
        version_a_tag = find_tag(section, 'a')

        href = version_a_tag['href']
        version_link = urljoin(whats_new_url, href)

        response = get_response(session, version_link)
        if response is None:
            return

        soup = BeautifulSoup(response.text, features='lxml')

        h1 = find_tag(soup, 'h1')
        dl = find_tag(soup, 'dl')
        dl_text = dl.text.replace('\n', ' ')

        results.append(
            (version_link, h1.text, dl_text)
        )

    return results


def latest_versions(session):
    response = get_response(session, MAIN_DOC_URL)
    if response is None:
        return
    soup = BeautifulSoup(response.text, 'lxml')

    sidebar = find_tag(soup, 'div', attrs={'class': 'sphinxsidebarwrapper'})
    ul_tags = sidebar.find_all('ul')

    for ul in ul_tags:
        if 'All version' in ul.text:
            a_tags = ul.find_all('a')
            break
    else:
        raise Exception('Ничего не нашлось')
    results = []

    pattern = r'Python (?P<version>\d\.\d+) \((?P<status>.*)\)'
    for a_tag in a_tags:
        link = a_tag['href']
        text_match = re.search(pattern, a_tag.text)
        if text_match is not None:
            version, status = text_match.groups()
        else:
            version, status = a_tag.text, ''
        results.append(
            (link, version, status)
        )

    return results


def download(session):
    downloads_url = urljoin(MAIN_DOC_URL, 'download.html')
    response = session.get(downloads_url)
    response.encoding = 'utf-8'
    soup = BeautifulSoup(response.text, 'lxml')
    main_tag = find_tag(soup, 'div', attrs={'role': 'main'})
    table_tag = find_tag(main_tag, 'table', attrs={'class': 'docutils'})
    pdf_a4_tag = find_tag(
        table_tag, 'a', {'href': re.compile(r'.+pdf-a4\.zip$')}
    )
    pdf_a4_link = pdf_a4_tag['href']
    archive_url = urljoin(downloads_url, pdf_a4_link)
    file_name = archive_url.split('/')[-1]
    downloads_dir = BASE_DIR / 'downloads'
    downloads_dir.mkdir(exist_ok=True)
    archive_path = downloads_dir / file_name
    response = session.get(archive_url)
    with open(archive_path, 'wb') as file:
        file.write(response.content)
    logging.info(f'Архив был загружен и сохранён: {archive_path}')


MODE_TO_FUNCTION = {
    'latest-versions': latest_versions,
    'whats-new': whats_new,
    'download': download,
    'pep': pep,
}


def main():
    configure_logging()
    logging.info('Парсер запущен!')
    arg_parser = configure_argument_parser(MODE_TO_FUNCTION.keys())
    args = arg_parser.parse_args()
    logging.info(f'Аргументы командной строки {args}')
    session = requests_cache.CachedSession()
    if args.clear_cache:
        session.cache.clear()
    parse_mode = args.mode
    results = MODE_TO_FUNCTION[parse_mode](session)

    if results is not None:
        control_output(results, args)

    logging.info('Парсер завершил работу!')


if __name__ == '__main__':
    main()
