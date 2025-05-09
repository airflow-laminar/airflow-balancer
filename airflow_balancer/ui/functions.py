from __future__ import annotations

from pathlib import Path

from hydra.errors import InstantiationException

from airflow_balancer import BalancerConfiguration
from airflow_balancer.testing import pools

__all__ = (
    "get_hosts_from_yaml",
    "get_yaml_files",
)


def get_hosts_from_yaml(yaml: str) -> list[str]:
    # Process the yaml
    yaml_file = Path(yaml).resolve()
    try:
        inst = BalancerConfiguration.load(yaml_file)
    except InstantiationException:
        # Mock SQL connections to instantiate
        with pools():
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

    # Look if the file directly instantiates a BalancerConfiguration
    for path in base_path.glob("**/*.yaml"):
        if path.is_file():
            if "_target_: airflow_balancer.BalancerConfiguration" in path.read_text():
                yamls.append(path)
    len_yamls = len(yamls)
    len_yamls_last = 0
    # If we have yamls, look for any that reference them
    while len_yamls != len_yamls_last:
        for path in base_path.glob("**/*.yaml"):
            if path.is_file() and path not in yamls:
                # Check and see if this references any existing yamls
                for yaml in yamls:
                    if path.parent == yaml.parent and f"{yaml.stem}@" in path.read_text():
                        yamls.append(path)
                        break
        len_yamls_last = len_yamls
        len_yamls = len(yamls)
    return yamls
