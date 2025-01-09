from unittest.mock import patch

from airflow.models.pool import PoolNotFound
from airflow_config import load_config

from airflow_balancer import BalancerConfiguration


class TestConfig:
    def test_load_config(self):
        with patch("airflow_balancer.config.Pool") as pool_mock:
            pool_mock.get_pool.return_value = "Test"
            config = BalancerConfiguration()
            assert config

        with patch("airflow_balancer.config.Pool") as pool_mock:
            pool_mock.get_pool.side_effect = PoolNotFound()
            config = BalancerConfiguration()
            assert config

    def test_load_config_hydra(self):
        with patch("airflow_balancer.config.Pool"):
            config = load_config(config_name="config")
            assert config
            assert "balancer" in config.extensions
            assert len(config.extensions["balancer"].hosts) == 3
            assert [x.name for x in config.extensions["balancer"].hosts] == ["host1", "host2", "host3"]
            for host in config.extensions["balancer"].hosts:
                assert host.hook
