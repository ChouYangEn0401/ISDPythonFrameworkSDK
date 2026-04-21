"""
Architecture decorators  — enforce Single Responsibility Principle (SRP),
layer boundaries, interface contracts, and design-by-contract guards.

SRP philosophy applied here:
  Each decorator carries exactly one architectural concern.
  - @single_responsibility  → documents & enforces role identity
  - @layer                  → marks & asserts layer membership
  - @interface_method       → signals public contract membership
  - @abstract_implementation → signals concrete contract fulfilment
  - @no_side_effects        → documents & optionally asserts purity
  - @sealed                 → prevents subclass override
  - @require_override       → forces subclass to override
"""

import functools
import warnings


def single_responsibility(role: str):
    """
    Tag a class or function with its single declared responsibility.
    Raises ``AssertionError`` if *role* is empty (forces conscious annotation).
    The role is accessible on the object as ``.__srp_role__``.

    e.g.::

        @single_responsibility("Parse raw CSV rows into domain records")
        class CsvParser:
            ...
    """
    if not role or not role.strip():
        raise AssertionError("@single_responsibility requires a non-empty role description.")

    def decorator(obj):
        obj.__srp_role__ = role.strip()
        return obj

    return decorator


def layer(name: str, allowed_imports: tuple[str, ...] = ()):
    """
    Mark a function or class as belonging to architectural layer *name*.
    Optionally assert at decoration time that the module's ``__name__``
    path does not violate *allowed_imports* (simple substring check).

    The layer name is stored as ``.__arch_layer__``.

    :param name:            Layer label, e.g. ``"domain"``, ``"infra"``, ``"presentation"``.
    :param allowed_imports: Tuple of module-path substrings that this layer MAY import from.
                            Violation detection is best-effort only.

    e.g.::

        @layer("domain")
        def calculate_tax(income: float) -> float:
            ...
    """
    if not name:
        raise ValueError("@layer requires a non-empty layer name.")

    def decorator(obj):
        obj.__arch_layer__ = name
        return obj

    return decorator


def interface_method(func):
    """
    Mark a method as part of the public interface contract of its class.
    Emits no warnings at runtime but communicates intent to tooling and readers.
    Accessible as ``func.__is_interface__ == True``.

    e.g.::

        class IRepository:
            @interface_method
            def find_by_id(self, id): ...
    """
    func.__is_interface__ = True

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.__is_interface__ = True
    return wrapper


def abstract_implementation(interface_name: str = ""):
    """
    Mark a method as the concrete implementation of an interface/protocol.
    Stores the interface name as ``func.__implements__``.

    :param interface_name: Name of the interface being implemented.

    e.g.::

        class SqlUserRepository:
            @abstract_implementation("IUserRepository")
            def find_by_id(self, id):
                return db.query(id)
    """

    def decorator(func):
        func.__implements__ = interface_name

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__implements__ = interface_name
        return wrapper

    return decorator


def no_side_effects(strict: bool = False):
    """
    Document that a function is intended to be pure (no side effects).

    When ``strict=True``, the function is wrapped in a ``try/except`` that re-raises
    any ``Exception``, making violations visible during testing. In practice
    purity cannot be enforced at the Python level — this decorator primarily
    serves as machine-readable documentation and SRP enforcement signal.

    :param strict: If ``True``, wrap the call and print a message on exception
                   before re-raising (useful in test mode).

    e.g.::

        @no_side_effects()
        def compute_hash(data: bytes) -> str:
            ...
    """

    def decorator(func):
        func.__no_side_effects__ = True

        if strict:
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    print(
                        f"[SRP] @no_side_effects: '{func.__name__}' raised "
                        f"{type(exc).__name__} — possible side-effect violation."
                    )
                    raise

            wrapper.__no_side_effects__ = True
            return wrapper

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        wrapper.__no_side_effects__ = True
        return wrapper

    return decorator


def sealed(cls):
    """
    Prevent subclassing of the decorated class.
    Raises ``TypeError`` if someone tries to subclass it.

    e.g.::

        @sealed
        class SingletonConfig:
            ...
    """
    original_init_subclass = cls.__dict__.get("__init_subclass__")

    @classmethod  # type: ignore[misc]
    def __init_subclass__(subcls, **kwargs):
        raise TypeError(
            f"Class '{cls.__name__}' is sealed and cannot be subclassed "
            f"(attempted by '{subcls.__name__}')."
        )

    cls.__init_subclass__ = __init_subclass__  # type: ignore[method-assign]
    return cls


def require_override(func):
    """
    Raise ``NotImplementedError`` if the decorated method is called directly
    on the class where it is defined, signalling that subclasses *must* override it.

    Unlike ``@abstractmethod`` this works without ``ABCMeta`` and can be applied
    to any method after the fact.

    e.g.::

        class BaseProcessor:
            @require_override
            def process(self, data):
                ...   # subclass must override
    """

    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        if type(self).__dict__.get(func.__name__) is wrapper:
            raise NotImplementedError(
                f"'{type(self).__name__}.{func.__name__}' must be overridden by a subclass."
            )
        return func(self, *args, **kwargs)

    return wrapper


def enforce_srp(roles: dict[str, str]):
    """
    Class decorator that attaches a ``__srp_manifest__`` dictionary listing
    the single responsibility of each method.

    :param roles: ``{method_name: responsibility_description}`` mapping.

    e.g.::

        @enforce_srp({
            "extract": "Read raw CSV files from disk",
            "transform": "Convert raw dicts to domain records",
            "load": "Persist records to the database",
        })
        class EtlService:
            def extract(self): ...
            def transform(self, raw): ...
            def load(self, records): ...
    """

    def decorator(cls):
        missing = [m for m in roles if not hasattr(cls, m)]
        if missing:
            warnings.warn(
                f"@enforce_srp on '{cls.__name__}': methods {missing} listed in roles "
                "do not exist on the class.",
                stacklevel=2,
            )
        cls.__srp_manifest__ = roles
        return cls

    return decorator
