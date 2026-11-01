/* 牌阵定义：牌位顺序即解读顺序 */
window.SPREADS = {
  partnership: {
    id: 'partnership',
    name: '合作契合牌阵',
    sub: '深度看清一段合作关系',
    cardCount: 6,
    positions: [
      { key:'self',      label:'你的状态', hint:'你在合作中的角色与心态' },
      { key:'other',     label:'对方状态', hint:'对方的真实状态与核心诉求' },
      { key:'now',       label:'合作现状', hint:'这段关系当下的样貌' },
      { key:'challenge', label:'潜在挑战', hint:'要警惕的隐藏风险' },
      { key:'advice',    label:'行动建议', hint:'推进合作的具体做法' },
      { key:'future',    label:'未来走向', hint:'维持现状将走向何方' }
    ]
  },

  decision: {
    id: 'decision',
    name: '合作决策牌阵',
    sub: '要不要与对方合作',
    cardCount: 3,
    positions: [
      { key:'gain',    label:'合作之得', hint:'能带来的价值' },
      { key:'risk',    label:'合作之失', hint:'要付出的代价' },
      { key:'verdict', label:'结论建议', hint:'是否该推进' }
    ]
  }
};

/* 牌位引导语：让文案拼接读起来自然 */
window.POSITION_LEAD = {
  self:      '在这段合作中，你此刻的状态是——',
  other:     '对方在这段关系中的真实状态是——',
  now:       '你们当下的合作现状呈现出——',
  challenge: '这段合作里需要警惕的是——',
  advice:    '要让合作变好，建议这样做——',
  future:    '若维持现状，这段合作将走向——',
  gain:      '这次合作能带给你的是——',
  risk:      '需要留意与承担的是——',
  verdict:   '综合来看，结论是——'
};
