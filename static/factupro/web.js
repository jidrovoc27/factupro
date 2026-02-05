(function () {
  const burger = document.getElementById('navBurger');
  const mobile = document.getElementById('navMobile');

  if (burger && mobile) {
    burger.addEventListener('click', () => {
      const isOpen = mobile.style.display === 'block';
      mobile.style.display = isOpen ? 'none' : 'block';
    });

    // Cierra menú al hacer click
    mobile.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => mobile.style.display = 'none');
    });
  }
})();
