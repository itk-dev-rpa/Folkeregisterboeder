"""This module handles interaction with KMD Nova."""

import os
import uuid
from datetime import datetime
from io import BytesIO
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, CaseParty, Caseworker, Department, Document

from robot_framework import config


# def login(orchestrator_connection: OrchestratorConnection) -> webdriver.Chrome:
#     """Open a Chrome browser and login to KMD Nova.

#     Args:
#         orchestrator_connection: The connection to Orchestrator.

#     Returns:
#         A browser logged in to KMD Nova.
#     """
#     nova_creds = orchestrator_connection.get_credential(config.NOVA_CREDS)

#     browser = webdriver.Chrome()
#     browser.maximize_window()

#     browser.get("http://kmdnovaesdh.kmd.dk/")

#     wait = WebDriverWait(browser, 20)
#     wait.until(EC.element_to_be_clickable((By.ID, "inputUsername")))

#     browser.find_element(By.ID, "inputUsername").send_keys(nova_creds.username)
#     browser.find_element(By.ID, "inputPassword").send_keys(nova_creds.password)
#     browser.find_element(By.ID, "logonBtn").click()

#     browser.minimize_window()

#     return browser


# def send_digital_post(browser: webdriver.Chrome, document_id: str) -> None:
#     """Open a document in KMD Nova and send it as Digital Post.

#     Args:
#         browser: A browser logged in to KMD Nova.
#         document_id: The id of the document e.g. D2024-123456
#     """
#     browser.maximize_window()

#     browser.get(f"https://capwebwlbs-wm2q2012.kmd.dk/KMDNovaESDH/soegning/dokumenter/{document_id}")

#     wait = WebDriverWait(browser, 20)

#     more_button = wait.until(EC.element_to_be_clickable((By.ID, "document_details_show_multi_function")))
#     more_button.click()

#     browser.find_element(By.CSS_SELECTOR, "span.test-send-digital-post").click()

#     # Wait for the popup to load properly by expanding the 'Flere oplysninger' panel and checking the 'IO Manager aftale' select element.
#     wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "div.test-moreinfo-panel minor-collapsible-panel-header"))).click()
#     wait.until(EC.text_to_be_present_in_element_value((By.ID, "model_digitalPost_AgreementKey"), 'af3156e4-c3b0-4c53-ad5f-a3b8c36f89d1'))

#     send_button = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#nova-dialog button.test-send")))
#     send_button.click()

#     # Wait for confirmation popup
#     wait.until(EC.visibility_of_element_located((By.ID, "popup-notification")))
#     # TODO

#     browser.minimize_window()


def create_case(cpr: str, name: str, nova_access: NovaAccess) -> tuple[str, str]:
    """Create a case in KMD Nova on the given cpr number.

    Args:
        cpr: The cpr of the person to create the case on.
        name: The name of the person to create the case on.
        nova_access: The NovaAccess object used to authenticate.

    Returns:
        The uuid and number of the created case.
    """

    party = CaseParty(
        role="Primær",
        identification_type="CprNummer",
        identification=cpr,
        name=name
    )

    caseworker = Caseworker(
        name='svcitkopeno svcitkopeno',
        ident='AZX0080',
        uuid='0bacdddd-5c61-4676-9a61-b01a18cec1d5'
    )

    department = Department(
        id=818485,
        name="Borgerservice",
        user_key="4BBORGER"
    )

    case_uuid = str(uuid.uuid4())
    case_title = "Bøder efter CPR lovens § 57"

    case = NovaCase(
        uuid=case_uuid,
        title=case_title,
        case_date=datetime.now(),
        progress_state="Opstaaet",
        case_parties=[party],
        kle_number="23.05.13",
        proceeding_facet="G01",
        sensitivity="Fortrolige",
        caseworker=caseworker,
        responsible_department=department,
        security_unit=department,
    )

    nova_cases.add_case(case, nova_access)

    # Get the case back from Nova to get the case number
    # It might take some time for the case to be created so try a few times
    for _ in range(5):
        cases = nova_cases.get_cases(nova_access, cpr=cpr, case_title=case_title)
        for case in cases:
            if case.uuid == case_uuid:
                return case_uuid, case.case_number

        time.sleep(2)

    raise RuntimeError("Couldn't find case.")


def add_letter_to_case(case_uuid: str, document_file: BytesIO, nova_access: NovaAccess) -> str:
    """Add a letter document to the given case.

    Args:
        case_uuid: The uuid of the case to add the letter to.
        document_file: The document file.
        nova_access: The NovaAccess object used to authenticate.

    Returns:
        The uuid of the document.
    """
    doc_uuid = nova_documents.upload_document(document_file, "Bøde - For sent anmeldt flytning.docx", nova_access)

    # TODO: Move to args
    caseworker = Caseworker(
        name='svcitkopeno svcitkopeno',
        ident='AZX0080',
        uuid='0bacdddd-5c61-4676-9a61-b01a18cec1d5'
    )

    document = Document(
        uuid=doc_uuid,
        title="Bøde - For sent anmeldt flytning",
        sensitivity='Fortrolige',
        document_type="Udgående",
        description="Oprettet af robot.",
        approved=True,
        category_uuid='92e1a314-d0f7-4b99-b199-1ecd88f3a999',  # Afgørelse
        caseworker=caseworker
    )

    nova_documents.attach_document_to_case(case_uuid, document, nova_access)

    return doc_uuid


def add_invoice_to_case(case_uuid: str, document_file: BytesIO, nova_access: NovaAccess) -> None:
    """Add an invoice document to the given case.

    Args:
        case_uuid: The uuid of the case to add the letter to.
        document_file: The document file.
        nova_access: The NovaAccess object used to authenticate.
    """
    doc_uuid = nova_documents.upload_document(document_file, "Faktura.pdf", nova_access)

    # TODO: Move to args
    caseworker = Caseworker(
        name='svcitkopeno svcitkopeno',
        ident='AZX0080',
        uuid='0bacdddd-5c61-4676-9a61-b01a18cec1d5'
    )

    document = Document(
        uuid=doc_uuid,
        title="Faktura",
        sensitivity='Fortrolige',
        document_type="Internt",
        description="Oprettet af robot.",
        approved=True,
        category_uuid='aa015e27-669c-4934-a661-46900351f0aa',  # Dokumentation
        caseworker=caseworker
    )

    nova_documents.attach_document_to_case(case_uuid, document, nova_access)


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Nova test", conn_string, crypto_key, "")
    b = login(oc)
    for i in range(10):
        send_digital_post(b, "D2024-140420")
    print("hej")
