from pathlib import Path
from unittest.mock import patch

import pytest

from airflow_balancer import BalancerConfiguration
from airflow_balancer.testing import pools
from airflow_balancer.ui.functions import get_hosts_from_yaml, get_yaml_files
from airflow_balancer.ui.standalone import build_app, main


class TestAirflowPlugin:
    def test_plugin(self):
        try:
            from airflow_balancer.ui.airflow import AirflowBalancerViewerPlugin, AirflowBalancerViewerPluginView
        except ImportError:
            return pytest.skip("Airflow not installed")

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
        assert get_hosts_from_yaml(Path(root) / "config/extensions/default.yaml").startswith(
            '{"hosts":[{"name":"host0","username":"timkpaine","password":null,"'
        )
        assert get_hosts_from_yaml(Path(root) / "config/extensions/balancer.yaml").startswith(
            '{"hosts":[{"name":"host0","username":"test","password":null,"'
        )

    def test_plugin_functions_get_hosts_airflow_config(self):
        root = Path(__file__).parent
        assert get_hosts_from_yaml(Path(root) / "config/config.yaml").startswith('{"hosts":[{"name":"host0","username":"test","password":null,')


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
