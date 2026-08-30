import { useState, useEffect, useRef } from 'react';
import {
  HiOutlineChevronLeft,
  HiOutlineChevronRight,
  HiOutlineZoomIn,
  HiOutlineZoomOut,
  HiOutlineInformationCircle,
} from 'react-icons/hi';

/* Box color per verdict */
const BOX_COLORS = {
  correct:   { stroke: '#10b981', fill: 'rgba(16,185,129,0.12)', tag: '#10b981' },
  partial:   { stroke: '#f59e0b', fill: 'rgba(245,158,11,0.12)', tag: '#f59e0b' },
  incorrect: { stroke: '#ef4444', fill: 'rgba(239,68,68,0.12)',  tag: '#ef4444' },
  unanswered:{ stroke: '#64748b', fill: 'rgba(100,116,139,0.08)', tag: '#64748b' },
};

export default function AnswerSheetViewer({ pages, highlightBlocks, verdict, questionLabel }) {
  const canvasRef = useRef(null);
  const wrapRef = useRef(null);
  const imgRef = useRef(null);
  const [currentPage, setCurrentPage] = useState(1);
  const [zoom, setZoom] = useState(1.0);

  const pageData = pages.find((p) => p.page === currentPage);
  const colors = BOX_COLORS[verdict] || BOX_COLORS.incorrect;

  /* Load image whenever page changes */
  useEffect(() => {
    if (!pageData) return;
    const img = new Image();
    img.onload = () => {
      imgRef.current = img;
      draw();
    };
    img.src = `data:image/jpeg;base64,${pageData.b64}`;
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pageData?.b64]);

  /* Redraw when highlight, page, or zoom changes */
  useEffect(() => {
    if (imgRef.current) draw();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightBlocks, currentPage, zoom, verdict]);

  /* Auto-jump to first page that has a highlight */
  useEffect(() => {
    if (!highlightBlocks?.length) return;
    const firstPage = highlightBlocks[0]?.page;
    if (firstPage && firstPage !== currentPage) setCurrentPage(firstPage);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [highlightBlocks]);

  function draw() {
    const img = imgRef.current;
    const canvas = canvasRef.current;
    if (!img || !canvas) return;

    const w = img.naturalWidth * zoom;
    const h = img.naturalHeight * zoom;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext('2d');
    ctx.drawImage(img, 0, 0, w, h);

    /* Draw boxes for current page */
    const pageBlocks = (highlightBlocks || []).filter((b) => b.page === currentPage);
    pageBlocks.forEach((b) => {
      const x = b.left * zoom;
      const y = b.top * zoom;
      const bw = b.width * zoom;
      const bh = b.height * zoom;

      /* Fill + stroke */
      ctx.save();
      ctx.fillStyle = colors.fill;
      ctx.strokeStyle = colors.stroke;
      ctx.lineWidth = 2.5;
      ctx.fillRect(x, y, bw, bh);
      ctx.strokeRect(x, y, bw, bh);

      /* Tag label above box */
      if (questionLabel) {
        const tag = questionLabel;
        const pad = 5;
        const fontSize = Math.max(12, 13 * zoom);
        ctx.font = `bold ${fontSize}px Inter, sans-serif`;
        const tw = ctx.measureText(tag).width + pad * 2;
        const th = fontSize + pad * 2;
        ctx.fillStyle = colors.tag;
        const tx = x;
        const ty = Math.max(0, y - th - 2);
        ctx.beginPath();
        ctx.roundRect(tx, ty, tw, th, 4);
        ctx.fill();
        ctx.fillStyle = '#fff';
        ctx.fillText(tag, tx + pad, ty + th - pad - 1);
      }
      ctx.restore();
    });
  }

  const hasPrev = currentPage > 1;
  const hasNext = currentPage < pages.length;
  const pagesWithHighlight = new Set((highlightBlocks || []).map((b) => b.page));
  const zoomPct = Math.round(zoom * 100);

  return (
    <div className="asv-root">
      {/* Top bar: zoom + page nav */}
      <div className="asv-toolbar">
        <div className="asv-zoom-group">
          <button
            className="asv-icon-btn"
            onClick={() => setZoom((z) => Math.max(0.4, +(z - 0.2).toFixed(1)))}
            title="Zoom out"
          >
            <HiOutlineZoomOut />
          </button>
          <span className="asv-zoom-label">{zoomPct}%</span>
          <button
            className="asv-icon-btn"
            onClick={() => setZoom((z) => Math.min(3, +(z + 0.2).toFixed(1)))}
            title="Zoom in"
          >
            <HiOutlineZoomIn />
          </button>
        </div>

        <div className="asv-page-group">
          <button
            className="asv-icon-btn"
            onClick={() => setCurrentPage((p) => p - 1)}
            disabled={!hasPrev}
          >
            <HiOutlineChevronLeft />
          </button>
          <span className="asv-page-label">
            Page {currentPage} of {pages.length}
          </span>
          <button
            className="asv-icon-btn"
            onClick={() => setCurrentPage((p) => p + 1)}
            disabled={!hasNext}
          >
            <HiOutlineChevronRight />
          </button>
        </div>
      </div>

      {/* Multi-page notice */}
      {highlightBlocks?.length > 0 && pagesWithHighlight.size > 1 && (
        <div className="asv-notice">
          <HiOutlineInformationCircle />
          Answer spans {pagesWithHighlight.size} pages — use navigation to view all highlighted regions
        </div>
      )}

      {/* Canvas */}
      <div className="asv-canvas-wrap" ref={wrapRef}>
        {pageData ? (
          <canvas ref={canvasRef} className="asv-canvas" />
        ) : (
          <div className="asv-placeholder">
            Select a question to highlight its answer region
          </div>
        )}
      </div>

      {/* Page dots */}
      {pages.length > 1 && (
        <div className="asv-dots">
          {pages.map((p) => (
            <button
              key={p.page}
              className={[
                'asv-dot',
                currentPage === p.page ? 'asv-dot--active' : '',
                pagesWithHighlight.has(p.page) ? 'asv-dot--highlighted' : '',
              ].join(' ')}
              onClick={() => setCurrentPage(p.page)}
              title={`Page ${p.page}${pagesWithHighlight.has(p.page) ? ' (answer here)' : ''}`}
            />
          ))}
        </div>
      )}
    </div>
  );
}
