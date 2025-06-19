from contextlib import contextmanager
from unittest.mock import MagicMock, patch

__all__ = ("pools", "variables")


@contextmanager
def pools(return_value=None, side_effect=None):
    with patch("airflow_balancer.config.balancer.Pool") as pool_mock, patch("airflow_balancer.config.balancer.get_parsing_context") as context_mock:
        pool_mock.get_pool.return_value = return_value
        if side_effect:
            pool_mock.get_pool.side_effect = side_effect
        context_mock.return_value = MagicMock()
        context_mock.return_value.dag_id = "airflow_balancer.testing.pools"
        yield pool_mock


@contextmanager
def variables(return_value=None, side_effect=None):
    with patch("airflow.models.variable.Variable.get") as get_mock:
        get_mock.return_value = return_value
        if side_effect:
            get_mock.side_effect = side_effect
        yield get_mock
