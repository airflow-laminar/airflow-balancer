from __future__ import annotations

import os

from airflow.configuration import conf
from airflow.plugins_manager import AirflowPlugin
from airflow.security import permissions
from airflow.www.auth import has_access
from flask import Blueprint, request
from flask_appbuilder import BaseView, expose

from .functions import get_hosts_from_yaml, get_yaml_files

__all__ = (
    "AirflowBalancerViewerPluginView",
    "AirflowBalancerViewerPlugin",
)


class AirflowBalancerViewerPluginView(BaseView):
    """Creating a Flask-AppBuilder View"""

    default_view = "home"

    @expose("/hosts")
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def hosts(self):
        """Create hosts view"""
        yaml = request.args.get("yaml")
        if not yaml:
            return self.render_template("airflow_config/500.html", yaml="- yaml file not specified")
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
        dags_folder = os.environ.get("AIRFLOW__CORE__DAGS_FOLDER", conf.getsection("core").get("dags_folder"))
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
    static_folder="static",
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
    flask_blueprints = [bp]
    appbuilder_views = [view_subitem]
    appbuilder_menu_items = [docs_link_subitem]
