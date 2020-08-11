import time
import wget
import os
import re
import logging

from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.chrome.options import Options
from sys import argv
import configparser

header = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Accept': '*/*'}

chrome_options = Options()
chrome_options.add_argument('start-maximized')
# на всякий случай, без этого могло упасть по timeout:
chrome_options.add_argument('enable-features=NetworkServiceInProcess')
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome('./chromedriver', options=chrome_options)

# Чтение конфига
config = configparser.ConfigParser()  # создаём объекта парсера
config.read("config.ini")  # читаем конфиг
time_wanted = (config["keys"]["time_wanted"])
name = (config["keys"]["name"])
organization = (config["keys"]["organization"])
phone = (config["keys"]["phone"])
addr = (config["keys"]["addr"])
email = (config["keys"]["email"])
room = (config["keys"]["room"])
reverse_day_order = (config["keys"]["reverse_day_order"])

url = f'https://www.kurgan-city.ru/gosserv/prerecord/?ROOM_ID={room}'

times_list = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00',
              '14:30', '15:00', '15:30']


def parse_room(room_url):
    driver.get(room_url)

    # Сохраняем список URLs на марки:
    free_dates = driver.find_elements_by_class_name('view-month-calendar-day-have-free-slots')
    logging.info(f'Marks count: {len(free_dates)}')
    day_urls = []  # каждый URL ведет на конкретную дату
    for i in range(len(free_dates)):
        # mark_name = marks_urls_blocks[i].text
        day_link = free_dates[i].find_element_by_class_name('view-month-calendar-day-link')
        day_url = day_link.get_attribute('href')
        day_urls.append(day_url)

    return day_urls


def parse_day(day_url):
    driver.get(day_url)

    times = driver.find_elements_by_class_name('day-hour')
    record_urls = {}
    for time in times:
        record = {}
        time_clock = time.find_element_by_class_name('day-hour-time').text
        time_link = None
        try:
            time_link = time.find_element_by_class_name('add-record')
        except:
            pass
        if time_link:
            record_urls[time_clock] = time_link.get_attribute('href')
        # records.append(record)

    return record_urls


def parse_record(record_url, submission):
    driver.get(record_url)

    driver.find_element_by_id('record-name').send_keys(name)
    driver.find_element_by_id('record-organization').send_keys(organization)
    driver.find_element_by_id('record-phone').send_keys(phone)
    driver.find_element_by_id('record-addr').send_keys(addr)
    driver.find_element_by_id('record-email').send_keys(email)
    if submission:
        driver.find_element_by_id('record-email').submit()


if __name__ == "__main__":

    script, if_submit = argv
    submission = False
    if if_submit == 'submit':
        submission = True

    # вынимаем URl доступных дней из комнаты
    day_urls = parse_room(url)

    # Если в конфиге revers day order, меняем порядок дней, чтобы начать перебор с последнего
    if reverse_day_order == True:
        day_urls.reverse()

    # TBD алгоритм неидеален, стоит переработать, если будет время
    # для кадого доступного дня перебираем его талоны:
    for day_url in day_urls:
        # маркер того, что еще не записались:
        done = False
        # список доступных записей дня:
        records = parse_day(day_url)

        # ищем желаемое время среди списка талонов:
        while time_wanted not in records:
            # узнаем индекс времени из списка времен:
            pos_in_list = times_list.index(time_wanted)
            # пробуем взять следующее время из списка времен?
            try:
                next_pos = pos_in_list + 1
                time_wanted = times_list[next_pos]
            #если не получилось, значит, прошли весь день и не нашли ни одного талона:
            except IndexError:
                # сбрасываем значение времени на желаемое:
                time_wanted = (config["keys"]["time_wanted"])
                break
            except KeyError:
                time_wanted = (config["keys"]["time_wanted"])
                break
        # если желаемое (или большее время) нашлось:
        if time_wanted in records:
            # заполняем форму
            record_url = records[time_wanted]
            parse_record(record_url, submission)
            done = True
        # если не нашлось, идем в следующий день
        else:
            pass

        # если запись удалась, не идем в следующий день, работа окончена:
        if done:
            break
