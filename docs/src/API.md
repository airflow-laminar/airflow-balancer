---
myst:
  heading_anchors: 3
---

# Reference

`airflow_balancer` reexports the models in `airflow_pydantic.extras.balancer`. This reference describes `airflow-pydantic` 1.7. The Python package requires Python 3.11 or later and supports the Airflow 2 and 3 installation extras.

## BalancerConfiguration

| Field                | Default                      | Meaning                                                           |
| -------------------- | ---------------------------- | ----------------------------------------------------------------- |
| `hosts`              | `[]`                         | Host declarations; duplicate names are rejected.                  |
| `ports`              | `[]`                         | Port declarations; duplicate `(host, port)` pairs are rejected.   |
| `default_username`   | `"airflow"`                  | Username applied to hosts without one.                            |
| `default_password`   | `None`                       | String or Variable applied to hosts without a password.           |
| `default_key_file`   | `None`                       | Key path applied to hosts without one.                            |
| `default_size`       | `8`                          | Capacity applied to hosts without a truthy size.                  |
| `primary_queue`      | `"default"`                  | Configuration label for the primary queue.                        |
| `secondary_queue`    | `"default"`                  | Configuration label for the secondary queue.                      |
| `default_queue`      | `"default"`                  | Configuration label for the default queue.                        |
| `override_pool_size` | `False`                      | Reconciliation may change existing pool slot counts when true.    |
| `create_connection`  | `False`                      | Declared flag; the current validator does not create Connections. |
| `pool_manager`       | `PoolManagerConfiguration()` | Generated reconciliation DAG settings.                            |

Validation normalizes defaults and creates missing host **Pool models** without querying Airflow. It resolves `Port.host_name` against the configured hosts, then sorts hosts by name and ports by host name/port number. Unknown hosts, duplicate hosts, and duplicate port usage produce validation errors.

`all_hosts` and `all_ports` return sorted, deduplicated declarations. `managed_dags()` returns the pool-manager Dag model, or an empty list when disabled. `generated_files(airflow_major_version=2)` returns filename/source mappings for that manager.

## Host

| Field      | Default  | Meaning                                                    |
| ---------- | -------- | ---------------------------------------------------------- |
| `name`     | Required | Hostname and default pool name.                            |
| `username` | `None`   | SSH username; normalized from the balancer default.        |
| `password` | `None`   | String or `airflow_pydantic.Variable`.                     |
| `key_file` | `None`   | SSH private-key path.                                      |
| `os`       | `None`   | Operating-system label used by filters.                    |
| `pool`     | `None`   | Pool declaration; normalized from name/size when absent.   |
| `size`     | `None`   | Host capacity; normalized from `default_size` when falsey. |
| `queues`   | `[]`     | Queue labels used by filters.                              |
| `tags`     | `[]`     | Tags used by filters.                                      |

`Host.hook(username=None, use_local=True, **hook_kwargs)` returns an SSHHook. It forwards extra keyword arguments to the SSHHook constructor. With `use_local=True`, a name without a dot gets a `.local` suffix. An explicit username takes precedence over the Host username. A password takes precedence over a key file when both are configured.

Variable passwords are looked up when creating the hook. Dictionary values use the `password` key. Failed offline lookup produces an unresolved placeholder which DAG rendering replaces with a runtime lookup. `hook()` constructs the hook; opening a network connection is a separate operation.

`Host.override(**kwargs)` returns a new Host with overridden fields. Pool declarations serialize as objects containing `pool`, `slots`, `description`, and `include_deferred`; `host.pool.pool` is the string identifier.

## Port

| Field       | Default  | Meaning                                      |
| ----------- | -------- | -------------------------------------------- |
| `name`      | `""`     | Optional identifier.                         |
| `host`      | `None`   | Host object.                                 |
| `host_name` | `""`     | Hostname resolved by the enclosing balancer. |
| `port`      | Required | Integer from 1 through 65535.                |
| `tags`      | `[]`     | Tags used by filters.                        |

At least one of `host` and `host_name` is required. When both are present, their names must match. The enclosing balancer requires a resolved host.

`port.pool` returns `name` when nonempty, otherwise `<host-name>-<port>`. This computed identifier determines Port equality and hashing. The `name` query filter matches the explicit `name` field.

## Queries

| Method           | Filters                                | Result                    |
| ---------------- | -------------------------------------- | ------------------------- |
| `filter_hosts()` | `name`, `queue`, `os`, `tag`, `custom` | List of matching Hosts.   |
| `select_host()`  | `name`, `queue`, `os`, `tag`, `custom` | One randomly chosen Host. |
| `filter_ports()` | `name`, `tag`, `custom`                | List of matching Ports.   |
| `select_port()`  | `name`, `tag`, `custom`                | One randomly chosen Port. |

