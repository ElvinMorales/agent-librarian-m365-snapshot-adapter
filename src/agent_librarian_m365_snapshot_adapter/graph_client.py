class LiveExportDisabled(RuntimeError):
    """Raised whenever the unimplemented live boundary is invoked."""


class GraphClient:
    """Design boundary for future, separately approved Microsoft Graph access."""

    def __init__(self, *args: object, **kwargs: object) -> None:
        raise LiveExportDisabled(
            "Live Microsoft 365 export is not implemented in this prototype. "
            "Use export-synthetic or complete the documented security gates first."
        )
