/* لائبریری: افتتاحی اسکرین، اشاعتوں کے کارڈ، تلاش، ٹلٹ اور ابھرنے کے اثرات */
(function () {
  'use strict';
  var NR = window.NR, ISSUES = window.ISSUES || [], body = document.body;
  var $ = function (id) { return document.getElementById(id); };
  var N = ISSUES.length;

  /* ---------- رسائل کے متحرک فوری لنکس ---------- */
  function quick(cls) {
    var h = '<nav class="qlinks ' + cls + '" aria-label="تمام رسائل">';
    ISSUES.forEach(function (it, i) {
      h += '<a class="qlink" style="--i:' + i + '" href="issues/' + it.slug + '/index.html">' +
           '<em>' + (i + 1) + '</em><span>' + it.title + (it.period ? '<small>' + it.period + '</small>' : '') + '</span></a>';
    });
    return h + '</nav>';
  }

  /* ---------- ہیڈر اور ہیرو ---------- */
  $('top').innerHTML =
    '<a class="brand" href="index.html">' + NR.BOOK(false) +
    '<span class="t"><b>' + NR.SITE + '</b><small>اسلامی روحانی مجلہ — تمام اشاعتیں</small></span></a>' +
    '<div class="tools"><a class="btn group link" href="links.html" title="ہر اشاعت اور صفحے کے لنک">' + NR.ICON.link + '<span class="lbl">تمام روابط</span></a></div>';

  $('hero').innerHTML = NR.BOOK(true) + '<h1>' + NR.SITE + '</h1>' +
    '<p>اسلامی روحانی مجلہ — جملہ اشاعتیں آن لائن</p>' +
    '<span class="count">' + N + ' اشاعتیں</span>' + quick('in-hero');

  /* ---------- کارڈ ---------- */
  var shelf = $('shelf'), html = '';
  ISSUES.forEach(function (it, i) {
    var base = 'issues/' + it.slug + '/';
    html +=
      '<article class="card" style="--i:' + (i % 6) + '" data-t="' + (it.title + ' ' + (it.period || '')).toLowerCase() + '">' +
        '<div class="tilt"><a class="face" href="' + base + 'index.html" aria-label="' + it.title + ' پڑھیں">' +
          '<span class="no">' + (i + 1) + '</span>' +
          '<img loading="lazy" decoding="async" src="' + base + 'images/cover.' + (it.ext || 'jpg') + '" alt="' + it.title + ' کا سرورق"></a></div>' +
        '<div class="meta"><h2>' + it.title + '</h2><small>' + (it.period ? it.period + ' • ' : '') + it.pages + ' صفحات</small>' +
          '<div class="acts"><a class="pill main" href="' + base + 'index.html">پڑھیں</a>' +
          '<a class="pill" href="' + base + 'index.html#1&v=2">دو صفحات</a></div></div>' +
      '</article>';
  });
  shelf.innerHTML = html;

  /* ---------- تلاش ---------- */
  $('q').addEventListener('input', function () {
    var q = this.value.trim().toLowerCase(), shown = 0;
    Array.prototype.forEach.call(shelf.children, function (c) {
      var ok = !q || c.dataset.t.indexOf(q) !== -1;
      c.classList.toggle('gone', !ok);
      if (ok) { shown++; c.classList.add('in'); }
    });
    $('empty').style.display = shown ? 'none' : 'block';
  });

  /* ---------- اسکرول پر ابھرنا ---------- */
  var cards = Array.prototype.slice.call(shelf.children);
  if ('IntersectionObserver' in window) {
    var io = new IntersectionObserver(function (es) {
      es.forEach(function (e) { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } });
    }, { threshold: 0.12 });
    cards.forEach(function (c) { io.observe(c); });
  } else { cards.forEach(function (c) { c.classList.add('in'); }); }

  /* ---------- ماؤس کے ساتھ تھری ڈی جھکاؤ ---------- */
  if (window.matchMedia('(hover:hover)').matches) {
    shelf.addEventListener('pointermove', function (e) {
      var f = e.target.closest && e.target.closest('.face');
      if (!f) return;
      var r = f.getBoundingClientRect(), x = (e.clientX - r.left) / r.width, y = (e.clientY - r.top) / r.height;
      f.style.setProperty('--ry', ((x - 0.5) * 14).toFixed(1) + 'deg');
      f.style.setProperty('--rx', ((0.5 - y) * 12).toFixed(1) + 'deg');
      f.style.setProperty('--mx', (x * 100).toFixed(0) + '%');
      f.style.setProperty('--my', (y * 100).toFixed(0) + '%');
    });
    shelf.addEventListener('pointerout', function (e) {
      var f = e.target.closest && e.target.closest('.face');
      if (f) { f.style.setProperty('--ry', '0deg'); f.style.setProperty('--rx', '0deg'); }
    });
  }

  /* ---------- افتتاحی اسکرین ---------- */
  var seen = null;
  try { seen = sessionStorage.getItem('nr-splash'); } catch (e) {}
  if (seen) return;
  try { sessionStorage.setItem('nr-splash', '1'); } catch (e) {}
  var s = document.createElement('div'); s.id = 'splash';
  s.innerHTML = NR.BOOK(true) + '<h1>' + NR.SITE + '</h1><p>اسلامی روحانی مجلہ — تمام اشاعتیں</p>' +
    quick('in-splash') +
    '<button type="button" class="enter" id="bEnter"><span>مزید پڑھیں</span>' + NR.ICON.left + '</button>';
  body.appendChild(s);
  body.style.overflow = 'hidden';
  var btn = s.querySelector('#bEnter');
  btn.onclick = function () {
    s.classList.add('hide'); body.style.overflow = '';
    setTimeout(function () { s.remove(); }, 1000);
  };
  setTimeout(function () { btn.focus({ preventScroll: true }); }, 1600);
})();
