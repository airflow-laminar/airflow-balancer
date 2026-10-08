# Select a worker and inspect its configuration

Create a YAML file, load it, and select a worker and a configured port. This exercise uses Python 3.11 or later and does not connect to a worker or an Airflow metadata database. The shell commands use Linux/macOS syntax.

## Install the packages

In an empty directory:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install airflow-balancer 'airflow-pydantic>=1.7,<1.8'
```

## Describe a worker

Save `balancer.yaml`:

```yaml
_target_: airflow_balancer.BalancerConfiguration
default_username: airflow
hosts:
  - name: worker1
    size: 2
    os: linux
    queues: [workers]
    tags: [cpu]
ports:
  - name: reporting-api
    host_name: worker1
    port: 8080
    tags: [api]
```

## Load and select

Save `inspect_balancer.py` beside the YAML file:

```python
from airflow_balancer import BalancerConfiguration

balancer = BalancerConfiguration.load_path("balancer.yaml")
host = balancer.select_host(queue="workers", tag="cpu")
port = balancer.select_port(name="reporting-api")

print(host.name, host.username, host.pool.pool, host.size)
print(port.host.name, port.port, port.pool)
```

Run it:

```bash
python inspect_balancer.py
```

The script prints these lines; Airflow logging may also report the queries:

```text
worker1 airflow worker1 2
worker1 8080 reporting-api
```

The host inherits `default_username`; its pool declaration uses its name and size. The named port has a separate pool identifier.

## Filter the configuration

Add this to the Python file and run it again:

```python
print([host.name for host in balancer.filter_hosts(os="linux")])
print([port.port for port in balancer.filter_ports(tag="api")])
```

The two additional lines are:

```text
['worker1']
[8080]
```

Continue with [using the selected host in an SSH task](examples.md#how-to-run-an-ssh-task-on-a-selected-host) or [composing the configuration with airflow-config](examples.md#how-to-load-a-balancer-through-airflow-config).
