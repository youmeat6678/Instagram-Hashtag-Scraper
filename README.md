### Instagram Hashtag Scraper 🌟


This is an **Instagram hashtag and user reels scraping tool** 🤖 that allows you to extract data from Instagram's search results and user profiles. It utilizes **Selenium with ChromeDriver** 🚗 for web automation and **BeautifulSoup** 🥣 for parsing HTML content.


---

## Features ✨
- **Search Results Scraping**: Extract post links based on specific hashtags 🔍.
- **User Reels Scraping**: Scrape reel links from user profiles 🎬.
- **Configurable Options**: Customize behavior via `config.json` (e.g., headless mode, timeouts) ⚙️.
- **Error Handling**: Robust error handling for network issues, login failures, and unexpected changes in Instagram's layout 🚨.
- **Logging**: Detailed logs for debugging and tracking progress 📝.
- **Progress Visualization**: Real-time progress updates using the `rich` library 📊.

---

## Requirements 🛠️
To run this scraper, ensure you have the following installed:
- **Python 3.8 or higher** 🐍
- **Google Chrome** (latest version recommended) 🌐
- **ChromeDriver** (matching your Chrome version) 🚗

### Install Dependencies
Run the following command to install the required Python packages:
```bash
pip install -r requirements.txt
```

Dependencies include:
- `selenium`
- `beautifulsoup4`
- `rich`
- `webdriver-manager` (optional, for automatic driver management)

---

## Setup Instructions 🚀

1. **Clone the Repository** 📂
   ```bash
   git clone https://github.com/xlastfire/Instagram-Hashtag-Scraper.git
   cd Instagram-Hashtag-Scraper
   ```

2. **Install Dependencies** 💻
   ```bash
   pip install -r requirements.txt
   ```

3. **Download ChromeDriver** 🚗
   - Download the ChromeDriver executable that matches your installed version of Google Chrome from the [official site](https://sites.google.com/chromium.org/driver/).
   - Place the `chromedriver` executable in a directory of your choice and update the path in `config.json`.

4. **Update Configuration** 📝
   Edit the `config.json` file to include:
   - Your Instagram credentials (`username` and `password`) 🔑.
   - Desired queries (hashtags or usernames) under the `queries` section.

5. **Run the Script** ▶️
   Execute the scraper:
   ```bash
   python scraper.py
   ```

---

## Configuration ⚙️

The `config.json` file contains all configurable options. Below is an example configuration:

```json
{
  "username": "your_instagram_username",
  "password": "your_instagram_password",
  "driver_executable_path": "/path/to/chromedriver",
  "headless": true,
  "disable_images": true,
  "disable_videos": false,
  "default_timeout": 10,
  "search_post_count": 100,
  "follow_user_reels": false,
  "log_file": "logs/instagram.log",
  "search_path": "data/search/",
  "user_reels_path": "data/user_reels/",
  "queries": {
    "#nature": "search",
    "natgeo": "user_reels"
  },
  "completed_queries": {}
}
```

### Key Fields 🔑
- `username`, `password`: Your Instagram login credentials 🔑.
- `driver_executable_path`: Path to the ChromeDriver executable 🚗.
- `headless`: Run browser in headless mode (no GUI) 👻.
- `disable_images`, `disable_videos`: Optimize performance by disabling media loading 🖼️🎬.
- `search_post_count`: Target number of posts to scrape per search query 🔢.
- `follow_user_reels`: Automatically follow users when scraping their reels 👥.
- `queries`: Dictionary of queries to process, where keys are hashtags or usernames and values are either `"search"` or `"user_reels"`.

---

## Usage 📋

### Scraping Hashtags 🔍
Add your desired hashtags to the `queries` section in `config.json` with the value `"search"`. For example:
```json
"queries": {
  "#nature": "search",
  "#travel": "search"
}
```
Run the script:
```bash
python scraper.py
```
Scraped data will be saved in the directory specified by `search_path`.

### Scraping User Reels 🎬
Add usernames to the `queries` section with the value `"user_reels"`. For example:
```json
"queries": {
  "natgeo": "user_reels",
  "bbcearth": "user_reels"
}
```
Run the script:
```bash
python scraper.py
```
Reel links will be saved in the directory specified by `user_reels_path`.

### Logs 📝
Detailed logs are stored in the file specified by `log_file`. Use these logs to debug issues or track progress.

---

## Contributing 👥

Contributions are welcome! If you'd like to contribute, please follow these steps:
1. Fork the repository 🍴.
2. Create a new branch for your feature or bug fix 🌿.
3. Submit a pull request with a clear description of your changes 📝.

Please ensure your code adheres to the project's coding standards and includes appropriate documentation.

---

## License 📄

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## Disclaimer ⚠️

This tool is intended for educational and research purposes only. Ensure you comply with Instagram's [Terms of Service](https://help.instagram.com/581066165581870) before using it. The author is not responsible for any misuse or violations of terms resulting from the use of this script.
