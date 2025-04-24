type Host = {
  name: string;
  username: string;
  password: string | null;
  password_variable: string | null;
  password_variable_key: string | null;
  key_file: string;
  os: string;
  pool: string;
  size: number;
  queues: string[];
  tags: string[];
};

type Port = {
  name: string;
  host: Host;
  host_name: string;
  port: number;
  tags: string[];
};
type Config = {
  hosts?: Host[];
  ports?: Port[];
  default_username?: string;
  default_password_variable?: string;
  default_password_variable_key?: string;
  default_key_file?: string;
  default_size?: number;
};

document.addEventListener("DOMContentLoaded", async () => {
  const raw_config: string = window.__AIRFLOW_BALANCER_CONFIG__;
  const root_node: HTMLDivElement = document.getElementById(
    "airflow-balancer-root",
  );
  if (raw_config === undefined) {
    root_node!.innerHTML = `
        <div class="alert alert-danger" role="alert">
            <strong>Airflow Balancer Config not found!</strong>
            <p>Please make sure you are running the Airflow Balancer with the correct configuration.</p>
        </div>
        `;
  }

  const config: Config = JSON.parse(raw_config);

  root_node.innerHTML = `
    <div class="airflow-balancer-defaults">
        <h2>Defaults</h2>
        <div class="form-group">
            <label for="default-username">Default Username</label>
            <input type="text" class="form-control" id="default-username" disabled value="${config.default_username || ""}">
            <small class="form-text text-muted">Default username for all hosts.</small>
            <br>
            <label for="default-password-variable">Default Password Variable</label>
            <input type="text" class="form-control" id="default-password-variable" disabled value="${config.default_password_variable || ""}">
            <small class="form-text text-muted">Default password variable for all hosts.</small>
            <br>
            <label for="default-password-variable-key">Default Password Variable Key</label>
            <input type="text" class="form-control" id="default-password-variable-key" disabled value="${config.default_password_variable_key || ""}">
            <small class="form-text text-muted">Default password variable key for all hosts.</small>
            <br>
            <label for="default-key-file">Default Key File</label>
            <input type="text" class="form-control" id="default-key-file" disabled value="${config.default_key_file || ""}">
            <small class="form-text text-muted">Default key file for all hosts.</small>
            <br>
            <label for="default-size">Default Size</label>
            <input type="number" class="form-control" id="default-size" disabled value="${config.default_size || 0}">
            <small class="form-text text-muted">Default size for all hosts.</small>
        </div>
    </div>`;

  let host_table = `
    <div class="airflow-balancer-hosts">
      <h2>Hosts</h2>
      <table class="table table-striped table-bordered table-hover">
        <thead>
          <tr>
            <th>Name</th>
            <th>Username</th>
            <th>Password</th>
            <th>Password Variable</th>
            <th>Password Variable Key</th>
            <th>Key File</th>
            <th>OS</th>
            <th>Pool</th>
            <th>Size</th>
            <th>Queues</th>
            <th>Tags</th>
          </tr>
        </thead>
        <tbody>`;
  config.hosts?.forEach((host: Host) => {
    const host_name = host.name;
    const host_username = host.username;
    const host_password = host.password || "None";
    const host_password_variable = host.password_variable || "None";
    const host_password_variable_key = host.password_variable_key || "None";
    const host_key_file = host.key_file || "None";
    const host_os = host.os || "None";
    const host_pool = host.pool || "None";
    const host_size = host.size || 0;
    const host_queues = host.queues
      .map((queue) => `<span class="badge badge-secondary">${queue}</span>`)
      .join(" ");
    const host_tags = host.tags
      .map((tag) => `<span class="badge badge-secondary">${tag}</span>`)
      .join(" ");
    host_table += `
          <tr>
            <td><span>${host_name}</span></td>
            <td><span>${host_username}</span></td>
            <td><span>${host_password}</span></td>
            <td><span>${host_password_variable}</span></td>
            <td><span>${host_password_variable_key}</span></td>
            <td><span>${host_key_file}</span></td>
            <td><span>${host_os}</span></td>
            <td><span>${host_pool}</span></td>
            <td><span>${host_size}</span></td>
            <td>${host_queues}</td>
            <td>${host_tags}</td>
          </tr>
        `;
  });
  root_node.innerHTML += host_table;

  let port_table = `
    <div class="airflow-balancer-ports">
      <h2>Ports</h2>
      <table class="table table-striped table-bordered table-hover">
        <thead>
          <tr>
            <th>Name</th>
            <th>Host</th>
            <th>Port</th>
            <th>Tags</th>
          </tr>
        </thead>
        <tbody>`;
  config.ports?.forEach((port: Port) => {
    const port_name = port.name;
    const port_tags = port.tags
      .map((tag) => `<span class="badge badge-secondary">${tag}</span>`)
      .join(" ");
    const host = port.host_name || port.host.name;
    const port_number = port.port;
    port_table += `
          <tr>
            <td><span>${port_name}</span></td>
            <td><span>${host}</span></td>
            <td><span>${port_number}</span></td>
            <td>${port_tags}</td>
          </tr>
        `;
  });
  port_table += `
        </tbody>
        </table>
    </div>
    `;
  root_node.innerHTML += port_table;
});
