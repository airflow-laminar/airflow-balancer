from pathlib import Path

from airflow.models.pool import PoolNotFound
from airflow_config import load_config

from airflow_balancer import BalancerConfiguration
from airflow_balancer.testing import pools


class TestConfig:
    def test_load_config(self):
        with pools(return_value="Test"):
            config = BalancerConfiguration()
            assert config

        with pools(side_effect=PoolNotFound()):
            config = BalancerConfiguration()
            assert config

    def test_load_config_direct(self):
        with pools():
            fp = Path(__file__).parent.resolve() / "config" / "extensions" / "default.yaml"
            config = BalancerConfiguration.load_path(fp)
            print(config)
            assert config
            assert isinstance(config, BalancerConfiguration)
            assert len(config.hosts) == 4

    def test_load_config_direct_via_airflow_config(self):
        with pools():
            fp = Path(__file__).parent.resolve() / "config" / "extensions" / "default.yaml"
            config = BalancerConfiguration.load(config_name=fp.stem, config_dir=fp.parent)
            print(config)
            assert config
            assert isinstance(config, BalancerConfiguration)
            assert len(config.hosts) == 4

    def test_load_config_direct_via_airflow_config_fallback(self):
        with pools():
            fp = Path(__file__).parent.resolve() / "config" / "extensions" / "default.yaml"
            config = BalancerConfiguration.load(config_name=fp, config_dir="")
            print(config)
            assert config
            assert isinstance(config, BalancerConfiguration)
            assert len(config.hosts) == 4

    def test_load_config_serialize(self):
        # Test serialization needed by the viewer
        with pools():
            fp = str(Path(__file__).parent.resolve() / "config" / "extensions" / "balancer.yaml")
            config = BalancerConfiguration.load_path(fp)
            assert config
            assert isinstance(config, BalancerConfiguration)
            assert len(config.hosts) == 4
            config.model_dump_json(serialize_as_any=True)

    def test_load_config_hydra(self):
        with pools():
            config = load_config("config", "config")
            assert config
            assert "balancer" in config.extensions
            assert len(config.extensions["balancer"].hosts) == 4
            assert [x.name for x in config.extensions["balancer"].hosts] == ["host0", "host1", "host2", "host3"]
            assert config.extensions["balancer"].default_username == "test"
            for host in config.extensions["balancer"].hosts:
                assert host.hook()
