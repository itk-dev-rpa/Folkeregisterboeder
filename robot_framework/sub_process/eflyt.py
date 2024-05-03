"""This module handles interaction with eFlyt."""

from datetime import date

from selenium import webdriver
from selenium.webdriver.common.by import By

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config


def login(orchestrator_connection: OrchestratorConnection) -> webdriver.Chrome:
    """Opens a browser and logs in to Eflyt.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        A selenium browser object.
    """
    eflyt_creds = orchestrator_connection.get_credential(config.EFLYT_CREDS)

    browser = webdriver.Chrome()
    browser.maximize_window()
    browser.get("https://notuskommunal.scandihealth.net/")

    user_field = browser.find_element(By.ID, "Login1_UserName")
    user_field.send_keys(eflyt_creds.username)

    pass_field = browser.find_element(By.ID, "Login1_Password")
    pass_field.send_keys(eflyt_creds.password)

    browser.find_element(By.ID, "Login1_LoginImageButton").click()
    browser.minimize_window()

    return browser


def search_case_address(browser: webdriver.Chrome, case_number: str) -> str:
    """Find the address of a given case in eFlyt.

    Args:
        browser: The browser object already logged in to eFlyt.
        case_number: The case number of the case to find the address for.

    Returns:
        The address of the given case.
    """
    browser.maximize_window()

    browser.find_element(By.ID, "ctl00_ContentPlaceHolder1_searchControl_imgLogo").click()

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

    browser.minimize_window()

    return address
