let map;

const sectorColors = {
  "Public Administration": "#120078",
  "Transportation": "#FECD1A",
  "Water": "#f032e6",
  "Education": "#e6194B",
  "Energy": "#3cb44b",
  "Health": "#ffe119",
  "Industry": "#4363d8",
  "IT": "#f58231",
  "Infrastructure": "#911eb4",
  "Food": "#bcf60c"
};

document.addEventListener("DOMContentLoaded", () => {
  initMap();
  loadProjects();
});

function initMap() {
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

  document.getElementById("reset-view").addEventListener("click", () => {
    map.flyTo({ center: [44.3661, 33.3152], zoom: 5.3 });
  });

  document.getElementById("toggle-filters").addEventListener("click", () => {
    const fg = document.getElementById("filter-group");
    fg.style.display = fg.style.display === "block" ? "none" : "block";
  });
}

function loadProjects() {
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
      renderProjects(data);
      renderMapPoints(data);
    })
    .catch(err => console.error("Error loading project data:", err));
}

function renderProjects(data) {
  const container = document.getElementById("projectListGroup");
  container.innerHTML = "";
  data.forEach((proj, idx) => {
    const item = document.createElement("div");
    item.className = "list-group-item list-group-item-action mb-3 border rounded";
    item.innerHTML = `
      <div class="d-flex justify-content-between">
        <div><strong>#${idx + 1} ${proj.Project_Title}</strong></div>
        <div class="badge bg-success text-white">Score: ${proj.Score.toFixed(3)}</div>
      </div>
      <div><strong>Sector:</strong> ${proj.Sector} | <strong>Province:</strong> ${proj.Province}</div>
      <div><strong>Coords:</strong> (${proj.Latitude}, ${proj.Longitude})</div>
      <div class="mt-2"><strong>Description:</strong>
        <div class="bg-light p-2 rounded mt-1" style="max-height: 100px; overflow-y: auto;">${proj.Project_Description}</div>
      </div>
    `;
    container.appendChild(item);
  });
}

function renderMapPoints(data) {
  const geojson = {
    type: "FeatureCollection",
    features: data
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
          Sector: d.Sector
        }
      }))
  };

  map.on("load", () => {
    map.addSource("points", { type: "geojson", data: geojson });

    const popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false });
    const filterGroup = document.getElementById("filter-group");
    const seen = new Set();

    geojson.features.forEach((f) => {
      const sector = f.properties.Sector;
      if (!sector || seen.has(sector)) return;
      seen.add(sector);
      const layerID = `layer-${sector}`;

      map.addLayer({
        id: layerID,
        type: "circle",
        source: "points",
        filter: ["==", ["get", "Sector"], sector],
        paint: {
          "circle-color": sectorColors[sector] || "#ccc",
          "circle-radius": 8,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#fff"
        }
      });

      const input = document.createElement("input");
      input.type = "checkbox";
      input.id = layerID;
      input.checked = true;
      filterGroup.appendChild(input);

      const label = document.createElement("label");
      label.setAttribute("for", layerID);
      label.innerHTML = `
        <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background-color:${sectorColors[sector] || "#ccc"};margin-right:8px;"></span>
        ${sector}
      `;
      filterGroup.appendChild(label);

      input.addEventListener("change", e => {
        map.setLayoutProperty(layerID, "visibility", e.target.checked ? "visible" : "none");
      });

      map.on("mouseenter", layerID, e => {
        const feat = e.features && e.features[0];
        if (!feat) return;
        map.getCanvas().style.cursor = "pointer";
        const { ProjectTitle, Province, Sector } = feat.properties;
        popup.setLngLat(feat.geometry.coordinates)
          .setHTML(`
            <strong>Project Title:</strong> ${ProjectTitle}<br>
            <strong>Province:</strong> ${Province}<br>
            <strong>Sector:</strong> ${Sector}
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
