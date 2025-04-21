from __future__ import annotations

import os
from pathlib import Path

from airflow.configuration import conf
from airflow.plugins_manager import AirflowPlugin
from airflow.security import permissions
from airflow.www.auth import has_access
from flask import Blueprint, request
from flask_appbuilder import BaseView, expose

from airflow_balancer import BalancerConfiguration

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
            # Process the yaml
            yaml_file = Path(yaml).resolve()
            inst = BalancerConfiguration.load(yaml_file)
            for host in inst.hosts:
                if host.password:
                    host.password = "***"
            if inst.default_password:
                inst.default_password = "***"
            for port in inst.ports:
                if port.host.password:
                    port.host.password = "***"
        except FileNotFoundError:
            return self.render_template("airflow_balancer/500.html", yaml=yaml)
        return self.render_template("airflow_balancer/hosts.html", config=str(inst.model_dump_json(serialize_as_any=True)))

    @expose("/")
    @has_access([(permissions.ACTION_CAN_READ, permissions.RESOURCE_WEBSITE)])
    def home(self):
        """Create default view"""
        # Locate the dags folder
        dags_folder = os.environ.get("AIRFLOW__CORE__DAGS_FOLDER", conf.getsection("core").get("dags_folder"))
        if not dags_folder:
            return self.render_template("airflow_balancer/404.html")

        # Look for yamls inside the dags folder
        yamls = []
        base_path = Path(dags_folder)
        for path in base_path.glob("**/*.yaml"):
            if path.is_file():
                if "_target_: airflow_balancer.BalancerConfiguration" in path.read_text():
                    yamls.append(path)
        return self.render_template("airflow_balancer/home.html", yamls=yamls)


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
