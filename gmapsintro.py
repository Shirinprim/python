import numpy as np
import folium
from folium.plugins import HeatMap
import webbrowser

data = (
    np.random.normal(size=(100, 3)) * np.array([[1, 1, 1]])
    + np.array([[28.644800, 77.216721, 1]])
).tolist()

m = folium.Map(location=[28.644800, 77.216721], zoom_start=12, tiles=None)

# Reliable tiles
folium.TileLayer("OpenStreetMap", name="OSM").add_to(m)
folium.TileLayer("CartoDB Positron", name="Carto Light").add_to(m)
folium.TileLayer("CartoDB Dark_Matter", name="Carto Dark").add_to(m)

folium.Marker([28.695800, 77.244721], popup="Marker1").add_to(m)
folium.Marker([28.645800, 77.214721], popup="Marker2").add_to(m)
folium.Marker([28.655800, 77.274721], popup="Marker3").add_to(m)

HeatMap(data, name="Heatmap").add_to(m)

folium.LayerControl(collapsed=False).add_to(m)
m.save("map1.html")
webbrowser.open("map1.html")
