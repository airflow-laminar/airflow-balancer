---
myst:
  heading_anchors: 3
---

# How host selection relates to Airflow scheduling

## Configured candidates and random selection

A balancer declaration describes eligible worker hosts, their labels, and known ports. Filters narrow that inventory by name, queue, operating system, tag, or a predicate. Selection chooses randomly from the remaining candidates.

The selection algorithm does not poll CPU usage or inspect live Airflow pool occupancy. A host with more configured slots is not given a larger selection weight. Operating-system names and tags are labels supplied by the configuration author.

A `queue` filter selects hosts carrying that label. It does not set an operator's Celery queue. The SSH hook chooses the remote machine; the operator's `queue` chooses where Airflow executes the task itself.

If selection runs while the DAG is parsed, the selected host is part of that parsed DAG until it is parsed again. This affects repeated runs: random selection during parsing does not imply a fresh selection for each task attempt.

## Pool ownership

A host's pool declaration expresses Airflow concurrency capacity. It can use the host's name or a custom pool name. Operators participate in that limit when their `pool` argument names the corresponding pool; `host.pool.pool` supplies that identifier.

Pool declarations remain usable while generating DAG files without an Airflow metadata database. The pool-manager extension reconciles those declarations in a scheduled task. This separates configuration parsing from pool mutations and gives reconciliation a task state, logs, and retries.

The manager creates missing pools. Existing slot counts remain under deployment control unless `override_pool_size` is enabled. Description and deferred-task settings are reconciled independently. Host pool capacity comes from the host's `size`; each configured port gets a one-slot pool.

A declared port pool only constrains tasks that use it. A pool does not reserve a network socket, and declaring a host does not create an SSH Connection automatically.

## Port availability

`free_port()` means unlisted in the current configuration for the chosen host. It neither probes the network nor records its choice in the configuration. Two callers can therefore receive the same port, and an unlisted port can already be in use by another service.

When a service needs a stable endpoint, a configured `Port` gives it a predictable identifier. Dynamic allocation needs another owner for reservation and release, such as the process that binds the socket or the workload scheduler.

## Models, composition, and the viewer

`airflow-pydantic` implements the models and queries. `airflow-balancer` reexports them and supplies the viewer; `airflow-config` composes them with DAG and environment configuration.

The viewer shows that declared configuration. Its Hosts table shows a pool's name, and its Ports table shows configured endpoints. It is not a display of live pool occupancy or operating-system port usage.
