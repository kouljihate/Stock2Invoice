document.addEventListener('DOMContentLoaded', function () {
  var alerts = document.querySelectorAll('.flash-toast.alert-dismissible');
  alerts.forEach(function (a) {
    setTimeout(function () {
      a.classList.remove('show');
      a.classList.add('fade');
      setTimeout(function () { a.remove(); }, 300);
    }, 5000);
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
      if (!form && btn.getAttribute('type') !== 'submit' && btn.getAttribute('target') !== '_blank') {
        showLoader();
      }
    });
  });

  document.querySelectorAll('a.nav-link').forEach(function (link) {
    link.addEventListener('click', function (e) {
      var href = link.getAttribute('href');
      if (href && href !== '#' && !href.startsWith('javascript:') && !link.hasAttribute('data-bs-toggle') && link.getAttribute('target') !== '_blank') {
        showLoader();
      }
    });
  });
});
