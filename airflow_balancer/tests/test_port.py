from unittest.mock import patch

import pytest
from airflow.models.pool import PoolNotFound

from airflow_balancer import BalancerConfiguration, Host, Port


class TestConfig:
    def test_no_duplicate_ports(self):
        with patch("airflow_balancer.config.balancer.Pool") as pool_mock:
            pool_mock.get_pool.side_effect = PoolNotFound()
            h1 = Host(name="host1")
            h2 = Host(name="host2")
            p1 = Port(host=h1, port=1002)
            p2 = Port(host=h2, port=1000)
            p1dupe = Port(host_name="host1", port=1002)

            BalancerConfiguration(
                hosts=[h1, h2],
                ports=[p1, p2],
            )

            with pytest.raises(ValueError):
                BalancerConfiguration(
                    hosts=[h1, h2],
                    ports=[p1, p2, p1dupe],
                )
