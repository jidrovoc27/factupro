$(function () {
  const methodReq = "POST";
  const loadingHtml = '<i class="fa fa-cog fa-spin" role="status" aria-hidden="true"></i>';
  const defaultBtnHtml = '<i class="fa fa-check-circle" role="status" aria-hidden="true"></i> Guardar';

  // Detecta inputs con data-datoseguro="true" y toma su name
  const inputsEncrypted = $('*[data-datoseguro=true]')
    .toArray()
    .map(el => $(el).attr('name'))
    .filter(Boolean);

  // Helper: url actual relativa
  function getCurrentRelativeUrl() {
    return window.location.pathname + window.location.search;
  }

  // Helper: mostrar errores por campo (Django style)
  function paintFieldErrors(form, formErrors) {
    // Limpia mensajes previos
    form.find('.is-invalid').removeClass('is-invalid');
    form.find('[id^="errorMessage"]').html('');

    if (!Array.isArray(formErrors)) return;

    formErrors.forEach(obj => {
      Object.keys(obj).forEach(fieldName => {
        const $input = form.find('#id_' + fieldName);
        $input.addClass('is-invalid');

        // Si tienes contenedor #errorMessage{field}
        const $msg = form.find('#errorMessage' + fieldName);
        if ($msg.length) $msg.html(obj[fieldName]);
      });
    });
  }

  // Helper: encriptar campos marcados (solo strings no vacíos)
  function encryptFormData(fd) {
    for (const name of inputsEncrypted) {
      if (!fd.has(name)) continue;

      const val = fd.get(name);
      if (typeof val !== 'string') continue;
      if (!val.trim()) continue;

      try {
        fd.set(name, doRSA(val));
      } catch (e) {
        console.warn('Error cifrando campo:', name, e);
      }
    }
  }

  // Helper: intenta leer mensaje de error desde response
  function getAjaxErrorMessage(jqXHR) {
    // Si el backend devuelve JSON: {"mensaje": "..."}
    try {
      const ct = jqXHR.getResponseHeader('content-type') || '';
      if (ct.includes('application/json')) {
        const resp = jqXHR.responseJSON || JSON.parse(jqXHR.responseText);
        return resp.mensaje || resp.error || 'Ocurrió un error en el servidor';
      }
    } catch (e) {}
    return 'No se pudo completar la operación. Intente nuevamente.';
  }

  $('formc:not([method=GET], [method=get])').on('submit', function (e) {
    e.preventDefault();

    const $form = $(this);

    // ✅ Botón submit: busca dentro del formulario, no global
    const $btnSubmit = $form.find('#submit, #submit2, #submit3, button[type="submit"]').first();

    const originalBtnHtml = $btnSubmit.length ? $btnSubmit.html() : defaultBtnHtml;

    // ✅ Limpieza solo dentro del formulario
    $form.find('input, textarea, select').removeClass('is-invalid');
    $form.find('[id^="errorMessage"]').html('');

    const pkRaw = $form.find('input[name=pk]').val();
    const pk = pkRaw ? parseInt(pkRaw, 10) : 0;

    const action = $form.find('input[name=action]').val() || null;

    const urlSubmit = $form.find('input[name=urlsubmit]').val() || getCurrentRelativeUrl();

    const fd = new FormData($form[0]);

    // Normaliza pk y action
    if (pk) fd.set('pk', String(pk));
    if (action) fd.set('action', action);

    // Encripta campos marcados
    encryptFormData(fd);

    // Adjunta lista_items1 si existe
    if (typeof window.lista_items1 !== 'undefined') {
      try {
        fd.set("lista_items1", JSON.stringify(window.lista_items1));
      } catch (err) {
        console.warn('No se pudo serializar lista_items1:', err);
      }
    }

    $.ajax({
      type: methodReq,
      url: urlSubmit,
      data: fd,
      dataType: "json",
      cache: false,
      contentType: false,
      processData: false,
      beforeSend: function () {
        if ($btnSubmit.length) {
          $btnSubmit.html(loadingHtml).prop("disabled", true);
        }
        bloqueointerface();
      }
    })
    .done(function (data) {
      /**
       * OJO: En tu código original parecía invertida la lógica.
       * Aquí asumo: data.result === true => éxito.
       * Si tu backend usa al revés, cambia a:
       * const isSuccess = !data.result;
       */
      const isSuccess = !!data.result;

      if (isSuccess) {
        // ✅ ÉXITO
        if (data.modalname) {
          $('#' + data.modalname).modal('hide');
        } else {
          $(".modal").modal('hide');
        }

        if (data.to) {
          if (data.modalsuccess) {
            $.unblockUI();
            $('#textpanelmensaje').html(data.mensaje || '');
            $('#returnpanelmensaje').attr("href", data.to);
            $('#waitpanelmensaje').modal({ backdrop: 'static' }).modal('show');
            return;
          }
          window.location = data.to;
          return;
        }

        if (data.cerrar) {
          $.unblockUI();
          Swal.fire(data.mensaje || 'Proceso realizado', '', 'success');
          return;
        }

        if (data.noreload) {
          $.unblockUI();
          mensajeSuccess(data.mensaje || 'Proceso realizado');
          return;
        }

        window.location.reload();
      } else {
        // ❌ ERROR (validación o mensaje)
        paintFieldErrors($form, data.form);
        alertaDanger(data.mensaje || 'Revise los datos e intente nuevamente.');
      }
    })
    .fail(function (jqXHR) {
      const msg = getAjaxErrorMessage(jqXHR);
      alertaDanger(msg);
    })
    .always(function () {
      if ($btnSubmit.length) {
        $btnSubmit.html(originalBtnHtml).prop("disabled", false);
      }
      $.unblockUI();
    });
  });
});
