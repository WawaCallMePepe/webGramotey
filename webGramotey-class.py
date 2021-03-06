from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
import requests
import time

LOGIN, PASSWORD = ('y000000', '0000')
driver = Chrome()


class MyError(Exception):
    def __init__(self, text):
        self.text = text


class Web(object):
    """ Description """

    def __init__(self, login, password, exerciseNumber=0, continueWork=False):
        self._login = login
        self._password = password
        self._exerciseNumber = exerciseNumber
        self._continueWork = continueWork
        self._mistakeExist = False

    def _get_soup(self):
        self._soup = BeautifulSoup(driver.page_source, 'html.parser')
        return self._soup

    def _get_statistics(self):
        print(self._yourName)
        print(self._exerciseInfo[self._exerciseNumber][0])
        self._wordsDone = self._exerciseInfo[self._exerciseNumber][2][0]
        self._wordsLeft = self._exerciseInfo[self._exerciseNumber][2][1]
        print(f'Выполнено: {self._wordsDone}/{self._wordsLeft}')

    def _get_word_info(self):
        if self._mistakeExist:
            print('(ошибка)', end=' ')
            self._mistakeExist = False
        print('')
        print(f'{self._wordsDone}. {self._requestingText}', end=' ')

    def _sign_up(self):
        driver.get("https://login.cerm.ru/login.php")
        time.sleep(0.5)
        elementLogin = driver.find_element_by_name('simora_login')
        elementLogin.send_keys(self._login)
        elementLogin = driver.find_element_by_name('simora_pass')
        elementLogin.send_keys(self._password)
        elementLogin.send_keys(Keys.ENTER)
        if self._get_soup().find('div', {'id': 'error'}):
            raise MyError('Логин или пароль указаны неверно')

    def _select_exercise(self):
        driver.get('https://login.cerm.ru/_user/user_app.php?mod=pwg')
        if self._get_soup().find('div', {'class': 'shadow_for_box red_signal'}):
            raise MyError('Аккаунт заблокирован')
        self._yourName = driver.find_element_by_class_name('content_label').text[20:]
        driver.find_element_by_class_name('inactiveToggle').click()
        exerciseClosed = driver.find_elements_by_class_name('exerciseClosed')
        self._exerciseInfo = []
        for exercise in exerciseClosed:
            exerciseLink = exercise.find_element_by_tag_name('a')
            exerciseName = exerciseLink.text
            exerciseProgress = exercise.find_element_by_class_name('indicator_label').text.split('/')
            exerciseProgress = [int(i) for i in exerciseProgress]

            self._exerciseInfo.append([exerciseName, exerciseLink, exerciseProgress])

        if not self._get_soup().find('div', {'class': 'exerciseClosed'}):
            raise MyError('Нет такого упражнения (list index out of range)')
        self._exerciseInfo[self._exerciseNumber][1].click()

    def _correct_mistake(self):
        trainer_rno_right = str(self._get_soup().
                                find('div', {'id': 'trainer_rno_right'})). \
            replace('<div id="trainer_rno_right">', ''). \
            replace('</div>', '')
        for i in range(3):
            driver.find_element_by_id('prno').send_keys(trainer_rno_right)
            time.sleep(1)

    def _do_exercise(self):
        variantList = list()
        try:
            driver.find_element_by_class_name('btn_yellow').click()
            time.sleep(1.5)
        except:
            pass
        question = str(self._soup.find('div', {'id': 'trainer_question'}))
        question = question.replace('<div id="trainer_question">', ''). \
            replace('<span class="word_hole"></span>', '^'). \
            replace('</div>', ''). \
            replace('<span>́</span>', '')

        variants = str(self._soup.find('div', {'id': 'trainer_variants'}))
        variants = variants.replace('<div id="trainer_variants"><a class="trainer_variant">', ''). \
            replace('</a><span class="trainer_separator"></span><a class="trainer_variant">', ' '). \
            replace('</a></div>', '').split(' ')

        for i in variants:
            if i == '(раздельно)' or i == '(пробел)':
                variantList.append(' ')
            elif i == '(слитно)' or i == '(ничего)':
                variantList.append('')
            elif i == '(дефис)':
                variantList.append('-')
            else:
                variantList.append(i)

        for i in variantList:
            self._requestingText = question.replace('^', i)
            url = 'https://speller.yandex.net/services/spellservice/checkText?text=' + self._requestingText
            if requests.get(url).text == '<?xml version="1.0" encoding="utf-8"?>\n<SpellResult/>':
                driver.find_elements_by_class_name('trainer_variant')[variantList.index(i)].click()
                variantList.clear()
                time.sleep(1)
                break

    def do_work(self):
        try:
            self._sign_up()
            self._select_exercise()
            self._get_statistics()
            time.sleep(2)
            while self._continueWork or self._wordsDone < self._wordsLeft:

                if self._get_soup().find('div', {'id': 'trainer_rno_right'}):
                    self._correct_mistake()
                    self._mistakeExist = True
                elif self._get_soup().find('div', {'id': 'trainer_variants'}):
                    self._do_exercise()
                    self._get_word_info()
                    self._wordsDone += 1

        except Exception as e:
            print(f'Возникла ошибка: {e}')

        driver.quit()


if __name__ == '__main__':
    Web(login=LOGIN,
        password=PASSWORD,
        exerciseNumber=1231,
        continueWork=False
        ).do_work()

    input('\nНажмите Enter для выхода...')
