from rich import print
import os
import json
from time import sleep
import logging
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (TimeoutException)
from selenium.webdriver.chrome.options import Options as ChromeOptions

from selenium_stealth import stealth

config = {}

REQUIRED_KEYS = {
    "username",
    "password",
    "headless",
    "download_directory",
    "disable_images",
    "disable_videos",
    "driver_executable_path",
    "disable_saving_password",
    "select_results",
    "default_timeout",
    "log_file",
    "post_count",
    "save_directory",
    "search_queries"
}


def setup_logging(log_file):
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    logging.info("Logging initialized.")


def setup_driver():
    logging.info("Setting up WebDriver...")
    options = ChromeOptions()

    if config['headless']:
        logging.info("Headless mode enabled.")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")

    prefs = {}
    if config['disable_saving_password']:
        prefs = {
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        }
    if config['disable_images']:
        logging.info("Disabling images.")
        prefs["profile.managed_default_content_settings.images"] = 2
    else:
        prefs["profile.managed_default_content_settings.images"] = 1

    if config['disable_videos']:
        logging.info("Disabling videos.")
        prefs["profile.managed_default_content_settings.media_stream"] = 2
    else:
        prefs["profile.managed_default_content_settings.images"] = 1

    if prefs:
        options.add_experimental_option("prefs", prefs)

    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    service = None
    if config['driver_executable_path']:
        if os.path.exists(config['driver_executable_path']):
            logging.info(f"Using specified chromedriver executable: {config['driver_executable_path']}")
            service = Service(executable_path=config['driver_executable_path'])
        else:
            logging.error(f"Specified chromedriver path does not exist: {config['driver_executable_path']}")
            raise FileNotFoundError(
                f"ChromeDriver executable not found at specified path: {config['driver_executable_path']}")
    else:
        logging.info(f"No driver_executable_path found in config")
        logging.info(f"Returning")
        return

    try:
        logging.info("Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)
        logging.info("WebDriver initialized successfully.")

        try:
            stealth(driver,
                    languages=["en-US", "en"],
                    vendor="Google Inc.",
                    platform="Win32",
                    webgl_vendor="Intel Inc.",
                    renderer="Intel Iris OpenGL Engine",
                    fix_hairline=True,
                    )
            logging.info("Selenium Stealth applied.")
        except NameError:
            logging.warning("`stealth` function not found or imported, skipping stealth application.")
        except Exception as e:
            logging.warning(f"Error applying Selenium Stealth: {e}")

        return driver

    except Exception as e:
        logging.error(f"Error initializing WebDriver: {e}")
        raise


def navigate_to_url(driver, url):
    try:
        logging.info(f"Navigating to: {url}")
        driver.get(url)
    except Exception as e:
        logging.error(f"Error navigating to {url}: {e}")


def close_driver(driver):
    if driver:
        try:
            driver.quit()
            logging.info("WebDriver closed.")
        except Exception as e:
            logging.error(f"Error closing WebDriver: {e}")


def get_element(driver, by, value):
    timeout = config['default_timeout']

    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except TimeoutException:
        logging.warning(f"Element not found within {timeout}s: By={by}, Value={value}")
        return None
    except Exception as e:
        logging.error(f"Error finding element (By={by}, Value={value}): {e}")
        return None


def get_elements(driver, by, value):
    timeout = config['default_timeout']
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((by, value)))
        elements = driver.find_elements(by, value)
        return elements
    except TimeoutException:
        logging.warning(f"No elements found within {timeout}s: By={by}, Value={value}")
        return []
    except Exception as e:
        logging.error(f"Error finding elements (By={by}, Value={value}): {e}")
        return []


def get_element_by_xpath(driver, xpath):
    return get_element(driver, By.XPATH, xpath, )


def take_screenshot(driver, filename="screenshot.png"):
    try:
        driver.save_screenshot(filename)
        logging.info(f"Screenshot saved to {filename}")
        return True
    except Exception as e:
        logging.error(f"Error taking screenshot: {e}")
        return False


