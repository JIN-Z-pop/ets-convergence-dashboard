import { CardsGrid, KPICard } from 'ets-editorial';

export const FourCountries = () => (
  <CardsGrid>
    <KPICard
      flag="🇪🇺" name="EU" value="€72/t" sub="~$79/t (2026 avg)" color="#4A90D9"
      stats={[{ value: '40%', label: 'Coverage' }, { value: '~11,000', label: 'Entities' }, { value: '2005', label: 'Since' }]}
    />
    <KPICard
      flag="🇰🇷" name="Korea" value="₩13,679/t" sub="~$10/t (2026 avg)" color="#56B870"
      stats={[{ value: '68%', label: 'Coverage' }, { value: '~680', label: 'Entities' }, { value: '2015', label: 'Since' }]}
    />
    <KPICard
      flag="🇨🇳" name="China" value="¥79.4/t" sub="~$11/t (2026 avg)" color="#E8943A"
      stats={[{ value: '60%', label: 'Coverage' }, { value: '~3,500', label: 'Entities' }, { value: '2021', label: 'Since' }]}
    />
    <KPICard
      flag="🇯🇵" name="Japan" value="GX-ETS" sub="Phase 2 (2026-04~)" color="#D64545"
      stats={[{ value: '60%*', label: 'Coverage' }, { value: '~747', label: 'Entities' }, { value: '2023', label: 'Since' }]}
    />
  </CardsGrid>
);
