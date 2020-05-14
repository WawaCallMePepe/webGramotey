from bs4 import BeautifulSoup
from selenium.webdriver import Chrome
from selenium.webdriver.common.keys import Keys
import requests
import time

"""TODO:
1. оптимизация 
2. soup и def page_load
3. надо бы к словам в скобках добавить (оШЫБКА) если такая есть 
4. а дальше как пойдет

"""

LOGIN, PASSWORD = ('y864280', '4704')  # похуй акк уже мертв
driver = Chrome()


def login(log, password):
    # вот тут логинимся и отправляем данные по ссылке https://login.cerm.ru/login.php
    driver.get("https://login.cerm.ru/login.php")
    time.sleep(0.5)
    element_login = driver.find_element_by_name('simora_login')
    element_login.send_keys(log)
    element_login = driver.find_element_by_name('simora_pass')
    element_login.send_keys(password)
    element_login.send_keys(Keys.ENTER)


def exercise_selection(exercise_number=1):
    driver.get('https://login.cerm.ru/_user/user_app.php?mod=pwg')  # страница с доступными упражнениями
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # нажимаем кнопочку, чтобы увидеть неактивные упражнения
    unactivatedExerciseButton = driver.find_element_by_class_name('inactiveToggle')
    unactivatedExerciseButton.click()

    # выбираем строку с упражнением
    exerciseBarList = driver.find_elements_by_class_name('exerciseClosed')
    exerciseList = []

    # ищем нужные куски этой строки: ссылки на упражнения, прогресс упражнений
    for exerciseClosed in exerciseBarList:
        exerciseLink = exerciseClosed.find_element_by_tag_name('a')  # ссылка на упражнение
        progress = exerciseClosed.find_element_by_class_name('indicator_label').text.split('/')  # текущий прогресс
        progress = [int(i) for i in progress]  # переделываем из букав в цифры
        exerciseList.append([exerciseLink, progress])  # запихиваем все в массив
    #
    print('----------------------------')  # да-да, кто-то использует это уродство для красоты
    print(driver.find_element_by_class_name('content_label').text[20:])  # твое прекрассное имя здесь
    print(exerciseList[exercise_number][0].text)  # название и номер упражнения
    print(f'Выполнено: {exerciseList[exercise_number][1][0]}/{exerciseList[exercise_number][1][1]}')  # проргресс
    print('----------------------------')

    exerciseList[exercise_number][0].click()  # нажимаем на выбранное упражнение
    return exerciseList[exercise_number][1][1] - exerciseList[exercise_number][1][0]  # количество оставшихся слов


def correct_mistake():  # ну тут только дэбилу будет непонятно
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # обрезаем правильный ответ
    trainer_rno_right = str(soup.find('div', {'id': 'trainer_rno_right'})). \
        replace('<div id="trainer_rno_right">', ''). \
        replace('</div>', '')

    # и впихиваем его три раза в строку
    for i in range(3):
        element = driver.find_element_by_id('prno')
        element.send_keys(trainer_rno_right)
        time.sleep(1)  # не трогай а то забанят к хуям (пизда акку, помянем)


def do_exercise():
    b_s = list()  # список вариантов ответов
    try:
        # обход желтой кнопки в начале упражнения
        yellow_button = driver.find_element_by_class_name('btn_yellow')
        yellow_button.click()
        time.sleep(1.5)
    except Exception as NoYellowButton:
        pass  # ее может и не быть так что вот да

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    # обрезаем нужную часть слова с пропуском
    question = str(soup.find('div', {'id': 'trainer_question'}))
    question = question. \
        replace('<div id="trainer_question">', ''). \
        replace('<span class="word_hole"></span>', '^'). \
        replace('</div>', ''). \
        replace('<span>́</span>', '')

    # обрезаем варианты ответов
    variants = str(soup.find('div', {'id': 'trainer_variants'}))
    variants = variants. \
        replace('<div id="trainer_variants"><a class="trainer_variant">', ''). \
        replace('</a><span class="trainer_separator"></span><a class="trainer_variant">', ' '). \
        replace('</a></div>', '').split(' ')

    # варианты ответов в скобках пределываем в "-" " " "" (типа слитно да)
    for i in variants:
        if i == '(раздельно)' or i == '(пробел)':
            b_s.append(' ')
        elif i == '(слитно)' or i == '(ничего)':
            b_s.append('')
        elif i == '(дефис)':
            b_s.append('-')
        else:
            b_s.append(i)  # и добавряем то что осталось

    # соединяем слово с пропуском с вариантами ответов и кидаем в яндекс
    for i in b_s:
        requesting_text = question.replace('^', i)
        url = 'https://speller.yandex.net/services/spellservice/checkText?text=' + requesting_text
        result = requests.get(url).text

        # если пришло вот это \/ \/ \/ выбираем правильный ответ и нажимаем его
        if result == '<?xml version="1.0" encoding="utf-8"?>\n<SpellResult/>':
            element = driver.find_elements_by_class_name('trainer_variant')
            print(f'{requesting_text}')
            element[b_s.index(i)].click()
            b_s.clear()
            time.sleep(1.5)  # не прогай блять оно тебя сожрет
            break


def main():
    try:
        login(LOGIN, PASSWORD)

        # inputLogin = input('LOGIN: ')
        # inputPassword = int(input('PASSWORD: '))
        # login(inputLogin, inputPassword)

        wordsLeft = exercise_selection(int(input('Номер упражнения(0-30): ')))
        wordsDone = 1

        time.sleep(2)

        # ну тут опять все понятно
        while wordsDone <= wordsLeft:
            time.sleep(1)
            soup = BeautifulSoup(driver.page_source, 'html.parser')

            if soup.find('div', {'id': 'trainer_rno_right'}):  # если ошиблись - исправляем
                correct_mistake()
            elif soup.find('div', {'id': 'trainer_variants'}):  # делаем задание и выводим слова
                print(f'{wordsDone}.', end=' ')
                do_exercise()
                wordsDone += 1

    except:
        # мне лень пилить какую либо систему проверки пароля так шо пiхуй, и так сойдет
        print("не робит, либо пароль неправильный либо еще что-то, в душе не ебу")

    driver.quit()  # все пока


if __name__ == '__main__':
    main()
