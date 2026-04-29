import asyncio
import logging

from asyncua import Client, ua
from asyncua.common.node import Node

from config import settings
from opcua.handler import DataChangeHandler


logger = logging.getLogger(__name__)


class OPCUAClient:
    def __init__(self, handler: DataChangeHandler):
        self.handler = handler
        self.client = Client(url=settings.OPC_SERVER_URL)
        self._running = False
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()
        self._connected_event = asyncio.Event()
        self.sensor_nodes: dict[str, Node] = {}
        self.monitored_items = 0

    async def connect_and_subscribe(self) -> None:
        while not self._stop_event.is_set():
            self.client = Client(url=settings.OPC_SERVER_URL)
            try:
                async with self.client:
                    sensor_nodes = await self._browse_sensors()
                    self.sensor_nodes = sensor_nodes

                    params = ua.CreateSubscriptionParameters()
                    params.RequestedPublishingInterval = 1000
                    params.RequestedLifetimeCount = max(settings.OPC_KEEPALIVE_COUNT * 10, 30)
                    params.RequestedMaxKeepAliveCount = settings.OPC_KEEPALIVE_COUNT
                    params.MaxNotificationsPerPublish = 10000
                    params.PublishingEnabled = True
                    params.Priority = 0

                    subscription = await self.client.create_subscription(params, self.handler)

                    monitored_items = 0
                    for sensor_id, node in sensor_nodes.items():
                        await subscription.subscribe_data_change(
                            nodes=node,
                            sampling_interval=self._get_interval(sensor_id),
                        )
                        monitored_items += 1

                    self.monitored_items = monitored_items
                    self._running = True
                    self._connected_event.set()
                    logger.info(
                        "OPC-UA Client subscribed to %s sensors at %s",
                        monitored_items,
                        settings.OPC_SERVER_URL,
                    )

                    while not self._stop_event.is_set():
                        try:
                            await asyncio.wait_for(self._stop_event.wait(), timeout=1)
                        except asyncio.TimeoutError:
                            await self.client.check_connection()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                self._running = False
                self._connected_event.clear()
                self.monitored_items = 0
                logger.error("OPC-UA Client disconnected: %s. Reconnecting in 5s...", exc)
                try:
                    await asyncio.wait_for(self._stop_event.wait(), timeout=5)
                except asyncio.TimeoutError:
                    pass

        self._running = False
        self._connected_event.clear()
        self.monitored_items = 0

    async def _browse_sensors(self) -> dict[str, Node]:
        objects = self.client.nodes.objects
        plant_node = None
        for child in await objects.get_children():
            browse_name = await child.read_browse_name()
            if browse_name.Name == "BHELPlant":
                plant_node = child
                break

        if plant_node is None:
            raise RuntimeError("BHELPlant folder not found in OPC-UA address space")

        sensor_nodes: dict[str, Node] = {}
        for subsystem_node in await plant_node.get_children():
            for sensor_node in await subsystem_node.get_children():
                browse_name = await sensor_node.read_browse_name()
                sensor_id = browse_name.Name
                if self._is_sensor_id(sensor_id):
                    sensor_nodes[sensor_id] = sensor_node

        if not sensor_nodes:
            raise RuntimeError("No sensor nodes found under BHELPlant")
        return sensor_nodes

    def _get_interval(self, sensor_id: str) -> int:
        if sensor_id.startswith("G"):
            return 2000
        if sensor_id.startswith("B"):
            return 5000
        if sensor_id.startswith("TR"):
            return 15000
        if sensor_id.startswith("T"):
            return 10000
        return 15000

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop_event.clear()
        self._connected_event.clear()
        self._task = asyncio.create_task(self.connect_and_subscribe(), name="bhel-opcua-client")
        try:
            await asyncio.wait_for(self._connected_event.wait(), timeout=15)
        except asyncio.TimeoutError:
            logger.warning("OPC-UA Client did not connect within 15s; reconnect loop is still running")

    async def stop(self) -> None:
        self._stop_event.set()
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None
        self._running = False
        self._connected_event.clear()
        self.monitored_items = 0

    def is_connected(self) -> bool:
        return self._running

    def _is_sensor_id(self, value: str) -> bool:
        return value[:1] in {"T", "B", "G", "C", "A"} or value.startswith("TR")
