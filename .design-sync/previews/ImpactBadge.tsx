import { ImpactBadge } from 'ets-editorial';

export const BothVariants = () => (
  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
    <ImpactBadge variant="kr">🇰🇷 K-CBAM legislation proposed</ImpactBadge>
    <ImpactBadge variant="cn">🇨🇳 CCER re-launch leverage</ImpactBadge>
  </div>
);
