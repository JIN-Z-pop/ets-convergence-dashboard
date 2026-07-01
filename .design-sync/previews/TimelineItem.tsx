import { Timeline, TimelineItem, ImpactBadge } from 'ets-editorial';

/** TimelineItem needs the Timeline spine — composed inside its parent (the only true render). */
export const CriticalWithImpacts = () => (
  <Timeline>
    <TimelineItem
      date="2026-01"
      title="CBAM definitive regime"
      severity="critical"
      description="Certificate purchases begin for cement, steel, aluminium, fertilizers, electricity and hydrogen."
      impacts={
        <>
          <ImpactBadge variant="kr">🇰🇷 Export exposure ~15%</ImpactBadge>
          <ImpactBadge variant="cn">🇨🇳 Steel rerouting risk</ImpactBadge>
        </>
      }
    />
  </Timeline>
);

export const PlainEvent = () => (
  <Timeline>
    <TimelineItem
      date="2015-01"
      title="K-ETS launch"
      description="Korea becomes the first nationwide mandatory ETS in East Asia."
    />
  </Timeline>
);
