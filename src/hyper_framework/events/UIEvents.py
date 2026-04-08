from typing import Any
from dataclasses import dataclass

try:
    from hyper_framework.api.APICaller import ICommand  # optional consumer API interface
except Exception:
    ICommand = Any

from hyper_framework.events.Events import IParsEventBase, IEventBase


@dataclass
class CommandAutomationStart(IParsEventBase):
    command: ICommand
@dataclass
class CommandAutomationCompleted(IParsEventBase):
    command: ICommand
@dataclass
class CommandAutomationError(IParsEventBase):
    error: str
    command: Any
class CommandAutomationFinished(IEventBase):
    pass
@dataclass
class CommandAutomationWaitForEventSuccess(IParsEventBase):
    id_mark: str

