"""This module contains the main process of the robot."""

import os
from datetime import datetime, timedelta
import json

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.sap import multi_session

from robot_framework.sub_process import queue_process, eflyt, nova_process, word_process, sap, digital_post
from robot_framework import config


START_TIME = datetime.today()


def process(orchestrator_connection: OrchestratorConnection) -> None:
    """Do the primary process of the robot."""
    orchestrator_connection.log_trace("Running process.")

    queue_process.check_queue_and_email(orchestrator_connection)

    sap_session = multi_session.get_all_sap_sessions()[0]

    nova_creds = orchestrator_connection.get_credential(config.NOVA_API)
    nova_access = NovaAccess(nova_creds.username, nova_creds.password)

    digital_post_header = digital_post.get_headers(orchestrator_connection)
    digital_post_key = json.loads(orchestrator_connection.get_credential(config.NOVA_KEY).password)

    eflyt_browser = eflyt.login(orchestrator_connection)

    for i in range(1000):
        orchestrator_connection.log_trace(f"Beginning loop {i}")

        if datetime.today() - START_TIME >= timedelta(minutes=60):
            orchestrator_connection.log_info("Process has exceeded 60 minutes.")
            break

        task = queue_process.get_next_task(orchestrator_connection)
        if task is None:
            orchestrator_connection.log_info("No more queue elements for now.")
            break

        # Create case
        if task.nova_case_uuid is None:
            task.nova_case_uuid, task.nova_case_number = nova_process.create_case(task.cpr, task.name, nova_access)

        # Get address
        elif task.address is None:
            address, journal_path = eflyt.search_case_info(eflyt_browser, task.eflyt_case_number)
            with open(journal_path, 'rb') as file:
                nova_process.add_journal_to_case(task.nova_case_uuid, file, nova_access)

            task.address = address

        # Generate and upload letter
        elif task.document_uuid is None:
            template_path = r"robot_framework\docs\Din flytning er anmeldt for sent.docx"
            result_path = "letter.docx"

            fine_rate = sap.get_fine_rate(task.move_date + timedelta(days=6))

            address_lines = nova_process.get_address_lines(task.cpr, nova_access)

            keywords_replacements = {
                "SENDEDATO": word_process.format_date(datetime.today()),
                "ANMELDELSESDATO": word_process.format_date(task.register_date),
                "FLYTTEDATO": word_process.format_date(task.move_date),
                "ADRESSE1": address_lines[0],
                "ADRESSE2": address_lines[1],
                "ADRESSE3": address_lines[2],
                "ADRESSE4": address_lines[3],
                "ADRESSE5": address_lines[4],
                "FLYTTE_ADRESSE": task.address,
                "BELØB": str(fine_rate),
                "KONTAKT": task.case_worker_name,
                "SAGSNUMMER": task.nova_case_number
            }

            word_process.replace_keywords_in_word_template(template_path, result_path, keywords_replacements)
            with open(result_path, 'rb') as file:
                document_uuid = nova_process.add_letter_to_case(task.nova_case_uuid, file, nova_access)
            os.remove(result_path)

            task.document_uuid = document_uuid

        # Send letter
        elif task.letter_date is None:
            digital_post.send_digital_post(digital_post_header, digital_post_key, task.nova_case_uuid, task.document_uuid, task.cpr)
            task.letter_date = datetime.today()

        # Create invoice
        elif task.invoice_date is None:
            sap.create_invoice(sap_session, task.cpr, task.move_date, task.register_date, task.address)
            sap.do_immediate_invoicing(sap_session, task.cpr)
            task.invoice_date = datetime.today()

        # Save and upload invoice
        elif task.journal_date is None:
            invoice_path = sap.save_invoice(sap_session, task.cpr, task.invoice_date)
            with open(invoice_path, 'rb') as file:
                nova_process.add_invoice_to_case(task.nova_case_uuid, file, nova_access)
            os.remove(invoice_path)
            task.journal_date = datetime.today()

        # Update queue element
        queue_process.update_queue_element(orchestrator_connection, task)
    else:
        orchestrator_connection.log_info("Loop limit reached.")

    queue_process.do_status_update(orchestrator_connection)


if __name__ == '__main__':
    conn_string = os.getenv("OpenOrchestratorConnString")
    crypto_key = os.getenv("OpenOrchestratorKey")
    oc = OrchestratorConnection("Bøde test", conn_string, crypto_key, '{"approved users":["az68933"]}')
    process(oc)
