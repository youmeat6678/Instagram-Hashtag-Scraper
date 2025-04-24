from datetime import datetime
from rich import print
import os
import json
import time
import logging
from rich.progress import Progress, TimeElapsedColumn, BarColumn, TextColumn, TimeRemainingColumn
from rich.console import Console
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException
from selenium.webdriver.chrome.options import Options as ChromeOptions

PREFIX = 'https://www.instagram.com'
CONFIG_FILE = "config.json"
config = {}


def setup_logging(log_file):
    """Sets up logging to file."""
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        try:
            os.makedirs(log_dir)
        except OSError as e:
            print(f"[bold red]❌ Failed to create log directory '{log_dir}': {e}[/bold red]")
    try:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
            ]
        )
        logging.info("📝 Logging initialized.")
    except Exception as e:
        print(f"[bold red]❌ Failed to initialize logging to '{log_file}': {e}[/bold red]")


def setup_driver():
    """Configures and initializes the Selenium WebDriver."""
    logging.info("⚙️ Setting up WebDriver...")
    print("⚙️ Setting up WebDriver...")
    options = ChromeOptions()
    driver_path = config.get('driver_executable_path')

    if config.get('headless'):
        logging.info("👻 Headless mode enabled.")
        print("👻 Headless mode enabled.")
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-gpu")

    prefs = {}
    if config.get('disable_saving_password'):
        prefs.update({
            "credentials_enable_service": False,
            "profile.password_manager_enabled": False
        })
    if config.get('disable_images'):
        logging.info("🖼️ Disabling images.")
        print("🖼️ Disabling images.")
        prefs["profile.managed_default_content_settings.images"] = 2
    else:
        prefs["profile.managed_default_content_settings.images"] = 1

    if config.get('disable_videos'):
        logging.info("🎬 Disabling videos.")
        print("🎬 Disabling videos.")
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
    if driver_path:
        if os.path.exists(driver_path):
            logging.info(f"🚗 Using specified chromedriver executable: {driver_path}")
            print(f"🚗 Using specified chromedriver executable: [cyan]{driver_path}[/cyan]")
            try:
                service = Service(executable_path=driver_path)
            except WebDriverException as e:
                logging.error(f"❌ Failed to create WebDriver service with path {driver_path}: {e}")
                print(
                    f"[bold red]❌ Failed to create WebDriver service:[/bold red] Check if '{driver_path}' is a valid ChromeDriver executable. Error: {e}")
                raise
            except Exception as e:
                logging.error(f"❌ Unexpected error creating WebDriver service: {e}")
                print(f"[bold red]❌ Unexpected error creating WebDriver service:[/bold red] {e}")
                raise
        else:
            logging.error(f"❌ Specified chromedriver path does not exist: {driver_path}")
            print(f"[bold red]❌ Specified chromedriver path does not exist:[/bold red] [cyan]{driver_path}[/cyan]")
            raise FileNotFoundError(f"ChromeDriver executable not found at specified path: {driver_path}")
    else:
        logging.info("🤔 No driver_executable_path found in config. Attempting to use system PATH.")
        print("🤔 No driver_executable_path found in config. Attempting to use system PATH for ChromeDriver.")

    try:
        logging.info("🚀 Initializing Chrome WebDriver...")
        print("🚀 Initializing Chrome WebDriver...")
        driver = webdriver.Chrome(service=service, options=options)

        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        logging.info("✅ WebDriver initialized successfully.")
        print("✅ WebDriver initialized successfully.")
        return driver
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException initializing WebDriver: {e}")
        print(
            f"[bold red]❌ WebDriver Error:[/bold red] Could not initialize Chrome. Check ChromeDriver/Chrome compatibility and installation. Details: {e}")
        raise
    except Exception as e:
        logging.error(f"❌ Fatal error initializing WebDriver: {e}")
        print(f"[bold red]❌ Fatal error initializing WebDriver:[/bold red] {e}")
        raise


def navigate_to_url(driver, url):
    """Navigates the driver to the specified URL with error handling."""
    try:
        logging.info(f"🌍 Navigating to: {url}")
        print(f"🌍 Navigating to: [link={url}]{url}[/link]")
        driver.get(url)
        time.sleep(2)
        return True  
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException navigating to {url}: {e}")
        print(
            f"[bold red]❌ WebDriver Error navigating to {url}:[/bold red] Check network connection or URL validity. Details: {e}")
        return False 
    except Exception as e:
        logging.error(f"❌ Unexpected error navigating to {url}: {e}")
        print(f"[bold red]❌ Unexpected error navigating to {url}:[/bold red] {e}")
        return False 


def close_driver(driver):
    """Closes the WebDriver session with error handling."""
    if driver:
        print("🚪 Closing WebDriver...")
        try:
            driver.quit()
            logging.info("✅ WebDriver closed.")
            print("✅ WebDriver closed.")
        except WebDriverException as e:
            logging.error(f"❌ WebDriverException closing WebDriver: {e}")
            print(f"[bold red]❌ WebDriver Error closing session:[/bold red] {e}")
        except Exception as e:
            logging.error(f"❌ Error closing WebDriver: {e}")
            print(f"[bold red]❌ Error closing WebDriver:[/bold red] {e}")


