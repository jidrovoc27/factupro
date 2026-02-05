// js/uploader.js

/**
 * Módulo para manejar el envío de datos a un servidor.
 * Utiliza jQuery para las peticiones AJAX.
 */
const UploaderModule = (function($) {
        let path = window.path || '';

    /**
     * Envía una imagen (Blob) y un nombre de usuario al servidor usando FormData y AJAX.
     * jQuery se encargará de añadir el token CSRF si está configurado globalmente.
     * @param {Blob} imageBlob El objeto Blob de la imagen a enviar.
     * @param {string} fileName El nombre del archivo para la imagen.
     * @param {string} username El nombre de usuario a adjuntar.
     * @returns {Promise<any>} Una promesa que se resuelve con la respuesta del servidor o se rechaza en caso de error.
     */
    const uploadImage = (imageBlob, fileName = 'captured_image.png', username = '') => {
        if (!imageBlob) {
            console.error("No hay una imagen para enviar.");
            return Promise.reject("No hay imagen capturada.");
        }
        if (!username.trim()) {
            console.error("El nombre de usuario no puede estar vacío.");
            return Promise.reject("El nombre de usuario es requerido.");
        }

        const formData = new FormData();
        formData.append('image', imageBlob, fileName);
        formData.append('username', username);

        return new Promise((resolve, reject) => {
            $.ajax({
                url: path,
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false,
                success: function(response) {
                    console.log('Datos enviados con éxito:', response);
                    if (response.status === 'success') {
                        alert('Datos registrados correctamente.');
                        location.reload();
                    }
                },
                error: function(jqXHR, textStatus, errorThrown) {
                    console.error('Error al enviar los datos:', textStatus, errorThrown, jqXHR.responseText);
                    reject(new Error(`Error al enviar: ${jqXHR.responseText || errorThrown}`));
                }
            });
        });
    };

    return {
        upload: uploadImage
    };
})(jQuery);