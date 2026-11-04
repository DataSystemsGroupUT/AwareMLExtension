from .state import ensure_research_state, phase_status
def __getattr__(name):
    if name == 'PAGE_REGISTRY_V2':
        from .pages import PAGE_REGISTRY_V2
        return PAGE_REGISTRY_V2
    raise AttributeError(name)

__all__ = ["ensure_research_state", "phase_status", "PAGE_REGISTRY_V2"]