def get_element(driver, by, value, timeout=None):
    """Finds and returns a single web element with explicit wait and detailed error handling."""
    timeout = timeout if timeout is not None else config.get('default_timeout', 10)
    try:
        wait = WebDriverWait(driver, timeout)
        element = wait.until(EC.presence_of_element_located((by, value)))
        return element
    except TimeoutException:
        logging.warning(f"⏳ Timeout: Element not found within {timeout}s: By={by}, Value='{value}'")
        return None
    except NoSuchElementException:
        logging.warning(f"🚫 Element not present in DOM: By={by}, Value='{value}'")
        return None
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException finding element (By={by}, Value='{value}'): {e}")
        print(f"[bold red]❌ WebDriver Error finding element (By={by}, Value='{value}'): {e}[/bold red]")
        return None
    except Exception as e:
        logging.error(f"❌ Unexpected Error finding element (By={by}, Value='{value}'): {e}")
        print(f"[bold red]❌ Unexpected Error finding element (By={by}, Value='{value}'): {e}[/bold red]")
        return None


def get_elements(driver, by, value, timeout=None):
    """Finds and returns a list of web elements with explicit wait and error handling."""
    timeout = timeout if timeout is not None else config.get('default_timeout', 10)
    try:
        wait = WebDriverWait(driver, timeout)
        wait.until(EC.presence_of_element_located((by, value)))
        elements = driver.find_elements(by, value)
        return elements
    except TimeoutException:
        logging.warning(f"⏳ Timeout: No elements found within {timeout}s: By={by}, Value='{value}'")
        return [] 
    except NoSuchElementException:
        logging.warning(f"🚫 No elements present in DOM: By={by}, Value='{value}'")
        return []
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException finding elements (By={by}, Value='{value}'): {e}")
        print(f"[bold red]❌ WebDriver Error finding elements (By={by}, Value='{value}'): {e}[/bold red]")
        return []
    except Exception as e:
        logging.error(f"❌ Unexpected Error finding elements (By={by}, Value='{value}'): {e}")
        print(f"[bold red]❌ Unexpected Error finding elements (By={by}, Value='{value}'): {e}[/bold red]")
        return []


def get_element_by_xpath(driver, xpath, timeout=None):
    """Convenience function using get_element with XPath."""
    return get_element(driver, By.XPATH, xpath, timeout)


def take_screenshot(driver, filename="screenshot.png"):
    """Takes a screenshot with error handling."""
    screenshot_dir = os.path.dirname(filename)
    if screenshot_dir and not os.path.exists(screenshot_dir):
        try:
            os.makedirs(screenshot_dir)
        except OSError as e:
            print(f"[bold red]❌ Failed to create directory for screenshot '{screenshot_dir}': {e}[/bold red]")

    try:
        if driver.save_screenshot(filename):
            logging.info(f"📸 Screenshot saved to {filename}")
            print(f"📸 Screenshot saved to [green]{filename}[/green]")
            return True
        else:
            logging.error(f"❌ Failed to save screenshot to {filename} (driver returned false).")
            print(f"[bold red]❌ Failed to save screenshot to {filename}[/bold red]")
            return False
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException taking screenshot: {e}")
        print(f"[bold red]❌ WebDriver Error taking screenshot:[/bold red] {e}")
        return False
    except Exception as e:
        logging.error(f"❌ Error taking screenshot: {e}")
        print(f"[bold red]❌ Error taking screenshot:[/bold red] {e}")
        return False


def get_soup(driver):
    """Gets page source and parses with BeautifulSoup, with error handling."""
    try:
        page_source = driver.page_source
        if not page_source or len(page_source) < 500:  
            logging.warning("⚠️ Page source seems empty or too short. Possible page load issue.")
        soup = BeautifulSoup(page_source, 'html.parser')
        return soup
    except WebDriverException as e:
        logging.error(f"❌ WebDriverException getting page source: {e}")
        print(f"[bold red]❌ WebDriver Error getting page source:[/bold red] {e}")
        return None
    except Exception as e:
        logging.error(f"❌ Error getting page source or parsing with BeautifulSoup: {e}")
        print(f"[bold red]❌ Error getting page source or parsing:[/bold red] {e}")
        return None


