import { CatTag } from 'ets-editorial';

export const CategoryPalette = () => (
  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
    <CatTag label="MRV" color="#63b3ed" />
    <CatTag label="オフセット" color="#d69e2e" />
    <CatTag label="国際制度" color="#805ad5" />
    <CatTag label="基本制度" color="#48bb78" />
    <CatTag label="市場取引" color="#ed8936" />
    <CatTag label="業種" color="#e53e3e" />
    <CatTag label="配額分配" color="#38b2ac" />
  </div>
);
