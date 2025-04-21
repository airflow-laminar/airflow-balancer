from fnmatch import fnmatch
from pathlib import Path
from random import choice
from typing import Callable, List, Optional, Union

from airflow.models.pool import Pool, PoolNotFound  # noqa: F401
from hydra import compose, initialize_config_dir
from hydra.utils import instantiate
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

from .host import Host
from .port import Port

__all__ = ("BalancerConfiguration",)


class BalancerConfiguration(BaseModel):
    hosts: List[Host] = Field(default_factory=list)
    ports: List[Port] = Field(default_factory=list)

    default_username: str = "airflow"
    # Password
    default_password: Optional[str] = None
    # If password is stored in a variable
    default_password_variable: Optional[str] = None
    # if stored in structured container, access by key
    default_password_variable_key: Optional[str] = None
    # Or get key file
    default_key_file: Optional[str] = None

    # The queue that might include the host running airflow itself
    primary_queue: str = "default"

    # The queue that does not include the host running airflow itself
    secondary_queue: str = "default"

    # The default worker queue
    default_queue: str = "default"

    # The default pool size
    default_size: int = Field(default=8)

    # rewrite pool size from config if differs from airflow variable stored value
    override_pool_size: bool = False

    # create connection object in airflow for host
    create_connection: bool = False

    @property
    def all_hosts(self):
        return sorted(list(set(self.hosts)))

    @property
    def all_ports(self):
        return sorted(list(set(self.ports)))

    @model_validator(mode="after")
    def _validate(self) -> Self:
        # Validate no duplicate hosts
        seen_hostnames = set()
        for host in self.hosts:
            if host.name in seen_hostnames:
                raise ValueError(f"Duplicate host found: {host.name}")
            seen_hostnames.add(host.name)

        # Handle limits
        for host in self.hosts:
            if not host.pool:
                host.pool = host.name
            if not host.size:
                host.size = self.default_size
            # check airflow first
            try:
                res = Pool.get_pool(host.pool)

                # airflow return value differs version-to-version
                if res is None:
                    raise PoolNotFound
                elif res.slots != host.size:
                    if self.override_pool_size:
                        Pool.create_or_update_pool(
                            name=host.pool,
                            slots=host.size,
                            description=f"Balancer pool for host({host.name}) pool({host.pool})",
                            include_deferred=False,
                        )
                    else:
                        host.size = res.slots
            except PoolNotFound:
                # else set to default
                Pool.create_or_update_pool(
                    name=host.pool, slots=host.size, description=f"Balancer pool for host({host.name}) pool({host.pool})", include_deferred=False
                )
            if not host.username and self.default_username:
                host.username = self.default_username
            if not host.password and self.default_password:
                host.password = self.default_password
            if not host.password_variable and self.default_password_variable:
                host.password_variable = self.default_password_variable
            if not host.password_variable_key and self.default_password_variable_key:
                host.password_variable_key = self.default_password_variable_key
            if not host.key_file and self.default_key_file:
                host.key_file = self.default_key_file
            if not host.size:
                host.size = self.default_size

        # Handle ports
        _used_ports = set()
        for port in self.ports:
            if port.host_name and not port.host:
                port.host = next((host for host in self.all_hosts if host.name == port.host_name), None)
            if not port.port:
                raise ValueError("Port must be specified")
            if not port.host:
                raise ValueError("Host must be specified")
            if (port.host.name, port.port) in _used_ports:
                raise ValueError(f"Duplicate port usage for host: {port.host.name}:{port.port}")
            _used_ports.add((port.host.name, port.port))

            # Create pools
            # TODO reenable
            # Pool.create_or_update_pool(
            #     name=port.pool,
            #     slots=1,
            #     description=f"Balancer pool for host({port.port}) port({port.port})",
            #     include_deferred=True,
            # )

    def filter_hosts(
        self,
        name: Optional[Union[str, List[str]]] = None,
        queue: Optional[Union[str, List[str]]] = None,
        os: Optional[Union[str, List[str]]] = None,
        tag: Optional[Union[str, List[str]]] = None,
        custom: Optional[Callable] = None,
    ) -> List[Host]:
        name = name or []
        queue = queue or []
        os = os or []
        tag = tag or []
        if isinstance(name, str):
            name = [name]
        if isinstance(queue, str):
            queue = [queue]
        if isinstance(os, str):
            os = [os]
        if isinstance(tag, str):
            tag = [tag]

        return [
            host
            for host in self.all_hosts
            if (not name or any(fnmatch(host.name, n) for n in name))
            and (not queue or any(fnmatch(host_queue, queue_pat) for queue_pat in queue for host_queue in host.queues))
            and (not tag or any(fnmatch(host_tag, tag_pat) for tag_pat in tag for host_tag in host.tags))
            and (not os or any(fnmatch(host.os, o) for o in os))
            and (not custom or custom(host))
        ]

    def select_host(
        self,
        name: Optional[Union[str, List[str]]] = None,
        queue: Optional[Union[str, List[str]]] = None,
        os: Union[str, List[str]] = "",
        tag: Union[str, List[str]] = "",
        custom: Callable = None,
    ) -> List[Host]:
        candidates = self.filter_hosts(name=name, queue=queue, os=os, tag=tag, custom=custom)
        if not candidates:
            raise RuntimeError(f"No host found for {name} / {queue} / {os} / {tag}")
        # TODO more schemes, interrogate usage
        return choice(candidates)

    def filter_ports(
        self,
        name: Optional[Union[str, List[str]]] = None,
        tag: Optional[Union[str, List[str]]] = None,
        custom: Optional[Callable] = None,
    ) -> List[Host]:
        name = name or []
        tag = tag or []
        if isinstance(name, str):
            name = [name]
        if isinstance(tag, str):
            tag = [tag]

        return [
            port
            for port in self.all_ports
            if (not name or any(fnmatch(port.name, n) for n in name))
            and (not tag or any(fnmatch(port_tag, tag_pat) for tag_pat in tag for port_tag in port.tags))
            and (not custom or custom(port))
        ]

    def select_port(
        self,
        name: Optional[Union[str, List[str]]] = None,
        tag: Union[str, List[str]] = "",
        custom: Callable = None,
    ) -> List[Host]:
        candidates = self.filter_ports(name=name, tag=tag, custom=custom)
        if not candidates:
            raise RuntimeError(f"No port found for {name} / {tag}")
        # TODO more schemes, interrogate usage
        # TODO select by host
        return choice(candidates)

    def free_port(
        self,
        host: Host,
        min: int = 1000,
        max: int = 65535,
    ) -> Port:
        used_ports = [port.port for port in self.ports if port.host == host]
        port = Port(host=host, port=choice(range(min, max)))
        while port.port in used_ports:
            port = Port(host=host, port=choice(range(min, max)))
            # TODO add pool around port? or just allow? context manager?
        return port

    @staticmethod
    def load(yaml_file: str | Path) -> Self:
        """Load configuration from yaml file"""
        if not isinstance(yaml_file, Path):
            yaml_file = Path(yaml_file).resolve()
        if not yaml_file.suffix == ".yaml":
            raise ValueError(f"File {yaml_file} must end in .yaml")

        file_name = yaml_file.stem
        config_dir = str(yaml_file.parent)

        # TODO: how to get the underlying value directly
        with initialize_config_dir(config_dir=config_dir, version_base=None):
            cfg = compose(config_name=file_name, overrides=[])
            config = instantiate(cfg)[yaml_file.parent.stem]
            if not isinstance(config, BalancerConfiguration):
                for value in config.values():
                    if isinstance(value, BalancerConfiguration):
                        config = value
                        break
                else:
                    raise ValueError(f"Config {file_name} does not contain a BalancerConfiguration")
            return config


load = BalancerConfiguration.load