def wait_for_text_to_appear(driver, text, timeout_per_attempt=5, attempts=6):
    """Waits for specific text to appear in the page source."""
    print(f"⏳ Waiting for text '{text[:30]}...' to appear (max {attempts * timeout_per_attempt}s)...")
    for attempt in range(attempts):
        try:
            page_source = driver.page_source
            if not page_source:  
                print("[yellow]⚠️ Got empty page source while waiting for text.[/yellow]")
                time.sleep(timeout_per_attempt)
                continue
            soup = BeautifulSoup(page_source, 'html.parser')
            if text in soup.get_text():
                print(f"✅ Found text '{text[:30]}...'")
                return True

        except WebDriverException as e:
            print(f"[yellow]⚠️ WebDriver Error during text check (Attempt {attempt + 1}/{attempts}): {e}[/yellow]")
        except Exception as e:
            print(f"[yellow]⚠️ Exception during text check (Attempt {attempt + 1}/{attempts}): {e}[/yellow]")

        with Progress(
                TextColumn(f"[bold blue]Waiting {timeout_per_attempt}s (Attempt {attempt + 1}/{attempts})"),
                BarColumn(),
                TimeElapsedColumn(),
                transient=True,  
        ) as progress:
            task = progress.add_task(description="", total=timeout_per_attempt)
            for _ in range(timeout_per_attempt):
                time.sleep(1)
                progress.update(task, advance=1)

    print(f"[yellow]⚠️ Text '{text[:30]}...' not found after {attempts} attempts.[/yellow]")
    return False


def login(my_driver):
    """Logs into Instagram using credentials from config, keeping original XPaths."""
    username = config.get('username')
    password = config.get('password')

    if not username or not password:
        logging.error("❌ Username or password missing in config.json")
        print("[bold red]❌ Username or password missing in config.json. Please update it.[/bold red]")
        return False 

    print("🔑 Attempting Instagram login...")
    if not navigate_to_url(my_driver, 'https://www.instagram.com/'):
        print("[bold red]❌ Failed to navigate to Instagram login page.[/bold red]")
        return False

    if not wait_for_text_to_appear(my_driver, "Don't have an account? Sign up"):
        print(
            "[yellow]⚠️ Login page structure might have changed (did not find 'Sign up' text). Proceeding anyway.[/yellow]")

    try:
        print("📝 Locating login fields...")
        username_box = get_element_by_xpath(my_driver,
                                            "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[1]/div/label/input")
        if not username_box:
            print("[bold red]❌ Login Error: Could not find username input field (check XPath).[/bold red]")
            take_screenshot(my_driver, "error_login_username_missing.png")
            return False

        password_box = get_element_by_xpath(my_driver,
                                            "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[2]/div/label/input")
        if not password_box:
            print("[bold red]❌ Login Error: Could not find password input field (check XPath).[/bold red]")
            take_screenshot(my_driver, "error_login_password_missing.png")
            return False

        log_in_button = get_element_by_xpath(my_driver,
                                             "/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[1]/div/section/main/article/div[2]/div[1]/div[2]/div/form/div[1]/div[3]/button")
        if not log_in_button:
            print("[bold red]❌ Login Error: Could not find login button (check XPath).[/bold red]")
            take_screenshot(my_driver, "error_login_button_missing.png")
            return False

        print("🖋️ Entering credentials...")
        username_box.send_keys(username)
        time.sleep(0.5)
        password_box.send_keys(password)
        time.sleep(0.5)

        print("🖱️ Clicking login button...")
        log_in_button.click()

        print("⏳ Waiting for post-login confirmation text...")
        login_confirm_text = "Save your login info"
        if wait_for_text_to_appear(my_driver, login_confirm_text, attempts=8):
            print("✅ Login successful (detected confirmation text).")
            return True
        else:
            print("[bold red]❌ Login Failed:[/bold red] Did not detect expected text after login.")
            current_url = my_driver.current_url
            if "accounts/onetap/?next=%2F" in current_url:
                return True
            else:
                print(
                    f"   (Navigated away from login page to {current_url}, but confirmation text missing - check for 2FA or changed layout)")
            take_screenshot(my_driver, "error_login_failed_confirmation.png")
            return False

    except WebDriverException as e:
        print(f"[bold red]❌ WebDriver Error during login interaction: {e}[/bold red]")
        logging.error(f"WebDriverException during login: {e}")
        take_screenshot(my_driver, "error_login_webdriver_exception.png")
        return False
    except Exception as e:
        print(f"[bold red]❌ Unexpected error during login: {e}[/bold red]")
        logging.exception("Unexpected error during login") 
        take_screenshot(my_driver, "error_login_unexpected.png")
        return False


def colorful_sleep(seconds: int):
    console = Console()  
    with Progress(
        TextColumn("[bold magenta]Sleeping..."),
        BarColumn(bar_width=None),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(),
        console=console
    ) as progress:
        task = progress.add_task("sleep", total=seconds)
        for _ in range(seconds):
            time.sleep(1)
            progress.update(task, advance=1)


