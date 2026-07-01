import { TopNav } from 'ets-editorial';

export const FullNav = () => (
  <TopNav
    brand="ETS Convergence Dashboard"
    links={[
      { label: 'Overview', active: true },
      { label: 'Compare' },
      { label: 'CBAM' },
      { label: 'Rosetta' },
    ]}
    langs={['EN', 'JA', 'KO', 'ZH']}
    activeLang="EN"
  />
);

export const NoLangSwitcher = () => (
  <TopNav
    brand="Carbon Market Monitor"
    links={[{ label: 'Prices', active: true }, { label: 'Auctions' }, { label: 'Policy' }]}
  />
);
