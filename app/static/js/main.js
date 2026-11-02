function readCookie(name) {
  var match = document.cookie.match('(?:^|; )' + name + '=([^;]*)');
  return match ? decodeURIComponent(match[1]) : '';
}

/*
 * The JWT cookie is protected with a double-submit CSRF token
 * (JWT_COOKIE_CSRF_PROTECT). The token lives in the readable
 * `csrf_access_token` cookie; attach it here once so no template or view has
 * to. The submit listener is delegated so dynamically rendered forms are
 * covered too.
 */
document.addEventListener('submit', function (e) {
  var form = e.target;
  if (!form || !form.tagName || form.tagName !== 'FORM') return;
  var token = readCookie('csrf_access_token');
  if (!token) return;
  var field = form.querySelector('input[name="csrf_token"]');
  if (!field) {
    field = document.createElement('input');
    field.type = 'hidden';
    field.name = 'csrf_token';
    form.appendChild(field);
  }
  field.value = token;
}, true);

var _nativeFetch = window.fetch;
if (_nativeFetch) {
  window.fetch = function (input, init) {
    init = init || {};
    var method = (init.method || (input && input.method) || 'GET').toUpperCase();
    var token = readCookie('csrf_access_token');
    if (token && method !== 'GET' && method !== 'HEAD' && method !== 'OPTIONS') {
      if (init.headers && typeof init.headers.append === 'function') {
        init.headers.append('X-CSRF-TOKEN', token);
      } else {
        init.headers = Object.assign({}, init.headers, {'X-CSRF-TOKEN': token});
      }
    }
    return _nativeFetch.call(window, input, init);
  };
}

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
