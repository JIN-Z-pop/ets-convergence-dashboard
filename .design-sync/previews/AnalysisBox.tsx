import { AnalysisBox } from 'ets-editorial';

export const WithTitle = () => (
  <AnalysisBox title="About this dashboard">
    <p>
      This dashboard visualizes the convergence and divergence of Emission Trading Systems (ETS)
      across four major economies — EU, Korea, China, and Japan — as they approach 2030.
    </p>
    <p>
      Navigate using the top bar to explore system comparisons, allocation evolution, CBAM impacts,
      convergence mapping, and a 4-language ETS terminology reference.
    </p>
  </AnalysisBox>
);

export const WithCode = () => (
  <AnalysisBox title="Banking rules differ sharply">
    <p>
      Korea caps carryover at <code>NS × 5</code> (net sales times five), China at{' '}
      <code>100K + NS × 1.5</code>, while the EU allows unlimited banking since Phase 2.
    </p>
  </AnalysisBox>
);
