# Instagram Hashtag Scraper 📸🔍

A Python project for scraping Instagram posts based on specific hashtags. This tool uses **Selenium** for browser automation and **BeautifulSoup** for scraping content from Instagram. It's designed to fetch posts by hashtag, with customizable options to automate login, scrape content, and interact with Instagram posts.


---

## Features ✨

- **Hashtag Scraping** 🏷️: Scrape Instagram posts by hashtag (e.g., `#nature`, `#technology`).
- **Automatic Login** 🔑: Logs in to Instagram using provided credentials.
- **Headless Browser** 🌐: Supports headless mode for automation without GUI.
- **Customizable Scraping** ⚙️: Allows user-defined post count and result filtering.
- **Stealth Mode** 🕶️: Prevents detection of Selenium automation using the `selenium-stealth` library.
- **Logging** 📝: Built-in logging system for tracking progress and errors.

---

## Requirements 📋

- Python 3.6+
- Chrome WebDriver (ensure it's compatible with your Chrome version)
- Required Python packages (listed below)

---

## Installation ⚙️

1. Clone the repository:
   ```bash
   git clone https://github.com/xlastfire/Instagram-Hashtag-Scraper.git
   cd instagram-hashtag-scraper
   ```

2. Create a virtual environment (optional but recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # For Windows use: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Setup 🔧

1. Download and install **ChromeDriver**:
   - Go to [ChromeDriver downloads](https://sites.google.com/a/chromium.org/chromedriver/) and download the driver for your operating system.
   - Ensure the version of ChromeDriver matches your installed version of Chrome.

2. Place the **chromedriver** executable in the appropriate path or specify it in the `config.json` file.

---

## Usage 🚀

1. **Create a `config.json` file** in the project root with your Instagram credentials and preferences.

   Example `config.json`:

   ```json
   {
     "username": "your_username",
     "password": "your_password",
     "headless": false, 
     "download_directory": "/path/to/download",
     "disable_images": false,
     "disable_videos": false,
     "driver_executable_path": "/path/to/chromedriver",
     "disable_saving_password": true,
     "select_results": true,
     "default_timeout": 30,
     "log_file": "scraper.log",
     "post_count": 50,
     "save_directory": "/path/to/save",
     "search_queries": ["nature", "technology"]
   }
   ```

2. **Run the scraper** by executing the following in your terminal:

   ```bash
   python scraper.py
   ```

   This will start the script, log you into Instagram, search for posts based on your provided hashtag(s), and scrape the content.

---

## Configuration ⚙️

The `config.json` file should contain the following keys:

- **username**: Your Instagram username.
- **password**: Your Instagram password.
- **headless**: Set to `true` for headless operation (without GUI). **(Note: Didn't check)**
- **download_directory**: Path where downloaded media will be stored.
- **disable_images**: Set to `true` to disable image loading in the browser.
- **disable_videos**: Set to `true` to disable video loading in the browser.
- **driver_executable_path**: Path to the ChromeDriver executable.
- **disable_saving_password**: Set to `true` to disable saving passwords.
- **select_results**: Set to `true` to allow interactive selection of search results.
- **default_timeout**: Timeout value (in seconds) for waiting for elements to load.
- **log_file**: Path to the log file where logs will be saved.
- **post_count**: Number of posts to scrape.
- **save_directory**: Directory where scraped posts will be saved.
- **search_queries**: List of hashtags to search for on Instagram (e.g., `#nature`, `#technology`).

---

## Logging 📝

The scraper uses Python's `logging` module to log events during execution. Logs are saved to the file specified in the `log_file` field in `config.json`. By default, logs are also printed to the console for real-time monitoring.

You can adjust the logging level by modifying the `level` parameter in the `setup_logging` function.


---

## License 📄

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

Made with ❤️ by [**xlastfire**](https://github.com/xlastfire)

---


