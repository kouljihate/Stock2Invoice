document.addEventListener('DOMContentLoaded', function () {
  var alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (a) {
    setTimeout(function () { a.classList.add('fade'); }, 5000);
  });

  var loader = document.getElementById('loader-overlay');

  function showLoader() {
    if (loader) loader.style.display = 'flex';
  }

  document.querySelectorAll('form').forEach(function (form) {
    form.addEventListener('submit', showLoader);
  });

  document.querySelectorAll('.btn').forEach(function (btn) {
    btn.addEventListener('click', function (e) {
      var form = btn.closest('form');
      if (!form && btn.getAttribute('type') !== 'submit') {
        showLoader();
      }
    });
  });

  document.querySelectorAll('a.nav-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = link.getAttribute('href');
      if (href && href !== '#' && !href.startsWith('javascript:') && !link.hasAttribute('data-bs-toggle')) {
        showLoader();
      }
    });
  });
});
