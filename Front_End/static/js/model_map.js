let map;

document.addEventListener("DOMContentLoaded", () => {
  fetchModelProjects();
});

function fetchModelProjects() {
  const payload = {
    title: sessionStorage.getItem("projectTitle"),
    province: sessionStorage.getItem("province"),
    description: sessionStorage.getItem("projectDescription"),
    radius: parseInt(sessionStorage.getItem("radius_test") || "50"),
    disable_radius: sessionStorage.getItem("disableRadius_test") === "true",
    num_projects: parseInt(sessionStorage.getItem("numProjects_test") || "5")
  };

  fetch("http://127.0.0.1:8000/get_projects", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload)
  })
    .then(res => res.json())
    .then(data => {
      if (Array.isArray(data)) {
        const queryPoint = {
          type: "Feature",
          geometry: {
            type: "Point",
            coordinates: [
              parseFloat(sessionStorage.getItem("longitude")),
              parseFloat(sessionStorage.getItem("latitude"))
            ]
          },
          properties: {
            ProjectTitle: payload.title,
            ProjectDescription: payload.description,
            Province: payload.province,
            Sector: "Your Query",
            Score: 1.0
          }
        };

        const geojson = {
          type: "FeatureCollection",
          features: [queryPoint, ...data
            .filter(d => d.Latitude && d.Longitude)
            .map(d => ({
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates: [+d.Longitude, +d.Latitude]
              },
              properties: {
                Score: d.Score,
                ProjectTitle: d.Project_Title,
                ProjectDescription: d.Project_Description,
                Province: d.Province,
                Sector: "Similar Project"
              }
            }))
          ]
        };

        initMap(geojson);
      } else {
        console.error("Invalid data returned:", data);
      }
    })
    .catch(err => console.error("Error fetching project data:", err));
}

function initMap(data) {
  mapboxgl.accessToken = "pk.eyJ1IjoibWF5dW15Y29yZG92YTI0IiwiYSI6ImNtYzZwd2Z3OTE1Y3YybHEweWY3dnVnODcifQ.xSw3NyZ_4T-kdFhw5PYGmg";
  map = new mapboxgl.Map({
    container: "map",
    center: [44.3661, 33.3152],
    zoom: 5.3,
    minZoom: 1.7,
    maxZoom: 15,
    style: "mapbox://styles/mapbox/streets-v11",
    cooperativeGestures: true
  });

  const popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false });

  document.getElementById("reset-view").addEventListener("click", () => {
    map.flyTo({ center: [44.3661, 33.3152], zoom: 5.3 });
  });

  document.getElementById("toggle-filters").addEventListener("click", () => {
    const fg = document.getElementById("filter-group");
    fg.style.display = fg.style.display === "block" ? "none" : "block";
  });

  map.on("load", () => {
    map.addSource("points", {
      type: "geojson",
      data: data
    });

    // Add Similar Project Layer (crimson red)
    map.addLayer({
      id: "similar-projects",
      type: "circle",
      source: "points",
      filter: ["==", ["get", "Sector"], "Similar Project"],
      paint: {
        "circle-color": "#DC143C", // crimson red
        "circle-radius": 8,
        "circle-stroke-width": 2,
        "circle-stroke-color": "#fff"
      }
    });

    // Add Query Project Layer (green and bigger)
    map.addLayer({
      id: "query-project",
      type: "circle",
      source: "points",
      filter: ["==", ["get", "Sector"], "Your Query"],
      paint: {
        "circle-color": "#00AA00", // green
        "circle-radius": 10,
        "circle-stroke-width": 3,
        "circle-stroke-color": "#fff"
      }
    });

    // Unified interactivity for both layers
    ["similar-projects", "query-project"].forEach(layerID => {
      map.on("mouseenter", layerID, e => {
        const feat = e.features?.[0];
        if (!feat) return;
        map.getCanvas().style.cursor = "pointer";
        const { ProjectTitle, Province, Sector, Score, ProjectDescription } = feat.properties;
        popup.setLngLat(feat.geometry.coordinates)
          .setHTML(`
            <strong>Project Title:</strong> ${ProjectTitle}<br>
            <strong>Province:</strong> ${Province}<br>
            <strong>Sector:</strong> ${Sector}<br>
            <strong>Score:</strong> ${Score.toFixed(3)}<br>
            <strong>Description:</strong><br>
            <div style="max-height:100px; overflow:auto;">${ProjectDescription}</div>
          `)
          .addTo(map);
      });

      map.on("mouseleave", layerID, () => {
        map.getCanvas().style.cursor = "";
        popup.remove();
      });

      map.on("click", layerID, e => {
        map.flyTo({
          center: e.features[0].geometry.coordinates,
          zoom: 12
        });
      });
    });
  });
}
