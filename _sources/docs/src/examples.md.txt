# Examples

This page provides comprehensive examples of using `airflow-balancer` for various use cases.

## Basic Configuration

### Minimal Configuration

The simplest configuration with just hosts:

```yaml
# config/balancer.yaml
_target_: airflow_balancer.BalancerConfiguration

hosts:
  - name: worker1
    size: 8

  - name: worker2
    size: 8
```

```python
from airflow_balancer import BalancerConfiguration

config = BalancerConfiguration.load_path("config/balancer.yaml")

# Select any available host
host = config.select_host()
print(f"Selected: {host.name}")
```

### Full Configuration

A complete configuration with all options:

```yaml
# config/balancer.yaml
_target_: airflow_balancer.BalancerConfiguration

# Default credentials for all hosts
default_username: airflow
default_key_file: /home/airflow/.ssh/id_rsa

# Queue definitions
primary_queue: primary
secondary_queue: workers
default_queue: default

# Default pool size for hosts without explicit size
default_size: 8

# Whether to override pool sizes in Airflow if they differ
override_pool_size: false

# Create Airflow connections for each host
create_connection: false

hosts:
  - name: primary-host
    size: 32
    os: ubuntu
    queues: [primary]
    tags: [scheduler]

  - name: worker-01
    size: 16
    os: ubuntu
    queues: [workers]
    tags: [compute]

  - name: worker-02
    size: 16
    os: ubuntu
    queues: [workers]
    tags: [compute]

  - name: gpu-worker
    size: 8
    os: ubuntu
    queues: [gpu]
    tags: [compute, cuda, ml]

  - name: mac-runner
    os: macos
    size: 8
    queues: [macos]
    tags: [ios, xcode]

ports:
  - host_name: primary-host
    port: 8080
    tags: [api]

  - host_name: worker-01
    port: 8793
    tags: [flower]
```

## Host Selection

### Selecting by Queue

```python
from airflow_balancer import BalancerConfiguration

config = BalancerConfiguration.load_path("config/balancer.yaml")

# Select a single host from the workers queue
worker = config.select_host(queue="workers")

# Filter to get all hosts in the workers queue
all_workers = config.filter_hosts(queue="workers")

# Select from multiple queues
host = config.select_host(queue=["workers", "gpu"])
```

### Selecting by Operating System

```python
# Select an Ubuntu host
ubuntu_host = config.select_host(os="ubuntu")

# Select a macOS host for iOS builds
mac_host = config.select_host(os="macos")

# Filter all Ubuntu hosts
ubuntu_hosts = config.filter_hosts(os="ubuntu")
```

### Selecting by Tags

```python
# Select a host with the 'cuda' tag for GPU work
gpu_host = config.select_host(tag="cuda")

# Use wildcards for flexible matching
compute_hosts = config.filter_hosts(tag="comp*")

# Multiple tags (must match at least one)
ml_hosts = config.filter_hosts(tag=["cuda", "ml"])
```

### Selecting by Name

```python
# Select a specific host by name
host = config.select_host(name="worker-01")

# Use wildcards to match host name patterns
workers = config.filter_hosts(name="worker-*")
```

### Combined Criteria

```python
# Select an Ubuntu host from the workers queue with compute tag
host = config.select_host(
    queue="workers",
    os="ubuntu",
    tag="compute"
)
```

### Custom Selection Logic

```python
# Use a custom function for complex selection logic
def has_enough_capacity(host):
    return host.size >= 16

large_hosts = config.filter_hosts(custom=has_enough_capacity)
```

## SSH Integration

### Basic SSH Hook Usage

```python
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow_balancer import BalancerConfiguration

config = BalancerConfiguration.load_path("config/balancer.yaml")
host = config.select_host(queue="workers")

# Create an SSH hook from the host
ssh_hook = host.hook()

# Use with SSHOperator
task = SSHOperator(
    task_id="remote_task",
    ssh_hook=ssh_hook,
    command="ls -la /data",
)
```

### Customizing the SSH Hook

```python
# Override username for specific use case
ssh_hook = host.hook(username="admin")

# Pass additional SSH hook parameters
ssh_hook = host.hook(
    keepalive_interval=10,
    banner_timeout=30,
)

# Use .local suffix for hostname resolution (default behavior)
ssh_hook = host.hook(use_local=True)  # host1 -> host1.local

# Disable .local suffix
ssh_hook = host.hook(use_local=False)
```

### Using Password or Key Authentication

```yaml
# config/balancer.yaml
hosts:
  # Key-based authentication (recommended)
  - name: secure-host
    username: deploy
    key_file: /home/airflow/.ssh/deploy_key

  # Password authentication
  - name: legacy-host
    username: admin
    password: "{{ var.json.legacy_host_credentials.password }}"

  # Using Airflow Variables for password
  - name: variable-auth-host
    username: admin
    password:
      _target_: airflow_pydantic.Variable
      key: host_password
```

### Overriding Host Configuration

```python
# Create a modified copy of a host for specific use cases
host = config.select_host(queue="workers")

# Override username for this specific use
admin_host = host.override(username="admin")
ssh_hook = admin_host.hook()
```

## Port Management

### Tracking Port Usage

```yaml
# config/balancer.yaml
ports:
  # Associate port with host by name
  - host_name: worker-01
    port: 8080
    tags: [api]

  # Associate port with host object reference
  - host: ${...hosts[0]}
    port: 8793

  # Named port for easier reference
  - name: flower-ui
    host_name: worker-01
    port: 5555
    tags: [monitoring]
```

