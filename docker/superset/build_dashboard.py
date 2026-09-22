"""One-off script: builds the 'Hive-on-Tez: People' dashboard via Superset's
REST API. Run once inside the superset container, then export the result
with `superset export-dashboards` and check the export into
docker/superset/dashboards/ for the entrypoint to auto-import. Not itself
part of the reproducible startup path -- kept here as a record of how the
checked-in export was produced. Idempotent: safe to rerun, reuses existing
database/dataset/charts/dashboard by name instead of duplicating them.
"""
import json as _json
import sys

import requests

BASE = "http://localhost:8088"
s = requests.Session()

login = s.post(f"{BASE}/api/v1/security/login", json={
    "username": "admin", "password": "admin", "provider": "db", "refresh": True,
})
login.raise_for_status()
token = login.json()["access_token"]
s.headers["Authorization"] = f"Bearer {token}"

csrf = s.get(f"{BASE}/api/v1/security/csrf_token/")
csrf.raise_for_status()
s.headers["X-CSRFToken"] = csrf.json()["result"]


def post(path, payload):
    r = s.post(f"{BASE}{path}", json=payload)
    if not r.ok:
        print("FAILED", path, r.status_code, r.text[:2000])
        sys.exit(1)
    return r.json()


def put(path, payload):
    r = s.put(f"{BASE}{path}", json=payload)
    if not r.ok:
        print("FAILED", path, r.status_code, r.text[:2000])
        sys.exit(1)
    return r.json()


def find_one(path, column, value):
    filters = _json.dumps({"filters": [{"col": column, "opr": "eq", "value": value}]})
    r = s.get(f"{BASE}{path}", params={"q": filters})
    r.raise_for_status()
    result = r.json()["result"]
    return result[0] if result else None


# 1. Database connection
db = find_one("/api/v1/database/", "database_name", "Hive (hiveserver2)")
if db is None:
    db = post("/api/v1/database/", {
        "database_name": "Hive (hiveserver2)",
        "sqlalchemy_uri": "hive://root@hiveserver2:10000/default",
    })
db_id = db["id"]
print("database id", db_id)

# 2. Dataset over the `people` table
ds = find_one("/api/v1/dataset/", "table_name", "people")
if ds is None:
    ds = post("/api/v1/dataset/", {
        "database": db_id,
        "schema": "default",
        "table_name": "people",
    })
ds_id = ds["id"]
print("dataset id", ds_id)

# 3. Charts


def qc(queries):
    return _json.dumps({
        "datasource": {"id": ds_id, "type": "table"},
        "force": False,
        "queries": queries,
        "result_format": "json",
        "result_type": "full",
    })