def search_scraper(my_driver):
    """Scrapes search result links using original logic."""
    print("📜 Starting search results scroll and scrape...")
    all_links = []
    processed_links = set()  
    body = None
    try:
        body = my_driver.find_element(By.TAG_NAME, "body")
    except NoSuchElementException:
        print("[bold red]❌ Cannot find page body element to send scroll keys.[/bold red]")
        logging.error("Failed to find body element for search scraping.")
        return []  

    soup = get_soup(my_driver)
    if soup and "We couldn't find anything for that search" in soup.get_text(): 
        print("🤷 No results found for this search term.")
        logging.info("Search returned no results.")
        return []

    def temp_scrape():
        """Inner function to scrape links currently visible."""
        nonlocal all_links 
        newly_found_count = 0
        try:
            soup = get_soup(my_driver)
            if not soup:
                print("[yellow]⚠️ Could not get page source for scraping pass.[/yellow]")
                return 0  
            container_class = 'x78zum5 xdt5ytf xwrv7xz x1n2onr6 xph46j xfcsdxf xsybdxg x1bzgcud'
            container = soup.find('div', class_=container_class)
            if container:
                temp_links = [PREFIX + each['href'] for each in container.find_all('a') if each.get('href')]
                for each_link in temp_links:
                    if each_link.startswith(PREFIX + '/p/') and each_link not in processed_links:
                        all_links.append(each_link)
                        processed_links.add(each_link)
                        newly_found_count += 1
              
            else:
                logging.warning(f"Search results container ('{container_class}') not found in this scrape pass.")
                pass 
        except Exception as e:
            print(f"[red]❌ Error in temp_scrape: {e}[/red]")
            logging.error(f"Error during search temp_scrape: {e}")
        return newly_found_count  

    post_count_target = config.get('search_post_count', 100) 
    scroll_attempts = 0
    no_new_links_streak = 0

    print(f"🎯 Aiming for approximately {post_count_target} posts.")

    while True:
        if len(all_links) >= post_count_target:
            print(f"\n✅ Reached target post count ({len(all_links)} >= {post_count_target}).")
            break
        try:
            body.send_keys(Keys.PAGE_DOWN)
            scroll_attempts += 1
            print(f"\t\r📜 Scrolled ({scroll_attempts}). Found {len(all_links)} links...")
            time.sleep(1.5)
        except WebDriverException as e:
            print(f"\n[bold red]❌ WebDriver Error sending scroll key: {e}[/bold red]")
            logging.error(f"WebDriverException during search scroll: {e}")
            break
        except Exception as e:
            print(f"\n[bold red]❌ Unexpected error sending scroll key: {e}[/bold red]")
            logging.error(f"Unexpected error during search scroll: {e}")
            break 

        try:
            new_links_found = temp_scrape()
            if new_links_found == 0:
                no_new_links_streak += 1
            else:
                no_new_links_streak = 0 
        except Exception as e:
            print(f"\n[yellow]⚠️ Continuing scroll despite error in scraping pass {scroll_attempts}.[/yellow]")
            no_new_links_streak += 1  
            continue

    print()  
    print(f"🏁 Finished search scraping. Found {len(all_links)} unique post links.")
    return all_links


def get_today():
    """Gets the current date and time formatted."""
    now = datetime.now()
    formatted = now.strftime("%Y-%m-%d %H:%M:%S")
    return formatted


def search_handler(my_driver, query):
    """Handles search query using original logic with added exceptions/output."""
    print(f"[bold cyan]🔍 Searching Instagram for:[/bold cyan] #{query}")
    logging.info(f"Starting search for query: {query}")

    search_url = f"https://www.instagram.com/explore/search/keyword/?q=%23{query}"
    if not navigate_to_url(my_driver, search_url):
        print(f"[bold red]❌ Failed to navigate to search page for #{query}. Skipping.[/bold red]")
        return  

    print(f"[yellow]🔗 Scraping links for #{query}...[/yellow]")
    logging.info(f"Scraping links for search query: {query}")

    while True:
        soup = get_soup(my_driver)
        if "We couldn't find anything for that search" in soup.text:
            all_links = []
            break
        if soup.find('div', class_='x1qjc9v5 x972fbf xcfux6l x1qhh985 xm0m39n x9f619 x1lliihq xdt5ytf x2lah0s xrbpyxo x1a7h2tk x14miiyz xat24cr x1mh8g0r xexx8yu x4uap5 x18d9i69 xkhd6sd x1n2onr6 x11njtxf x1bfs520 xph46j x9i3mqj xcghwft x1bzgcud xhdunbi') is None:
            colorful_sleep(5)
            continue
        else:
            all_links = search_scraper(my_driver) 
            break

    if not all_links:
        print(f"[yellow]⚠️ No links found or scraped for #{query}.[/yellow]")
        logging.warning(f"No links scraped for search query: {query}")
        config['completed_queries'][query] = {
            'type': 'search',
            'post_count': 0, 
            'updated': get_today(),
            'saved_file': None,
            'status': 'No Results Found/Scraped'
        }
        if query in config.get('queries', {}):
            config['queries'].pop(query)
        update_config()
        return  

    filename = os.path.join(config.get('search_path', 'search/'), f"{query}.json")
    print(f"💾 Preparing to save/update results to: [green]{filename}[/green]")
    logging.info(f"Saving/updating search results to: {filename}")

    existing_data = {}
    updated_count = 0 
    new_file = True

    if os.path.isfile(filename):
        new_file = False
        print(f"📄 Existing file found. Loading previous data...")
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"📊 Loaded {len(existing_data)} existing links.")
        except json.JSONDecodeError as e:
            print(
                f"[bold red]❌ Error decoding JSON from {filename}. File might be corrupt. Starting fresh for this query.[/bold red]")
            logging.error(f"JSONDecodeError reading {filename}: {e}")
            existing_data = {} 
            new_file = True 
        except (IOError, OSError) as e:
            print(
                f"[bold red]❌ File Error reading {filename}: {e}. Cannot update, skipping save for this query.[/bold red]")
            logging.error(f"File Error reading {filename}: {e}")
            return 
        except Exception as e:
            print(f"[bold red]❌ Unexpected error reading file {filename}: {e}[/bold red]")
            logging.exception(f"Unexpected error reading file {filename}")
            return 

    temp_json = existing_data.copy() 
    added_count = 0
    for each_link in all_links:
        if each_link not in temp_json:
            temp_json[each_link] = False  
            added_count += 1

    updated_count = added_count  

    
    if updated_count > 0 or new_file:
        print(f"➕ Found {updated_count} new links to add.")
        try:
            os.makedirs(os.path.dirname(filename), exist_ok=True)
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(temp_json, f, indent=4, ensure_ascii=False)
            print(f"✅ Successfully saved {len(temp_json)} total links to [green]{filename}[/green]")
            logging.info(f"Saved {len(temp_json)} links to {filename}. Added {updated_count} new links.")
        except (IOError, OSError) as e:
            print(f"[bold red]❌ File Error writing search results to {filename}: {e}[/bold red]")
            logging.error(f"File Error writing search results to {filename}: {e}")
            
            return  
        except Exception as e:
            print(f"[bold red]❌ Unexpected error writing file {filename}: {e}[/bold red]")
            logging.exception(f"Unexpected error writing file {filename}")
            return  
    else:
        print("✅ No new links found for this search.")
        logging.info(f"No new links added for search query: {query}")


    if 'completed_queries' not in config: config['completed_queries'] = {}
    if query not in config['completed_queries']: config['completed_queries'][query] = {}

    config['completed_queries'][query]['type'] = 'search'
    config['completed_queries'][query][
        'post_count'] = updated_count  
    config['completed_queries'][query]['updated'] = get_today()
    config['completed_queries'][query]['saved_file'] = filename
    config['completed_queries'][query]['status'] = 'Completed'  

    
    if 'queries' in config and query in config['queries']:
        config['queries'].pop(query)

    update_config() 