### Finding Free Ports

```python
# Get a random free port on a host
host = config.select_host(queue="workers")
free_port = config.free_port(host=host)

# Specify port range
free_port = config.free_port(host=host, min=8000, max=9000)
```

### Filtering Ports

```python
# Filter ports by tag
api_ports = config.filter_ports(tag="api")

# Filter by name pattern
flower_ports = config.filter_ports(name="flower*")

# Select a single port
port = config.select_port(tag="monitoring")
```

## Integration with airflow-config

### Basic Extension Configuration

```yaml
# config/config.yaml
# @package _global_
_target_: airflow_config.Configuration
defaults:
  - extensions/balancer@extensions.balancer
```

```yaml
# config/extensions/balancer.yaml
# @package extensions.balancer
_target_: airflow_balancer.BalancerConfiguration

default_username: airflow
hosts:
  - name: worker1
    size: 8
    queues: [workers]
```

```python
from airflow_config import load_config

config = load_config("config", "config")
balancer = config.extensions["balancer"]

host = balancer.select_host(queue="workers")
```

### Environment-Specific Configurations

```yaml
# config/extensions/balancer/base.yaml
# @package extensions.balancer
_target_: airflow_balancer.BalancerConfiguration

default_username: airflow
default_size: 8

# config/extensions/balancer/production.yaml
# @package extensions.balancer
defaults:
  - base

default_key_file: /home/airflow/.ssh/prod_key
hosts:
  - name: prod-worker-01
    size: 32
    queues: [workers]
  - name: prod-worker-02
    size: 32
    queues: [workers]

# config/extensions/balancer/development.yaml
# @package extensions.balancer
defaults:
  - base

hosts:
  - name: dev-worker
    size: 8
    queues: [workers]
```

### Using with airflow-pydantic Models

Since `airflow-balancer` builds on `airflow-pydantic`, you get full integration with the Pydantic-based Airflow models:

```yaml
# config/dag.yaml
_target_: airflow_config.Configuration

default_args:
  _target_: airflow_pydantic.TaskArgs
  owner: data-team
  retries: 3
  pool: "{{ extensions.balancer.hosts[0].name }}"

extensions:
  balancer:
    _target_: airflow_balancer.BalancerConfiguration
    hosts:
      - name: compute-pool
        size: 16
        queues: [compute]
```

## Complete DAG Example

Here's a complete example showing how to use `airflow-balancer` in a real DAG:

```python
from datetime import datetime
from airflow import DAG
from airflow.providers.ssh.operators.ssh import SSHOperator
from airflow_config import load_config
from airflow_balancer import BalancerConfiguration

# Load configuration
config = load_config("config", "production")
balancer: BalancerConfiguration = config.extensions["balancer"]

# Select hosts for different workloads
compute_host = balancer.select_host(queue="workers", tag="compute")
gpu_host = balancer.select_host(queue="gpu", tag="cuda")

with DAG(
    dag_id="distributed_ml_pipeline",
    start_date=datetime(2024, 1, 1),
    schedule="0 6 * * *",
    catchup=False,
) as dag:

    # Run data preparation on compute host
    prepare_data = SSHOperator(
        task_id="prepare_data",
        ssh_hook=compute_host.hook(),
        command="python /opt/ml/prepare_data.py",
        pool=compute_host.name,  # Use host-specific pool
    )

    # Run training on GPU host
    train_model = SSHOperator(
        task_id="train_model",
        ssh_hook=gpu_host.hook(),
        command="python /opt/ml/train.py --gpu",
        pool=gpu_host.name,
    )

    # Run evaluation back on compute host
    evaluate = SSHOperator(
        task_id="evaluate",
        ssh_hook=compute_host.hook(),
        command="python /opt/ml/evaluate.py",
        pool=compute_host.name,
    )

    prepare_data >> train_model >> evaluate
```

## Testing

### Using the Testing Utilities

`airflow-balancer` provides testing utilities to mock pool and variable operations:

```python
from airflow_balancer import BalancerConfiguration, Host
from airflow_balancer.testing import pools, variables

def test_my_balancer_logic():
    # Mock pool operations
    with pools():
        config = BalancerConfiguration(
            hosts=[
                Host(name="test-host", size=8, queues=["test"]),
            ]
        )
        assert config.select_host(queue="test").name == "test-host"

def test_with_variables():
    # Mock variable operations
    with variables("my-password"):
        host = Host(
            name="test-host",
            username="admin",
            password=Variable(key="test"),
        )
        assert host.hook().password == "my-password"
```

### Testing Host Selection

```python
from airflow_balancer import BalancerConfiguration, Host
from airflow_balancer.testing import pools

def test_host_filtering():
    with pools():
        config = BalancerConfiguration(
            hosts=[
                Host(name="host1", os="ubuntu", queues=["compute"]),
                Host(name="host2", os="macos", queues=["build"]),
                Host(name="host3", os="ubuntu", queues=["compute", "gpu"]),
            ]
        )

        # Test filtering
        ubuntu_hosts = config.filter_hosts(os="ubuntu")
        assert len(ubuntu_hosts) == 2

        compute_hosts = config.filter_hosts(queue="compute")
        assert len(compute_hosts) == 2

        # Test selection returns one of the filtered hosts
        selected = config.select_host(os="ubuntu")
        assert selected in ubuntu_hosts
```
