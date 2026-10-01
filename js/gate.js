/* Preview gate: keeps casual visitors out of the private preview.
   Only a SHA-256 fingerprint of the password is stored here. Remove this script (and the
   noindex meta) at go-live. Loaded in <head> so nothing flashes before it decides. */
(function () {
  var HASH = 'caf39b231ebf961b33b4b5b5ce32ac3bae9cfb18de3ba01099fcd5b3565ba15f';
  var KEY = 't4-preview';
  var root = document.documentElement;
  var base = (document.currentScript && document.currentScript.src || '').replace(/js\/gate\.js.*$/, '');

  function remembered() { try { return localStorage.getItem(KEY) === HASH; } catch (e) { return false; } }
  if (remembered()) return;
  root.classList.add('gated');

  function sha256(text) {
    return crypto.subtle.digest('SHA-256', new TextEncoder().encode(text)).then(function (buf) {
      return Array.prototype.map.call(new Uint8Array(buf), function (b) { return ('0' + b.toString(16)).slice(-2); }).join('');
    });
  }

  function build() {
    var g = document.createElement('div');
    g.className = 'gate';
    g.setAttribute('role', 'dialog');
    g.setAttribute('aria-modal', 'true');
    g.setAttribute('aria-labelledby', 'gate-title');
    g.innerHTML =
      '<div class="gate-glow" aria-hidden="true"></div>' +
      '<form class="gate-card" novalidate>' +
        '<img class="gate-logo" src="' + base + 'assets/twenty4-logo-rev.svg" alt="Twenty4" width="132" height="30">' +
        '<p id="gate-title" class="gate-title">Private preview</p>' +
        '<label class="gate-field">' +
          '<span class="sr-only">Password</span>' +
          '<input type="password" name="password" autocomplete="current-password" placeholder="Password" required>' +
          '<button type="submit" aria-label="Enter"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 12h13M13 6l6 6-6 6"/></svg></button>' +
        '</label>' +
        '<p class="gate-note" aria-live="polite"></p>' +
      '</form>';
    document.body.appendChild(g);
    var form = g.querySelector('form'), input = g.querySelector('input'), note = g.querySelector('.gate-note');
    setTimeout(function () { input.focus(); }, 300);

    form.addEventListener('submit', function (e) {
      e.preventDefault();
      sha256(input.value).then(function (h) {
        if (h !== HASH) {
          note.textContent = 'That isn’t quite right.';
          form.classList.remove('wrong'); void form.offsetWidth; form.classList.add('wrong');
          input.select();
          return;
        }
        try { localStorage.setItem(KEY, HASH); } catch (err) {}
        g.classList.add('open');
        root.classList.remove('gated');
        document.dispatchEvent(new Event('t4:unlock'));
        setTimeout(function () { g.remove(); }, 1400);
      });
    });
  }

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', build); else build();
})();
