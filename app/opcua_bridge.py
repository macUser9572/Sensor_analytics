import asyncio
import logging
import signal

from opcua.server import OPCUAServer
from simulator.service import SimulatorService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
for noisy_logger in (
    "asyncua",
    "asyncua.server",
    "asyncua.server.address_space",
    "asyncua.server.binary_server_asyncio",
    "asyncua.server.internal_server",
    "asyncua.server.internal_session",
    "asyncua.server.uaprocessor",
    "asyncua.uaprotocol",
):
    logging.getLogger(noisy_logger).setLevel(logging.WARNING)


async def main() -> None:
    stop_event = asyncio.Event()

    def request_stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, request_stop)

    simulator = SimulatorService()
    await simulator.start()
    opc_server = OPCUAServer(simulator)
    await opc_server.start()
    logger.info("Standalone OPC-UA bridge started")

    try:
        await stop_event.wait()
    finally:
        await opc_server.stop()
        await simulator.stop()
        logger.info("Standalone OPC-UA bridge stopped")


if __name__ == "__main__":
    asyncio.run(main())