CHART_SPECS = {
    "total": {
        "slice_name": "Total People",
        "viz_type": "big_number_total",
        "params": '{"metric":{"expressionType":"SQL","sqlExpression":"COUNT(*)","label":"Total People"},"adhoc_filters":[],"header_font_size":0.4,"subheader_font_size":0.15}',
        "query_context": qc([{"metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "Total People"}], "row_limit": 1}]),
    },
    "avg_age": {
        "slice_name": "Average Age",
        "viz_type": "big_number_total",
        "params": '{"metric":{"expressionType":"SQL","sqlExpression":"AVG(age)","label":"Average Age"},"adhoc_filters":[],"header_font_size":0.4,"subheader_font_size":0.15}',
        "query_context": qc([{"metrics": [{"expressionType": "SQL", "sqlExpression": "AVG(age)", "label": "Average Age"}], "row_limit": 1}]),
    },
    "dept": {
        "slice_name": "Average Age by Department",
        "viz_type": "echarts_timeseries_bar",
        "params": (
            '{"metrics":[{"expressionType":"SQL","sqlExpression":"AVG(age)","label":"Average Age"}],'
            '"groupby":["department"],"adhoc_filters":[],"row_limit":100,'
            '"x_axis":"department","orientation":"vertical"}'
        ),
        "query_context": qc([{"metrics": [{"expressionType": "SQL", "sqlExpression": "AVG(age)", "label": "Average Age"}], "groupby": ["department"], "row_limit": 100}]),
    },
    "city": {
        "slice_name": "People Count by City",
        "viz_type": "echarts_timeseries_bar",
        "params": (
            '{"metrics":[{"expressionType":"SQL","sqlExpression":"COUNT(*)","label":"People Count"}],'
            '"groupby":["city"],"adhoc_filters":[],"row_limit":100,'
            '"x_axis":"city","orientation":"vertical"}'
        ),
        "query_context": qc([{"metrics": [{"expressionType": "SQL", "sqlExpression": "COUNT(*)", "label": "People Count"}], "groupby": ["city"], "row_limit": 100}]),
    },
    "table": {
        "slice_name": "People (raw)",
        "viz_type": "table",
        "params": '{"query_mode":"raw","columns":["name","age","department","city"],"adhoc_filters":[],"row_limit":100}',
        "query_context": qc([{"columns": ["name", "age", "department", "city"], "row_limit": 100}]),
    },
}

chart_ids = {}
for key, spec in CHART_SPECS.items():
    chart = find_one("/api/v1/chart/", "slice_name", spec["slice_name"])
    payload = {
        "slice_name": spec["slice_name"],
        "viz_type": spec["viz_type"],
        "datasource_id": ds_id,
        "datasource_type": "table",
        "params": spec["params"],
        "query_context": spec["query_context"],
        "query_context_generation": False,
    }
    if chart is None:
        chart = post("/api/v1/chart/", payload)
    else:
        put(f"/api/v1/chart/{chart['id']}", payload)
    chart_ids[key] = chart["id"]
print("chart ids", chart_ids)

# Fetch each chart's real uuid -- the dashboard layout format needs it
# alongside chartId/sliceName, or the frontend can't resolve the tile.
chart_uuid_map = {}
for key, cid in chart_ids.items():
    r = s.get(f"{BASE}/api/v1/chart/{cid}")
    r.raise_for_status()
    chart_uuid_map[key] = r.json()["result"].get("uuid") or r.json()["id"]

# 4. Dashboard, with a grid layout. Each CHART node needs chartId, uuid, and
# sliceName in its meta -- a layout with only chartId is what silently
# produced "no chart definition associated with this component" plus a
# duplicated auto-repaired row the one time this was gotten wrong.
LAYOUT_SPEC = [
    ("ROW-1", [("total", 3, 25), ("avg_age", 3, 25)]),
    ("ROW-2", [("dept", 6, 50), ("city", 6, 50)]),
    ("ROW-3", [("table", 12, 50)]),
]

layout = {
    "DASHBOARD_VERSION_KEY": "v2",
    "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
    "GRID_ID": {
        "type": "GRID", "id": "GRID_ID",
        "children": [row_id for row_id, _ in LAYOUT_SPEC],
        "parents": ["ROOT_ID"],
    },
}
for row_id, charts_in_row in LAYOUT_SPEC:
    chart_node_ids = [f"CHART-{key}" for key, _, _ in charts_in_row]
    layout[row_id] = {
        "type": "ROW", "id": row_id,
        "children": chart_node_ids,
        "meta": {"background": "BACKGROUND_TRANSPARENT"},
        "parents": ["ROOT_ID", "GRID_ID"],
    }
    for key, width, height in charts_in_row:
        layout[f"CHART-{key}"] = {
            "type": "CHART", "id": f"CHART-{key}",
            "children": [],
            "meta": {
                "chartId": chart_ids[key],
                "uuid": chart_uuid_map[key],
                "sliceName": CHART_SPECS[key]["slice_name"],
                "width": width,
                "height": height,
            },
            "parents": ["ROOT_ID", "GRID_ID", row_id],
        }

dash = find_one("/api/v1/dashboard/", "slug", "hive-on-tez-people")
if dash is None:
    dash = post("/api/v1/dashboard/", {
        "dashboard_title": "Hive-on-Tez: People",
        "slug": "hive-on-tez-people",
        "position_json": _json.dumps(layout),
    })
else:
    put(f"/api/v1/dashboard/{dash['id']}", {
        "position_json": _json.dumps(layout),
    })
print("dashboard id", dash["id"])

# position_json alone only sets the visual layout -- Superset's frontend
# renders "no chart definition associated with this component" unless each
# chart is also explicitly linked to the dashboard via this reverse (chart
# -> dashboards) association field.
for chart_id in chart_ids.values():
    put(f"/api/v1/chart/{chart_id}", {"dashboards": [dash["id"]]})

print("DONE")
