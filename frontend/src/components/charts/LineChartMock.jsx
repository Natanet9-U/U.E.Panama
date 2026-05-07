import React from 'react';

function LineChartMock({ data = [], labels = [] , color = '#4f46e5'}) {
  if (!data || data.length === 0) return <div className="h-full w-full flex items-center justify-center text-slate-400">Sin datos</div>;

  const width = 800;
  const height = 200;
  const padding = 20;

  const max = Math.max(...data);
  const min = Math.min(...data);
  const range = max - min || 1;

  const points = data.map((d, i) => {
    const x = padding + (i * (width - padding * 2)) / (data.length - 1 || 1);
    const y = padding + (1 - (d - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-full" preserveAspectRatio="none">
      <defs>
        <linearGradient id="g" x1="0" x2="0" y1="0" y2="1">
          <stop offset="0%" stopColor={color} stopOpacity="0.18" />
          <stop offset="100%" stopColor={color} stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x="0" y="0" width={width} height={height} fill="transparent" />
      <polyline fill="none" stroke={color} strokeWidth="2" points={points} strokeLinecap="round" strokeLinejoin="round" />
      {/* area */}
      <polygon points={`${points} ${width - padding},${height - padding} ${padding},${height - padding}`} fill="url(#g)" />
      {/* dots */}
      {data.map((d, i) => {
        const x = padding + (i * (width - padding * 2)) / (data.length - 1 || 1);
        const y = padding + (1 - (d - min) / range) * (height - padding * 2);
        return <circle key={i} cx={x} cy={y} r="3" fill={color} />;
      })}
    </svg>
  );
}

export default LineChartMock;