def get_soup(driver):
    try:
        page_source = driver.page_source
        soup = BeautifulSoup(page_source, 'html.parser')
        return soup
    except Exception as e:
        logging.error(f"Error getting page source or parsing with BeautifulSoup: {e}")
        return None


def search(my_driver, query):
    search_button = get_element_by_xpath(my_driver,
                                         "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[2]/span/div")
    search_button.click()
    search_query = "#" + query

    search_box = get_element_by_xpath(my_driver,
                                      "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div[1]/div/div/input")

    search_box.send_keys(search_query)
    sleep(2)  # Small delay to allow results to populate

    soup = get_soup(my_driver)

    search_container = soup.find('div', class_='x9f619 x78zum5 xdt5ytf x1iyjqo2 x6ikm8r x1odjw0f xh8yej3 xocp1fn')

    tags = search_container.find_all('a')

    if config['select_results']:
        results_and_xpaths = []
        print("[bold yellow]Search Results:[/bold yellow]")
        for i, each in enumerate(tags, start=1):
            try:
                spans = each.find_all('span')
                result_name = spans[0].text
                post_counts = spans[2].text if len(spans) > 2 else "Unknown"

                xpath = f'/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div[2]/div/a[{str(i)}]'
                results_and_xpaths.append({
                    "result_name": result_name,
                    "post_counts": post_counts,
                    "xpath": xpath
                })

                print(f"[cyan]{i}.[/cyan] [green]{result_name}[/green] → [magenta]{post_counts}[/magenta]")

            except Exception as e:
                logging.warning(f"Skipping a tag due to parsing error: {e}")

        return results_and_xpaths

    return []


#
# def search(my_driver, query):
#     search_button = get_element_by_xpath(my_driver,
#                                          "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div/div/div[2]/div[2]/span/div")
#     search_button.click()
#     search_query = "#" + query
#
#     search_box = get_element_by_xpath(my_driver,
#                                       "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div[1]/div/div/input")
#
#     search_box.send_keys(search_query)
#     soup = get_soup(my_driver)
#
#     search_container = soup.find('div', class_='x9f619 x78zum5 xdt5ytf x1iyjqo2 x6ikm8r x1odjw0f xh8yej3 xocp1fn')
#
#     tags = search_container.find_all('a')
#
#     xpath = '/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div[2]/div/a[1]'
#     if config['select_results']:
#         results_and_xpaths = []
#         for i, each in enumerate(tags, start=1):
#             result_name = each.find_all('span')[0].text
#             post_counts = each.find_all('span')[2].text
#             xpath = f'/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div[2]/div/div/div[2]/div/div/div/div[2]/div/div/div[2]/div/a[{str(i)}]'
#             results_and_xpaths.append(
#                 {
#                     "result_name": result_name,
#                     "post_counts": post_counts,
#                     "xpath": xpath
#                 }
#             )
#             summary = f'''{str(i)}. {result_name} -> {post_counts}'''
#             print(summary)
#
#         ask = int(input('Select>'))
#         xpath = results_and_xpaths[ask - 1]['xpath']
#
#     first_result = get_element_by_xpath(my_driver, xpath)
#     first_result.click()


PREFIX = 'https://www.instagram.com'


def wait_for_text_to_appear(driver, text, timeout=30):
    from rich.progress import Progress, TextColumn, BarColumn, TimeElapsedColumn
    from bs4 import BeautifulSoup
    import time

    for attempt in range(6):
        try:
            page_source = driver.page_source
            soup = BeautifulSoup(page_source, 'html.parser')
            if soup.find(string=lambda s: s and text in s):
                return True
        except Exception as e:
            print(f"Exception during parsing: {e}")

        with Progress(
                TextColumn(f"[bold blue]Waiting 5s (Attempt {attempt + 1}/6)"),
                BarColumn(),
                TimeElapsedColumn(),
                transient=True,
        ) as progress:
            task = progress.add_task(description="", total=5)
            for _ in range(5):
                time.sleep(1)
                progress.update(task, advance=1)

    return False


