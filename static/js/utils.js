function getCsrfToken() {
  const meta = document.querySelector('meta[name="csrf-token"]');
  return meta ? meta.getAttribute('content') : '';
}

document.addEventListener('DOMContentLoaded', function() {
const alerts = document.querySelectorAll('.alert');

alerts.forEach(function(alert) {
    setTimeout(function() {
        alert.style.transition = 'opacity 0.3s ease-out';
        alert.style.opacity = '0';

        setTimeout(function() {
            alert.remove();
        }, 300);
    }, 5000);
});
});

function showAlert(message, type = 'info') {
const alertContainer = document.querySelector('.alert-container') || createAlertContainer();

const alert = document.createElement('div');
alert.className = `alert alert-${type}`;
alert.textContent = message;

alertContainer.appendChild(alert);
setTimeout(() => {
    alert.style.opacity = '0';
    setTimeout(() => alert.remove(), 300);
}, 5000);
}

function createAlertContainer() {
const container = document.createElement('div');
container.className = 'alert-container';
document.body.appendChild(container);
return container;
}

document.addEventListener('DOMContentLoaded', function() {
const mobileToggle = document.querySelector('.mobile-menu-toggle');
const navMenu = document.querySelector('.nav-menu');

if (mobileToggle && navMenu) {
    mobileToggle.addEventListener('click', function() {
        this.classList.toggle('active');
        navMenu.classList.toggle('active');
    });
    const navLinks = navMenu.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', () => {
            mobileToggle.classList.remove('active');
            navMenu.classList.remove('active');
        });
    });
}
});

document.addEventListener('DOMContentLoaded', function() {
const deleteForms = document.querySelectorAll('form[action*="eliminar"]');

deleteForms.forEach(form => {
    form.addEventListener('submit', function(e) {
        const confirmed = confirm('¿Estás seguro de que deseas eliminar este elemento? Esta acción no se puede deshacer.');
        if (!confirmed) {
            e.preventDefault();
        }
    });
});
});

function setupImagePreview() {
const fileInputs = document.querySelectorAll('input[type="file"][accept*="image"]');

fileInputs.forEach(input => {
    input.addEventListener('change', function(e) {
        const file = e.target.files[0];

        if (file) {
            const reader = new FileReader();

            reader.onload = function(e) {
                let preview = document.getElementById('image-preview');

                if (!preview) {
                    preview = document.createElement('div');
                    preview.id = 'image-preview';
                    preview.style.marginTop = '1rem';
                    input.parentElement.appendChild(preview);
                }

                preview.innerHTML = '';

                const img = document.createElement('img');
                img.src = e.target.result;
                img.alt = 'Preview';
                img.style.cssText = 'max-width: 100%; max-height: 300px; border-radius: var(--border-radius); box-shadow: var(--shadow);';

                const p = document.createElement('p');
                p.style.cssText = 'margin-top: 0.5rem; color: var(--gray); font-size: var(--font-sm);';
                p.textContent = `${file.name} (${(file.size / 1024).toFixed(2)} KB)`;

                preview.appendChild(img);
                preview.appendChild(p);
            };

            reader.readAsDataURL(file);
        }
    });
});
}
document.addEventListener('DOMContentLoaded', setupImagePreview);

function setupCharacterCounter() {
const textareas = document.querySelectorAll('textarea[maxlength]');
textareas.forEach(textarea => {
    const maxLength = textarea.getAttribute('maxlength');
    if (maxLength) {

        const counter = document.createElement('div');
        counter.className = 'character-counter';
        counter.style.textAlign = 'right';
        counter.style.fontSize = 'var(--font-sm)';
        counter.style.color = 'var(--gray)';
        counter.style.marginTop = '0.25rem';

        textarea.parentElement.appendChild(counter);

        function updateCounter() {
            const remaining = maxLength - textarea.value.length;
            counter.textContent = `${remaining} caracteres restantes`;

            if (remaining < 50) {
                counter.style.color = 'var(--warning-color)';
            } else {
                counter.style.color = 'var(--gray)';
            }
        }

        textarea.addEventListener('input', updateCounter);
        updateCounter();
    }
});
}
document.addEventListener('DOMContentLoaded', setupCharacterCounter);

