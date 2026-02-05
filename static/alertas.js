// static/js/alertas.js

(function (window) {

  function ensureSwal() {
    if (typeof Swal === 'undefined') {
      console.error('SweetAlert2 no está cargado.');
      return false;
    }
    return true;
  }

  const toastBase = {
    toast: true,
    position: 'top-end',
    showConfirmButton: false,
    timer: 5000,
    timerProgressBar: true,
    didOpen: (toast) => {
      toast.addEventListener('mouseenter', Swal.stopTimer);
      toast.addEventListener('mouseleave', Swal.resumeTimer);
    }
  };

  function toast(msg, icon = 'info', ms = 5000) {
    if (!ensureSwal()) return;

    Swal.fire({
      ...toastBase,
      icon,
      title: msg || '',
      timer: ms
    });
  }

  function modal(msg, icon = 'success', footer = '') {
    if (!ensureSwal()) return;

    Swal.fire({
      icon,
      title: msg || '',
      footer
    });
  }

  // API pública
  window.alertaSuccess = (m) => toast(m, 'success');
  window.alertaWarning = (m) => toast(m, 'warning');
  window.alertaInfo    = (m) => toast(m, 'info');
  window.alertaDanger  = (m) => toast(m, 'error');

  window.alertaToast = toast;

  window.mensajeModal = modal;

  window.mensajeSuccess = (m) => modal(m, 'success', window.APP_ALIAS || '');
  window.mensajeWarning = (m) => modal(m, 'warning', window.APP_ALIAS || '');
  window.mensajeDanger  = (m) => modal(m, 'error', window.APP_ALIAS || '');

})(window);