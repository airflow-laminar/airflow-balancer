from getpass import getuser
from unittest.mock import patch

from airflow.models.pool import PoolNotFound
from airflow_config import load_config

from airflow_balancer import BalancerConfiguration, Host


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
                assert host.hook()

    def test_load_hook(self):
        h = Host(name="test", username="test")

        assert h.hook()
        assert h.hook().username == "test"
        assert h.hook().remote_host == "test.local"
        assert h.hook().password is None
        assert h.hook().key_file is None

        h = Host(name="test", username="test", password="test")
        assert h.hook()
        assert h.hook().username == "test"
        assert h.hook().remote_host == "test.local"
        assert h.hook().password == "test"
        assert h.hook().key_file is None

        h = Host(name="test", username="test", password_variable="test")
        with patch("airflow.models.variable.Variable.get") as get_mock:
            get_mock.return_value = "test"
            assert h.hook()
            assert h.hook().username == "test"
            assert h.hook().remote_host == "test.local"
            assert h.hook().password == "test"
            assert h.hook().key_file is None

        h = Host(name="test", username="test", password_variable="test", password_variable_key="test")
        with patch("airflow.models.variable.Variable.get") as get_mock:
            get_mock.return_value = {"test": "blerg"}
            assert h.hook()
            assert h.hook().username == "test"
            assert h.hook().remote_host == "test.local"
            assert h.hook().password == "blerg"
            assert h.hook().key_file is None

        h = Host(name="test", username="test", key_file="test")
        assert h.hook()
        assert h.hook().username == "test"
        assert h.hook().remote_host == "test.local"
        assert h.hook().password is None
        assert h.hook().key_file == "test"

        h = Host(name="test")
        assert h.hook()
        assert h.hook().username == getuser()
        assert h.hook().remote_host == "test.local"
        assert h.hook().password is None
        assert h.hook().key_file is None

    def test_filter_hosts(self):
        with patch("airflow_balancer.config.Pool") as pool_mock:
            pool_mock.get_pool.side_effect = PoolNotFound()
            b = BalancerConfiguration(
                hosts=[
                    Host(name="host1", os="ab", queues=["ab"], tags=["tag1", "tag2"]),
                    Host(name="host2", os="abc", queues=["abc"], tags=["tg2"]),
                    Host(name="host3", os="ac", queues=["ac"], tags=["tag3"]),
                ]
            )

            assert len(b.filter_hosts(queue="ab")) == 1
            assert len(b.filter_hosts(queue=["abc"])) == 1
            assert len(b.filter_hosts(queue=["ac"])) == 1
            assert len(b.filter_hosts(queue=["ab", "abc"])) == 2
            assert len(b.filter_hosts(queue="ab*")) == 2

            assert b.select_host(queue="ab") in b.filter_hosts(queue="ab")
            assert b.select_host(queue=["abc"]) in b.filter_hosts(queue=["abc"])
            assert b.select_host(queue=["ac"]) in b.filter_hosts(queue=["ac"])
            assert b.select_host(queue=["ab", "abc"]) in b.filter_hosts(queue=["ab", "abc"])
            assert b.select_host(queue="ab*") in b.filter_hosts(queue="ab*")

            assert len(b.filter_hosts(tag="tag1")) == 1
            assert len(b.filter_hosts(tag="tag*")) == 2
            assert len(b.filter_hosts(tag="t*")) == 3
            assert len(b.filter_hosts(tag=["tag1", "tag2"])) == 1

            assert b.select_host(tag="tag1") in b.filter_hosts(tag="tag1")
            assert b.select_host(tag="tag*") in b.filter_hosts(tag="tag*")
            assert b.select_host(tag="t*") in b.filter_hosts(tag="t*")
            assert b.select_host(tag=["tag1", "tag2"]) in b.filter_hosts(tag=["tag1", "tag2"])

            assert len(b.filter_hosts(os="ab")) == 1
            assert len(b.filter_hosts(os="ab*")) == 2
            assert len(b.filter_hosts(os="abc")) == 1
            assert len(b.filter_hosts(os=["ab*", "ac"])) == 3

            assert b.select_host(os="ab") in b.filter_hosts(os="ab")
            assert b.select_host(os="ab*") in b.filter_hosts(os="ab*")
            assert b.select_host(os="abc") in b.filter_hosts(os="abc")
            assert b.select_host(os=["ab*", "ac"]) in b.filter_hosts(os=["ab*", "ac"])
