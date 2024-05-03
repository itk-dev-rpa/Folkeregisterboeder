from datetime import datetime
from dataclasses import dataclass, asdict, fields
import json
from typing import Optional, Self

from OpenOrchestrator.database.queues import QueueElement


@dataclass
# pylint: disable=too-many-instance-attributes
class Task:
    """A dataclass representing a single task."""
    task_date: datetime
    move_date: datetime
    register_date: datetime
    eflyt_case_number: str
    eflyt_categories: str
    eflyt_status: str
    cpr: str
    name: str

    address: Optional[str] = None
    nova_case_uuid: Optional[str] = None
    nova_case_number: Optional[str] = None
    document_uuid: Optional[str] = None
    letter_date: Optional[datetime] = None
    invoice_date: Optional[datetime] = None
    journal_date: Optional[datetime] = None

    queue_element_id: str = None

    def to_json_strings(self) -> tuple[str, str]:
        """Convert the Task to two json string representing the data and message part
        of a corresponding queue element.
        All datetime fields are converted to iso format.
        """
        task_dict = asdict(self)
        data_dict = dict(list(task_dict.items())[0:8])
        message_dict = dict(list(task_dict.items())[8:15])

        def datetime_encoder(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()

            raise TypeError(f"Object is not JSON serializable: {type(obj)}")

        return json.dumps(data_dict, default=datetime_encoder), json.dumps(message_dict, default=datetime_encoder)

    @classmethod
    def from_queue_element(cls, queue_element: QueueElement) -> Self:
        """Convert two json strings to a Task object.
        All datetime fields are converted from iso format.
        """
        data_dict = json.loads(queue_element.data)
        message_dict = json.loads(queue_element.message) if queue_element.message else {}

        task_dict = data_dict | message_dict

        for field in fields(cls):
            if field.type in (datetime, Optional[datetime]) and task_dict.get(field.name):
                task_dict[field.name] = datetime.fromisoformat(task_dict[field.name])

        return Task(**task_dict, queue_element_id=queue_element.id)
