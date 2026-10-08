---
myst:
  heading_anchors: 3
---

# How-to guides

## How to define hosts in Python

```python
from airflow_balancer import BalancerConfiguration, Host, Port

balancer = BalancerConfiguration(
    default_username="airflow",
    hosts=[
        Host(
            name="worker1", os="linux", size=8, queues=["workers"], tags=["cpu"],
            pool={"pool": "cpu-workers", "slots": 8},
        ),
        Host(name="gpu1", os="linux", size=4, queues=["gpu"], tags=["cuda"]),
    ],
    ports=[Port(name="reporting-api", host_name="worker1", port=8080, tags=["api"])],
)

host = balancer.select_host(queue="workers", os="linux")
port = balancer.select_port(name="reporting-api")
```

Use `filter_hosts()` or `filter_ports()` to obtain all matches. Selection and filtering both raise `RuntimeError` when there are no matches; see [query behavior](API.md#queries).

## How to load a balancer through airflow-config

Save `config/config.yaml`:

```yaml
# @package _global_
_target_: airflow_config.Configuration
defaults:
  - extensions/balancer@extensions.balancer
  - _self_
```

Save `config/extensions/balancer.yaml`:

```yaml
# @package extensions.balancer
_target_: airflow_balancer.BalancerConfiguration
default_username: airflow
default_size: 8
hosts:
  - name: worker1
    os: linux
    queues: [workers]
    tags: [cpu]
```

Load it from a Python file beside the `config` directory:

```python
from airflow_config import load_config

config = load_config("config", "config")
balancer = config.extensions["balancer"]
host = balancer.select_host(queue="workers")
```

For a single balancer file, use `BalancerConfiguration.load_path("balancer.yaml")`. The exported `load_config` in **airflow-balancer** aliases `BalancerConfiguration.load`; **airflow-config** exports the loader for the enclosing `Configuration`.

## How to run an SSH task on a selected host

Install `airflow-balancer[airflow]` for Airflow 2 or `airflow-balancer[airflow3]` for Airflow 3. Configure SSH access to the worker and reconcile its pool before running the DAG.

```python
from datetime import UTC, datetime

from airflow_balancer import BalancerConfiguration, Host
from airflow_pydantic.airflow import DAG, SSHOperator

balancer = BalancerConfiguration(
    default_username="airflow",
    default_key_file="/home/airflow/.ssh/id_rsa",
    hosts=[Host(name="worker1.example.com", size=8, queues=["workers"])],
)
host = balancer.select_host(queue="workers")

with DAG(
    dag_id="run_on_worker",
    start_date=datetime(2025, 1, 1, tzinfo=UTC),
    schedule=None,
    catchup=False,
) as dag:
    SSHOperator(
        task_id="inspect_worker",
        ssh_hook=host.hook(conn_timeout=20, cmd_timeout=60, keepalive_interval=10),
        command="hostname",
        pool=host.pool.pool,
    )
```

`host.pool` is a `Pool` model. Pass `host.pool.pool` to an operator's `pool` argument, including when the configured pool name differs from the hostname.

To use a short hostname without appending `.local`, call `host.hook(use_local=False)`. To select a different SSH port, pass `port=2222`. Additional SSHHook keyword arguments belong on the `hook()` call; the Host model does not store an arbitrary hook-arguments mapping.

To override host fields for one use:

```python
admin_host = host.override(username="admin")
admin_hook = admin_host.hook(conn_timeout=20)
```

## How to load a password from an Airflow Variable

Set the `worker_password` Variable in Airflow, then configure the host:

```python
from airflow_balancer import Host
from airflow_pydantic import Variable

host = Host(
    name="worker1.example.com",
    username="airflow",
    password=Variable(key="worker_password"),
)
ssh_hook = host.hook()
```

For YAML, replace the host's password value with:

```yaml
password:
  _target_: airflow_pydantic.Variable
  key: worker_password
```

A JSON Variable with `deserialize_json: true` must contain a `password` key. When constructing a hook offline, an unavailable Variable produces an unresolved placeholder; use generated DAGs so the renderer replaces it with a runtime lookup.

## How to reconcile configured pools

The pool-manager models described here are provided by `airflow-pydantic` 1.7. Use a balancer extension in an `airflow-config` configuration as above. Add this to the balancer YAML:

```yaml
pool_manager:
  backend: auto
  connection_id: airflow_laminar_api
```

Generate the configuration's DAGs:

```python
from airflow_config import load_config

config = load_config("config", "config")
config.generate("generated", airflow_major_version=3)
```

For Airflow 2, set `airflow_major_version=2`. Place the generated files in the deployment's DAG directory. The default manager DAG is `airflow_laminar_pool_manager`, with a `reconcile_pools` task scheduled every five minutes.

For Airflow 3, create the `airflow_laminar_api` Connection with the API server's base URL in `extra.base_url`, plus either `extra.token` or a login/password accepted by `/auth/token`. The authenticated user needs permission to read and create/update pools. The Airflow 2 backend uses the metadata database from the reconciliation task.

If YAML slot counts should update existing pools, add:

```yaml
override_pool_size: true
```

To disable the generated manager DAG:

```yaml
pool_manager:
  dag:
    enabled: false
```

Loading a balancer configuration alone does not create the pools. See [pool ownership](explanation.md#pool-ownership) and the [pool-manager reference](API.md#pool-manager).

## How to select an unconfigured port

```python
host = balancer.select_host(queue="workers")
port = balancer.free_port(host=host, min=8000, max=9000)
print(port.port)
```

The upper bound is exclusive. This excludes ports already listed for that host in the configuration. Supply a range with at least one unconfigured port, and arrange a separate reservation or bind check if multiple processes allocate ports.

## How to inspect configuration in the viewer

In Airflow 2, open **Laminar → Airflow Balancer Viewer**. In Airflow 3, open the **Airflow Balancer Viewer** external view in the admin navigation. The Airflow plugin reads the configured DAG directory and lists matching YAML files.

To run the viewer outside Airflow:

```bash
pip install airflow-balancer fastapi uvicorn
AIRFLOW__CORE__DAGS_FOLDER="$PWD/config" PORT=8000 airflow-balancer-viewer
```

Open `http://localhost:8000/`, select a file, and open the Hosts or Ports tab. Host pool names are displayed from their serialized Pool models. Password values are masked.

If no files appear, check that the directory contains `.yaml` files with `_target_: airflow_balancer.BalancerConfiguration`, or enclosing `airflow-config` files that reference those configurations. The [reference](API.md#viewer) lists directory precedence and runtime dependencies.

## How to test selection without contacting Airflow

Configuration loading and host selection use model declarations. To mock Airflow Variable lookup while testing a hook:

```python
from airflow_balancer import Host
from airflow_balancer.testing import variables
from airflow_pydantic import Variable

with variables("example-password"):
    host = Host(name="worker1", username="airflow", password=Variable(key="worker_password"))
    assert host.hook().password == "example-password"
```

For code that calls Airflow pool helpers, `airflow_balancer.testing.pools()` mocks pool lookup, creation, and mutation. These helpers are for tests; runtime pool reconciliation belongs in the generated manager task.
