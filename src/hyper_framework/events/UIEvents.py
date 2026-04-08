from typing import Any
from dataclasses import dataclass

from src.hyper_framework.api.APICaller import ICommand
from src.hyper_framework.events.Events import IParsEventBase, IEventBase


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

