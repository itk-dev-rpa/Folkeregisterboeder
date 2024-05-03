# Folkeregisterbøder (Udsendelse af afgørelser + Fakturering)


## Queue elements

A queue elements reference is a combination of the email address of the requester
and the timestamp of when the email was read.

E.g.:
`hello@mail.com;2024-04-01T00:00:00`

Queue elements should be created with the following data:

Queue element data:

```json
{
    "task_date": "iso date",
    "move_date": "iso date",
    "register_date": "iso date",
    "eflyt_case_number": "string",
    "eflyt_categories": "string",
    "eflyt_status": "string",
    "cpr": "string",
    "name": "string"
}

//Example:
{
    "date": "2024-04-01T00:00:00",
    "move_date": "2024-04-01T00:00:00",
    "register_date": "2024-04-20T00:00:00",
    "eflyt_case_number": "123456789",
    "eflyt_categories": "For sent anmeldt, Boligselskab",
    "eflyt_status": "I gang",
    "cpr": "8412893981",
    "name": "Testbruger Et"
}
```

During the process the message field of the queue element is used both for storing resulting data
and for tracking the progress of the queue element.

Queue element "message" (working data):

```json
{
    "address": "string",
    "nova_case_uuid": "string",
    "nova_case_number": "string",
    "document_id": "string",
    "letter_date": "iso date",
    "invoice_date": "iso date",
    "journal_date": "iso date"
}

//Example:
{
    "address": "Hejvej 1, 1234 Hejby",
    "nova_case_uuid": "8d50ee05-5799-4a7b-8c94-e86679f2a051",
    "nova_case_number": "S2024-12345",
    "document_id": "D2024-12345",
    "letter_date": "2024-04-29T13:24:33.273767",
    "invoice_date": "2024-04-29T13:25:33.273767",
    "journal_date": "2024-04-29T13:26:33.273767"
}
```

## Process flow

To improve error handling and processing time the robot has a special process flow.

A process consists of the following steps:

1. Get case address.
2. Create Nova case.
3. Generate and upload letter
4. Send letter.
5. Create invoice.
6. Journalize invoice.

After each step the respective queue element is updated to track the process.

There should be a waiting period of about 10 minutes between step 5 and 6, which means
the robot might need to continue on a second case before finishing the first to be
more time efficient.

To allow this the process will jump in and out after each step to check the queue to see what to do next.
If a queue element is in progress it will be prioritized over a new element. A queue element that
has waited more than 10 minutes between step 5 and 6 will be prioritized over other in progress queue elements.

## Process arguments

```json
{
    "approved users": [string, ...]
}
```

## Linting and Github Actions

This template is also setup with flake8 and pylint linting in Github Actions.
This workflow will trigger whenever you push your code to Github.
The workflow is defined under `.github/workflows/Linting.yml`.

