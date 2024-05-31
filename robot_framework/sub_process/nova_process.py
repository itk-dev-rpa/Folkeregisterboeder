"""This module handles interaction with KMD Nova."""

import uuid
from datetime import datetime
from io import BytesIO
import time

from itk_dev_shared_components.kmd_nova.authentication import NovaAccess
from itk_dev_shared_components.kmd_nova import nova_cases, nova_documents
from itk_dev_shared_components.kmd_nova.nova_objects import NovaCase, CaseParty, Caseworker, Department, Document


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

    # TODO
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
