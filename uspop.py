import json
import pandas as pd
import folium
from folium.plugins import HeatMap
import webbrowser

EXCEL_PATH = "uscitiesfull.xlsx"
OUT_HTML = "us_heat_markers.html"

# Optional (only if you want the choropleth layer too)
GEOJSON_PATH = "gz_2010_us_040_00_500k.json"
ADD_CHOROPLETH = True  # set False if you don't care about choropleth


def fmt_int(x):
    try:
        return f"{int(x):,}"
    except Exception:
        return str(x)


# ---- Load + clean ----
df = pd.read_excel(EXCEL_PATH)

# Force correct dtypes (this is where "population missing" usually comes from)
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
df["population"] = pd.to_numeric(df["population"], errors="coerce")

# Keep only valid rows
df = df.dropna(subset=["state_name", "lat", "lng", "population"])
df = df[df["population"] > 0]

# ---- Aggregate by state for markers ----
state_df = (
    df.groupby("state_name", as_index=False)
      .agg(lat=("lat", "mean"), lng=("lng", "mean"), population=("population", "sum"))
)

# ---- Build ONE map ----
m = folium.Map(location=[43, -100], zoom_start=5, tiles="CartoDB Positron", control_scale=True)

# ---- Heatmap (city-level, weighted by population) ----
# HeatMap expects rows as [lat, lon, weight]
heat_points = df[["lat", "lng", "population"]].values.tolist()
HeatMap(
    heat_points,
    name="Heatmap (city population-weighted)",
    radius=8,
    blur=12,
    min_opacity=0.2,
).add_to(m)

# ---- Markers (state-level) with hover + popup ----
markers_fg = folium.FeatureGroup(name="State markers", show=True).add_to(m)

for _, r in state_df.iterrows():
    state = r["state_name"]
    pop = r["population"]
    lat = float(r["lat"])
    lng = float(r["lng"])

    tooltip_html = f"{state} • {fmt_int(pop)}"
    popup_html = f"<b>{state}</b><br>Population (sum of cities): {fmt_int(pop)}"

    folium.CircleMarker(
        location=[lat, lng],
        radius=6,
        weight=2,
        fill=True,
        fill_opacity=0.7,
        tooltip=tooltip_html,                 # hover
        popup=folium.Popup(popup_html, max_width=300),  # click
    ).add_to(markers_fg)

# ---- Optional Choropleth layer (states polygons) ----
if ADD_CHOROPLETH:
    with open(GEOJSON_PATH, "r", encoding="utf-8") as f:
        states_gj = json.load(f)

    # Auto-detect the right state-name property in your GeoJSON
    props_keys = states_gj["features"][0]["properties"].keys()
    # Common ones for this file family:
    for candidate in ["NAME", "NAME10", "STATE_NAME", "NAME_LONG"]:
        if candidate in props_keys:
            GEO_NAME_KEY = candidate
            break
    else:
        # If nothing matches, print keys and skip choropleth
        print("Could not find a state-name key in GeoJSON. Keys example:", list(props_keys))
        GEO_NAME_KEY = None

    if GEO_NAME_KEY:
        folium.Choropleth(
            geo_data=states_gj,
            data=state_df,
            columns=["state_name", "population"],
            key_on=f"feature.properties.{GEO_NAME_KEY}",
            name="Choropleth (state totals)",
            fill_opacity=0.35,
            line_opacity=0.3,
            legend_name="Population (sum of cities in Excel)",
        ).add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.save(OUT_HTML)
print("Saved ->", OUT_HTML)
webbrowser.open(OUT_HTML)
