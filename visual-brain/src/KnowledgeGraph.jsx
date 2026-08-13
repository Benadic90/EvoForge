import { useEffect, useRef, useState, useCallback, useMemo } from 'react';
import ForceGraph2D from 'react-force-graph-2d';

const ICONS = {
  person: new Path2D('M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'),
  database: new Path2D('M12 3c-4.97 0-9 1.61-9 3.6v10.8c0 1.99 4.03 3.6 9 3.6s9-1.61 9-3.6V6.6C21 4.61 16.97 3 12 3zm0 15.6c-3.69 0-7-1.12-7-2.6v-2.31c1.88.94 4.3 1.51 7 1.51 2.7 0 5.12-.57 7-1.51V16c0 1.48-3.31 2.6-7 2.6zM12 9.4c-2.7 0-5.12-.57-7-1.51V6.6c0 1.48 3.31 2.6 7 2.6s7-1.12 7-2.6v1.29c-1.88.94-4.3 1.51-7 1.51z'),
  shield: new Path2D('M12 1L3 5v6c0 5.55 3.84 10.74 9 12 5.16-1.26 9-6.45 9-12V5l-9-4zm0 10.99h7c-.53 4.12-3.28 7.79-7 8.94V12H5V6.3l7-3.11v8.8z'),
  gear: new Path2D('M19.14,12.94c0.04-0.3,0.06-0.61,0.06-0.94c0-0.32-0.02-0.64-0.06-0.94l2.03-1.58c0.18-0.14,0.23-0.41,0.12-0.61 l-1.92-3.32c-0.12-0.22-0.37-0.29-0.59-0.22l-2.39,0.96c-0.5-0.38-1.03-0.7-1.62-0.94L14.4,2.81c-0.04-0.24-0.24-0.41-0.48-0.41 h-3.84c-0.24,0-0.43,0.17-0.47,0.41L9.25,5.35C8.66,5.59,8.12,5.92,7.63,6.29L5.24,5.33c-0.22-0.08-0.47,0-0.59,0.22L2.73,8.87 C2.62,9.08,2.66,9.34,2.86,9.48l2.03,1.58C4.84,11.36,4.8,11.69,4.8,12s0.02,0.64,0.06,0.94l-2.03,1.58 c-0.18,0.14-0.23,0.41-0.12,0.61l1.92,3.32c0.12,0.22,0.37,0.29,0.59,0.22l2.39-0.96c0.5,0.38,1.03,0.7,1.62,0.94l0.36,2.54 c0.05,0.24,0.24,0.41,0.48,0.41h3.84c0.24,0,0.43-0.17,0.47-0.41l0.36-2.54c0.59-0.24,1.13-0.56,1.62-0.94l2.39,0.96 c0.22,0.08,0.47,0,0.59-0.22l1.92-3.32c0.12-0.22,0.07-0.49-0.12-0.61L19.14,12.94z M12,15.6c-1.98,0-3.6-1.62-3.6-3.6 s1.62-3.6,3.6-3.6s3.6,1.62,3.6,3.6S13.98,15.6,12,15.6z'),
  briefcase: new Path2D('M20 6h-4V4c0-1.11-.89-2-2-2h-4c-1.11 0-2 .89-2 2v2H4c-1.11 0-1.99.89-1.99 2L2 19c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V8c0-1.11-.89-2-2-2zm-6 0h-4V4h4v2z'),
  python: new Path2D('M12,2C6.48,2,2,6.48,2,12s4.48,10,10,10s10-4.48,10-10S17.52,2,12,2z M12,17c-2.76,0-5-2.24-5-5s2.24-5,5-5s5,2.24,5,5 S14.76,17,12,17z'),
  default: new Path2D('M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2z')
};

