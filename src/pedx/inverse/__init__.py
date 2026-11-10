from .model import LEVERS, CellState, audit, score, simulate

__all__ = ["LEVERS", "CellState", "audit", "score", "simulate", "InverseEngine", "Prescription", "project_box_budget"]


def __getattr__(name):  # lazy: the engine needs JAX, the model does not
    if name in ("InverseEngine", "Prescription", "project_box_budget"):
        from . import engine

        return getattr(engine, name)
    raise AttributeError(name)
