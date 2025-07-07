// main.js — full mapping logic with embedded CSV

// Sector colors
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

const csvPath = "/static/data/OECD_Project_Data_Final(6.1).csv";
fetch(csvPath)
  .then(res => res.text())
  .then(csvText => {
    Papa.parse(csvText, {
      header: true,
      dynamicTyping: true,
      complete: (results) => {
        const geojson = {
          type: "FeatureCollection",
          features: results.data
            .filter(d => d.Latitude && d.Longitude)
            .map(d => ({
              type: "Feature",
              geometry: {
                type: "Point",
                coordinates: [+d.Longitude, +d.Latitude]
              },
              properties: {
                DonorName: d.DonorName,
                ProjectTitle: d.ProjectTitle,
                Year: d.Year,
                Province: d.Province,
                Sector: d.BroadSector
              }
            }))
        };

        initMap(geojson);
      }
    });
  });

function initMap(data) {
  // Initialize Map
  mapboxgl.accessToken = "pk.eyJ1IjoibWF5dW15Y29yZG92YTI0IiwiYSI6ImNtYzZwd2Z3OTE1Y3YybHEweWY3dnVnODcifQ.xSw3NyZ_4T-kdFhw5PYGmg";
  const map = new mapboxgl.Map({
    container: "map",
    center: [44.3661, 33.3152],
    zoom: 5.3,
    minZoom: 1.7,
    maxZoom: 15,
    style: "mapbox://styles/mapbox/streets-v11",
    cooperativeGestures: true
  });

  const originalCenter = [44.3661, 33.3152];
  const originalZoom = 5.3;

  const popup = new mapboxgl.Popup({ closeButton: false, closeOnClick: false });
  const filterGroup = document.getElementById("filter-group");
  const toggleButton = document.getElementById("toggle-filters");
  const resetButton = document.getElementById("reset-view");

  toggleButton.addEventListener("click", () => {
    const isVisible = filterGroup.style.display === "block";
    filterGroup.style.display = isVisible ? "none" : "block";
  });

  resetButton.addEventListener("click", () => {
    map.flyTo({ center: originalCenter, zoom: originalZoom });
  });

  map.on("load", () => {
    map.addSource("points", {
      type: "geojson",
      data: data
    });

    // Create one layer per sector
    const sectorsSeen = new Set();

    for (const feature of data.features) {
      const sector = feature.properties.Sector;
      if (!sector) continue;
      const layerID = `layer-${sector}`;

      if (sectorsSeen.has(sector)) continue;
      sectorsSeen.add(sector);

      map.addLayer({
        id: layerID,
        type: "circle",
        source: "points",
        filter: ["==", ["get", "Sector"], sector],
        paint: {
          "circle-color": sectorColors[sector] || "#ccc",
          "circle-radius": 8,
          "circle-stroke-width": 2,
          "circle-stroke-color": "#ffffff"
        }
      });

      // UI checkbox
      const input = document.createElement("input");
      input.type = "checkbox";
      input.id = layerID;
      input.checked = true;
      filterGroup.appendChild(input);

      const label = document.createElement("label");
      label.setAttribute("for", layerID);
      label.innerHTML = `
        <span style="
          display:inline-block;
          width:12px;
          height:12px;
          border-radius:50%;
          background-color:${sectorColors[sector] || "#ccc"};
          margin-right:8px;
          vertical-align:middle;
        "></span>${sector}
      `;
      filterGroup.appendChild(label);

      input.addEventListener("change", e => {
        map.setLayoutProperty(
          layerID,
          "visibility",
          e.target.checked ? "visible" : "none"
        );
      });

      // Add interactivity
      map.on("mouseenter", layerID, e => {
        const feature = e.features && e.features[0];
        if (!feature) return;
        map.getCanvas().style.cursor = "pointer";

        const { ProjectTitle, Year, Province, DonorName, Sector } = feature.properties;
        const coords = feature.geometry.coordinates.slice();

        popup.setLngLat(coords)
          .setHTML(`
            <strong>Project Title:</strong> ${ProjectTitle}<br>
            <strong>Year:</strong> ${Year}<br>
            <strong>Province:</strong> ${Province}<br>
            <strong>Donor:</strong> ${DonorName}<br>
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
    }
  });
}
