document.addEventListener('DOMContentLoaded', function() {
  const timelineItems = document.querySelectorAll('.timeline-item');
  const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
          if (entry.isIntersecting) {
              entry.target.style.opacity = '1';
              entry.target.style.transform = 'translateY(0)';
          }
      });
  }, { threshold: 0.1 });

  timelineItems.forEach(item => {
      item.style.opacity = '0';
      item.style.transform = 'translateY(20px)';
      item.style.transition = 'all 0.5s ease-out';
      observer.observe(item);
  });
});

function filtrarEventosPorTipo(tipo) {
  const eventos = document.querySelectorAll('.timeline-item');

  eventos.forEach(evento => {
      if (tipo === 'todos' || evento.dataset.tipo === tipo) {
          evento.style.display = '';
          evento.style.animation = 'fadeIn 0.3s ease-in';
      } else {
          evento.style.display = 'none';
      }
  });
}

document.addEventListener('DOMContentLoaded', function() {
  const filtrosContainer = document.querySelector('.timeline-filters');
  if (!filtrosContainer) return;

  const botonesFiltro = filtrosContainer.querySelectorAll('button');
  botonesFiltro.forEach(btn => {
      btn.addEventListener('click', function() {
          botonesFiltro.forEach(b => {
              b.classList.remove('btn-primary');
              b.classList.add('btn-secondary');
          });
          this.classList.remove('btn-secondary');
          this.classList.add('btn-primary');

          const tipo = this.dataset.tipo;
          filtrarEventosPorTipo(tipo);
      });
  });
});

window.filtrarEventosPorTipo = filtrarEventosPorTipo;