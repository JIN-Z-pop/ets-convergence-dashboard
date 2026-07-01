import { DashFooter } from 'ets-editorial';

export const Full = () => (
  <DashFooter
    credit="JIN-Z-pop and his merry AI brothers | Plotly.js"
    disclaimer="This tool is provided for research and educational purposes only. The authors make no warranties regarding accuracy, completeness, or fitness for any particular purpose, and accept no liability for any loss or damage arising from its use."
    lastUpdated="Data as of: 2026-04-21"
  />
);

export const CreditOnly = () => <DashFooter credit="JIN-Z-pop and his merry AI brothers" />;
