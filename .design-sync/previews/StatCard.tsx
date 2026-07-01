import { StatCard } from 'ets-editorial';

export const SimulatorGrid = () => (
  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
    <StatCard label="🇰🇷 Korea Year 1" value="13,679" note="NS × 5 = 13,679" color="#56B870" />
    <StatCard label="🇰🇷 Korea Year 2" value="13,679" note="NS × 5 = 13,679" color="#56B870" />
    <StatCard label="🇨🇳 China" value="104,104" note="100K + NS × 1.5 = 104,104" color="#E8943A" />
    <StatCard label="🇪🇺 EU" value="∞" note="Unlimited banking" color="#4A90D9" />
  </div>
);

export const Single = () => <StatCard label="Net sales (NS)" value="2,736" note="tCO₂e" />;
