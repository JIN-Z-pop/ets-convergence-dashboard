import { CatButton } from 'ets-editorial';

export const FilterRow = () => (
  <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
    <CatButton label="All" active />
    <CatButton label="MRV" />
    <CatButton label="基本制度" />
    <CatButton label="市場取引" />
    <CatButton label="配額分配" />
  </div>
);
