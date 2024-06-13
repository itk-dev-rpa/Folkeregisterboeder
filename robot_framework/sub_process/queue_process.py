"""This module handles interactions with the Orchestrator Queue including creating new queue elements from emails."""

import json
from datetime import datetime, timedelta

from OpenOrchestrator.orchestrator_connection.connection import OrchestratorConnection
from OpenOrchestrator.database.queues import QueueStatus
from itk_dev_shared_components.graph import mail as graph_mail

from robot_framework import config
from robot_framework.sub_process import email_process, excel
from robot_framework.sub_process.task import Task


CURRENT_REFERENCE = None


def get_next_task(orchestrator_connection: OrchestratorConnection) -> Task | None:
    """Get the next queue element to take the next step.
    Prioritize the queue elements in the following order:
    1. In progress between step 5 and 6 with more than 10 minutes between.
    2. In progress.
    3. New.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        The next queue element to process if any.
    """
    global CURRENT_REFERENCE  # pylint: disable=global-statement

    # Check for in progress elements
    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=CURRENT_REFERENCE, status=QueueStatus.IN_PROGRESS)

    # Check for a queue element in between step 5 and 6
    for queue_element in queue_elements:
        message_dict = json.loads(queue_element.message)

        # Check if the queue element is between step 5 and 6
        if message_dict['invoice_date'] is not None:
            # Check if more than 10 minutes have passed
            invoice_date = datetime.fromisoformat(message_dict['invoice_date'])
            if (datetime.today() - invoice_date) >= timedelta(minutes=10):
                CURRENT_REFERENCE = queue_element.reference
                return Task.from_queue_element(queue_element)

    # Find another in progress queue element
    for queue_element in queue_elements:
        message_dict = json.loads(queue_element.message)

        # Check if the queue element is not between step 5 and 6
        if message_dict['invoice_date'] is None:
            CURRENT_REFERENCE = queue_element.reference
            return Task.from_queue_element(queue_element)

    # Get a new queue element
    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=CURRENT_REFERENCE, status=QueueStatus.NEW, limit=1)
    if queue_elements:
        CURRENT_REFERENCE = queue_elements[0].reference
        return Task.from_queue_element(queue_elements[0])

    return None


def update_queue_element(orchestrator_connection: OrchestratorConnection, task: Task):
    """Update the queue element associated with the given task object.

    Args:
        orchestrator_connection: The connection to Orchestrator.
        task: The task object.
    """
    _, message = task.to_json_strings()

    if task.journal_date:
        orchestrator_connection.set_queue_element_status(task.queue_element_id, status=QueueStatus.DONE, message=message)
    else:
        orchestrator_connection.set_queue_element_status(task.queue_element_id, status=QueueStatus.IN_PROGRESS, message=message)


def is_queue_empty(orchestrator_connection: OrchestratorConnection) -> bool:
    """Check if there are currently any new or in progress queue elements in the queue.

    Args:
        orchestrator_connection: The connection to Orchestrator.

    Returns:
        True if no queue elements are new or in progress.
    """
    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, status=QueueStatus.IN_PROGRESS)

    if queue_elements:
        return False

    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, status=QueueStatus.NEW)

    if queue_elements:
        return False

    return True


def check_queue_and_email(orchestrator_connection: OrchestratorConnection):
    """Check if the queue is empty. If it is check if there are any emails waiting to
    be inserted into the queue. Only insert one email.

    Args:
        orchestrator_connection: The connection to Orchestrator.
    """
    if not is_queue_empty(orchestrator_connection):
        return

    approved_users = json.loads(orchestrator_connection.process_arguments)["approved users"]

    graph_access = email_process.create_graph_access(orchestrator_connection)
    emails = email_process.get_emails(graph_access)

    email_info = None
    for email in emails:
        email_info = email_process.get_email_data(email, graph_access)
        if email_info.receiver_ident not in approved_users:
            email_process.send_rejection(email_info.receiver_email)
            graph_mail.delete_email(email, graph_access)
            email_info = None
        else:
            email_process.send_acceptance(email_info.receiver_email)
            graph_mail.delete_email(email, graph_access)
            break

    if email_info:
        tasks = excel.read_excel(email_info.excel_file)
        reference = f"{email_info.receiver_email};{datetime.today().isoformat()}"

        for task in tasks:
            data, _ = task.to_json_strings()

            orchestrator_connection.create_queue_element(
                queue_name=config.QUEUE_NAME,
                reference=reference,
                data=data,
                created_by="Robot"
            )


def do_status_update(orchestrator_connection: OrchestratorConnection):
    """Send a status update on the queue elements that have been handled in this run.

    Args:
        orchestrator_connection: The connection to Orchestrator.
    """
    if not CURRENT_REFERENCE:
        orchestrator_connection.log_info("No queue elements to report on.")
        return

    orchestrator_connection.log_info(f"Doing status on '{CURRENT_REFERENCE}'")

    queue_elements = orchestrator_connection.get_queue_elements(config.QUEUE_NAME, reference=CURRENT_REFERENCE)
    tasks = [Task.from_queue_element(qe) for qe in queue_elements]

    receiver = CURRENT_REFERENCE.split(";")[0]

    excel_sheet = excel.write_excel(tasks)
    email_process.send_status(receiver, excel_sheet)