def login(my_driver):
    username = config['username']
    password = config['password']

    navigate_to_url(my_driver, 'https://www.instagram.com/')

    wait_for_text_to_appear(my_driver, "Don't have an account? Sign up")

    username_box = get_element_by_xpath(my_driver,
                                        "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[1]/div/label/input")
    username_box.send_keys(username)

    password_box = get_element_by_xpath(my_driver,
                                        "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[2]/div/label/input")
    password_box.send_keys(password)

    log_in_button = get_element_by_xpath(my_driver,
                                         "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[3]/button")
    log_in_button.click()

    wait_for_text_to_appear(my_driver,
                            "We can save your login info on this browser so you don't need to enter it again")


def scrape(my_driver):
    body = my_driver.find_element(By.TAG_NAME, "body")
    all_links = []

    def temp_scrape():
        soup = get_soup(my_driver)
        container = soup.find('div', class_='x78zum5 xdt5ytf xwrv7xz x1n2onr6 xph46j xfcsdxf xsybdxg x1bzgcud')
        temp_links = [PREFIX + each['href'] for each in container.find_all('a')]
        for each in temp_links:
            if each not in all_links:
                all_links.append(each)

    post_count = config['post_count']
    while True:
        body.send_keys(Keys.PAGE_DOWN)
        sleep(1)
        try:
            temp_scrape()
        except Exception as e:
            print(f"Error: Loading content {e}")
            continue
        if len(all_links) >= post_count:
            break

    return all_links


def processor(my_driver, query):
    print(f"[bold cyan]🔍 Searching for:[/bold cyan] {query}")
    search(my_driver, query)

    print("[yellow]🔗 Scraping links...[/yellow]")
    all_links = scrape(my_driver)
    print(f"[green]✅ Found {len(all_links)} links.[/green]")

    filename = config['save_directory'] + query + '.json'
    updated = 0

    if os.path.isfile(filename):
        print(f"[blue]📁 Existing file found:[/blue] {filename}")
        with open(filename, 'r') as f:
            temp_json = json.load(f)

        for each in all_links:
            if each not in temp_json:
                temp_json[each] = False
                updated += 1
    else:
        print(f"[red]📁 File not found. Creating new:[/red] {filename}")
        temp_json = {each: False for each in all_links}
        updated = len(all_links)

    with open(filename, 'w') as f:
        json.dump(temp_json, f, indent=4)

    print(f"[bold green]💾 Saved file with {len(temp_json)} links. {updated} new added.[/bold green]")


def main():
    setup_logging(config['log_file'])

    my_driver = setup_driver()

    login(my_driver)

    search_queries = config['search_queries']

    for each in search_queries:
        processor(my_driver, each)

    close_driver(my_driver)


def load_config(config_file="config.json"):
    global config
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        print(f"[bold green]✅ Configuration loaded from[/bold green] [cyan]{config_file}[/cyan]")

        if 'save_directory' in config:
            os.makedirs(config['save_directory'], exist_ok=True)
            print(f"[bold blue]📂 Save directory ensured:[/bold blue] {config['save_directory']}")
        else:
            print("[bold red]⚠️ 'save_directory' key missing, skipping directory creation[/bold red]")

    except FileNotFoundError:
        print("[bold red]❌ Error: Configuration file not found.[/bold red]")
        return False
    except json.JSONDecodeError as e:
        print(f"[bold red]❌ Error: Invalid JSON - {e}[/bold red]")
        return False

    missing_keys = REQUIRED_KEYS - config.keys()
    if missing_keys:
        print(f"[bold red]❌ Error: Missing config keys: {missing_keys}[/bold red]")
        return False

    return True


if __name__ == '__main__':
    if load_config():
        main()
