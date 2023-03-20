from config import tg_bot_token
import datetime
from aiogram import Bot, types
from aiogram.dispatcher import Dispatcher
from aiogram.utils import executor
from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
import os
import json
import urllib.request
import pytesseract
from PIL import Image
import pprint

bot = Bot(token=tg_bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start"])
async def star_comand(message: types.Message):
    await message.reply("Привет! Я выгружаю с авито объявления по поиску земли по Ярославскому шоссе до 10 соток и до "
                        "2 млн. рублей. Напиши сколько последних объявлений (от 2 до 50) выгрузить и увидишь результат")


@dp.message_handler()
async def get_avito_ad(message: types.Message):
    """
        :param message:
        :param url: url from avito.ru with optins for search
        :return:  json and csv files included ad information from avito.ru
        """

    try:
        numbers_of_ads = int(message.text)
        await message.reply("Начинаю выгружать данные...")
        url = "https://www.avito.ru/moskovskaya_oblast/zemelnye_uchastki/prodam/izhs-ASgBAQICAUSWA9oQAUCmCBTmVQ?f=" \
              "ASgBAQECAUSWA9oQAUCmCBTmVQNFlAkZeyJmcm9tIjoxNDM4NCwidG8iOjE0Mzg3fbgTGHsiZnJvbSI6bnVsbCwidG8iOjE0NDU0fc" \
              "aaDBd7ImZyb20iOjAsInRvIjoyMDAwMDAwfQ&moreExpensive=1&road=32&s=104"
        # Текущее время для названия файла
        cur_time = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
        # options
        options = webdriver.ChromeOptions()
        options.add_argument("window-size=1200x600")
        # use-agent
        options.add_argument("user-agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
                             " AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36")
        # disable webdriver mode
        options.add_argument("--disable-blink-features=AutomationControlled")
        # headless mode
        options.add_argument("--headless")

        driver = webdriver.Chrome(
            executable_path="/Users/maxr/PycharmProjects/chromedriver/chromedriver",
            options=options
        )

        # Создаем словарь для данных из оъявлений
        ad_dict = []

        try:
            driver.get(url=url)
            driver.implicitly_wait(5)
            # Объект поиска объявлений
            ad_search_title = driver.find_element(By.CSS_SELECTOR, 'div [data-marker="page-title/text"]').text
            # Все объявления на странице
            all_ad_on_page = driver.find_elements(By.CSS_SELECTOR, 'div[data-marker="item"]')
            # Счетчик для нумерации файлов с номером телефона
            count = 0
            for ad in all_ad_on_page[:numbers_of_ads]:
                # Собираем цены в объявлениях потом метод get("content")
                try:
                    ad_price = ad.find_element(By.CSS_SELECTOR, 'meta[itemprop="price"]').get_attribute("content")
                except:
                    ad_price = "Нет цены в объявлении"

                # Собираем url объявлений
                try:
                    ad_url = ad.find_element(By.CSS_SELECTOR, 'div [data-marker="item-title"]').get_attribute("href")
                except:
                    ad_url = "Нет ссылки на объявление"

                # Собираем названия объявлений
                try:
                    ad_name = ad.find_element(By.CSS_SELECTOR, 'h3[itemprop = "name"]').text
                except:
                    ad_name = "Нет названия объявления"

                # Собираем удельные цены (за сотку и т.д.)
                try:
                    ad_unit_price = ad.find_element(By.CSS_SELECTOR, 'span[class*="price-noaccent"]').text
                except:
                    ad_unit_price = "Нет удельной цены"

                # Собираем адрес состоящий из двух строк
                try:
                    ad_address = ad.find_element(By.CSS_SELECTOR,
                                                 'span[class*="geo-address"] > span').text + ad.find_element(
                        By.CSS_SELECTOR, 'div[class*="geo-georeferences"] > span > span').text
                except:
                    ad_address = "Нет адреса в объявлении"

                # Собираем описания объявлений
                try:
                    ad_descr_title = ad.find_element(By.XPATH, '//div[@class="iva-item-descriptionStep-C0ty1"]/div').text
                except:
                    ad_descr_title = "Нет описания в объявлении"

                # Собираем время публикации объявлений
                try:
                    ad_publ_time = ad.find_element(By.CSS_SELECTOR, 'div[data-marker="item-date"]').text
                except:
                    ad_publ_time = "Нет времени публикации объявления"
                try:
                    # Наводим курсор на кнопку телефона и нажимаем на нее для отображения картинки с номером телефона
                    button_phone = ad.find_element(By.CSS_SELECTOR, 'div[class*="button-button"] > span')
                    ActionChains(driver).move_to_element(button_phone).click(button_phone).perform()

                    # Скачиваем img с номерами телефонов и кладем в папку "phone_num_imgs", проверив, есть ли она
                    ad_phone_num_img_urls = ad.find_element(By.CSS_SELECTOR, 'img[class*="button-phone-image"]')
                    num_img_url = ad_phone_num_img_urls.get_attribute("src")
                    if not os.path.exists("phone_num_imgs"):
                        os.mkdir("phone_num_imgs")
                    urllib.request.urlretrieve(num_img_url, f"phone_num_imgs/{count}_phone_img.png")

                    # Открываем картинку с помощью PIL
                    img = Image.open(f"phone_num_imgs/{count}_phone_img.png")

                    # Распознаем текст телефона с картинки с помощью tesseract
                    custom_config = r"--oem3 --psm13"  # Настройки для tesseract, эти по сути автоматические https://help.ubuntu.ru/wiki/tesseractб, oem3 это это режим работы движка, он и так по умолчанию 3, но вот остальные режимы: 0 = Original Tesseract only. 1 = Neural nets LSTM only. 2 = Tesseract + LSTM. 3 = Default, based on what is available.
                    phone_num = pytesseract.image_to_string(img).replace("\n", "")
                    os.remove(f"phone_num_imgs/{count}_phone_img.png")
                except:
                    phone_num = "Не получилось выгрузить номер телефона"

                # Добавляем все сведения из объявления  в словарь
                ad_dict_new = {
                    "Имя объявления": ad_name,
                    "URL объявления": ad_url,
                    "Цена в объявлении": ad_price,
                    "Описание объявления": ad_descr_title,
                    "Цена за единицу(удельная)": ad_unit_price,
                    "Адрес в объявлении": ad_address,
                    "Время публикации": ad_publ_time,
                    "Номер телефона": phone_num
                }
                await message.reply(f"Имя объявления: {ad_dict_new['Имя объявления']}\n"
                                    f"URL объявления: {ad_dict_new['URL объявления']}\n"
                                    f"Цена в объявлении: <b>{ad_dict_new['Цена в объявлении']}</b>\n"
                                    f"Описание объявления: {ad_dict_new['Описание объявления']}\n"
                                    f"Цена за единицу(удельная): {ad_dict_new['Цена за единицу(удельная)']}\n"
                                    f"Адрес в объявлении: {ad_dict_new['Адрес в объявлении']}\n"
                                    f"Время публикации: {ad_dict_new['Время публикации']}\n"
                                    f"Номер телефона: {ad_dict_new['Номер телефона']}\n")
                ad_dict.append(ad_dict_new)
                count += 1
                await message.reply(f"Обрабобтано объявлений: {count} из {numbers_of_ads}")
            # Помещаем все данные в json файл
            with open(f"avito_search_{cur_time}.json", "a") as file:
                json.dump(ad_dict, file, indent=4, ensure_ascii=False)


        except Exception as ex:
            print(ex)
        finally:
            driver.close()
            driver.quit()
    except Exception as ex:
        await message.reply("Нужно указать целое число от 2 до 50 включительно! Попробуй еще раз!")

if __name__ == '__main__':
    executor.start_polling(dp)