"""
Architecture / design-contract exceptions — errors that represent violations of
architectural contracts, interface obligations, and structural design rules.

Migrated from exceptions.py:
  - WrongImplementationException
"""

import inspect


class WrongImplementationException(Exception):
    """
    Raised when a function or class is used in a way that violates its implementation contract.

    e.g.::

        raise WrongImplementationException(restriction="此方法不可在 __init__ 中呼叫")
    """

    def __init__(self, restriction: str, message: str | None = None):
        if message is None:
            message = f"此函式不允許這樣使用 !! \n 限制：{restriction}"
        super().__init__(message)
        self.restriction = restriction

    def __str__(self) -> str:
        frame = inspect.currentframe().f_back
        while frame:
            if "self" in frame.f_locals:
                calling_class = frame.f_locals["self"].__class__.__name__
                return (
                    f"錯誤：在類別 '{calling_class}' 中發生 WrongImplementationException。\n"
                    f"{super().__str__()}"
                )
            frame = frame.f_back
        return super().__str__()


class AbstractMethodNotImplementedError(Exception):
    """
    Raised when an abstract method is called without a concrete implementation
    in the subclass (use instead of or alongside Python's ``NotImplementedError``
    when you want a structured, domain-aware error).
    """

    def __init__(self, method: str = "", cls: str = "", message: str | None = None):
        if message is None:
            if method and cls:
                message = f"Abstract method '{method}' in class '{cls}' must be implemented by a subclass."
            elif method:
                message = f"Abstract method '{method}' must be implemented by a subclass."
            else:
                message = "This abstract method must be implemented by a subclass."
        super().__init__(message)
        self.method = method
        self.cls = cls


class InterfaceContractError(Exception):
    """
    Raised when a class claims to implement an interface/protocol but fails to
    honour its required contract (missing methods, wrong signatures, etc.).
    """

    def __init__(self, cls: str = "", interface: str = "", detail: str = "", message: str | None = None):
        if message is None:
            if cls and interface:
                msg = f"Class '{cls}' does not fulfil the contract of interface '{interface}'"
                message = (msg + f": {detail}.") if detail else (msg + ".")
            else:
                message = f"Interface contract violation: {detail}." if detail else "Interface contract violation."
        super().__init__(message)
        self.cls = cls
        self.interface = interface
        self.detail = detail


class CircularDependencyError(Exception):
    """Raised when a circular dependency is detected between components or modules."""

    def __init__(self, cycle: list | None = None, message: str | None = None):
        if message is None:
            if cycle:
                chain = " → ".join(str(c) for c in cycle)
                message = f"Circular dependency detected: {chain}."
            else:
                message = "A circular dependency was detected."
        super().__init__(message)
        self.cycle = cycle or []


class ComponentNotRegisteredError(Exception):
    """Raised when a required component or plugin is not found in the registry."""

    def __init__(self, component: str = "", message: str | None = None):
        if message is None:
            if component:
                message = f"Component '{component}' is not registered. Register it before use."
            else:
                message = "The requested component is not registered."
        super().__init__(message)
        self.component = component


class ComponentAlreadyRegisteredError(Exception):
    """Raised when a component is registered more than once and duplicates are not allowed."""

    def __init__(self, component: str = "", message: str | None = None):
        if message is None:
            if component:
                message = f"Component '{component}' has already been registered."
            else:
                message = "A component has already been registered under this key."
        super().__init__(message)
        self.component = component


class LayerViolationError(Exception):
    """
    Raised when code in one architectural layer illegally accesses or depends on
    a layer it should not (e.g. domain layer importing from infrastructure).
    """

    def __init__(self, from_layer: str = "", to_layer: str = "", message: str | None = None):
        if message is None:
            if from_layer and to_layer:
                message = f"Architectural layer violation: '{from_layer}' must not depend on '{to_layer}'."
            else:
                message = "An architectural layer violation was detected."
        super().__init__(message)
        self.from_layer = from_layer
        self.to_layer = to_layer
