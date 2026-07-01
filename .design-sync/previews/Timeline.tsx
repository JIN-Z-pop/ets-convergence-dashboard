import { Timeline, TimelineItem, ImpactBadge } from 'ets-editorial';

export const CBAMTimeline = () => (
  <Timeline>
    <TimelineItem
      date="2023-10"
      title="CBAM transitional period begins"
      description="Importers report embedded emissions quarterly; no certificates required yet."
    />
    <TimelineItem
      date="2026-01"
      title="CBAM definitive regime"
      severity="critical"
      description="Certificate purchases begin for cement, steel, aluminium, fertilizers, electricity and hydrogen."
      impacts={
        <>
          <ImpactBadge variant="kr">🇰🇷 K-CBAM legislation proposed</ImpactBadge>
          <ImpactBadge variant="cn">🇨🇳 CCER re-launch leverage</ImpactBadge>
        </>
      }
    />
    <TimelineItem
      date="2030"
      title="Sector scope review"
      severity="high"
      description="Potential extension to organic chemicals and polymers under the 2030 review clause."
      impacts={<ImpactBadge variant="cn">🇨🇳 Petrochemical exposure</ImpactBadge>}
    />
  </Timeline>
);
