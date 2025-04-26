from __future__ import annotations

from pathlib import Path

from airflow_balancer import BalancerConfiguration

__all__ = (
    "get_hosts_from_yaml",
    "get_yaml_files",
)


def get_hosts_from_yaml(yaml: str) -> list[str]:
    # Process the yaml
    yaml_file = Path(yaml).resolve()
    inst = BalancerConfiguration.load(yaml_file)
    for host in inst.hosts:
        if host.password:
            host.password = "***"
    if inst.default_password:
        inst.default_password = "***"
    for port in inst.ports:
        if port.host.password:
            port.host.password = "***"
    return str(inst.model_dump_json(serialize_as_any=True))


def get_yaml_files(dags_folder: str) -> list[Path]:
    # Look for yamls inside the dags folder
    yamls = []
    base_path = Path(dags_folder)
    for path in base_path.glob("**/*.yaml"):
        if path.is_file():
            if "_target_: airflow_balancer.BalancerConfiguration" in path.read_text():
                yamls.append(path)
    return yamls
