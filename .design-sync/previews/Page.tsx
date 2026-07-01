import {
  Page,
  TopNav,
  PageHeader,
  CardsGrid,
  KPICard,
  AnalysisBox,
  DashFooter,
} from 'ets-editorial';

export const OverviewPage = () => (
  <Page>
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
    <PageHeader
      title="ETS Convergence Dashboard"
      subtitle="4-Country ETS Convergence & Divergence toward 2030"
    />
    <CardsGrid>
      <KPICard flag="🇪🇺" name="EU" value="€72/t" sub="~$79/t (2026 avg)" color="#4A90D9" />
      <KPICard flag="🇰🇷" name="Korea" value="₩13,679/t" sub="~$10/t (2026 avg)" color="#56B870" />
      <KPICard flag="🇨🇳" name="China" value="¥79.4/t" sub="~$11/t (2026 avg)" color="#E8943A" />
    </CardsGrid>
    <AnalysisBox title="About">
      <p>
        Four carbon markets, one destination: this dashboard tracks how the EU, Korean, Chinese and
        Japanese emission trading systems converge — and where they still diverge — on the road to 2030.
      </p>
    </AnalysisBox>
    <DashFooter credit="JIN-Z-pop and his merry AI brothers | Plotly.js" lastUpdated="Data as of: 2026-04-21" />
  </Page>
);
