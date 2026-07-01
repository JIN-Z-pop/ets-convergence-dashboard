import { PhaseButton } from 'ets-editorial';

export const CountrySelector = () => (
  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', alignItems: 'center' }}>
    <span style={{ fontSize: '0.85em', color: 'var(--muted)', marginRight: 4 }}>Phase view</span>
    <PhaseButton label="All" active />
    <PhaseButton label="EU" color="#4A90D9" />
    <PhaseButton label="Korea" color="#56B870" />
    <PhaseButton label="China" color="#E8943A" />
    <PhaseButton label="Japan" color="#D64545" />
  </div>
);

export const ActiveColored = () => (
  <div style={{ display: 'flex', gap: 8 }}>
    <PhaseButton label="EU" color="#4A90D9" active />
    <PhaseButton label="Korea" color="#56B870" />
  </div>
);
