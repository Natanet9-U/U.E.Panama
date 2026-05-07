import React from 'react';

function BarChartMock({ data = [], labels = [], color = '#7c3aed' }) {
  if (!data || data.length === 0) return <div className="h-full w-full flex items-center justify-center text-slate-400">Sin datos</div>;

  const max = Math.max(...data) || 1;

  return (
    <div className="flex h-full items-end gap-3">
      {data.map((d, i) => (
        <div key={i} className="flex-1">
          <div className="relative h-40 w-full">
            <div
              style={{ height: `${(d / max) * 100}%`, background: color }}
              className="rounded-t-md"
            />
          </div>
          <div className="mt-2 text-center text-xs text-slate-500">{labels[i] || `#${i + 1}`}</div>
        </div>
      ))}
    </div>
  );
}

export default BarChartMock;
