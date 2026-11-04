(function () {
  var screens = [
    { src: '/compose-waiter.webp', name: 'Официант. Всё под рукой.', alt: 'Интерфейс официанта: заказ для стола 5 и разделение счёта по гостям' },
    { src: '/kitchen.webp', name: 'Кухня. Каждый заказ на виду.', alt: 'Экран кухни с очередью заказов и таймингами блюд' },
    { src: '/stock.webp', name: 'Склад. Цифры под контролем.', alt: 'Экран склада с остатками продуктов' }
  ];
  var buttons = document.querySelectorAll('[data-screen]');
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var i = Number(button.dataset.screen), screen = screens[i];
      document.getElementById('hero-screen').src = screen.src;
      document.getElementById('hero-screen').alt = screen.alt;
      document.getElementById('screen-name').textContent = screen.name;
      document.querySelector('.visual-top > span:last-child').textContent = '0' + (i + 1) + ' / 03';
      buttons.forEach(function (item) { item.setAttribute('aria-pressed', String(item === button)); });
    });
  });
})();
