/* مشترکہ اجزاء: آئیکن، کتابی اینیمیشن، ذرات، بٹنوں کی لہر */
(function () {
  'use strict';
  var NR = window.NR = {};
  NR.SITE = 'ماہنامہ نظامِ رنگ';

  NR.ICON = {
    menu: '<svg viewBox="0 0 24 24"><path d="M4 6h16M4 12h16M4 18h16"/></svg>',
    plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
    minus: '<svg viewBox="0 0 24 24"><path d="M5 12h14"/></svg>',
    fit: '<svg viewBox="0 0 24 24"><path d="M4 9V4h5M20 9V4h-5M4 15v5h5M20 15v5h-5"/></svg>',
    link: '<svg viewBox="0 0 24 24"><path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/></svg>',
    full: '<svg viewBox="0 0 24 24"><path d="M9 4H4v5M15 4h5v5M9 20H4v-5M15 20h5v-5"/></svg>',
    right: '<svg viewBox="0 0 24 24"><path d="M9 6l6 6-6 6"/></svg>',
    left: '<svg viewBox="0 0 24 24"><path d="M15 6l-6 6 6 6"/></svg>',
    close: '<svg viewBox="0 0 24 24"><path d="M6 6l12 12M18 6L6 18"/></svg>',
    home: '<svg viewBox="0 0 24 24"><path d="M4 11l8-7 8 7v9h-5v-6H9v6H4z"/></svg>'
  };

  /* کھلی کتاب جس کے ورق باری باری پلٹتے ہیں */
  NR.BOOK = function (big) {
    var pages = '';
    for (var i = 0; i < 7; i++) { pages += '<i class="pg" style="--i:' + i + '"></i>'; }
    return '<span class="bkw' + (big ? ' big' : '') + '" aria-hidden="true"><span class="bk"><i class="cover"></i>' + pages + '<i class="spine"></i></span></span>';
  };

  /* تیرتے سنہری ذرات */
  NR.dust = function () {
    var d = document.createElement('div'); d.className = 'dust'; d.setAttribute('aria-hidden', 'true');
    var h = '';
    for (var i = 0; i < 18; i++) {
      h += '<i style="left:' + (Math.random() * 100).toFixed(1) + '%;--s:' + (2 + Math.random() * 4).toFixed(1) + 'px;' +
           '--d:' + (14 + Math.random() * 16).toFixed(1) + 's;--l:-' + (Math.random() * 20).toFixed(1) + 's;' +
           '--x:' + (Math.random() * 120 - 60).toFixed(0) + 'px"></i>';
    }
    d.innerHTML = h;
    document.body.insertBefore(d, document.body.firstChild);
  };

  /* بٹنوں پر لہر کا اثر */
  document.addEventListener('pointerdown', function (e) {
    var b = e.target.closest && e.target.closest('.btn');
    if (!b || b.disabled) return;
    b.classList.remove('rip'); void b.offsetWidth; b.classList.add('rip');
  });

  NR.dust();
})();
