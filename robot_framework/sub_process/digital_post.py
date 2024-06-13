"""This module is responsible for sending Digital Post through the KMD Nova UI."""

import uuid

import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection

from robot_framework import config


def login(orchestrator_connection: OrchestratorConnection) -> webdriver.Chrome:
    """Open a Chrome browser and login to KMD Nova.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        A browser logged in to KMD Nova.
    """
    nova_creds = orchestrator_connection.get_credential(config.NOVA_CREDS)

    browser = webdriver.Chrome()
    browser.maximize_window()

    browser.get("http://kmdnovaesdh.kmd.dk/")

    wait = WebDriverWait(browser, 20)
    wait.until(EC.element_to_be_clickable((By.ID, "inputUsername")))

    browser.find_element(By.ID, "inputUsername").send_keys(nova_creds.username)
    browser.find_element(By.ID, "inputPassword").send_keys(nova_creds.password)
    browser.find_element(By.ID, "logonBtn").click()

    browser.minimize_window()

    return browser


def get_headers(orchestrator_connection: OrchestratorConnection) -> dict[str, str]:
    """Login to KMD Nova in the browser and extract the necessary info for a
    Digital Post Http request.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        A dictionary of headers used when sending Digital Post.
    """
    browser = login(orchestrator_connection)

    rv_token_l = browser.get_cookie("__RequestVerificationToken_L0tNRE5vdmFFU0RI0")['value']
    session_handler = browser.get_cookie("KMDLogonWebSessionHandler")['value']

    rv_token = browser.find_element(By.NAME, "__RequestVerificationToken").get_attribute("ncg-request-verification-token")

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "gzip, deflate, br, zstd",
        "Accept-Language": "en,da;q=0.9,en-GB;q=0.8,en-US;q=0.7",
        "Connection": "keep-alive",
        "Content-Type": "application/json;charset=UTF-8",
        "Cookie": f"kmdNovaIndstillingerCurrent=Standardgruppe; KMDLogonWebSessionHandler={session_handler}; __RequestVerificationToken_L0tNRE5vdmFFU0RI0={rv_token_l}",
        "RequestVerificationToken": rv_token
    }

    return headers


def send_digital_post(headers: dict, encryption_key: dict, case_uuid: str, doc_uuid: str, cpr: str):
    """Send Digital Post by using the unofficial api in KMD Nova.

    Args:
        headers: A header dict gotten from get_headers.
        encryption_key: A encryption key dict gotten from get_encryption_key.
        case_uuid: The uuid of the case of the document.
        doc_uuid: The uuid of the document to send.
        cpr: The cpr number of the receiver.
    """
    payload = {
        "digitalPost": {
            "BatchId": str(uuid.uuid4()),
            "Title": "Bøde - For sent anmeldt flytning",
            "Channel": {
                "Code": "DIGITALPOST",
                "Name": "Send til Digital Post / KMD Print"
            },
            "PostPriority": "B",
            "Key": encryption_key,
            "DocumentType": {
                "Id": "22fdd50b-b888-4bfd-b019-6399fd0f93f2",
                "Description": "Oprettet af KMD",
                "Name": "KMDSAGBREV1",
                "ShowReceipt": False,
                "AcceptReply": True,
                "CanCaseworkerEdit": True,
                "PostPriority": "B",
                "IsDefault": True
            },
            "AgreementKey": {
                "Id": "af3156e4-c3b0-4c53-ad5f-a3b8c36f89d1",
                "Name": "Aarhus"
            },
            "AcceptReply": True,
            "RemoveBlankAddressPage": False,
            "IsMassMerge": False,
            "Recipients": [
                {
                    "SearchObjectType": "Person",
                    "SearchObjectSubCategory": 0,
                    "Id": cpr,
                    "Country": {
                        "Country": {
                            "Code": "DK",
                            "Name": "Danmark"
                        },
                        "AnotherCode": False,
                        "CountryCode": None
                    },
                }
            ],
            "MainDocument": {
                "Silo": "UNKNOWN",
                "DocumentId": doc_uuid,
                "DocumentVersion": 1,
                "MetadataId": doc_uuid,
                "DocumentName": "Bøde - For sent anmeldt flytning",
                "FileType": "docx"
            },
            "Attachments": [
            ],
            "CaseId": case_uuid
        }
    }

    url = "https://capwebwlbs-wm2q2012.kmd.dk/KMDNovaESDH/api/ServiceRelayer/kmdnova/v1/digitalpost/SendDigitalPost"

    response = requests.post(url, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
