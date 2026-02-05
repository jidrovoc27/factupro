// static/js/basescript.js

(function () {

  function loadScript(src) {
    return new Promise((resolve, reject) => {
      const s = document.createElement('script');
      s.src = src;
      s.defer = true;
      s.onload = resolve;
      s.onerror = () => reject(src);
      document.head.appendChild(s);
    });
  }

  async function init() {

    const basePath = document.currentScript.src
      .split('/')
      .slice(0, -1)
      .join('/');

    try {

      // 1) Alertas
      await loadScript('/static/alertas.js');

      // 2) Formularios
      await loadScript('/static/envioformulario.js');

      console.log('BaseScript cargado correctamente');

    } catch (err) {
      console.error('Error cargando JS:', err);
    }
  }

  init();

})();
