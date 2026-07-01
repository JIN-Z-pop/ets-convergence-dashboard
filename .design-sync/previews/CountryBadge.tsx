import { CountryBadge } from 'ets-editorial';

export const FourCountries = () => (
  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
    <CountryBadge flag="🇪🇺" label="EU" color="#4A90D9" />
    <CountryBadge flag="🇰🇷" label="Korea" color="#56B870" />
    <CountryBadge flag="🇨🇳" label="China" color="#E8943A" />
    <CountryBadge flag="🇯🇵" label="Japan" color="#D64545" />
  </div>
);

export const NoFlag = () => <CountryBadge label="EU ETS" color="#4A90D9" />;
