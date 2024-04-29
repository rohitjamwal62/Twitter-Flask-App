from os import system
from dependencies.sprint import *
from selenium import webdriver
# from seleniumwire import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from seleniumwire.utils import decode
import json, pickle
from tqdm import tqdm

config_file = os.path.abspath('./dev_mode.ini' if os.path.exists('./dev_mode.ini') else './config.ini')
config = ConfigParser()
config.read(config_file)

HEADLESS = True if config.get('Setup', 'headless', fallback='true').lower() == 'true' else False

def get_twitter_follows(usernames: list, max_refresh_times: int = 1):
    if not isinstance(usernames, list):
        raise TypeError("The argument 'usernames' be a list.")

    global driver
    cookies_file = os.path.join(config.get('Setup', 'temp_dir', fallback="temp"), "cookies.pkl")
    #region Internal Functions
    def _driver(action='start', url=None):

        global driver
        # setUpWebDriver
        if action == 'start':
            with contextlib.suppress(Exception):
                if driver:
                    try:
                        driver.get(url)
                    except:
                        _driver("restart",url)
                    return
            print()
            sprint(f"Starting Webdriver...{reset}", Type="info", end="\r")
        elif action == 'restart':
            if driver:
                driver.quit()
            sprint(f"Restarting Webdriver...{reset}", Type="info",  end="\r")
        elif action == 'refresh':
            sprint(f"Refreshing page...{reset}", Type="info",  end="\r")
            if driver:
                driver.refresh()
            return
        elif action in ("stop","quit","close","kill"):
            if driver:
                sprint(f"Stopping Webdriver...{reset}", Type="info",  end="\r")
                try:
                    driver.quit()
                    driver = None
                except:
                    sprint(f"Unable to stop Webdriver...{reset}", Type="alert",  end="\n")
                else:
                    sprint(f"🆗 Stopped Webdriver...{reset}", Type="info",  end="\n")
            return

        while True:
            try:
                options = webdriver.ChromeOptions()
                options.add_argument("--no-sandbox")
                options.add_argument("--disable-crash-reporter")
                options.add_argument("--disable-extensions")
                options.add_argument("--disable-in-process-stack-traces")
                options.add_argument("--disable-logging")
                options.add_argument("--disable-dev-shm-usage")
                options.add_argument('--log-level=3')
                options.add_argument('--blink-settings=imagesEnabled=false')
                options.add_argument("--disable-infobars")
                # options.add_argument("--output=/dev/null")
                # options.add_argument("--disable-gpu")
                if HEADLESS:
                    options.add_argument("--window-size=1920,1080")
                    options.add_argument("--headless")
                    options.add_argument('--disable-blink-features=AutomationControlled')  # Disable WebDriver
                    options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537')
                    import platform
                    os = platform.system()
                    if os == 'Windows':
                        useragent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.104 Safari/537.36"
                    elif os == 'Linux':
                        useragent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"
                    elif os == 'Darwin':  # 'Darwin' is the name returned by platform.system() for MacOS
                        useragent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36"

                    options.add_argument("--no-sandbox")
                    options.add_argument(f"user-agent={useragent}")
                    options.add_argument("--disable-web-security")
                    options.add_argument("--disable-xss-auditor")
                    
                    options.add_experimental_option("excludeSwitches", ["enable-automation", "load-extension"])
                driver = webdriver.Chrome(service=Service(
                    ChromeDriverManager().install()), options=options)
                

            except Exception as e:
                sprint(f"Unable to start webdriver... Trying again...\nException: {e}", Type="alert")
                with contextlib.suppress(Exception):
                    driver.quit()
            else:
                #! Try loading session cookies
                try:
                    driver.get("https://www.twitter.com")
                    cookies = pickle.load(open(cookies_file, "rb"))
                    for cookie in cookies:
                        driver.add_cookie(cookie)

                except Exception as e:
                    sprint(f"Error: {e}",Type="error")
                    error_info = traceback.format_exc()
                    sprint(error_info)
                else:
                    sprint("Session cookies loaded...")
                if url:
                    try:
                        driver.get(url)
                    except:
                        _driver("restart",url)
                break
        if action == 'start':
            sprint(f"🆗 Started Webdriver...{reset}", Type="info", end="\n")
        elif action == 'restart':
            sprint(f"🆗 Restarted Webdriver...{reset}", Type="info", end="\n")


    def wait_till_page_loads(timeout: int = 30):
        global driver
        times_checked = 0
        while True:
            page_state = driver.execute_script('return document.readyState;')
            if page_state == 'complete':
                break
            sleep(0.5)
            times_checked += 1
            if times_checked > timeout*2:
                sprint("Unable to load page", Type="error")
                return None, False

    def detect_captcha():
        global driver
        MAX_TRIES = 10
        tries = 0
        went_wrong = False
        while tries < MAX_TRIES:
            try:
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, '//html/body')))
                wait_till_page_loads()
                body_text = driver.find_element(By.XPATH, '//html/body').text
                # print(body_text)
                #! Check for captcha page
                if "unusual traffic" in body_text and "not a robot" in body_text:
                    # About this page
                    # Our systems have detected unusual traffic from your computer network. This page checks to see if it's really you sending the requests, and not a robot. Why did this happen?
                    # IP address: 103.139.56.216
                    # Time: 2023-06-28T10:01:37Z
                    # URL:
                    tries += 1
                    sprint(f"Captcha page detected... Trying again... {tries}/{MAX_TRIES}", Type="alert")
                    _driver("restart")
                elif "Something went wrong," in body_text:
                    went_wrong = True
                    sprint(f"Something went wrong... Trying again... {tries}/{MAX_TRIES}", Type="alert")
                    _driver("restart")
                    if went_wrong:
                        # give error and exit
                        sprint("Exiting script due to continous errors...", Type="error")
                        #  notiofy twitter might have added security measures and contact the developer akshay at +91 7897777779
                        sprint("Twitter might have added security measures...")
                        sprint("Contact the developer actualakshay@gmail.com at +91-7897777779")
                        sprint(f"For now you may disable {bold}get_users_following_data{reset} in {bold}config.ini{reset}")
                        _driver("kill")
                        exit(1)
                else:
                    break

            except Exception as e:
                sprint(f"Reloading page... {e}", Type="alert")
                with contextlib.suppress(Exception):
                    _driver("refresh")
                tries += 1
                if tries == MAX_TRIES:
                    sprint(
                        f"Continous error detected... Script will exit now... {e}", Type="error")
                    _driver("kill")
                    return None, False

    def _sign_in_twitter():
        global driver
        #! Signin
        url = "https://twitter.com/i/flow/login"
        _driver("start", url)
        detect_captcha()

        #! Logging in first
        sprint("Logging in into Twitter", Type="info", end="\r")

        with contextlib.suppress(Exception):
            fields = [
                {
                    "path":'//input[@autocomplete="username"]',
                    "send_keys":config.get('Twitter', 'username') + Keys.ENTER
                },
                {
                    "path":'//input[@autocomplete="current-password"]',
                    "send_keys":config.get('Twitter', 'password') + Keys.ENTER
                },
            ]
            for input_field in fields:
                WebDriverWait(driver, 5).until(
                    EC.visibility_of_element_located((By.XPATH, input_field["path"])))
                input_box = driver.find_element(By.XPATH, input_field["path"])
                input_box.clear()
                input_box.send_keys(input_field["send_keys"])


            wait_till_page_loads()
            wait_for = 30
            for i in range(0, wait_for):
                if driver.current_url.endswith("home"):
                    sprint("Logging in into Twitter", Type="success")
                    # After logging in, save cookies
                    if not os.path.exists(config.get('Setup', 'temp_dir', fallback="temp")):
                        os.mkdir(config.get('Setup', 'temp_dir', fallback="temp"))
                    pickle.dump(driver.get_cookies() , open(cookies_file,"wb"))
                    driver.minimize_window()
                    break
                if i==wait_for-1:
                    sprint("Logging in into Twitter", Type="error")
                    return None, False
                sleep(1)

    #endregion


    if not os.path.exists(cookies_file):
        _sign_in_twitter()
    else:
        _driver("start")
        driver.minimize_window()


    userdata = {}
    try:
        for n, username in enumerate(tqdm(usernames,desc="Scraping users followers/following")):

            userdata[username] = {
                        "following": [],
                        "followers": [],
                        }
            #region Following/Followers Scraping
            process_data = [
                                {
                                    "url":f"https://twitter.com/{username}/following",
                                    "key":"following",
                                    "request_regex":"Following?variables"
                                },
                                {
                                    "url":f"https://twitter.com/{username}/followers",
                                    "key":"followers",
                                    "request_regex":"Followers?variables"

                                    }
                            ]
            for data in process_data:

                for i in range(0, max_refresh_times):
                    while True:
                        _driver("start", data["url"])
                        detect_captcha()
                        if not driver.current_url.endswith(data["key"]):
                            _sign_in_twitter()
                        else:
                            break
                        sleep(1)
                    with contextlib.suppress(Exception):
                        WebDriverWait(driver, 10).until(
                            EC.visibility_of_element_located((By.XPATH, '//div[@data-testid="cellInnerDiv"]')))
                    for request in driver.requests:
                        if data["request_regex"] in request.url and request.response:
                            json_body = decode(request.response.body, request.response.headers.get('Content-Encoding', 'identity'))
                            json_body = json.loads(json_body)
                            for instruction in json_body["data"]["user"]["result"]["timeline"]["timeline"]["instructions"]:
                                if instruction["type"] == "TimelineAddEntries":
                                    json_body = instruction["entries"]

                                if len(json_body) > 0:
                                    new_body = []
                                    for entry in json_body:
                                        try:
                                            rest_id = entry["content"]["itemContent"]["user_results"]["result"]["rest_id"]
                                            user_name = entry["content"]["itemContent"]["user_results"]["result"]["legacy"]["screen_name"]
                                            new_body.append(
                                                {
                                                    "id": rest_id,
                                                    "username":user_name
                                                    }
                                                )
                                        except KeyError:
                                            continue
                                        except TypeError:
                                            continue

                                    json_body = new_body
                                    userdata[username][data["key"]].extend(json_body)
                                    # Create a new list with duplicates removed
                                    userdata[username][data["key"]] = list({v['id']:v for v in userdata[username][data["key"]]}.values())

                            # sprint(f'{data["key"]} {len(userdata[username][data["key"]])}')
                    # sprint_wait()
                    sleep(0.3)

            #endregion
    except Exception as e:
        sprint(f"Error: {e}", Type="error")
        error_info = traceback.format_exc()
        sprint(error_info)
        return None, False

    return userdata, True

