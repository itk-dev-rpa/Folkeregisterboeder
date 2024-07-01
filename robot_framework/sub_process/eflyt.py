"""This module handles interaction with eFlyt."""

from datetime import date
import os
import time

from selenium import webdriver
from selenium.webdriver.common.by import By

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config


DOWNLOAD_DIR = os.path.join(os.getcwd(), "downloads")


def login(orchestrator_connection: OrchestratorConnection) -> webdriver.Chrome:
    """Opens a browser and logs in to Eflyt.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        A selenium browser object.
    """
    eflyt_creds = orchestrator_connection.get_credential(config.EFLYT_CREDS)

    options = webdriver.ChromeOptions()
    options.add_experimental_option("prefs", {"download.default_directory": DOWNLOAD_DIR})
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)

    browser = webdriver.Chrome(options)
    browser.maximize_window()
    browser.get("https://notuskommunal.scandihealth.net/")

    user_field = browser.find_element(By.ID, "Login1_UserName")
    user_field.send_keys(eflyt_creds.username)

    pass_field = browser.find_element(By.ID, "Login1_Password")
    pass_field.send_keys(eflyt_creds.password)

    browser.find_element(By.ID, "Login1_LoginImageButton").click()
    browser.minimize_window()

    return browser


def search_case_info(browser: webdriver.Chrome, case_number: str) -> tuple[str, str]:
    """Find the address of a given case in eFlyt and download the case journal.

    Args:
        browser: The browser object already logged in to eFlyt.
        case_number: The case number of the case to find.

    Returns:
        The address of the given case and the file path of the downloaded journal.
    """
    browser.maximize_window()

    browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_imgLogo").click()
    browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_btnClear").click()

    case_number_input = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_txtSagNr")
    case_number_input.clear()
    case_number_input.send_keys(case_number)

    from_date_input = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_txtdatoFra")
    to_date_input = browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_txtdatoTo")

    from_date_input.clear()
    from_date_input.send_keys("01-01-2020")

    to_date_input.clear()
    to_date_input.send_keys(date.today().strftime("%d-%m-%Y"))

    browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_btnSearch").click()

    address = browser.find_element(By.CSS_SELECTOR, "#ctl00_ContentPlaceHolder1_searchControl_GridViewSearchResult > tbody > tr:nth-child(2) > td:nth-child(5)").text
    address = address.strip()

    journal_path = get_journal(browser)

    # Go back to main page
    browser.get("https://notuskommunal.scandihealth.net/web/SuperSearch.aspx")

    browser.minimize_window()

    return address, journal_path


def get_journal(browser: webdriver.Chrome) -> str:
    """Download the case journal.

    Args:
        browser: The browser object already logged in to eFlyt and with the
        relevant case in the search results.

    Raises:
        RuntimeError: If any unexpected files are downloaded.
        TimeoutError: If the file isn't downloaded within 10 seconds.

    Returns:
        The path to the downloaded file.
    """
    # Clear download dir
    for f in os.listdir(DOWNLOAD_DIR):
        os.remove(os.path.join(DOWNLOAD_DIR, f))

    # Open case and get journal
    browser.execute_script("__doPostBack('ctl00$ContentPlaceHolder1$searchControl$GridViewSearchResult','cmdRowSelected$0')")
    browser.find_element(By.ID, "ctl00_ContentPlaceHolder2_ptFanePerson_stcPersonTab1_btnJournal").click()

    # Wait for file download
    for _ in range(10):
        files = os.listdir(DOWNLOAD_DIR)
        if files:
            if len(files) != 1:
                raise RuntimeError(f"An unexpected number of files where found in the downloads folder: {files}")

            if files[0].endswith(".pdf"):
                return os.path.join(DOWNLOAD_DIR, files[0])

        time.sleep(1)

    raise TimeoutError("Downloaded file didn't appear within 10 seconds.")
