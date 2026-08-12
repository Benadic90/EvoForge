import { useEffect, useRef, useState, useCallback } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

export default function KnowledgeGraph({ data }) {
  const fgRef = useRef();
  const [dimensions, setDimensions] = useState({ width: 800, height: 600 });
  const containerRef = useRef();

  useEffect(() => {
    if (containerRef.current) {
      setDimensions({
        width: containerRef.current.offsetWidth,
        height: containerRef.current.offsetHeight
      });
    }
    
    // Zoom out slightly to fit
    if (fgRef.current) {
      setTimeout(() => {
        fgRef.current.d3Force('charge').strength(-600);
        fgRef.current.d3Force('link').distance(100);
      }, 500);
    }
  }, [data]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const label = node.id;
    const fontSize = 12 / globalScale;
    const radius = 12;
    
    const isCyan = node.group === 1;
    const color = isCyan ? '#00f0ff' : '#b026ff';
    const bgColor = '#0d111a';
    
    // Outer Glow
    ctx.shadowBlur = 25 * globalScale;
    ctx.shadowColor = color;
    
    // Brain Cell Outer Ring
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    
    // Reset shadow for inner elements
    ctx.shadowBlur = 0;
    
    // Inner Dark Core
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius - 3, 0, 2 * Math.PI, false);
    ctx.fillStyle = bgColor;
    ctx.fill();
    
    // Bright Center Nucleus
    ctx.beginPath();
    ctx.arc(node.x, node.y, radius - 6, 0, 2 * Math.PI, false);
    ctx.fillStyle = color;
    ctx.fill();
    
    // Draw text label
    ctx.font = `${fontSize}px Inter`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillStyle = '#ffffff';
    ctx.fillText(label, node.x, node.y + radius + 10 + fontSize);
  }, []);

  const paintLink = useCallback((link, ctx, globalScale) => {
     // Custom link text could go here, but react-force-graph provides linkCanvasObject for text
     // We will use standard link rendering and just add text
  }, []);

  return (
    <div className="glass-panel graph-container" ref={containerRef} style={{ width: '100%', height: '100%', border: 'none', background: 'transparent', backdropFilter: 'none' }}>
      
      {/* Background Grid and Axes matching the mockup */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
                    backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.05) 1px, transparent 1px)',
                    backgroundSize: '80px 80px', backgroundPosition: 'center center', zIndex: 1 }}>
        
        {/* Y Axis */}
        <div style={{ position: 'absolute', left: 40, top: 40, bottom: 40, width: 1, background: 'rgba(255,255,255,0.2)' }}>
           <div style={{ position: 'absolute', top: -5, left: -4, width: 0, height: 0, borderLeft: '4px solid transparent', borderRight: '4px solid transparent', borderBottom: '6px solid rgba(255,255,255,0.4)' }}></div>
        </div>
        
        {/* X Axis */}
        <div style={{ position: 'absolute', left: 40, bottom: 40, right: 40, height: 1, background: 'rgba(255,255,255,0.2)' }}>
           <div style={{ position: 'absolute', right: -5, bottom: -4, width: 0, height: 0, borderTop: '4px solid transparent', borderBottom: '4px solid transparent', borderLeft: '6px solid rgba(255,255,255,0.4)' }}></div>
        </div>
      </div>

      {data && (
        <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 5 }}>
          <ForceGraph2D
            ref={fgRef}
            width={dimensions.width}
            height={dimensions.height}
            graphData={data}
            nodeCanvasObject={paintNode}
            nodePointerAreaPaint={(node, color, ctx) => {
              ctx.fillStyle = color;
              ctx.beginPath();
              ctx.arc(node.x, node.y, 16, 0, 2 * Math.PI, false);
              ctx.fill();
            }}
            linkCurvature={0.2}
            linkColor={(link) => {
               // Gradient-like color based on source node
               return link.source.group === 1 ? 'rgba(0, 240, 255, 0.4)' : 'rgba(176, 38, 255, 0.4)';
            }}
            linkWidth={2}
            linkDirectionalParticles={4}
            linkDirectionalParticleWidth={3}
            linkDirectionalParticleColor={(link) => link.source.group === 1 ? '#00f0ff' : '#b026ff'}
            linkCanvasObjectMode={() => 'after'}
            linkCanvasObject={(link, ctx, globalScale) => {
              if (!link.label) return;
              const MAX_FONT_SIZE = 4;
              const LABEL_NODE_MARGIN = 20;
              const start = link.source;
              const end = link.target;
              
              if (typeof start !== 'object' || typeof end !== 'object') return;

              // Calculate text position along the curve (approximation)
              const textPos = Object.assign(...['x', 'y'].map(c => ({
                [c]: start[c] + (end[c] - start[c]) / 2 // middle point
              })));
              
              const fontSize = 10 / globalScale;
              ctx.font = `${fontSize}px Inter`;
              ctx.fillStyle = 'rgba(255, 255, 255, 0.6)';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              
              // Angle for text rotation
              let angle = Math.atan2(end.y - start.y, end.x - start.x);
              if (angle > Math.PI / 2 || angle < -Math.PI / 2) {
                 angle += Math.PI;
              }
              
              ctx.save();
              ctx.translate(textPos.x, textPos.y);
              ctx.rotate(angle);
              ctx.fillText(link.label, 0, -10 / globalScale); // Offset slightly above the line
              ctx.restore();
            }}
            backgroundColor="transparent"
          />
        </div>
      )}
    </div>
  );
}
