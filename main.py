import logging

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from sys import argv
from time import sleep
import configparser

header = {
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/84.0.4147.89 Safari/537.36',
    'Accept': '*/*'}

chrome_options = Options()
chrome_options.add_argument('start-maximized')
chrome_options.add_argument('enable-features=NetworkServiceInProcess')
chrome_options.add_argument('--no-sandbox')
driver = webdriver.Chrome('./chromedriver', options=chrome_options)

TIMES_LIST = ['09:00', '09:30', '10:00', '10:30', '11:00', '11:30', '12:00', '12:30', '13:00', '13:30', '14:00',
              '14:30', '15:00', '15:30']


def parse_room(room_url, day_of_month):
    """
    Room scrapping
    :param room_url: url of the room
    :param day_of_month: number of month's day
    :return: list of urls of dates
    """

    driver.get(room_url)

    # getting the list of urls of dates
    free_dates = driver.find_elements_by_class_name('view-month-calendar-day-have-free-slots')

    logging.info(f'Free dates count: {len(free_dates)}')

    day_urls = []  # every url is for specific date
    for i in range(len(free_dates)):
        # mark_name = marks_urls_blocks[i].text
        if day_of_month:
            day_number = free_dates[i].find_element_by_class_name('view-month-calendar-day-date')
            day_number = int(day_number.text)
            if day_number == day_of_month:
                take = True
            else:
                take = False
        else:
            take = True

        if take:
            day_link = free_dates[i].find_element_by_class_name('view-month-calendar-day-link')
            day_url = day_link.get_attribute('href')
            day_urls.append(day_url)

    return day_urls


def parse_day(day_url):
    """
    Date scrapping
    :param day_url: url of date
    :return: list of bookings
    """

    driver.get(day_url)
    times = driver.find_elements_by_class_name('day-hour')

    record_urls = {}
    for time in times:
        time_clock = time.find_element_by_class_name('day-hour-time').text
        time_link = None
        try:
            time_link = time.find_element_by_class_name('add-record')
        except:
            pass
        if time_link:
            record_urls[time_clock] = time_link.get_attribute('href')

    return record_urls


def parse_record(record_url, submission):
    """
    Scrapping og booking
    :param record_url: url for booking
    :param submission: mode
    :return: None
    """

    driver.get(record_url)

    driver.find_element_by_id('record-name').send_keys(name)
    driver.find_element_by_id('record-organization').send_keys(organization)
    driver.find_element_by_id('record-phone').send_keys(phone)
    driver.find_element_by_id('record-addr').send_keys(addr)
    driver.find_element_by_id('record-email').send_keys(email)

    if submission:
        driver.find_element_by_id('record-email').submit()


if __name__ == "__main__":

    done = False
    while done is not True:

        script, if_submit, configname = argv

        # For testing:
        # if_submit = False
        # configname = 'config.ini'

        # getting values from config file
        config = configparser.ConfigParser()
        config.read(configname, encoding='utf-8')
        time_wanted = (config["keys"]["time_wanted"])
        day_of_month = (config["keys"]["data"])
        name = (config["keys"]["name"])
        organization = (config["keys"]["organization"])
        phone = (config["keys"]["phone"])
        addr = (config["keys"]["addr"])
        email = (config["keys"]["email"])
        room = (config["keys"]["room"])
        reverse_day_order = (config["keys"]["reverse_day_order"])
        timeout = int((config["keys"]["timeout"]))

        url = f'https://www.kurgan-city.ru/gosserv/prerecord/?ROOM_ID={room}'

        submission = False
        if if_submit == 'submit':
            submission = True

        # getting date urls from room page
        day_urls = parse_room(url, day_of_month)

        if len(day_urls) == 0:
            sleep(timeout)

        if reverse_day_order:
            day_urls.reverse()

        # TBD refactor this algorithm in the future (not ideal)
        # going through booking for each available date
        for day_url in day_urls:
            done = False
            records = parse_day(day_url)

            # looking for desired time
            while time_wanted not in records:
                # getting the index of desired time
                pos_in_list = TIMES_LIST.index(time_wanted)
                # getting the next time from the list of times
                try:
                    next_pos = pos_in_list + 1
                    time_wanted = TIMES_LIST[next_pos]
                except IndexError:
                    # no one booking has been find
                    # setting the time value to the desired
                    time_wanted = (config["keys"]["time_wanted"])
                    break
                except KeyError:
                    time_wanted = (config["keys"]["time_wanted"])
                    break

            if time_wanted in records:  # if desired (or neighboring) time has been found
                # filling the web form
                record_url = records[time_wanted]
                parse_record(record_url, submission)
                done = True
            else:
                # going to the next date
                pass

            # if booking has been done, finish
            if done:
                break
