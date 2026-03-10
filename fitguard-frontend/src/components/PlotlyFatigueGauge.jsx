import React, { useEffect, useRef } from 'react';

const gaugeColor = (value) => {
  if (value >= 75) return '#ef4444';
  if (value >= 45) return '#f59e0b';
  return '#10b981';
};

const PlotlyFatigueGauge = ({ value = 0, title = 'Fatigue Score' }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    if (!chartRef.current || !window.Plotly) return;

    const safeValue = Math.max(0, Math.min(100, Number(value) || 0));
    const data = [
      {
        type: 'indicator',
        mode: 'gauge+number',
        value: safeValue,
        title: { text: title, font: { size: 15 } },
        gauge: {
          axis: { range: [0, 100], tickwidth: 1, tickcolor: '#94a3b8' },
          bar: { color: gaugeColor(safeValue), thickness: 0.45 },
          bgcolor: '#ffffff',
          borderwidth: 1,
          bordercolor: '#e2e8f0',
          steps: [
            { range: [0, 40], color: '#d1fae5' },
            { range: [40, 75], color: '#fef3c7' },
            { range: [75, 100], color: '#fee2e2' }
          ]
        }
      }
    ];

    const layout = {
      margin: { t: 40, b: 20, l: 15, r: 15 },
      paper_bgcolor: 'rgba(0,0,0,0)',
      font: { color: '#1e293b', family: 'ui-sans-serif, system-ui' }
    };

    window.Plotly.react(chartRef.current, data, layout, {
      displayModeBar: false,
      responsive: true
    });

    return () => {
      if (window.Plotly && chartRef.current) {
        window.Plotly.purge(chartRef.current);
      }
    };
  }, [title, value]);

  if (!window.Plotly) {
    return (
      <div className="h-72 flex items-center justify-center text-slate-400">
        Plotly is loading...
      </div>
    );
  }

  return <div ref={chartRef} className="h-72 w-full" />;
};

export default PlotlyFatigueGauge;

