# airflow balancer

Utilities for tracking hosts and ports and load balancing DAGs

[![Build Status](https://github.com/airflow-laminar/airflow-balancer/actions/workflows/build.yaml/badge.svg?branch=main&event=push)](https://github.com/airflow-laminar/airflow-balancer/actions/workflows/build.yaml)
[![codecov](https://codecov.io/gh/airflow-laminar/airflow-balancer/branch/main/graph/badge.svg)](https://codecov.io/gh/airflow-laminar/airflow-balancer)
[![License](https://img.shields.io/github/license/airflow-laminar/airflow-balancer)](https://github.com/airflow-laminar/airflow-balancer)
[![PyPI](https://img.shields.io/pypi/v/airflow-balancer.svg)](https://pypi.python.org/pypi/airflow-balancer)

## Overview

`airflow-balancer` is a utility library for Apache Airflow to track host and port usage via yaml files.
It is tightly integrated with [airflow-laminar/airflow-config](https://github.com/airflow-laminar/airflow-config).

With `airflow-balancer`, you can register host and port usage in configuration:

```yaml
_target_: airflow_balancer.BalancerConfiguration
default_username: timkpaine
hosts:
  - name: host1
    size: 16
    os: ubuntu
    queues: [primary]

  - name: host2
    os: ubuntu
    size: 16
    queues: [workers]

  - name: host3
    os: macos
    size: 8
    queues: [workers]

ports:
  - host: host1
    port: 8080

  - host_name: host2
    port: 8793
```

Either via `airflow-config` or directly, you can then select amongst available hosts for use in your DAGs.

```python
from airflow_balaner import BalancerConfiguration, load

balancer_config: BalancerConfiguration = load("balancer.yaml")

host = balancer_config.select_host(queue="workers")
port = balancer_config.free_port(host=host)

...

operator = SSHOperator(ssh_hook=host.hook(), ...)

```

### Visualization

Configuration, and Host and Port listing is built into the extension, available either from the topbar in Airflow or as a standalone viewer (via the `airflow-balancer-viewer` CLI).

<img src="https://raw.githubusercontent.com/airflow-laminar/airflow-balancer/refs/heads/main/docs/img/toolbar.png" width=400>

<img src="https://raw.githubusercontent.com/airflow-laminar/airflow-balancer/refs/heads/main/docs/img/home.png" width=400>

<img src="https://raw.githubusercontent.com/airflow-laminar/airflow-balancer/refs/heads/main/docs/img/hosts.png" width=800>


## Installation

You can install from pip:

```bash
pip install airflow-balancer
```

Or via conda:

```bash
conda install airflow-balancer -c conda-forge
```

## License

This software is licensed under the Apache 2.0 license. See the [LICENSE](LICENSE) file for details.
