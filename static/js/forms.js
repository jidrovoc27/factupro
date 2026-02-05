const _url = window.location.toString().split(window.location.host.toString())[1];
const cargando = '<span class="spinner-border spinner-border-sm" style="font-size: 12px;" role="status" aria-hidden="true"></span>';
const btnSubmit = $('#submit,#submit2,#submit3');
const error_btn = btnSubmit.html();
const method_req = "POST";
const _enc = $('*[data-datoseguro=true]').toArray();
var __enc = [];
for (var i = 0; i < _enc.length; i++) {
    __enc.push($(_enc[i]).attr('name'));
}
const inputsEncrypted = __enc.join('|');
const pk = $(this).find('input[name=pk]').length ? parseInt($(this).find('input[name=pk]').val()) : 0;
const action = $(this).find('input[name=action]').length ? $(this).find('input[name=action]').val() : false;
$(function () {
    if ($('#submitAndAdd').length) {
        $('#submitAndAdd').click(function () {
            $('form').append('<input type="hidden" name="_add" value="_add" />');
        });
    }
    $('#submit').click(function () {
        $('input[name=_add]').remove();
    });
    $('form:not(#frmEliminar, #frmVisita, #frmVisible, #frmEliPrg, #frmRespuesta, #frmGestion, #frmReactivar, #frmEliminarConComentario, #frmQuitarBestseller, #frmHacerBestseller, #frmActivarProducto, [method=GET], [method=get])').submit(function (e) {
        e.preventDefault();
        if (typeof funcionAntesDeGuardar === 'function') {
            funcionAntesDeGuardar();
        }
        sendFormWithPostMethod($(this)[0], pk, action);
    });
});

const sendFormWithPostMethod = (formObject, thePk, theAction) => new Promise((resolve, reject) => {
        $('input, textarea, select').removeClass('is-invalid');
        var _form = new FormData(formObject);
        if (thePk !== 0) {
            if (_form.has('pk')) {
                _form.set('pk', thePk.toString());
            } else {
                _form.append('pk', thePk.toString());
            }

        }
        if (theAction !== false) {
            if (_form.has('action')) {
                _form.set('action', theAction);
            } else {
                _form.append('action', theAction);
            }
        }
        const listInputsEnc = inputsEncrypted.split('|');
        for (var i = 0; i < listInputsEnc.length; i++) {
            if (_form.has(listInputsEnc[i])) {
                _form.set(listInputsEnc[i], doRSA(_form.get(listInputsEnc[i])));
            }
        }
        var inputsNoValidos = [];
        $.ajax({
            type: method_req,
            url: _url,
            data: _form,
            dataType: "json",
            enctype: $(formObject).attr('enctype'),
            cache: false,
            contentType: false,
            processData: false,
            beforeSend: function () {
                btnSubmit.html(cargando);
                btnSubmit.attr("disabled", true);
                bloqueointerface();
            }
        }).done(function (data) {
            data.forEach(function (value, index) {
                if (!value.error) {
                    if (value.reload) {
                        location.reload();
                    }
                    if (value.to) {
                        location = value.to;
                    }
                    if (value.function_js) {
                        eval(value.function_js);
                    }
                    resolve({resp: !value.error, model: value.model ? value.model : null});
                } else {
                    if (value.input_id) {
                        $("#" + value.input_id).addClass("is-invalid");
                        $("#" + value.div_id).html(value.message);
                    } else if (value.form) {
                        value.form.forEach(function (val, indx) {
                            var keys = Object.keys(val);
                            keys.forEach(function (val1, indx1) {
                                try {
                                    var h = $("#id_" + val1).height;
                                    inputsNoValidos.push(h);
                                } catch (e) {

                                }
                                $("#id_" + val1).addClass("is-invalid");
                                $("#errorMessage" + val1).html(val[val1]);
                            });
                        });
                    } else {
                        Swal.fire(value.message, '', 'error');
                    }
                }
            });
            if (inputsNoValidos.length > 0) {
                $([document.documentElement, document.body]).animate({
                    scrollTop: inputsNoValidos[inputsNoValidos.length - 1]
                }, 500);
            }
            btnSubmit.html(error_btn);
            btnSubmit.attr("disabled", false);
            $.unblockUI();
        }).fail(function (jqXHR, textStatus, errorThrown) {
            Swal.fire('Error en el servidor', '', 'error');
            btnSubmit.html(error_btn);
            btnSubmit.attr("disabled", false);
            $.unblockUI();
        }).always(function () {

        });
    }
);