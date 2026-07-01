import { SearchBar, CatButton } from 'ets-editorial';

export const WithFilters = () => (
  <SearchBar placeholder="Search 47 ETS terms in 4 languages…">
    <CatButton label="All" active />
    <CatButton label="MRV" />
    <CatButton label="市場取引" />
    <CatButton label="配額分配" />
  </SearchBar>
);

export const InputOnly = () => <SearchBar placeholder="Search terms…" defaultValue="benchmark" />;
