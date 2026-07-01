import { AxisItem } from 'ets-editorial';

export const ConvergenceList = () => (
  <div style={{ maxWidth: 560 }}>
    <AxisItem variant="convergence" title="Benchmark-based allocation">
      All four systems are shifting from grandfathering toward benchmarking.
    </AxisItem>
    <AxisItem variant="convergence" title="MRV standards">
      ISO 14064-aligned monitoring, reporting and verification is now the shared baseline.
    </AxisItem>
  </div>
);

export const DivergenceList = () => (
  <div style={{ maxWidth: 560 }}>
    <AxisItem variant="divergence" title="Carbon price levels">
      EU ~$79/t vs China ~$11/t — an order-of-magnitude gap persists into 2026.
    </AxisItem>
    <AxisItem variant="divergence" title="Cap stringency">
      Absolute declining caps (EU/Korea) vs intensity-based caps (China) vs voluntary phase-in (Japan).
    </AxisItem>
  </div>
);
