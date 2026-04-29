import asyncio
import logging

from asyncua import Server, ua
from asyncua.common.node import Node

from config import settings
from simulator.service import SimulatorService


logger = logging.getLogger(__name__)


class OPCUAServer:
    def __init__(self, simulator: SimulatorService):
        self.server = Server()
        self.simulator = simulator
        self.sensor_nodes: dict[str, Node] = {}
        self._update_task: asyncio.Task | None = None
        self._ready = asyncio.Event()
        self._running = False

    async def setup(self) -> None:
        await self.server.init()
        self.server.set_endpoint(settings.opc_bind_url())
        self.server.set_server_name(settings.OPC_SERVER_NAME)
        namespace_index = await self.server.register_namespace(settings.OPC_NAMESPACE)

        plant_node = await self.server.nodes.objects.add_folder(namespace_index, "BHELPlant")
        subsystems: dict[str, Node] = {}

        for sensor in self.simulator.registry:
            subsystem_node = subsystems.get(sensor.subsystem)
            if subsystem_node is None:
                subsystem_node = await plant_node.add_folder(namespace_index, sensor.subsystem.capitalize())
                subsystems[sensor.subsystem] = subsystem_node

            node = await subsystem_node.add_variable(namespace_index, sensor.id, sensor.baseline_value)
            await node.set_writable()
            await node.write_attribute(
                ua.AttributeIds.Description,
                ua.DataValue(
                    ua.Variant(
                        ua.LocalizedText(f"{sensor.name} | Unit: {sensor.unit}"),
                        ua.VariantType.LocalizedText,
                    )
                ),
            )
            self.sensor_nodes[sensor.id] = node

        logger.info("OPC-UA address space created with %s sensor nodes", len(self.sensor_nodes))

    async def update_loop(self) -> None:
        async with self.server:
            self._running = True
            self._ready.set()
            logger.info("OPC-UA Server listening on %s", settings.opc_bind_url())
            try:
                while True:
                    try:
                        readings = await self.simulator.tick()
                        for reading in readings:
                            if self.simulator.is_sensor_killed(reading.sensor_id):
                                continue
                            node = self.sensor_nodes.get(reading.sensor_id)
                            if node is not None:
                                await node.write_value(reading.value)
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        logger.exception("OPC-UA update loop failed; continuing")

                    await asyncio.sleep(settings.SIMULATOR_TICK_MS / 1000)
            finally:
                self._running = False

    async def start(self) -> None:
        await self.setup()
        self._update_task = asyncio.create_task(self.update_loop(), name="bhel-opcua-update-loop")
        ready_task = asyncio.create_task(self._ready.wait())
        done, pending = await asyncio.wait(
            {self._update_task, ready_task},
            return_when=asyncio.FIRST_COMPLETED,
        )
        if ready_task in pending:
            ready_task.cancel()
        if self._update_task in done:
            await self._update_task

    async def stop(self) -> None:
        if self._update_task:
            self._update_task.cancel()
            try:
                await self._update_task
            except asyncio.CancelledError:
                pass
            self._update_task = None
        else:
            await self.server.stop()
        self._running = False

    def is_running(self) -> bool:
        return self._running
