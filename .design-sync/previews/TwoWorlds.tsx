import { TwoWorlds } from 'ets-editorial';

export const EUvsAsia = () => (
  <TwoWorlds
    title="Two Regulatory Worlds"
    left={{
      title: 'EU World 🇪🇺',
      color: '#3182ce',
      items: [
        'Absolute cap, declining 4.3%/yr',
        'Full auctioning for power sector',
        'CBAM at the border from 2026',
        'MSR absorbs surplus allowances',
      ],
    }}
    right={{
      title: 'Asia World 🇰🇷🇨🇳🇯🇵',
      color: '#ed8936',
      items: [
        'Intensity-based or hybrid caps',
        'Free allocation still dominant',
        'Voluntary-to-mandatory transitions',
        'Offset mechanisms (CCER, KOC) active',
      ],
    }}
    note="Convergence pressure flows through CBAM, investor disclosure and Article 6 linkage."
  />
);
