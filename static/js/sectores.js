function initAdvancedSectoresMap(yacimiento, sectores, hallazgos) {
  const mapElement = document.getElementById('sectores-map');
  if (!mapElement) return;

  const centerLat = yacimiento.lat || 40.4168;
  const centerLng = yacimiento.lng || -3.7038;

  const map = L.map('sectores-map').setView([centerLat, centerLng], 16);

  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
      maxZoom: 19
  }).addTo(map);
  if (yacimiento.lat && yacimiento.lng) {
      const yacIcon = L.divIcon({
          className: 'yacimiento-marker',
          html: `<div style="background: #a0826d; width: 40px; height: 40px; border-radius: 50%; border: 4px solid white; box-shadow: 0 3px 10px rgba(0,0,0,0.4); display: flex; align-items: center; justify-content: center; font-size: 1.5rem;">🏛️</div>`,
          iconSize: [40, 40],
          iconAnchor: [20, 20]
      });

      L.marker([yacimiento.lat, yacimiento.lng], { icon: yacIcon })
          .addTo(map)
          .bindPopup(`<strong>${yacimiento.nombre}</strong>`);
  }
  if (sectores && sectores.length > 0) {
      sectores.forEach(sector => {
          if (sector.lat && sector.lng) {
              const radius = Math.sqrt(sector.area || 100) * 5;
              const circle = L.circle([sector.lat, sector.lng], {
                  color: sector.color || '#6366F1',
                  fillColor: sector.color || '#6366F1',
                  fillOpacity: 0.3,
                  radius: radius,
                  weight: 3
              }).addTo(map);

              const popupContent = `
                  <div style="min-width: 180px;">
                      <strong style="color: ${sector.color}; font-size: 1.1rem;">${sector.nombre}</strong><br>
                      <span style="font-size: 0.9rem;">Área: ${sector.area || 'N/A'} m²</span><br>
                      <span style="font-size: 0.9rem;">Hallazgos: ${sector.hallazgos_count || 0}</span><br>
                      <a href="/sector/${sector.id}" style="color: #6366F1; text-decoration: none; font-weight: 600; margin-top: 0.5rem; display: inline-block;">Ver detalles →</a>
                  </div>
              `;

              circle.bindPopup(popupContent);
              const label = L.marker([sector.lat, sector.lng], {
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
  if (hallazgos && hallazgos.length > 0) {
      const hallazgoGroup = L.markerClusterGroup({
          maxClusterRadius: 50,
          iconCreateFunction: function(cluster) {
              const count = cluster.getChildCount();
              return L.divIcon({
                  html: `<div style="background: #f59e0b; color: white; border-radius: 50%; width: 35px; height: 35px; display: flex; align-items: center; justify-content: center; font-weight: bold; border: 3px solid white; box-shadow: 0 2px 8px rgba(0,0,0,0.3);">${count}</div>`,
                  className: 'marker-cluster',
                  iconSize: [35, 35]
              });
          }
      });

      hallazgos.forEach(hallazgo => {
          if (hallazgo.lat && hallazgo.lng) {
              const sector = sectores.find(s => s.id === hallazgo.sector_id);
              const markerColor = sector ? sector.color : '#f59e0b';

              const marker = L.marker([hallazgo.lat, hallazgo.lng], {
                  icon: L.divIcon({
                      className: 'hallazgo-marker',
                      html: `<div style="background: ${markerColor}; width: 22px; height: 22px; border-radius: 50%; border: 2px solid white; box-shadow: 0 2px 5px rgba(0,0,0,0.3);"></div>`,
                      iconSize: [22, 22],
                      iconAnchor: [11, 11]
                  })
              });

              const popupContent = `
                  <div style="min-width: 150px;">
                      <strong>🏺 ${hallazgo.tipo}</strong><br>
                      <span style="font-family: monospace; color: #6366F1; font-size: 0.9rem;">${hallazgo.codigo}</span><br>
                      ${sector ? `<span style="font-size: 0.85rem;">📐 ${sector.nombre}</span><br>` : ''}
                      <a href="/hallazgo/${hallazgo.id}" style="color: #6366F1; text-decoration: none; font-weight: 600;">Ver detalles →</a>
                  </div>
              `;

              marker.bindPopup(popupContent);
              hallazgoGroup.addLayer(marker);
          }
      });

      map.addLayer(hallazgoGroup);
  }

  return map;
}
document.addEventListener('DOMContentLoaded', function() {
  const colorInput = document.getElementById('color');

  if (colorInput) {
      const colorPresets = [
          '#6366F1', '#8B5CF6', '#EC4899', '#F59E0B',
          '#10B981', '#3B82F6', '#EF4444', '#14B8A6',
          '#F97316', '#8B5A3C', '#6B7280', '#84CC16'
      ];

      const presetContainer = document.createElement('div');
      presetContainer.style.cssText = 'display: flex; gap: 0.5rem; flex-wrap: wrap; margin-top: 0.5rem;';

      colorPresets.forEach(color => {
          const colorBtn = document.createElement('button');
          colorBtn.type = 'button';
          colorBtn.style.cssText = `
              width: 35px;
              height: 35px;
              border-radius: 50%;
              border: 3px solid ${color === colorInput.value ? '#000' : '#ddd'};
              background: ${color};
              cursor: pointer;
              transition: all 0.2s;
              box-shadow: 0 2px 4px rgba(0,0,0,0.2);
          `;

          colorBtn.addEventListener('click', function() {
              colorInput.value = color;
              document.querySelectorAll('.color-preset-btn').forEach(btn => {
                  btn.style.borderColor = '#ddd';
              });
              this.style.borderColor = '#000';
              updateColorPreview(color);
          });

          colorBtn.classList.add('color-preset-btn');
          presetContainer.appendChild(colorBtn);
      });

      colorInput.parentElement.appendChild(presetContainer);
      const preview = document.createElement('div');
      preview.id = 'color-preview';
      preview.style.cssText = `
          margin-top: 1rem;
          padding: 1rem;
          background: ${colorInput.value || '#6366F1'};
          border-radius: var(--border-radius);
          color: white;
          text-align: center;
          font-weight: bold;
          box-shadow: var(--shadow);
      `;
      preview.textContent = 'Vista previa del color del sector';
      colorInput.parentElement.appendChild(preview);
      colorInput.addEventListener('change', function() {
          updateColorPreview(this.value);
      });
  }
});

function updateColorPreview(color) {
  const preview = document.getElementById('color-preview');
  if (preview) {
      preview.style.background = color;
  }
}

document.addEventListener('DOMContentLoaded', function() {
  const areaInput = document.getElementById('area');

  if (areaInput) {
      const calcTool = document.createElement('div');
      calcTool.style.cssText = 'margin-top: 0.5rem; padding: 1rem; background: var(--light-gray); border-radius: var(--border-radius); border-left: 3px solid var(--info-color);';
      calcTool.innerHTML = `
          <strong style="color: var(--info-color);">Calculadora de Área</strong>
          <div style="display: grid; grid-template-columns: 1fr 1fr auto; gap: 0.5rem; margin-top: 0.5rem; align-items: end;">
              <div>
                  <label style="font-size: var(--font-sm);">Largo (m)</label>
                  <input type="number" id="calc-largo" step="0.1" class="form-control" style="padding: 0.5rem;">
              </div>
              <div>
                  <label style="font-size: var(--font-sm);">Ancho (m)</label>
                  <input type="number" id="calc-ancho" step="0.1" class="form-control" style="padding: 0.5rem;">
              </div>
              <button type="button" id="btn-calcular-area" class="btn btn-info" style="padding: 0.5rem 1rem; white-space: nowrap;">
                  = Calcular
              </button>
          </div>
          <p id="resultado-calculo" style="margin-top: 0.5rem; color: var(--primary-color); font-weight: 600;"></p>
      `;

      areaInput.parentElement.appendChild(calcTool);
      document.getElementById('btn-calcular-area').addEventListener('click', function() {
          const largo = parseFloat(document.getElementById('calc-largo').value);
          const ancho = parseFloat(document.getElementById('calc-ancho').value);

          if (largo > 0 && ancho > 0) {
              const area = (largo * ancho).toFixed(2);
              areaInput.value = area;
              document.getElementById('resultado-calculo').textContent = `Área calculada: ${area} m²`;
              showAlert(`Área de ${area} m² calculada correctamente`, 'success');
          } else {
              showAlert('Introduce valores válidos para largo y ancho', 'warning');
          }
      });
  }
});

function mostrarEstadisticasSectores() {
  const sectores = document.querySelectorAll('.sector-card');
  if (sectores.length === 0) return;

  const stats = {
      total: sectores.length,
      conHallazgos: 0,
      areaTotal: 0,
      hallazgosTotales: 0
  };

  sectores.forEach(sector => {
      const hallazgosCount = parseInt(sector.dataset.hallazgos) || 0;
      const area = parseFloat(sector.dataset.area) || 0;

      if (hallazgosCount > 0) stats.conHallazgos++;
      stats.areaTotal += area;
      stats.hallazgosTotales += hallazgosCount;
  });

  const statsPanel = document.createElement('div');
  statsPanel.className = 'stats-grid';
  statsPanel.style.margin = '2rem 0';

  const statItems = [
      { value: stats.total, label: 'Total Sectores', style: '' },
      { value: stats.conHallazgos, label: 'Con Hallazgos', style: 'background: linear-gradient(135deg, var(--success-color), #059669);' },
      { value: stats.areaTotal.toFixed(0), label: 'Área Total (m²)', style: 'background: linear-gradient(135deg, var(--info-color), #2563eb);' },
      { value: stats.hallazgosTotales, label: 'Hallazgos Totales', style: 'background: linear-gradient(135deg, var(--warning-color), #f59e0b);' }
  ];

  statItems.forEach(item => {
      const card = document.createElement('div');
      card.className = 'stat-card';
      if (item.style) card.style.cssText = item.style;

      const h3 = document.createElement('h3');
      h3.textContent = item.value;
      card.appendChild(h3);

      const p = document.createElement('p');
      p.textContent = item.label;
      card.appendChild(p);

      statsPanel.appendChild(card);
  });

  const container = document.querySelector('.sectores-container');
  if (container) {
      container.parentNode.insertBefore(statsPanel, container);
  }
}
document.addEventListener('DOMContentLoaded', mostrarEstadisticasSectores);
window.initAdvancedSectoresMap = initAdvancedSectoresMap;
window.mostrarEstadisticasSectores = mostrarEstadisticasSectores;
window.updateColorPreview = updateColorPreview;