const getIconForNode = (title, id) => {
  const searchStr = (title || id || "").toLowerCase();
  if (searchStr.includes('agent') || searchStr.includes('developer') || searchStr.includes('qa') || searchStr.includes('reviewer')) return ICONS.person;
  if (searchStr.includes('memory') || searchStr.includes('data')) return ICONS.database;
  if (searchStr.includes('sec')) return ICONS.shield;
  if (searchStr.includes('logic') || searchStr.includes('api') || searchStr.includes('core')) return ICONS.gear;
  if (searchStr.includes('codebase')) return ICONS.briefcase;
  if (searchStr.includes('python')) return ICONS.python;
  return ICONS.person;
};

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
    
    if (fgRef.current) {
      setTimeout(() => {
        // Increase repulsion for a more spacious graph
        fgRef.current.d3Force('charge').strength(-1000);
        
        // Vary link distance deterministically to break the perfect circular layout
        fgRef.current.d3Force('link').distance(link => {
            const idStr = (link.target.id || link.source.id || "").toString();
            // Simple hash to generate a pseudo-random distance between 100 and 300
            let hash = 0;
            for (let i = 0; i < idStr.length; i++) {
                hash = idStr.charCodeAt(i) + ((hash << 5) - hash);
            }
            const rand = Math.abs(hash) % 200;
            return 100 + rand;
        });
      }, 500);
    }
  }, [data]);

  const paintNode = useCallback((node, ctx, globalScale) => {
    const label = node.title || node.id;
    const fontSize = 12 / globalScale;
    const radius = 16;
    
    // Core/Agents/Data -> Cyan, Logic/API/Python -> Purple
    const searchStr = (label).toLowerCase();
    const isPurple = searchStr.includes('logic') || searchStr.includes('api') || searchStr.includes('python');
    const color = isPurple ? '#9e47ff' : '#00e5ff';
    const darkBg = '#0b111e';
    
    // Generate a deterministic small rotation angle based on the ID for the "messy" look
    let hash = 0;
    const idStr = (node.id || "").toString();
    for (let i = 0; i < idStr.length; i++) {
        hash = idStr.charCodeAt(i) + ((hash << 5) - hash);
    }
    const angle = ((Math.abs(hash) % 30) - 15) * (Math.PI / 180); // between -15 and 15 degrees
    
    ctx.save();
    ctx.translate(node.x, node.y);
    ctx.rotate(angle);
    
    // Outer Glow
    ctx.shadowBlur = 30 * globalScale;
    ctx.shadowColor = color;
    
    // Draw "messy" non-circular block (rounded rectangle)
    const size = 32;
    const boxRadius = 4;
    
    ctx.beginPath();
    ctx.roundRect(-size/2, -size/2, size, size, boxRadius);
    ctx.fillStyle = color;
    ctx.fill();
    ctx.shadowBlur = 0; // Turn off shadow for inner drawing
    
    // Inner dark block
    ctx.beginPath();
    ctx.roundRect(-size/2 + 2, -size/2 + 2, size - 4, size - 4, boxRadius - 1);
    ctx.fillStyle = darkBg;
    ctx.fill();
    
    // Draw SVG Icon in the center
    const iconPath = getIconForNode(node.title, node.id);
    const iconScale = 1.0; 
    
    ctx.save();
    // Translate to top-left of the icon box (assume 24x24 viewBox)
    ctx.translate(-12 * iconScale, -12 * iconScale);
    ctx.scale(iconScale, iconScale);
    ctx.fillStyle = color;
    ctx.fill(iconPath);
    ctx.restore();
    
    ctx.restore(); // restore rotation
    
    // Draw text label below the node (unrotated)
    ctx.font = `500 ${fontSize}px "Inter", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'top';
    ctx.fillStyle = '#e2e8f0';
    ctx.fillText(label, node.x, node.y + (size/2) + 6);
  }, []);

  return (
    <div className="glass-panel graph-container" ref={containerRef} style={{ width: '100%', height: '100%', border: 'none', background: 'transparent', backdropFilter: 'none' }}>
      
      {/* Background Grid matching the mockup */}
      <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, pointerEvents: 'none',
                    backgroundImage: 'linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px)',
                    backgroundSize: '100px 100px', backgroundPosition: 'center center', zIndex: 1 }}>
        
        {/* Sub-grid for axes context */}
        <div style={{ position: 'absolute', left: '10%', top: '5%', bottom: '10%', width: 1, background: 'rgba(255,255,255,0.15)' }}>
           <div style={{ position: 'absolute', top: -10, left: -4, width: 0, height: 0, borderLeft: '4px solid transparent', borderRight: '4px solid transparent', borderBottom: '10px solid rgba(255,255,255,0.3)' }}></div>
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
            nodeRelSize={16}
            
            // Curved links like the design
            linkCurvature={0.25}
            linkColor={(link) => {
               const searchStr = (link.source.title || link.source.id || "").toLowerCase();
               const isPurple = searchStr.includes('logic') || searchStr.includes('api') || searchStr.includes('python');
               return isPurple ? '#9e47ff' : '#00e5ff';
            }}
            linkWidth={1.5}
            
            // Draw arrows at the end of the links
            linkDirectionalArrowLength={6}
            linkDirectionalArrowRelPos={1}
            linkDirectionalArrowColor={(link) => {
               const searchStr = (link.source.title || link.source.id || "").toLowerCase();
               const isPurple = searchStr.includes('logic') || searchStr.includes('api') || searchStr.includes('python');
               return isPurple ? '#9e47ff' : '#00e5ff';
            }}

            // Render curved text labels on the links
            linkCanvasObjectMode={() => 'after'}
            linkCanvasObject={(link, ctx, globalScale) => {
              if (!link.label) return;
              const start = link.source;
              const end = link.target;
              if (typeof start !== 'object' || typeof end !== 'object') return;

              // Calculate control point for quadratic bezier curve (curvature=0.25)
              const dx = end.x - start.x;
              const dy = end.y - start.y;
              const len = Math.sqrt(dx * dx + dy * dy);
              if (len === 0) return;
              
              // Find midpoint
              const midX = start.x + dx / 2;
              const midY = start.y + dy / 2;
              
              // Find normal vector
              const normX = -dy / len;
              const normY = dx / len;
              
              // Find curve offset based on length and curvature
              // The curvature of 0.25 means the control point is offset by 25% of the distance
              const offset = len * 0.25;
              const ctrlX = midX + normX * offset;
              const ctrlY = midY + normY * offset;
              
              // Evaluate bezier curve at t=0.5 to find the exact midpoint of the curve
              const textX = 0.25 * start.x + 0.5 * ctrlX + 0.25 * end.x;
              const textY = 0.25 * start.y + 0.5 * ctrlY + 0.25 * end.y;

              const fontSize = 10 / globalScale;
              ctx.font = `${fontSize}px Inter`;
              ctx.fillStyle = 'rgba(255, 255, 255, 0.7)';
              ctx.textAlign = 'center';
              ctx.textBaseline = 'middle';
              
              // Calculate tangent angle at t=0.5
              const tanX = ctrlX - 0.5 * start.x - 0.5 * end.x + end.x - start.x;
              const tanY = ctrlY - 0.5 * start.y - 0.5 * end.y + end.y - start.y;
              let angle = Math.atan2(tanY, tanX);
              
              // Ensure text is readable (not upside down)
              if (angle > Math.PI / 2 || angle < -Math.PI / 2) {
                 angle += Math.PI;
              }
              
              ctx.save();
              ctx.translate(textX, textY);
              ctx.rotate(angle);
              ctx.fillText(link.label, 0, -6 / globalScale); // Float slightly above the line
              ctx.restore();
            }}
            backgroundColor="transparent"
          />
        </div>
      )}
    </div>
  );
}
