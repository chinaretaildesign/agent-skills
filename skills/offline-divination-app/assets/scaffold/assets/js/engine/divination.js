/* ============================================================
 * 离线引擎：抽牌 + 规则解读 + 评分
 * 纯函数，不碰 DOM、不发请求，可直接在 node 里跑测试。
 * ============================================================ */
(function () {
  'use strict';

  /* 警示牌：正位代表问题显现，逆位反而代表走出困境 */
  var WARNING = ['ma16', 'ma15', 'ma13', 'ma18'];  // 塔 / 恶魔 / 死神 / 月亮

  function isWarning(id) { return WARNING.indexOf(id) !== -1; }

  function cardScore(card, reversed) {
    if (isWarning(card.id)) return reversed ? 1 : -1;
    return reversed ? -1 : 1;
  }

  function levelOf(score) {
    if (score >= 80) return { level: '高度契合', headline: '这段合作值得深交', tone: 'great' };
    if (score >= 65) return { level: '总体向好', headline: '基本面不错，留意个别卡点', tone: 'good' };
    if (score >= 45) return { level: '喜忧参半', headline: '有潜力，但需要主动经营', tone: 'fair' };
    if (score >= 30) return { level: '挑战较多', headline: '推进前先把关键分歧谈清楚', tone: 'warn' };
    return { level: '阻力较大', headline: '建议暂缓，先补足信任与共识', tone: 'bad' };
  }

  /* 抽牌：splice 抽取天然不重复；逆位概率 35% */
  function draw(spreadId) {
    var spread = window.SPREADS[spreadId];
    if (!spread) throw new Error('未知牌阵: ' + spreadId);
    var pool = window.TAROT_DECK.slice();
    var cards = [];
    for (var i = 0; i < spread.cardCount; i++) {
      var idx = Math.floor(Math.random() * pool.length);
      var card = pool.splice(idx, 1)[0];
      cards.push({ card: card, reversed: Math.random() < 0.35 });
    }
    return { spread: spread, cards: cards };
  }

  /* 解读：逐张计分 → 归一化 → 分段文案 */
  function interpret(drawResult) {
    var cards = drawResult.cards;
    var spread = drawResult.spread;
    var total = 0;

    var sections = cards.map(function (c, i) {
      var pos = spread.positions[i];
      var side = c.reversed ? c.card.rv : c.card.up;
      total += cardScore(c.card, c.reversed);
      return {
        label: pos.label,
        hint: pos.hint,
        name: c.card.n,
        reversed: c.reversed,
        keyword: side.kw,
        lead: window.POSITION_LEAD[pos.key] || (pos.label + '：'),
        body: side.coop
      };
    });

    var n = cards.length || 1;
    var score = 50 + (total / n) * 38;
    score = Math.max(5, Math.min(95, Math.round(score)));

    var meta = levelOf(score);
    var adviceCard = sections.filter(function (s) {
      return s.label.indexOf('建议') !== -1 || s.label.indexOf('结论') !== -1;
    })[0];

    return {
      score: score,
      level: meta.level,
      headline: meta.headline,
      tone: meta.tone,
      sections: sections,
      advice: adviceCard ? adviceCard.body : sections[sections.length - 1].body
    };
  }

  window.Divination = { draw: draw, interpret: interpret, levelOf: levelOf };
})();
