from pathlib import Path
from unittest.mock import patch

from airflow_balancer import BalancerConfiguration
from airflow_balancer.testing import pools
from airflow_balancer.ui.functions import get_hosts_from_yaml, get_yaml_files
from airflow_balancer.ui.standalone import build_app, main


class TestAirflowPlugin:
    def test_plugin(self):
        from airflow_balancer.ui.viewer import AirflowBalancerViewerPlugin, AirflowBalancerViewerPluginView

        AirflowBalancerViewerPluginView()
        AirflowBalancerViewerPlugin()

    # def test_plugin_view(self):
    #     with patch("airflow_balancer.ui.viewer.expose") as mock_expose, \
    #         patch("airflow_balancer.ui.viewer.has_access") as mock_has_access, \
    #             patch("airflow_balancer.ui.viewer.request") as mock_request:
    #         from airflow_balancer.ui.viewer import AirflowBalancerViewerPluginView
    #         mock_expose.side_effect = lambda x: lambda f: f
    #         mock_has_access.side_effect = lambda x: lambda f: f
    #         pv = AirflowBalancerViewerPluginView()
    #         pv.home()


class TestPluginFunctions:
    def test_plugin_functions_get_yamls(self):
        root = Path(__file__).parent
        assert get_yaml_files(root / "config") == (
            [
                Path(root) / "config/extensions/default.yaml",
                Path(root) / "config/extensions/balancer.yaml",
                Path(root) / "config/extensions/second.yaml",
            ],
            [
                Path(root) / "config/config.yaml",
            ],
        )

    def test_plugin_functions_load_yamls(self):
        root = Path(__file__).parent
        with pools():
            assert isinstance(BalancerConfiguration.load_path(Path(root) / "config/extensions/default.yaml"), BalancerConfiguration)
            assert isinstance(BalancerConfiguration.load_path(Path(root) / "config/extensions/balancer.yaml"), BalancerConfiguration)

    def test_plugin_functions_get_hosts(self):
        root = Path(__file__).parent
        assert (
            get_hosts_from_yaml(Path(root) / "config/extensions/default.yaml")
            == '{"hosts":[{"name":"host0","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host0","size":8,"queues":["workers"],"tags":[]},{"name":"host1","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},{"name":"host2","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},{"name":"host3","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"macos","pool":"host3","size":8,"queues":["workers"],"tags":[]}],"ports":[{"name":"","host":{"name":"host1","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},"host_name":"host1","port":8000,"tags":[]},{"name":"named-port","host":{"name":"host1","username":null,"password":null,"password_variable":null,"password_variable_key":null,"key_file":null,"os":"ubuntu","pool":null,"size":16,"queues":["primary"],"tags":[]},"host_name":"","port":8080,"tags":[]},{"name":"","host":{"name":"host2","username":"timkpaine","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},"host_name":"host2","port":8793,"tags":[]}],"default_username":"timkpaine","default_password":null,"default_password_variable":null,"default_password_variable_key":null,"default_key_file":"/home/airflow/.ssh/id_rsa","primary_queue":"primary","secondary_queue":"workers","default_queue":"default","default_size":8,"override_pool_size":false,"create_connection":false}'
        )
        assert (
            get_hosts_from_yaml(Path(root) / "config/extensions/balancer.yaml")
            == '{"hosts":[{"name":"host0","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host0","size":8,"queues":["workers"],"tags":[]},{"name":"host1","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},{"name":"host2","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},{"name":"host3","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"macos","pool":"host3","size":8,"queues":["workers"],"tags":[]}],"ports":[{"name":"","host":{"name":"host1","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},"host_name":"host1","port":8000,"tags":[]},{"name":"named-port","host":{"name":"host1","username":null,"password":null,"password_variable":null,"password_variable_key":null,"key_file":null,"os":"ubuntu","pool":null,"size":16,"queues":["primary"],"tags":[]},"host_name":"","port":8080,"tags":[]},{"name":"","host":{"name":"host2","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},"host_name":"host2","port":8793,"tags":[]}],"default_username":"test","default_password":null,"default_password_variable":null,"default_password_variable_key":null,"default_key_file":"/home/airflow/.ssh/id_rsa","primary_queue":"primary","secondary_queue":"workers","default_queue":"default","default_size":8,"override_pool_size":false,"create_connection":false}'
        )

    def test_plugin_functions_get_hosts_airflow_config(self):
        root = Path(__file__).parent
        assert (
            get_hosts_from_yaml(Path(root) / "config/config.yaml")
            == '{"hosts":[{"name":"host0","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host0","size":8,"queues":["workers"],"tags":[]},{"name":"host1","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},{"name":"host2","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},{"name":"host3","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"macos","pool":"host3","size":8,"queues":["workers"],"tags":[]}],"ports":[{"name":"","host":{"name":"host1","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host1","size":16,"queues":["primary"],"tags":[]},"host_name":"host1","port":8000,"tags":[]},{"name":"named-port","host":{"name":"host1","username":null,"password":null,"password_variable":null,"password_variable_key":null,"key_file":null,"os":"ubuntu","pool":null,"size":16,"queues":["primary"],"tags":[]},"host_name":"","port":8080,"tags":[]},{"name":"","host":{"name":"host2","username":"test","password":null,"password_variable":null,"password_variable_key":null,"key_file":"/home/airflow/.ssh/id_rsa","os":"ubuntu","pool":"host2","size":16,"queues":["workers"],"tags":[]},"host_name":"host2","port":8793,"tags":[]}],"default_username":"test","default_password":null,"default_password_variable":null,"default_password_variable_key":null,"default_key_file":"/home/airflow/.ssh/id_rsa","primary_queue":"primary","secondary_queue":"workers","default_queue":"default","default_size":8,"override_pool_size":false,"create_connection":false}'
        )


class TestStandaloneUI:
    def test_standalone_ui(self):
        # Test the build_app function
        app = build_app()
        assert app is not None

    def test_launch(self):
        # Test the main function
        with patch("airflow_balancer.ui.standalone.run") as mock_run:
            main()
            mock_run.assert_called_once()

    def test_main(self):
        import airflow_balancer.ui.standalone.__main__  # noqa: F401