function setupFormValidation() {
const forms = document.querySelectorAll('form[data-validate="true"]');

forms.forEach(form => {
    form.addEventListener('submit', function(e) {
        const requiredFields = form.querySelectorAll('[required]');
        let isValid = true;

        requiredFields.forEach(field => {
            if (!field.value.trim()) {
                isValid = false;
                field.classList.add('error-field');
                if (!field.nextElementSibling || !field.nextElementSibling.classList.contains('error')) {
                    const errorMsg = document.createElement('span');
                    errorMsg.className = 'error';
                    errorMsg.textContent = 'Este campo es obligatorio';
                    field.parentElement.appendChild(errorMsg);
                }
            } else {
                field.classList.remove('error-field');
                const errorMsg = field.nextElementSibling;
                if (errorMsg && errorMsg.classList.contains('error')) {
                    errorMsg.remove();
                }
            }
        });

        if (!isValid) {
            e.preventDefault();
            showAlert('Por favor, completa todos los campos obligatorios', 'error');
        }
    });
});
}

document.addEventListener('DOMContentLoaded', setupFormValidation);

function setupTabs() {
const tabs = document.querySelectorAll('.tab');

tabs.forEach(tab => {
    tab.addEventListener('click', function() {
        const targetId = this.getAttribute('data-target');
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        this.classList.add('active');
        document.getElementById(targetId).classList.add('active');
    });
});
}

document.addEventListener('DOMContentLoaded', setupTabs);

function setupLiveSearch(searchInputId, itemsSelector) {
const searchInput = document.getElementById(searchInputId);

if (!searchInput) return;

searchInput.addEventListener('input', function() {
    const query = this.value.toLowerCase();
    const items = document.querySelectorAll(itemsSelector);

    items.forEach(item => {
        const text = item.textContent.toLowerCase();

        if (text.includes(query)) {
            item.style.display = '';
        } else {
            item.style.display = 'none';
        }
    });
});
}

function copyToClipboard(text, successMessage = 'Copiado al portapapeles') {
if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(() => {
        showAlert(successMessage, 'success');
    }).catch(err => {
        console.error('Error al copiar:', err);
        showAlert('Error al copiar', 'error');
    });
} else {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    document.body.appendChild(textArea);
    textArea.select();

    try {
        document.execCommand('copy');
        showAlert(successMessage, 'success');
    } catch (err) {
        console.error('Error al copiar:', err);
        showAlert('Error al copiar', 'error');
    }

    document.body.removeChild(textArea);
}
}

document.addEventListener('DOMContentLoaded', function() {
const accessCodes = document.querySelectorAll('.access-code');

accessCodes.forEach(code => {
    code.style.cursor = 'pointer';
    code.title = 'Clic para copiar';

    code.addEventListener('click', function() {
        copyToClipboard(this.textContent.trim(), 'Código copiado');
    });
});
});

function setupUnsavedChangesWarning() {
const forms = document.querySelectorAll('form');
let formChanged = false;

forms.forEach(form => {
    const inputs = form.querySelectorAll('input, textarea, select');

    inputs.forEach(input => {
        input.addEventListener('change', () => {
            formChanged = true;
        });
    });

    form.addEventListener('submit', () => {
        formChanged = false;
    });
});

window.addEventListener('beforeunload', (e) => {
    if (formChanged) {
        e.preventDefault();
        e.returnValue = '';
    }
});
}

document.addEventListener('DOMContentLoaded', setupUnsavedChangesWarning);

function formatDateES(dateString) {
const date = new Date(dateString);
const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];

return `${date.getDate()} de ${meses[date.getMonth()]} de ${date.getFullYear()}`;
}

function timeAgo(dateString) {
const date = new Date(dateString);
const now = new Date();
const seconds = Math.floor((now - date) / 1000);

const intervals = {
    año: 31536000,
    mes: 2592000,
    día: 86400,
    hora: 3600,
    minuto: 60
};

for (let [name, secs] of Object.entries(intervals)) {
    const interval = Math.floor(seconds / secs);
    if (interval >= 1) {
        return `Hace ${interval} ${name}${interval > 1 ? 's' : ''}`;
    }
}
return 'Hace unos segundos';
}

window.showAlert = showAlert;
window.setupLiveSearch = setupLiveSearch;
window.copyToClipboard = copyToClipboard;
window.formatDateES = formatDateES;
window.timeAgo = timeAgo;