/* ============================================================
 * 主控：界面交互
 * 改 index.html 的 id 时，必须同步下面的绑定表。
 * ============================================================ */
(function () {
  'use strict';

  var el = {};
  var currentSpread = 'partnership';
  var currentResult = null;

  function $(id) { return document.getElementById(id); }

  function bind() {
    el.formPanel = $('formPanel');
    el.resultPanel = $('resultPanel');
    el.nameA = $('nameA');
    el.nameB = $('nameB');
    el.drawBtn = $('drawBtn');
    el.againBtn = $('againBtn');
    el.scoreBox = $('scoreBox');
    el.cards = $('cards');
    el.summary = $('summary');
    el.spreadBtns = document.querySelectorAll('.spread-btn');
  }

  function bindPress(btn) {
    btn.addEventListener('pointerdown', function () { btn.classList.add('pressed'); });
    ['pointerup', 'pointercancel', 'pointerleave'].forEach(function (ev) {
      btn.addEventListener(ev, function () { btn.classList.remove('pressed'); });
    });
  }

  function setSpread(id) {
    currentSpread = id;
    Array.prototype.forEach.call(el.spreadBtns, function (b) {
      b.classList.toggle('active', b.getAttribute('data-spread') === id);
    });
  }

  function draw() {
    var result = window.Divination.draw(currentSpread);
    var reading = window.Divination.interpret(result);
    currentResult = { result: result, reading: reading };
    render(reading, result);
  }

  function render(reading, result) {
    el.formPanel.classList.add('hidden');
    el.resultPanel.classList.remove('hidden');

    var a = (el.nameA.value || '你').trim();
    var b = (el.nameB.value || '对方').trim();

    el.scoreBox.innerHTML =
      '<div class="score-num tone-' + reading.tone + '">' + reading.score + '</div>' +
      '<div class="score-level">' + reading.level + '</div>' +
      '<div class="score-headline">' + reading.headline + '</div>' +
      '<div class="score-names">' + a + ' × ' + b + '</div>';

    el.cards.innerHTML = '';
    reading.sections.forEach(function (s, i) {
      var card = document.createElement('button');
      card.className = 'card';
      card.type = 'button';
      card.innerHTML =
        '<div class="card-inner">' +
          '<div class="card-face card-back"><span>✦</span></div>' +
          '<div class="card-face card-front">' +
            '<div class="card-label">' + s.label + '</div>' +
            '<div class="card-name">' + s.name + (s.reversed ? '（逆）' : '') + '</div>' +
            '<div class="card-kw">' + s.keyword + '</div>' +
          '</div>' +
        '</div>';
      card.addEventListener('click', function () {
        if (card.classList.contains('flipped')) return;
        card.classList.add('flipped');
        showSection(s, i);
      });
      el.cards.appendChild(card);

      /* 逐张自动翻开，节奏感；用户点击可提前 */
      setTimeout(function () { card.classList.add('flipped'); }, 180 * i);
    });

    el.summary.innerHTML =
      '<p class="summary-text">' + reading.advice + '</p>' +
      '<div class="card-list">' + reading.sections.map(function (s) {
        return '<div class="row"><b>' + s.label + '</b>' +
               '<span>' + s.body + '</span></div>';
      }).join('') + '</div>';
  }

  function showSection(s) {
    /* 骨架版：点击卡片只做视觉反馈，完整版可在此弹出详情层 */
    var rows = el.summary.querySelectorAll('.row');
    Array.prototype.forEach.call(rows, function (r) {
      if (r.querySelector('b') && r.querySelector('b').textContent === s.label) {
        r.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
    });
  }

  function reset() {
    el.resultPanel.classList.add('hidden');
    el.formPanel.classList.remove('hidden');
    el.scoreBox.innerHTML = '';
    el.cards.innerHTML = '';
    el.summary.innerHTML = '';
    currentResult = null;
  }

  function init() {
    bind();
    Array.prototype.forEach.call(el.spreadBtns, function (b) {
      bindPress(b);
      b.addEventListener('click', function () { setSpread(b.getAttribute('data-spread')); });
    });
    bindPress(el.drawBtn);
    bindPress(el.againBtn);
    el.drawBtn.addEventListener('click', draw);
    el.againBtn.addEventListener('click', reset);
    setSpread('partnership');
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
