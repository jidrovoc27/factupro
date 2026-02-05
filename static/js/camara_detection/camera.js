// js/camera.js

/**
 * Módulo para manejar la interacción con la cámara web.
 * Expone funciones para iniciar, detener y capturar imágenes.
 */
const CameraModule = (function() {
    let videoElement = null;
    let canvasElement = null;
    let context = null;
    let stream = null; // Para almacenar el MediaStream
    let currentCapturedImageBlob = null; // Almacena el Blob de la última imagen capturada

    /**
     * Inicializa los elementos del DOM.
     * @param {HTMLVideoElement} videoElem El elemento <video>.
     * @param {HTMLCanvasElement} canvasElem El elemento <canvas>.
     */
    const init = (videoElem, canvasElem) => {
        videoElement = videoElem;
        canvasElement = canvasElem;
        context = canvasElement.getContext('2d');
    };

    /**
     * Inicia el stream de video de la cámara.
     * @returns {Promise<void>} Una promesa que se resuelve cuando la cámara se inicia.
     */
    const startCamera = async () => {
        if (stream) {
            console.log("Cámara ya iniciada.");
            return;
        }

        try {
            // Preferencias para la cámara, incluyendo sonido (audio: false)
            stream = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
            videoElement.srcObject = stream;
            videoElement.play();
            console.log("Cámara iniciada.");
        } catch (error) {
            console.error("Error al acceder a la cámara:", error);
            alert("No se pudo acceder a la cámara. Asegúrate de dar los permisos y de que no esté en uso.");
            throw error; // Re-lanza el error para que el llamador pueda manejarlo
        }
    };

    /**
     * Detiene el stream de video de la cámara.
     */
    const stopCamera = () => {
        if (stream) {
            stream.getTracks().forEach(track => track.stop());
            videoElement.srcObject = null;
            stream = null;
            console.log("Cámara detenida.");
        }
    };

    /**
     * Captura un fotograma del video y lo dibuja en el canvas, luego lo convierte a Blob.
     * @returns {Promise<Blob|null>} Una promesa que se resuelve con un Blob de la imagen o null si falla.
     */
    const captureImage = () => {
        if (!videoElement || !canvasElement || !stream) {
            console.warn("La cámara no está activa o los elementos no están inicializados.");
            return Promise.resolve(null);
        }

        // Asegurarse de que el canvas tenga el mismo tamaño que el video
        canvasElement.width = videoElement.videoWidth;
        canvasElement.height = videoElement.videoHeight;

        context.drawImage(videoElement, 0, 0, canvasElement.width, canvasElement.height);

        return new Promise((resolve) => {
            // Convertir el contenido del canvas a un Blob (representación binaria de la imagen)
            canvasElement.toBlob((blob) => {
                if (blob) {
                    currentCapturedImageBlob = blob;
                    console.log("Imagen capturada y convertida a Blob.");
                    resolve(blob);
                } else {
                    console.error("No se pudo convertir el canvas a Blob.");
                    currentCapturedImageBlob = null;
                    resolve(null);
                }
            }, 'image/png'); // Puedes cambiar a 'image/jpeg' si lo prefieres
        });
    };

    /**
     * Obtiene el último Blob de imagen capturado.
     * @returns {Blob|null} El Blob de la imagen.
     */
    const getCapturedImageBlob = () => {
        return currentCapturedImageBlob;
    };

    // Publicamos solo las funciones que queremos que sean accesibles desde fuera.
    return {
        init: init,
        start: startCamera,
        stop: stopCamera,
        capture: captureImage,
        getCapturedBlob: getCapturedImageBlob
    };
})();