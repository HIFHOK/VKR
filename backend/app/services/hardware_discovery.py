import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.hardware import HardwareComponent
from app.models.node import Node
from app.core.config import settings

PROMETHEUS_URL = "http://prometheus:9090"


async def _get_node_instance(db: AsyncSession, node_id: int) -> str:
    """
    Получает метку instance для Prometheus по ID узла.
    Формат: <address>:9100 (например, "192.168.1.14:9100")
    """
    node = await db.get(Node, node_id)
    if not node:
        raise ValueError(f"Node {node_id} not found")
    
    # Просто формируем instance из адреса узла
    # Это соответствует формату в prometheus.yml
    return f"{node.address}:9100"


async def discover_hardware(db: AsyncSession, node_id: int):
    instance = await _get_node_instance(db, node_id)
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        await _discover_cpus(db, node_id, client, instance)
        await _discover_ram(db, node_id, client, instance)
        await _discover_disks(db, node_id, client, instance)
        await _discover_network(db, node_id, client, instance)
    await db.commit()


async def _discover_cpus(db: AsyncSession, node_id: int, client: httpx.AsyncClient, instance: str):
    """Обнаружение CPU ядер с частотой из config"""
    
    default_freq_ghz = settings.cpu_max_frequency_ghz
    
    # ✅ ДОБАВЛЕНО: filter by instance!
    cores_query = f'count by (cpu) (node_cpu_seconds_total{{instance="{instance}",mode="idle"}})'
    response = await client.get(f"{PROMETHEUS_URL}/api/v1/query?query={cores_query}")
    data = response.json()
    
    if data.get("status") != "success":
        return
    
    for result in data["data"]["result"]:
        cpu_num = result["metric"].get("cpu", "0")
        
        exists = await db.execute(
            select(HardwareComponent).where(
                HardwareComponent.node_id == node_id,
                HardwareComponent.component_type == "cpu",
                HardwareComponent.component_id == f"cpu{cpu_num}"
            )
        )
        if exists.scalar_one_or_none():
            continue
        
        component = HardwareComponent(
            node_id=node_id,
            component_type="cpu",
            component_id=f"cpu{cpu_num}",
            name=f"CPU Core #{cpu_num}",
            max_capacity=default_freq_ghz,
            max_capacity_unit="GHz" if default_freq_ghz else None,
            # ✅ ДОБАВЛЕНО: instance в metric_query
            metric_query=f'100 - (avg by (cpu) (rate(node_cpu_seconds_total{{cpu="{cpu_num}",mode="idle",instance="{instance}"}}[1m])) * 100)',
            component_metadata={"frequency_ghz": default_freq_ghz} if default_freq_ghz else {}
        )
        db.add(component)


async def _discover_ram(db: AsyncSession, node_id: int, client: httpx.AsyncClient, instance: str):
    # ✅ ДОБАВЛЕНО: filter by instance
    query = f'node_memory_MemTotal_bytes{{instance="{instance}"}}'
    response = await client.get(f"{PROMETHEUS_URL}/api/v1/query?query={query}")
    data = response.json()
    
    if data.get("status") != "success" or not data["data"]["result"]:
        return
    
    result = data["data"]["result"][0]
    total_bytes = float(result["value"][1])
    total_gb = round(total_bytes / (1024**3), 2)
    
    exists = await db.execute(
        select(HardwareComponent).where(
            HardwareComponent.node_id == node_id,
            HardwareComponent.component_type == "ram",
            HardwareComponent.component_id == "memory"
        )
    )
    if exists.scalar_one_or_none():
        return
    
    component = HardwareComponent(
        node_id=node_id,
        component_type="ram",
        component_id="memory",
        name="System RAM",
        max_capacity=total_gb,
        max_capacity_unit="GB",
        # ✅ ДОБАВЛЕНО: instance в metric_query
        metric_query=f'(1 - (node_memory_MemAvailable_bytes{{instance="{instance}"}} / node_memory_MemTotal_bytes{{instance="{instance}"}})) * 100',
        component_metadata={"total_bytes": total_bytes}
    )
    db.add(component)


async def _discover_disks(db: AsyncSession, node_id: int, client: httpx.AsyncClient, instance: str):
    # ✅ ДОБАВЛЕНО: filter by instance
    query = f'node_filesystem_size_bytes{{instance="{instance}",fstype!~"tmpfs|squashfs"}}'
    response = await client.get(f"{PROMETHEUS_URL}/api/v1/query?query={query}")
    data = response.json()
    
    if data.get("status") != "success":
        return
    
    for result in data["data"]["result"]:
        labels = result["metric"]
        mountpoint = labels.get("mountpoint", "unknown")
        device = labels.get("device", "unknown")
        size_bytes = float(result["value"][1])
        size_gb = round(size_bytes / (1024**3), 2)
        
        component_id = f"disk:{mountpoint}"
        
        exists = await db.execute(
            select(HardwareComponent).where(
                HardwareComponent.node_id == node_id,
                HardwareComponent.component_type == "disk",
                HardwareComponent.component_id == component_id
            )
        )
        if exists.scalar_one_or_none():
            continue
        
        component = HardwareComponent(
            node_id=node_id,
            component_type="disk",
            component_id=component_id,
            name=f"Disk {mountpoint} ({device})",
            max_capacity=size_gb,
            max_capacity_unit="GB",
            # ✅ ДОБАВЛЕНО: instance в metric_query
            metric_query=f'(1 - (node_filesystem_avail_bytes{{instance="{instance}",mountpoint="{mountpoint}"}} / node_filesystem_size_bytes{{instance="{instance}",mountpoint="{mountpoint}"}})) * 100',
            component_metadata={"device": device, "mountpoint": mountpoint, "size_bytes": size_bytes}
        )
        db.add(component)


async def _discover_network(db: AsyncSession, node_id: int, client: httpx.AsyncClient, instance: str):
    """Обнаружение сетевых интерфейсов (только физические)"""
    # ✅ ДОБАВЛЕНО: filter by instance
    query = f'node_network_speed_bytes{{instance="{instance}",device!~"lo|virbr.*|docker.*|veth.*|br-.*"}}'
    response = await client.get(f"{PROMETHEUS_URL}/api/v1/query?query={query}")
    data = response.json()
    
    if data.get("status") != "success":
        return
    
    for result in data["data"]["result"]:
        labels = result["metric"]
        device = labels.get("device", "unknown")
        
        speed_bytes = float(result["value"][1])
        if speed_bytes <= 0:
            continue
            
        speed_gbps = round((speed_bytes * 8) / 1e9, 2)
        
        component_id = f"net:{device}"
        
        exists = await db.execute(
            select(HardwareComponent).where(
                HardwareComponent.node_id == node_id,
                HardwareComponent.component_type == "network",
                HardwareComponent.component_id == component_id
            )
        )
        if exists.scalar_one_or_none():
            continue
        
        # Исправлено: metadata → component_metadata (согласовано с другими компонентами)
        component = HardwareComponent(
            node_id=node_id,
            component_type="network",
            component_id=component_id,
            name=f"Network Interface {device}",
            max_capacity=speed_gbps,
            max_capacity_unit="Gbps",
            # ✅ ДОБАВЛЕНО: instance в metric_query
            metric_query=f'rate(node_network_receive_bytes_total{{instance="{instance}",device="{device}"}}[1m])',
            component_metadata={"device": device, "speed_bytes": speed_bytes}
        )
        db.add(component)