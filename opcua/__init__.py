__all__ = ["DataChangeHandler", "OPCUAClient", "OPCUAServer"]


def __getattr__(name: str):
    if name == "DataChangeHandler":
        from opcua.handler import DataChangeHandler

        return DataChangeHandler
    if name == "OPCUAClient":
        from opcua.client import OPCUAClient

        return OPCUAClient
    if name == "OPCUAServer":
        from opcua.server import OPCUAServer

        return OPCUAServer
    raise AttributeError(name)
