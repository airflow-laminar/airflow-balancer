from fnmatch import fnmatch
from random import choice
from typing import Callable, List, Optional, Union

from airflow.models.pool import Pool, PoolNotFound  # noqa: F401
from airflow.models.variable import Variable
from airflow.providers.ssh.hooks.ssh import SSHHook
from pydantic import BaseModel, Field, model_validator
from typing_extensions import Self

__all__ = (
    "Host",
    "BalancerConfiguration",
)


# TODO: hostname, user, password / secret variable, init routine
class Host(BaseModel):
    name: str
    username: Optional[str] = None

    # Password
    password: Optional[str] = None
    # If password is stored in a variable
    password_variable: Optional[str] = None
    # if stored in structured container, access by key
    password_variable_key: Optional[str] = None
    # Or get key file
    key_file: Optional[str] = None

    os: Optional[str] = None

    # Airflow / balance
    pool: Optional[str] = None
    size: Optional[int] = None
    queues: List[str] = Field(default_factory=list)

    tags: List[str] = Field(default_factory=list)

    def hook(self, use_local: bool = True) -> SSHHook:
        if use_local and not self.name.count(".") > 0:
            name = f"{self.name}.local"
        else:
            name = self.name
        if self.username and self.password:
            return SSHHook(remote_host=name, username=self.username, password=self.password)
        elif self.username and self.password_variable:
            if self.password_variable_key:
                credentials = Variable.get(self.password_variable, deserialize_json=True)
                password = credentials[self.password_variable_key]
            else:
                password = Variable.get(self.password_variable)
            return SSHHook(remote_host=name, username=self.username, password=password)
        elif self.username and self.key_file:
            return SSHHook(remote_host=name, username=self.username, key_file=self.key_file)
        elif self.username:
            return SSHHook(remote_host=name, username=self.username)
        else:
            return SSHHook(remote_host=name)

    def __lt__(self, other):
        return self.name < other.name

    def __hash__(self):
        return hash(self.name)


class BalancerConfiguration(BaseModel):
    hosts: List[Host] = Field(default_factory=list)

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
    default_size: int = Field(default=10)

    # rewrite pool size from config if differs from airflow variable stored value
    override_pool_size: bool = False

    # create connection object in airflow for host
    create_connection: bool = False

    @property
    def all_hosts(self):
        return sorted(list(set(self.hosts)))

    @model_validator(mode="after")
    def _sync_limits(self) -> Self:
        for host in self.hosts:
            if not host.pool:
                host.pool = host.name
            if not host.size:
                host.size = self.default_size
            # check airflow first
            try:
                Pool.get_pool(host.pool)
            except PoolNotFound:
                # else set to default
                Pool.create_or_update_pool(name=host.pool, slots=host.size, description=f"Balancer pool for host {host.name} / {host.pool}")
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
