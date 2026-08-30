from __future__ import annotations

import os
from logging import getLogger
from pathlib import Path

from airflow_config import ConfigNotFoundError, load_config
from airflow_config.ui.functions import get_yaml_files as airflow_config_get_yamls
from hydra.errors import InstantiationException

from airflow_balancer import BalancerConfiguration
from airflow_balancer.testing import pools

__all__ = (
    "get_dags_folder",
    "get_hosts_from_yaml",
    "get_yaml_files",
)

log = getLogger(__name__)


def get_dags_folder() -> str | None:
    """Resolve the dags folder from the environment, falling back to the Airflow config.

    Returns None when Airflow is unavailable, so the standalone viewer can supply its own default.
    """
    dags_folder = os.environ.get("AIRFLOW__CORE__DAGS_FOLDER")
    if dags_folder:
        return dags_folder
    try:
        from airflow.configuration import conf

        return (conf.getsection("core") or {}).get("dags_folder")
    except Exception:
        log.debug("Could not read dags_folder from the Airflow configuration", exc_info=True)
        return None


def _read_text(path: Path) -> str:
    """Read a yaml file, skipping any that cannot be decoded or accessed."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        log.debug(f"Skipping unreadable file {path}", exc_info=True)
        return ""


def get_hosts_from_yaml(yaml: str) -> list[str]:
    # Process the yaml
    yaml_file = Path(yaml).resolve()
    airflow_config_inst = None
    inst: BalancerConfiguration | None = None
    try:
        airflow_config_inst = load_config(str(yaml_file.parent.name), yaml_file.name, overrides=[], basepath=str(yaml_file))
    except (ConfigNotFoundError, InstantiationException):
        try:
            # Mock SQL connections to instantiate
            with pools():
                airflow_config_inst = load_config(str(yaml_file.parent.name), yaml_file.name, overrides=[], basepath=str(yaml_file))
        except (ConfigNotFoundError, InstantiationException):
            pass
    if airflow_config_inst is not None:
        if hasattr(airflow_config_inst, "balancer") and isinstance(airflow_config_inst.balancer, BalancerConfiguration):
            inst = airflow_config_inst.balancer
        elif hasattr(airflow_config_inst, "extensions"):
            for ext in airflow_config_inst.extensions.values():
                if isinstance(ext, BalancerConfiguration):
                    inst = ext
                    break
    if inst is None:
        try:
            inst = BalancerConfiguration.load_path(yaml_file)
        except InstantiationException:
            # Mock SQL connections to instantiate
            with pools():
                inst = BalancerConfiguration.load_path(yaml_file)
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
        if path.is_file() and "_target_: airflow_balancer.BalancerConfiguration" in _read_text(path):
            yamls.append(path)
    len_yamls = len(yamls)
    len_yamls_last = 0
    # If we have yamls, look for any that reference them
    while len_yamls != len_yamls_last:
        for path in base_path.glob("**/*.yaml"):
            if path.is_file() and path not in yamls:
                # Check and see if this references any existing yamls
                for yaml in yamls:
                    if path.parent == yaml.parent and f"{yaml.stem}@" in _read_text(path):
                        yamls.append(path)
                        break
        len_yamls_last = len_yamls
        len_yamls = len(yamls)
    try:
        yamls_airflow_config = airflow_config_get_yamls(dags_folder)
    except (OSError, UnicodeError):
        yamls_airflow_config = []
    return yamls, yamls_airflow_config
