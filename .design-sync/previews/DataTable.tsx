import { DataTable, CountryBadge, CatTag } from 'ets-editorial';

export const ComparisonTable = () => (
  <DataTable
    headers={[
      'Metric',
      <CountryBadge key="eu" flag="🇪🇺" label="EU" color="#4A90D9" />,
      <CountryBadge key="kr" flag="🇰🇷" label="Korea" color="#56B870" />,
      <CountryBadge key="cn" flag="🇨🇳" label="China" color="#E8943A" />,
      <CountryBadge key="jp" flag="🇯🇵" label="Japan" color="#D64545" />,
    ]}
    rows={[
      ['Launch year', '2005', '2015', '2021', '2023'],
      ['Coverage of national emissions', '40%', '68%', '60%', '60%*'],
      ['Covered entities', '~11,000', '~680', '~3,500', '~747'],
      ['Cap type', 'Absolute, declining', 'Absolute', 'Intensity-based', 'Voluntary → mandatory'],
      ['Primary allocation', 'Auction + benchmark', 'Benchmark + GF', 'Benchmark (free)', 'Grandfathering'],
    ]}
  />
);

export const TerminologyRows = () => (
  <DataTable
    headers={['EN', 'JA', 'KO', 'ZH', 'Category']}
    rows={[
      ['Allowance', '排出枠', '배출권', '配额', <CatTag key="c1" label="基本制度" color="#48bb78" />],
      ['Benchmark', 'ベンチマーク', '벤치마크', '基准线', <CatTag key="c2" label="配額分配" color="#38b2ac" />],
      ['MRV', '測定・報告・検証', '측정·보고·검증', '监测报告核查', <CatTag key="c3" label="MRV" color="#63b3ed" />],
      ['Carbon leakage', '炭素リーケージ', '탄소 누출', '碳泄漏', <CatTag key="c4" label="国際制度" color="#805ad5" />],
    ]}
  />
);
