import { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';
import { Search, Filter, Maximize } from 'lucide-react';

export default function NetworkView() {
  const fgRef = useRef();
  const containerRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

  const data = {
    nodes: [
      { id: 'Internet', group: 0, val: 2 },
      { id: 'API Gateway', group: 1, val: 3 },
      { id: 'WebSocket Server', group: 1, val: 2 },
      { id: 'Frontend UI', group: 2, val: 2 },
      { id: 'Orchestrator', group: 3, val: 4 },
      { id: 'Dev Agent Pool', group: 3, val: 3 },
      { id: 'Security Scanner', group: 3, val: 3 },
      { id: 'Vector DB', group: 4, val: 3 },
      { id: 'SQLite Relational', group: 4, val: 3 }
    ],
    links: [
      { source: 'Internet', target: 'Frontend UI', label: 'HTTPS' },
      { source: 'Frontend UI', target: 'API Gateway', label: 'REST' },
      { source: 'Frontend UI', target: 'WebSocket Server', label: 'WSS' },
      { source: 'API Gateway', target: 'Orchestrator', label: 'gRPC' },
      { source: 'WebSocket Server', target: 'Orchestrator', label: 'gRPC' },
      { source: 'Orchestrator', target: 'Dev Agent Pool', label: 'Task Stream' },
      { source: 'Orchestrator', target: 'Security Scanner', label: 'Audit Stream' },
      { source: 'Dev Agent Pool', target: 'Vector DB', label: 'Embeddings' },
      { source: 'Security Scanner', target: 'Vector DB', label: 'Signatures' },
      { source: 'Orchestrator', target: 'SQLite Relational', label: 'State' }
    ]
  };

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight
      });
    }
    if (fgRef.current) {
      setTimeout(() => {
        fgRef.current.d3Force('charge').strength(-800);
        fgRef.current.d3Force('link').distance(150);
      }, 500);
    }
  }, []);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const label = node.id;
    const fontSize = 12 / globalScale;
    const radius = node.val * 3;
    
    // Group Colors
    const colors = ['#ffffff', '#00f0ff', '#00ffaa', '#b026ff', '#ff3366'];
    const color = colors[node.group] || '#00f0ff';
    
    ctx.shadowBlur = 20 * globalScale;
    ctx.shadowColor = color;
    
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    
    ctx.shadowBlur = 0;
    
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius - 2, 0, 2 * Math.PI, false);
    ctx.fillStyle = '#0d111a';
    ctx.fill();
    
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius - 4, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    
    ctx.font = `${fontSize}px Inter`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(label, node.x, node.y + radius + 10 + fontSize);
  }, []);

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <h1 className="dashboard-title" style={{ marginBottom: '24px' }}>System Architecture & Network Topology</h1>
      
      <div className="glass-panel" style={{ flex: 1, position: 'relative', overflow: 'hidden' }} ref={containerRef}>
        <div style={{ position: 'absolute', top: 20, left: 20, right: 20, zIndex: 10, display: 'flex', gap: '12px' }}>
           <div className="search-bar" style={{ width: '100%', maxWidth: '300px', background: 'rgba(255,255,255,0.02)' }}>
              <Search size={14} color="var(--text-muted)" />
              <input type="text" placeholder="Search nodes..." />
           </div>
           <div className="search-bar" style={{ width: 'auto', background: 'rgba(255,255,255,0.02)', gap: '6px', cursor: 'pointer' }}>
              <Filter size={14} color="var(--text-muted)" />
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Filter Layers</span>
           </div>
           <div className="search-bar" style={{ width: 'auto', background: 'rgba(255,255,255,0.02)', gap: '6px', cursor: 'pointer', marginLeft: 'auto' }}>
              <Maximize size={14} color="var(--text-muted)" />
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Fullscreen</span>
           </div>
        </div>

        {/* High-tech grid background specific to network view */}
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
                      backgroundImage: 'linear-gradient(rgba(0, 240, 255, 0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(0, 240, 255, 0.04) 1px, transparent 1px)',
                      backgroundSize: '100px 100px', backgroundPosition: 'center center', zIndex: 1 }}>
        </div>

        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 5 }}>
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={data}
            nodeCanvasObject={paintNode}
            linkCurvature={0.15}
            linkColor={() => 'rgba(255, 255, 255, 0.15)'}
            linkWidth={1.5}
            linkDirectionalParticles={4}
            linkDirectionalParticleWidth={3}
            linkDirectionalParticleColor={(link) => {
              const colors = ['#ffffff', '#00f0ff', '#00ffaa', '#b026ff', '#ff3366'];
              return colors[link.source.group] || '#00f0ff';
            }}
            linkCanvasObjectMode={() => 'after'}
            linkCanvasObject={(link, ctx, globalScale) => {
              if (!link.label) return;
              const start = link.source;
              const end = link.target;
              if (typeof start !== 'object' || typeof end !== 'object') return;
              const textPos = Object.assign(...['x', 'y'].map(c => ({
                [c]: start[c] + (end[c] - start[c]) / 2
              })));
              const fontSize = 10 / globalScale;
              ctx.font = `${fontSize}px Inter`;
              ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              let angle = Math.atan2(end.y - start.y, end.x - start.x);
              if (angle > Math.PI / 2 || angle < -Math.PI / 2) angle += Math.PI;
              ctx.save();
              ctx.translate(textPos.x, textPos.y);
              ctx.rotate(angle);
              ctx.fillText(link.label, 0, -10 / globalScale);
              ctx.restore();
            }}
            backgroundColor="transparent"
          />
        </div>
      </div>
    </div>
  );
}
