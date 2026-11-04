(function () {
  var stages = [
    { src: '/compose-waiter.webp', label: 'РАБОЧЕЕ МЕСТО ОФИЦИАНТА', alt: 'Заказ стола 5 в интерфейсе официанта Падачи' },
    { src: '/kitchen.webp', label: 'ЭКРАН КУХНИ', alt: 'Заказы и тайминги блюд на экране кухни Падачи' },
    { src: '/stock.webp', label: 'СКЛАД И ОСТАТКИ', alt: 'Остатки продуктов на складе в Падаче' }
  ];
  var buttons = document.querySelectorAll('[data-stage]');
  buttons.forEach(function (button) {
    button.addEventListener('click', function () {
      var i = Number(button.dataset.stage);
      var image = document.getElementById('stage-image');
      image.src = stages[i].src;
      image.alt = stages[i].alt;
      document.getElementById('stage-label').textContent = stages[i].label;
      document.getElementById('stage-index').textContent = '0' + (i + 1) + ' — 03';
      buttons.forEach(function (item) { item.setAttribute('aria-pressed', String(item === button)); });
    });
  });
})();
