document.addEventListener('DOMContentLoaded', function() {
    const mapElement = document.getElementById('map');
    if (!mapElement) return;

    const map = L.map('map').setView([40.4168, -3.7038], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const yacimientosData = mapElement.getAttribute('data-yacimientos');
    if (!yacimientosData) return;

    let yacimientos;
    try {
        yacimientos = JSON.parse(yacimientosData);
    } catch (e) {
        console.error('Error al parsear datos de yacimientos:', e);
        return;
    }

    if (yacimientos && yacimientos.length > 0) {
        const markers = [];

        yacimientos.forEach(function(yacimiento) {
            if (yacimiento.lat && yacimiento.lng) {
                const icon = L.divIcon({
                    className: 'custom-marker',
                    html: '<div style="background: #a0826d; width: 30px; height: 30px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);"></div>',
                    iconSize: [30, 30],
                    iconAnchor: [15, 15]
                });

                const marker = L.marker([yacimiento.lat, yacimiento.lng], { icon: icon }).addTo(map);

                const popupContent = `
                    <div style="min-width: 200px;">
                        <strong style="font-size: 1.1rem; color: #a0826d;">${yacimiento.nombre}</strong><br>
                        <span style="color: #5d4037;">${yacimiento.ubicacion || 'Sin ubicación'}</span><br>
                        <a href="/yacimiento/${yacimiento.id}" style="color: #6366F1; text-decoration: none; font-weight: 600; margin-top: 0.5rem; display: inline-block;">Ver detalles</a>
                    </div>
                `;

                marker.bindPopup(popupContent);
                markers.push(marker);
            }
        });

        if (markers.length > 0) {
            const group = new L.featureGroup(markers);
            map.fitBounds(group.getBounds().pad(0.1));
        }
    }
});

function initFormMap(lat = 40.4168, lng = -3.7038) {
    const mapElement = document.getElementById('form-map');
    if (!mapElement) return;

    const map = L.map('form-map').setView([lat, lng], 6);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const marker = L.marker([lat, lng], {
        draggable: true,
        icon: L.divIcon({
            className: 'custom-marker',
            html: '<div style="background: #6366F1; width: 35px; height: 35px; border-radius: 50%; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; color: white; font-weight: bold;">📍</div>',
            iconSize: [35, 35],
            iconAnchor: [17.5, 17.5]
        })
    }).addTo(map);

    const latInput = document.getElementById('lat');
    const lngInput = document.getElementById('lng');

    if (latInput && lngInput) {
        latInput.value = lat.toFixed(6);
        lngInput.value = lng.toFixed(6);
        updateCoordinatesDisplay(lat, lng);
    }

    marker.on('dragend', function(e) {
        const position = marker.getLatLng();
        if (latInput && lngInput) {
            latInput.value = position.lat.toFixed(6);
            lngInput.value = position.lng.toFixed(6);
            updateCoordinatesDisplay(position.lat, position.lng);
        }
    });

    map.on('click', function(e) {
        marker.setLatLng(e.latlng);
        if (latInput && lngInput) {
            latInput.value = e.latlng.lat.toFixed(6);
            lngInput.value = e.latlng.lng.toFixed(6);
            updateCoordinatesDisplay(e.latlng.lat, e.latlng.lng);
        }
    });

    return map;
}

function updateCoordinatesDisplay(lat, lng) {
    const display = document.getElementById('coords-display');
    if (display) {
        display.textContent = `Coordenadas: ${lat.toFixed(6)}, ${lng.toFixed(6)}`;
    }
}

function initSectoresMap(yacimiento, sectores, hallazgos) {
    const mapElement = document.getElementById('sectores-map');
    if (!mapElement) return;

    const centerLat = yacimiento.lat || 40.4168;
    const centerLng = yacimiento.lng || -3.7038;

    const map = L.map('sectores-map').setView([centerLat, centerLng], 15);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
        maxZoom: 19
    }).addTo(map);

    const allLayers = [];

    if (yacimiento.lat && yacimiento.lng) {
        const yacMarker = L.marker([yacimiento.lat, yacimiento.lng], {
            icon: L.divIcon({
                className: 'yacimiento-marker',
                html: '<div style="background: #a0826d; width: 40px; height: 40px; border-radius: 50%; border: 4px solid white; box-shadow: 0 3px 10px rgba(0,0,0,0.3); display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">🏛️</div>',
                iconSize: [40, 40],
                iconAnchor: [20, 20]
            })
        }).addTo(map);

        yacMarker.bindPopup(`<strong>${yacimiento.nombre}</strong>`);
        allLayers.push(yacMarker);

        if (yacimiento.polygon_geojson) {
            try {
                let geojsonData = yacimiento.polygon_geojson;
                if (typeof geojsonData === 'string') {
                    geojsonData = JSON.parse(geojsonData);
                }

                const yacPolygon = L.geoJSON(geojsonData, {
                    style: {
                        color: '#8b6f47',
                        fillColor: '#a0826d',
                        fillOpacity: 0.15,
                        weight: 3,
                        dashArray: '10, 5'
                    }
                }).addTo(map);

                yacPolygon.bindPopup(`<strong>${yacimiento.nombre}</strong><br>Perímetro del yacimiento`);
                allLayers.push(yacPolygon);
            } catch (e) {
                console.error('Error al cargar polígono del yacimiento:', e);
            }
        }
    }

    if (sectores && sectores.length > 0) {
        sectores.forEach(sector => {
            if (sector.lat && sector.lng) {
                let sectorLayer;

                if (sector.polygon_geojson) {
                    try {
                        let geojsonData = sector.polygon_geojson;
                        if (typeof geojsonData === 'string') {
                            geojsonData = JSON.parse(geojsonData);
                        }

                        sectorLayer = L.geoJSON(geojsonData, {
                            style: {
                                color: sector.color || '#6366F1',
                                fillColor: sector.color || '#6366F1',
                                fillOpacity: 0.3,
                                weight: 2
                            }
                        }).addTo(map);

                        allLayers.push(sectorLayer);
                    } catch (e) {
                        console.error('Error al cargar polígono del sector:', e);
                       
                        sectorLayer = createSectorCircle(sector, map);
                        allLayers.push(sectorLayer);
                    }
                } else {
                    
                    sectorLayer = createSectorCircle(sector, map);
                    allLayers.push(sectorLayer);
                }

                // Popup para el sector
                const popupContent = `
                    <div style="min-width: 150px;">
                        <strong style="color: ${sector.color};">${sector.nombre}</strong><br>
                        <span style="font-size: 0.9rem;">Área: ${sector.area ? sector.area.toFixed(2) : 'N/A'} m²</span><br>
                        <span style="font-size: 0.9rem;">Hallazgos: ${sector.hallazgos_count || 0}</span><br>
                        <a href="/sector/${sector.id}" style="color: #6366F1; text-decoration: none;">Ver detalles →</a>
                    </div>
                `;

                if (sectorLayer) {
                    sectorLayer.bindPopup(popupContent);
                }

                // Etiqueta del sector
                const centerPoint = sector.polygon_geojson 
                    ? getCentroidFromGeojson(sector.polygon_geojson)
                    : [sector.lat, sector.lng];

                L.marker(centerPoint, {
                    icon: L.divIcon({
                        className: 'sector-label',
                        html: `<div style="background: rgba(255,255,255,0.9); padding: 4px 8px; border-radius: 4px; font-weight: bold; color: ${sector.color}; box-shadow: 0 2px 4px rgba(0,0,0,0.2); white-space: nowrap;">${sector.nombre}</div>`,
                        iconSize: null
                    }),
                    interactive: false
                }).addTo(map);
            }
        });
    }

    // Dibujar hallazgos
    if (hallazgos && hallazgos.length > 0) {
        hallazgos.forEach(hallazgo => {
            if (hallazgo.lat && hallazgo.lng) {
                const sector = sectores.find(s => s.id === hallazgo.sector_id);
                const markerColor = sector ? sector.color : '#f59e0b';

                const hallazgoMarker = L.marker([hallazgo.lat, hallazgo.lng], {
                    icon: L.divIcon({
                        className: 'hallazgo-marker',
                        html: `<div style="background: ${markerColor}; width: 20px; height: 20px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
                        iconSize: [20, 20],
                        iconAnchor: [10, 10]
                    })
                }).addTo(map);

                const popupContent = `
                    <div style="min-width: 150px;">
                        <strong>🏺 ${hallazgo.tipo}</strong><br>
                        <span style="font-family: monospace; color: #6366F1;">${hallazgo.codigo}</span><br>
                        <a href="/hallazgo/${hallazgo.id}" style="color: #6366F1; text-decoration: none;">Ver detalles →</a>
                    </div>
                `;

                hallazgoMarker.bindPopup(popupContent);
                allLayers.push(hallazgoMarker);
            }
        });
    }

    // Ajustar vista para mostrar todos los elementos
    if (allLayers.length > 0) {
        const group = new L.featureGroup(allLayers);
        map.fitBounds(group.getBounds().pad(0.1));
    }

    return map;
}

// Función auxiliar para crear círculo de sector
function createSectorCircle(sector, map) {
    const radius = Math.sqrt(sector.area || 100) * 5; // Radio más pequeño
    return L.circle([sector.lat, sector.lng], {
        color: sector.color || '#6366F1',
        fillColor: sector.color || '#6366F1',
        fillOpacity: 0.3,
        radius: radius,
        weight: 2
    }).addTo(map);
}

// Función auxiliar para obtener centroide de un GeoJSON
function getCentroidFromGeojson(geojsonData) {
    try {
        if (typeof geojsonData === 'string') {
            geojsonData = JSON.parse(geojsonData);
        }

        if (typeof turf !== 'undefined') {
            const centroid = turf.centroid(geojsonData);
            return [centroid.geometry.coordinates[1], centroid.geometry.coordinates[0]];
        }

        // Fallback: calcular centroide simple
        const coords = geojsonData.type === 'Polygon' 
            ? geojsonData.coordinates[0]
            : geojsonData.geometry.coordinates[0];

        let latSum = 0, lngSum = 0;
        coords.forEach(coord => {
            lngSum += coord[0];
            latSum += coord[1];
        });

        return [latSum / coords.length, lngSum / coords.length];
    } catch (e) {
        console.error('Error calculando centroide:', e);
        return null;
    }
}

// Exportar funciones
window.initFormMap = initFormMap;
window.initSectoresMap = initSectoresMap;