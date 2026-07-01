import type { ReactNode } from 'react';

export interface DataTableProps {
  /** Header cells — strings or nodes (e.g. CountryBadge per country column) */
  headers: ReactNode[];
  /** Body rows; cells may be strings or nodes (CatTag, CountryBadge, …) */
  rows: ReactNode[][];
  /** Wrap in the width-capped, horizontally scrollable container (default true) */
  scrollable?: boolean;
}

/**
 * The dashboard's data table: dark sticky header in the accent color, hairline
 * row borders, hover row highlight. Used for system comparison matrices and
 * the 4-language terminology table.
 */
export function DataTable({ headers, rows, scrollable = true }: DataTableProps) {
  const table = (
    <table className="ets-table">
      <thead>
        <tr>
          {headers.map((h, i) => (
            <th key={i}>{h}</th>
          ))}
        </tr>
      </thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            {r.map((c, j) => (
              <td key={j}>{c}</td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
  return scrollable ? <div className="term-table-wrap">{table}</div> : table;
}
