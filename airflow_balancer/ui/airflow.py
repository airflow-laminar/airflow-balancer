from __future__ import annotations

from pathlib import Path
from typing import ClassVar

from airflow.plugins_manager import AirflowPlugin

__all__ = (
    "AirflowBalancerViewerPlugin",
    "AirflowBalancerViewerPluginView",
)

try:
    from airflow.api_fastapi.auth.managers.models.resource_details import AccessView
    from airflow.api_fastapi.core_api.security import requires_access_view
except ImportError:
    from airflow.security import permissions
    from airflow.www.auth import has_access
    from flask import Blueprint, request
    from flask_appbuilder import BaseView, expose

    from .functions import get_dags_folder, get_hosts_from_yaml, get_yaml_files

    class AirflowBalancerViewerPluginView(BaseView):
        """Creating a Flask-AppBuilder View"""

        default_view = "home"

        @expose("/hosts")
        @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
        def hosts(self):
            """Create hosts view"""
            yaml = request.args.get("yaml")
            if not yaml:
                return self.render_template("airflow_balancer/500.html", yaml="- yaml file not specified")
            if not Path(yaml).is_file():
                return self.render_template("airflow_balancer/500.html", yaml=yaml)
            try:
                config = get_hosts_from_yaml(yaml)
            except FileNotFoundError:
                return self.render_template("airflow_balancer/500.html", yaml=yaml)
            return self.render_template("airflow_balancer/hosts.html", config=config)

        @expose("/")
        @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
        def home(self):
            """Create default view"""
            # Locate the dags folder
            dags_folder = get_dags_folder()
            if not dags_folder:
                return self.render_template("airflow_balancer/404.html")
            yamls, yamls_airflow_config = get_yaml_files(dags_folder)
            return self.render_template("airflow_balancer/home.html", yamls=yamls, yamls_airflow_config=yamls_airflow_config)

    # Instantiate a view
    airflow_balancer_viewer_plugin_view = AirflowBalancerViewerPluginView()

    # Creating a flask blueprint
    bp = Blueprint(
        "Airflow Balancer",
        __name__,
        template_folder="templates",
        static_folder=str(Path(__file__).parent.parent / "extension"),
        static_url_path="/static/airflow-balancer",
    )

    # Create menu items
    docs_link_subitem = {
        "label": "Airflow Balancer Docs",
        "name": "Airflow Balancer Docs",
        "href": "https://airflow-laminar.github.io/airflow-balancer/",
        "category": "Docs",
    }

    view_subitem = {"label": "Airflow Balancer Viewer", "category": "Laminar", "name": "Laminar", "view": airflow_balancer_viewer_plugin_view}

    class AirflowBalancerViewerPlugin(AirflowPlugin):
        """Defining the plugin class"""

        name = "Airflow Balancer"
        flask_blueprints: ClassVar[list] = [bp]
        appbuilder_views: ClassVar[list] = [view_subitem]
        appbuilder_menu_items: ClassVar[list] = [docs_link_subitem]

else:
    from fastapi import Depends

    from .standalone import build_app

    class AirflowBalancerViewerPluginView:  # type: ignore[no-redef]
        pass

    class AirflowBalancerViewerPlugin(AirflowPlugin):  # type: ignore[no-redef]
        """Airflow 3 FastAPI viewer plugin."""

        name = "Airflow Balancer"
        fastapi_apps: ClassVar[list] = [
            {
                "app": build_app(dependencies=[Depends(requires_access_view(AccessView.WEBSITE))]),
                "url_prefix": "/airflow-balancer",
                "name": "Airflow Balancer Viewer",
            }
        ]
        external_views: ClassVar[list] = [
            {
                "name": "Airflow Balancer Viewer",
                "href": "/airflow-balancer/",
                "destination": "nav",
                "category": "admin",
                "url_route": "airflow-balancer",
            },
            {
                "name": "Airflow Balancer Docs",
                "href": "https://airflow-laminar.github.io/airflow-balancer/",
                "destination": "nav",
                "category": "docs",
            },
        ]
