// js/main.js

$(document).ready(function() {
    // --- Configuración Global de jQuery para CSRF de Django ---
    // Esta es la parte más importante para Django y AJAX.
    // Busca el token en la cookie 'csrftoken' (que {% csrf_token %} crea)
    // y lo añade al encabezado 'X-CSRFToken' para todas las peticiones AJAX POST.
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                // Does this cookie string begin with the name we want?
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
    const csrftoken = getCookie('csrftoken');

    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!/^(GET|HEAD|OPTIONS|TRACE)$/.test(settings.type) && !this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
    // --------------------------------------------------------

    // Referencias a los elementos del DOM (todos con JavaScript Vanilla)
    const videoElement = document.getElementById('videoElement');
    const canvasElement = document.getElementById('canvasElement');
    const capturedImageElement = document.getElementById('capturedImage');
    const startButton = document.getElementById('startButton');
    const captureButton = document.getElementById('captureButton');
    const retryButton = document.getElementById('retryButton');
    const uploadButton = document.getElementById('uploadButton');
    const usernameInput = document.getElementById('usernameInput');
    const messageElement = document.getElementById('message');

    let currentImageBlob = null;

    // Inicializar el módulo de la cámara
    CameraModule.init(videoElement, canvasElement);

    /**
     * Muestra un mensaje en la interfaz.
     * @param {string} msg El mensaje a mostrar.
     * @param {string} type El tipo de mensaje ('success', 'error', 'info').
     */
    const showMessage = (msg, type = '') => {
        messageElement.textContent = msg;
        messageElement.classList.remove('success', 'error');
        if (type) {
            messageElement.classList.add(type);
        }
    };

    /**
     * Habilita/deshabilita los botones y controla la visibilidad del botón "Intentar de nuevo".
     * También controla si el botón de envío debe estar habilitado basándose en si hay una imagen y un username.
     * @param {boolean} start Habilitar/deshabilitar el botón de iniciar cámara.
     * @param {boolean} capture Habilitar/deshabilitar el botón de capturar.
     * @param {boolean} upload Habilitar/deshabilitar el botón de enviar.
     * @param {boolean} retry Mostrar/ocultar y habilitar/deshabilitar el botón de intentar de nuevo.
     */
    const toggleButtons = (start, capture, upload, retry) => {
        startButton.disabled = !start;
        captureButton.disabled = !capture;

        // El botón de upload solo se habilita si hay una imagen Y el username no está vacío Y si el 'upload' booleano lo permite
        // ¡Ya no necesitamos verificar csrfToken aquí, jQuery lo maneja!
        uploadButton.disabled = !upload || !currentImageBlob || usernameInput.value.trim() === '';

        retryButton.style.display = retry ? 'inline-block' : 'none';
        retryButton.disabled = !retry;
    };

    /**
     * Resetea la interfaz a su estado inicial y, opcionalmente, inicia la cámara.
     * @param {boolean} autoStartCamera Si es true, intentará iniciar la cámara automáticamente.
     */
    const resetUIForNewCapture = async (autoStartCamera = false) => {
        CameraModule.stop();
        currentImageBlob = null;

        capturedImageElement.src = '';
        capturedImageElement.style.display = 'none';

        videoElement.style.display = 'block';
        videoElement.srcObject = null;

        showMessage('Preparando para una nueva captura...', '');
        toggleButtons(false, false, false, false);

        if (autoStartCamera) {
            try {
                await CameraModule.start();
                showMessage('Cámara activa. ¡Lista para capturar!', 'success');
                toggleButtons(false, true, true, false);
            } catch (error) {
                showMessage('Error al iniciar la cámara automáticamente. ' + error.message + ' Presiona "Iniciar Cámara" manualmente.', 'error');
                toggleButtons(true, false, false, false);
            }
        } else {
            showMessage('Presiona "Iniciar Cámara" para comenzar.', '');
            toggleButtons(true, false, false, false);
        }
    };

    // --- Event Listeners ---

    $(startButton).on('click', async () => {
        showMessage('Iniciando cámara...', '');
        toggleButtons(false, false, false, false);

        try {
            await CameraModule.start();
            showMessage('Cámara activa. ¡Lista para capturar!', 'success');
            capturedImageElement.style.display = 'none';
            videoElement.style.display = 'block';
            toggleButtons(false, true, true, false);
        } catch (error) {
            showMessage('Error al iniciar la cámara. ' + error.message, 'error');
            toggleButtons(true, false, false, false);
        }
    });

    $(captureButton).on('click', async () => {
        showMessage('Capturando imagen y apagando cámara...', '');
        toggleButtons(false, false, false, false);

        try {
            currentImageBlob = await CameraModule.capture();
            if (currentImageBlob) {
                CameraModule.stop();
                const imageUrl = URL.createObjectURL(currentImageBlob);
                capturedImageElement.src = imageUrl;
                capturedImageElement.style.display = 'block';
                videoElement.style.display = 'none';
                showMessage('Imagen capturada. Introduce un usuario y puedes enviarla o intentar de nuevo.', 'success');
                toggleButtons(false, false, true, true);
            } else {
                showMessage('Fallo al capturar la imagen. Intenta de nuevo.', 'error');
                toggleButtons(false, true, false, true);
            }
        } catch (error) {
            showMessage('Error al capturar la imagen: ' + error.message, 'error');
            toggleButtons(false, true, false, true);
        }
    });

    $(usernameInput).on('input', () => {
        if (currentImageBlob) {
            toggleButtons(false, false, true, true);
        }
    });

    $(uploadButton).on('click', async () => {
        const username = usernameInput.value.trim();

        if (!username) {
            showMessage('Por favor, introduce un nombre de usuario antes de enviar.', 'error');
            return;
        }
        // Ya no necesitamos verificar csrfToken aquí explícitamente, jQuery lo maneja.
        // if (!csrfToken) { /* ... */ }

        showMessage('Enviando imagen y datos...', '');
        toggleButtons(false, false, false, false);

        try {
            // ¡Ya no pasamos el csrfToken aquí! jQuery lo añade automáticamente.
            await UploaderModule.upload(currentImageBlob, 'mi_captura_' + Date.now() + '.png', username);
            showMessage('Imagen y datos enviados con éxito al servidor. La cámara se reiniciará para una nueva captura.', 'success');
            resetUIForNewCapture(true);
        } catch (error) {
            showMessage('Error al enviar la imagen: ' + error.message, 'error');
            toggleButtons(false, false, true, true);
        }
    });

    $(retryButton).on('click', async () => {
        showMessage('Reiniciando para una nueva captura y encendiendo cámara...', '');
        await resetUIForNewCapture(true);
    });

    // Estado inicial de los botones cuando la página carga
    resetUIForNewCapture();
});