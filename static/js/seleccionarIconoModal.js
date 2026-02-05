$(function () {
    $('#id_icono').attr("type", "hidden");
    $('#txtBuscarIcono').keyup(function () {
        var critero = $(this).val().toUpperCase();
        $('.classIconos').each(function () {
            var currentLiText = $(this).attr('data-paraBuscar').toUpperCase(),
                showCurrentLi = currentLiText.indexOf(critero) !== -1;
            $(this).toggle(showCurrentLi);
        });
    });
});

function cargarModal() {
    $('#modalIcons').modal({width: '1200px'}).modal("show");
    for (var i = 0; i < fawIcons.length; i++) {
        var icono = fawIcons[i].classIcon;
        var nombre = fawIcons[i].paraBuscar.split("-").join(' ').trim();
        if (icono === $('#id_icono').val()) {
            $('#buscarIcono').html(`Ícono seleccionado: <i style="font-size: 20px;" class="${icono}"></i> ${nombre}`);
            $('#buscarIcono').removeClass('btn-light').addClass('btn-success');
        }
        $('#iconsContainer').append(`<label data-paraBuscar="${nombre}" onclick="agregarIcono('${icono}', '${nombre}')" onmouseenter="icMouseEnter(this)" onmouseleave="icMouseLeave(this)" 
            style="cursor: pointer;" for="radioIcons_${i}" class="span2 flex justify-content-center text-center mt-2 text-secondary classIconos">
                <input id="radioIcons_${i}" type="radio" style="display: none;" class="radioIcons" name="radioIcons" value="${icono}" /><i style="font-size: 40px;" class="${icono}">
               </i><br><b style="font-size: 10px;">${nombre}</b></label>`);
    }
}

function icMouseEnter(ctr) {
    $(ctr).removeClass('text-secondary').addClass('text-primary');
}

function icMouseLeave(ctr) {
    $(ctr).removeClass('text-primary').addClass('text-secondary');
}

function agregarIcono(valor, nombre) {
    $('#id_icono').val(valor);
    $('#buscarIcono').html(`Ícono seleccionado:   <i style="font-size: 20px;" class="${valor}"></i> ${nombre}`);
    $('#buscarIcono').removeClass('btn-light').addClass('btn-success');
    $('#modalIcons').modal("hide");
}