String filters accept `fnmatch` patterns. Lists use OR within one filter; different filters are combined with AND. Queue and tag filters match any corresponding label on a candidate. `custom` is a predicate called with each candidate. A no-match query raises `RuntimeError`, including a filter query. Declare `os` on candidate hosts when using an operating-system filter.

`BalancerHostQueryConfiguration` (`HostQuery`) and `BalancerPortQueryConfiguration` (`PortQuery`) expose the same filters as models. Their `kind` is `"select"` by default or `"filter"`; `balancer` is required. `custom` also accepts a callable path. `execute()` runs the query.

`free_port(host, min=1000, max=65535)` returns a new Port with a random number in `[min, max)` that is not listed for that host. It does not append the Port to `ports`, probe the network, or reserve a socket. The range must contain an unconfigured valid port; a fully configured range has no terminating candidate.

## Loading

| Entry point                                                                                                  | Behavior                                                                                                                                           |
| ------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `BalancerConfiguration.load_path(yaml_file, _config_dir=None)`                                               | Loads a `.yaml` file through Hydra. Relative strings are resolved from the working directory; `_config_dir` overrides its configuration directory. |
| `BalancerConfiguration.load(config_dir="config", config_name="", overrides=None, *, basepath="", _offset=4)` | Looks for a balancer extension through airflow-config, then falls back to a balancer file.                                                         |
| `airflow_balancer.load_config`                                                                               | Alias of `BalancerConfiguration.load`.                                                                                                             |

`load_path()` raises `ValueError` for a non-`.yaml` filename or a loaded document without a BalancerConfiguration. `load()` defaults its fallback filename to `balancer.yaml`.

## Pool manager

| Field                         | Default                          |
| ----------------------------- | -------------------------------- |
| `dag.dag_id`                  | `"airflow_laminar_pool_manager"` |
| `dag.schedule`                | `"*/5 * * * *"`                  |
| `dag.catchup`                 | `False`                          |
| `dag.max_active_runs`         | `1`                              |
| `dag.is_paused_upon_creation` | `False`                          |
| `task.pool`                   | `"default_pool"`                 |
| `task.retries`                | `2`                              |
| `task_id`                     | `"reconcile_pools"`              |
| `backend`                     | `"auto"`                         |
| `connection_id`               | `"airflow_laminar_api"`          |
| `mwaa_environment_name`       | `None`                           |
| `mwaa_region_name`            | `None`                           |

`dag` and `task` accept normal Dag and TaskArgs settings. `dag.enabled: false` disables generation. A task already using the reserved reconciliation task ID causes `ValueError`.

Backends are `auto`, `airflow2`, `airflow3`, and `mwaa`. Auto chooses MWAA when an environment name is configured, otherwise the installed Airflow major version. Airflow 2 uses database pool helpers. Airflow 3 uses the configured Connection: `extra.base_url` or the connection type/host/port forms the URL, and `extra.token` supplies authentication or login/password is exchanged at `/auth/token`. Pool requests use `/api/v2/pools`.

The MWAA backend calls `boto3.client("mwaa").invoke_rest_api`; it uses `mwaa_environment_name` or `AIRFLOW_ENV_NAME`, plus the optional region. Host pools use `host.size` slots; port pools use one slot and include deferred tasks. Reconciliation creates missing pools and updates descriptions/deferred-task settings. Existing slot counts change only with `override_pool_size=True`.

## Viewer

The viewer lists `.yaml` configurations beneath the DAG directory and shows their normalized defaults, hosts, and ports. Host pool names are read from serialized Pool objects; legacy string values and missing pools are also accepted. Password values are replaced with `***` before serialization.

| Setting                      | Behavior                                               |
| ---------------------------- | ------------------------------------------------------ |
| `AIRFLOW__CORE__DAGS_FOLDER` | First directory choice.                                |
| Airflow `core.dags_folder`   | Fallback when Airflow is installed.                    |
| `AIRFLOW_HOME`               | Standalone fallback when no DAG directory is resolved. |
| Packaged test directory      | Last standalone fallback.                              |
| `PORT`                       | Standalone HTTP port; defaults to `8000`.              |

The standalone CLI is `airflow-balancer-viewer`, also available through `python -m airflow_balancer.ui.standalone`. It needs FastAPI and Uvicorn in addition to the base package and listens on `0.0.0.0`. `/` lists files; `/hosts?yaml=<path>` displays a selected configuration. Airflow 2 uses a Flask-AppBuilder view; Airflow 3 mounts a FastAPI application at `/airflow-balancer` and applies website-read authorization.

## Testing helpers

`airflow_balancer.testing.pools` and `variables` reexport the airflow-pydantic context managers for mocked Airflow access. They do not reserve actual pools or change Variable values in an Airflow deployment.