def scroll_to_the_last(my_driver):
    """Scrolls to the bottom of the page using original comparison logic."""
    print("📜 Scrolling down to find the end of the page...")
    body = None
    try:
        body = my_driver.find_element(By.TAG_NAME, "body")
    except NoSuchElementException:
        print("[bold red]❌ Cannot find page body element to send scroll keys.[/bold red]")
        logging.error("Failed to find body element for scroll_to_the_last.")
        return 0 
    first_soup = get_soup(my_driver)
    if not first_soup:
        print("[yellow]⚠️ Could not get initial page source for comparison.[/yellow]")
        return 10 

    total_page_down = 0
    max_scrolls = 200  

    while total_page_down < max_scrolls:
        try:
            body.send_keys(Keys.PAGE_DOWN)
            total_page_down += 1
            print(f"\r📜 Scrolling down... (Scroll {total_page_down})", end="")
            time.sleep(3)  

            second_soup = get_soup(my_driver)
            if not second_soup:
                print("\n[yellow]⚠️ Failed to get page source for comparison, stopping scroll.[/yellow]")
                break  

            if second_soup == first_soup:
                print("\n M Page content stabilized. Reached the end (based on soup comparison).")
                break  

            first_soup = second_soup  

        except WebDriverException as e:
            print(f"\n[bold red]❌ WebDriver Error sending scroll key: {e}[/bold red]")
            logging.error(f"WebDriverException during scroll_to_the_last: {e}")
            break  
        except Exception as e:
            print(f"\n[bold red]❌ Unexpected error during scroll: {e}[/bold red]")
            logging.error(f"Unexpected error during scroll_to_the_last: {e}")
            break  

    if total_page_down >= max_scrolls:
        print(f"\n[yellow]⚠️ Reached scroll limit ({max_scrolls}) before page stabilized.[/yellow]")

    print(f"\n🏁 Finished scrolling down. Performed {total_page_down} scrolls.")
    
    scroll_up_count = total_page_down + 10
    print(f"   (Will attempt {scroll_up_count} scrolls UP in the scraper)")
    return scroll_up_count



def user_reels_scraper(my_driver, count):
    print(f"📜 Starting Reels scraping (scrolling UP {count} times)...")
    body = my_driver.find_element(By.TAG_NAME, "body")
    all_links = []

    def temp_scrape():
        soup = get_soup(my_driver)
        container = soup.find('div', class_='xg7h5cd x1n2onr6')
        temp_links = [PREFIX + each['href'] for each in container.find_all('a')]
        i = 0
        for each in temp_links:
            if each not in all_links:
                all_links.append(each)
                i += 1
        print(len(all_links), i)

    for _ in range(count):
        body.send_keys(Keys.PAGE_UP)
        time.sleep(1)
        temp_scrape()

    return all_links


