import asyncio
import logging
import signal

from simulator.service import SimulatorService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    stop_event = asyncio.Event()

    def request_stop() -> None:
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, request_stop)

    simulator = SimulatorService()
    await simulator.start()
    logger.info("Simulator runner started")

    try:
        await stop_event.wait()
    finally:
        await simulator.stop()
        logger.info("Simulator runner stopped")


if __name__ == "__main__":
    asyncio.run(main())