def user_reels_handler(my_driver, user, update):  
    """Handles user Reels scraping using original logic with added exceptions/output."""
    print(f"[bold magenta]👤 Processing user:[/bold magenta] {user}")
    logging.info(f"Starting Reels scrape for user: {user}")

    save_file_path = os.path.join(config.get('user_reels_path', 'user reels/'), f"{user}.json")
    user_link = f'https://www.instagram.com/{user}/reels/'

    if not navigate_to_url(my_driver, user_link):
        print(f"[bold red]❌ Failed to navigate to user Reels page for {user}. Skipping.[/bold red]")

        return

    
    print("📊 Fetching user profile info...")
    logging.info(f"Fetching profile info for {user}")
    posts = followers = following = "N/A"  
    info = []
    try:
        soup = get_soup(my_driver)
        info_class = 'x5n08af x1s688f'  
        info_elements = soup.find_all('span', class_=info_class)

        if info_elements and len(info_elements) >= 3:
            
            
            try:
                posts = info_elements[0].text.strip() if info_elements[0] else "N/A"
            except Exception:
                posts = "Error"
            try:
                followers = info_elements[1].text.strip() if info_elements[1] else "N/A"
            except Exception:
                followers = "Error"
            try:
                
                
                following = info_elements[2].text.strip() if info_elements[2] else "N/A"
            except Exception:
                following = "Error"

            print(f"    Posts: {posts}, Followers: {followers}, Following: {following}")
            logging.info(f"User info for {user}: Posts={posts}, Followers={followers}, Following={following}")
        else:
            print(
                f"[yellow]⚠️ Could not find expected user info elements (found {len(info_elements)} spans with class '{info_class}'). Using defaults.[/yellow]")
            logging.warning(f"Could not find expected user info elements for {user} using class '{info_class}'")

    except Exception as e:
        
        print(f"[red]❌ Error extracting user info: {e}[/red]")
        logging.error(f"Error extracting user info for {user}: {e}")

    
    
    page_downs_to_scroll_up = scroll_to_the_last(my_driver)

    
    all_reels = user_reels_scraper(my_driver, page_downs_to_scroll_up)

    if not all_reels:
        print(f"[yellow]⚠️ No Reel links scraped for user {user}.[/yellow]")
        logging.warning(f"No Reel links scraped for user: {user}")
        
        config['completed_queries'][user] = {
            'type': 'user_reels',
            'info': {'url': user_link, 'posts': posts, 'followers': followers, 'following': following},
            'post_saved': 0,  
            'saved_file': None,
            'updated': get_today(),
            'status': 'No Reels Found/Scraped'
        }
        if user in config.get('queries', {}): config['queries'].pop(user)
        update_config()
        return

    
    print(f"💾 Preparing to save/update Reels results to: [green]{save_file_path}[/green]")
    logging.info(f"Saving/updating Reels results for {user} to: {save_file_path}")

    existing_data = {}
    new_file = True

    followed = False

    
    if config['follow_user_reels']:
        
        try:
            follow_button = get_element_by_xpath(my_driver,'/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[2]/div/div/div[2]/div/div[1]/button')
            if follow_button.text == 'Follow':
                follow_button.click()
            followed = True
        except Exception as e:
            print(f"[bold red]❌ Unexpected error following user : {e}[/bold red]")
            logging.exception(f"Unexpected error following user : {e}")
    else:
        
        try:
            follow_button = get_element_by_xpath(my_driver,'/html/body/div[1]/div/div/div[2]/div/div/div[1]/div[2]/div/div[1]/section/main/div/header/section[2]/div/div/div[2]/div/div[1]/button')
            if follow_button.text == 'Following':
                follow_button.click()
                unfollow_button = get_element_by_xpath(my_driver, '/html/body/div[5]/div[2]/div/div/div[1]/div/div[2]/div/div/div/div/div[2]/div/div/div/div[8]/div[1]/div/div/div[1]/div/div/span/span')
                unfollow_button.click()
            followed = False
        except:
            print(f"[bold red]❌ Unexpected error unfollowing user : {e}[/bold red]")
            logging.exception(f"Unexpected error unfollowing user : {e}")

    
    
    
    if update and os.path.exists(save_file_path):  
        new_file = False
        print(f"📄 Update mode: Loading existing file...")
        try:
            with open(save_file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"📊 Loaded {len(existing_data)} existing Reel links.")
        except json.JSONDecodeError as e:
            print(
                f"[bold red]❌ Error decoding JSON from {save_file_path}. File might be corrupt. Treating as new file.[/bold red]")
            logging.error(f"JSONDecodeError reading {save_file_path}")
            existing_data = {}
            new_file = True
        except (IOError, OSError) as e:
            print(f"[bold red]❌ File Error reading {save_file_path}: {e}. Cannot update, skipping save.[/bold red]")
            logging.error(f"File Error reading {save_file_path}: {e}")
            return  
        except Exception as e:
            print(f"[bold red]❌ Unexpected error reading file {save_file_path}: {e}[/bold red]")
            logging.exception(f"Unexpected error reading file {save_file_path}")
            return  
    elif os.path.exists(save_file_path):  
        new_file = False
        print(f"📄 Existing file found (not in update mode). Loading previous data...")
        
        try:
            with open(save_file_path, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
            print(f"📊 Loaded {len(existing_data)} existing Reel links.")
        except json.JSONDecodeError as e:
            print(f"[bold red]❌ Error decoding JSON from {save_file_path}. Treating as new file.[/bold red]")
            logging.error(f"JSONDecodeError reading {save_file_path}")
            existing_data = {}
            new_file = True
        except (IOError, OSError) as e:
            print(f"[bold red]❌ File Error reading {save_file_path}: {e}. Skipping save.[/bold red]")
            logging.error(f"File Error reading {save_file_path}: {e}")
            return
        except Exception as e:
            print(f"[bold red]❌ Unexpected error reading file {save_file_path}: {e}[/bold red]")
            logging.exception(f"Unexpected error reading file {save_file_path}")
            return
    else:
        print("📄 No existing file found. Will create a new one.")
        new_file = True
        existing_data = {}

    
    added_count = 0
    temp_json = existing_data.copy()
    for each_reel in all_reels:
        if each_reel not in temp_json:
            temp_json[each_reel] = False  
            added_count += 1

    
    if added_count > 0 or new_file:
        print(f"➕ Found {added_count} new Reel links to add.")
        try:
            
            os.makedirs(os.path.dirname(save_file_path), exist_ok=True)
            with open(save_file_path, 'w', encoding='utf-8') as f:
                json.dump(temp_json, f, indent=4, ensure_ascii=False)
            print(f"✅ Successfully saved {len(temp_json)} total Reel links to [green]{save_file_path}[/green]")
            logging.info(f"Saved {len(temp_json)} Reel links for {user}. Added {added_count} new links.")
        except (IOError, OSError) as e:
            print(f"[bold red]❌ File Error writing Reels results to {save_file_path}: {e}[/bold red]")
            logging.error(f"File Error writing Reels results for {user} to {save_file_path}: {e}")
            return  
        except Exception as e:
            print(f"[bold red]❌ Unexpected error writing file {save_file_path}: {e}[/bold red]")
            logging.exception(f"Unexpected error writing file {save_file_path}")
            return  
    else:
        print("✅ No new Reel links found for this user.")
        logging.info(f"No new Reel links added for user: {user}")

    
    
    if 'completed_queries' not in config: config['completed_queries'] = {}
    if user not in config['completed_queries']: config['completed_queries'][user] = {}
    if 'info' not in config['completed_queries'][user]: config['completed_queries'][user]['info'] = {}

    config['completed_queries'][user]['type'] = "user_reels"
    config['completed_queries'][user]['info']['url'] = user_link
    config['completed_queries'][user]['info']['posts'] = posts
    config['completed_queries'][user]['info']['following'] = following  
    config['completed_queries'][user]['info']['followers'] = followers
    config['completed_queries'][user]['post_saved'] = len(temp_json)  
    config['completed_queries'][user]['saved_file'] = save_file_path
    config['completed_queries'][user]['updated'] = get_today()
    config['completed_queries'][user]['status'] = 'Completed'  
    config['completed_queries'][user]['followed'] = followed

    
    if 'queries' in config and user in config['queries']:
        config['queries'].pop(user)

    update_config()


def main():
    """Main execution function with added exceptions and output."""
    global config
    
    if not load_config():
        return

    
    try:
        
        user_reels_dir = config.get('user_reels_path', 'user reels/')
        search_dir = config.get('search_path', 'search/')
        log_file = config.get('log_file', 'instagram.log')

        
        os.makedirs(user_reels_dir, exist_ok=True)
        print(f"📁 Ensured user reels directory exists: [cyan]{user_reels_dir}[/cyan]")
        os.makedirs(search_dir, exist_ok=True)
        print(f"📁 Ensured search directory exists: [cyan]{search_dir}[/cyan]")

        
        config['user_reels_path'] = user_reels_dir
        config['search_path'] = search_dir
        config['log_file'] = log_file

    except OSError as e:
        print(f"[bold red]❌ Error creating necessary directories: {e}[/bold red]")
        logging.error(f"OSError creating directories: {e}")
        return  

    
    setup_logging(config['log_file'])

    my_driver = None  
    try:
        my_driver = setup_driver()
        if not my_driver:
            print("[bold red]❌ WebDriver setup failed. Exiting.[/bold red]")
            
            return

        
        if not login(my_driver):
            print("[bold red]❌ Login failed. Cannot proceed with scraping. Exiting.[/bold red]")
            
            
            return  

        
        
        pending_queries = config.get('queries', {})
        if not pending_queries:
            print("[yellow]🤔 No queries found in config file to process.[/yellow]")
            logging.info("No queries found in config file.")
        else:
            print(f"✨ Starting processing of {len(pending_queries)} queries...")
            
            for query, query_type in pending_queries.copy().items():
                print("-" * 40)  
                try:
                    
                    if query_type == 'user_reels':
                        
                        user_reels_handler(my_driver, query, False)
                    elif query_type == 'search':
                        
                        search_handler(my_driver, query)
                    else:
                        print(f"[yellow]⚠️ Unknown query type '{query_type}' for query '{query}'. Skipping.[/yellow]")
                        logging.warning(f"Unknown query type '{query_type}' for query '{query}'.")
                        
                        if 'completed_queries' not in config: config['completed_queries'] = {}
                        config['completed_queries'][query] = {'type': query_type, 'status': 'Unknown Type',
                                                              'updated': get_today()}
                        if query in config.get('queries', {}): config['queries'].pop(query)
                        update_config()

                except Exception as e:
                    
                    print(
                        f"[bold red]❌ An critical error occurred processing query '{query}' ({query_type}): {e}[/bold red]")
                    logging.exception(f"Unhandled exception processing query '{query}' ({query_type})")
                    
                    if 'completed_queries' not in config: config['completed_queries'] = {}
                    config['completed_queries'][query] = {'type': query_type, 'status': f'Runtime Error: {e}',
                                                          'updated': get_today()}
                    if query in config.get('queries', {}): config['queries'].pop(query)
                    update_config()
                    
                    

            print("-" * 40)
            
            remaining_queries = len(config.get('queries', {}))
            if remaining_queries == 0:
                print("[green]✅ All queries processed or removed due to errors.[/green]")
                logging.info("Finished processing loop for all queries.")
            else:
                print(
                    f"[yellow]⚠️ Query processing finished, but {remaining_queries} queries remain (likely due to errors).[/yellow]")
                logging.warning(f"{remaining_queries} queries remain in config after processing loop.")


    except WebDriverException as e:
        
        print(f"[bold red]💥 WebDriver Error during main execution: {e}[/bold red]")
        logging.exception("WebDriverException during main execution loop.")
    except Exception as e:
        
        print(f"[bold red]💥 An unexpected critical error occurred in main: {e}[/bold red]")
        logging.exception("Unexpected critical error during main execution.")
    finally:
        
        if my_driver:
            close_driver(my_driver)


def load_config(config_file=CONFIG_FILE):
    """Loads the configuration from the JSON file with error handling."""
    global config
    print(f"📄 Loading configuration from: [cyan]{config_file}[/cyan]")
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            config = json.load(f)
        print("✅ Configuration loaded successfully.")
        logging.info(f"Configuration loaded from {config_file}")
        
        if 'queries' not in config:
            print("[yellow]⚠️ 'queries' key missing in config. Assuming no tasks.[/yellow]")
            config['queries'] = {}  
        if 'completed_queries' not in config:
            config['completed_queries'] = {}  
        
        if 'default_timeout' not in config: config['default_timeout'] = 10  
        return True
    except FileNotFoundError:
        print(f"[bold red]❌ Error: Configuration file '{config_file}' not found.[/bold red]")
        logging.error(f"Configuration file '{config_file}' not found.")
        return False
    except json.JSONDecodeError as e:
        print(f"[bold red]❌ Error: Could not decode JSON from '{config_file}'. Check syntax.[/bold red] Details: {e}")
        logging.error(f"JSONDecodeError in '{config_file}': {e}")
        return False
    except (IOError, OSError) as e:
        print(f"[bold red]❌ File Error reading config '{config_file}': {e}[/bold red]")
        logging.error(f"File Error reading config '{config_file}': {e}")
        return False
    except Exception as e:
        
        print(f"[bold red]❌ Unexpected error loading config: {e}[/bold red]")
        logging.exception("Unexpected error loading config.")
        return False


def update_config(config_file=CONFIG_FILE):
    """Saves the current config state back to the JSON file with error handling."""
    global config
    
    logging.info(f"Attempting to update configuration file: {config_file}")
    try:
        
        config_dir = os.path.dirname(config_file)
        if config_dir:
            os.makedirs(config_dir, exist_ok=True)
        with open(config_file, "w", encoding="utf-8") as f:
            
            json.dump(config, f, indent=4, ensure_ascii=False)
        logging.info("✅ Configuration file updated successfully.")
    except (IOError, OSError) as e:
        
        print(f"[bold red]❌ File Error writing configuration to {config_file}: {e}[/bold red]")
        logging.error(f"File Error writing configuration to {config_file}: {e}")
    except TypeError as e:
        
        print(f"[bold red]❌ TypeError saving configuration: Data might not be JSON serializable. {e}[/bold red]")
        logging.error(f"TypeError saving configuration: {e}")
    except Exception as e:
        print(f"[bold red]❌ Unexpected error saving configuration: {e}[/bold red]")
        logging.exception("Unexpected error saving configuration.")


if __name__ == '__main__':
    print("\n" + "=" * 55)
    print(f"🚀 Instagram Scraper Script Started at {get_today()}")
    print("=" * 55 + "\n")
    main()
    print("\n" + "=" * 55)
    print(f"🏁 Script Finished at {get_today()}")
    print("=" * 55 + "\n")
