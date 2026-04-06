"use client";

import { useEffect, useRef, useCallback, useState } from "react";
import * as d3 from "d3";
import type { AccusationNode, AccusationEdge } from "@/types/analytics";
import { getProfileColor, getProfileLabel } from "./profileColors";

interface AccusationGraphProps {
  nodes: AccusationNode[];
  edges: AccusationEdge[];
}

interface SimNode extends d3.SimulationNodeDatum {
  id: string;
  profile: string;
  count: number;
}

interface SimLink extends d3.SimulationLinkDatum<SimNode> {
  weight: number;
}

export default function AccusationGraph({
  nodes,
  edges,
}: AccusationGraphProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const [tooltip, setTooltip] = useState<{
    x: number;
    y: number;
    content: string;
  } | null>(null);

  const render = useCallback(() => {
    const svg = svgRef.current;
    if (!svg || !nodes.length) return;

    const rect = svg.getBoundingClientRect();
    const width = rect.width || 600;
    const height = rect.height || 400;

    const d3Svg = d3.select(svg);
    d3Svg.selectAll("*").remove();

    // Build simulation data (deep copy to avoid D3 mutating props)
    const simNodes: SimNode[] = nodes.map((n) => ({
      id: n.id,
      profile: n.profile,
      count: n.count,
    }));

    const nodeMap = new Map(simNodes.map((n) => [n.id, n]));

    const simLinks: SimLink[] = edges
      .filter((e) => nodeMap.has(e.source) && nodeMap.has(e.target))
      .map((e) => ({
        source: e.source,
        target: e.target,
        weight: e.weight,
      }));

    const maxWeight = Math.max(1, ...simLinks.map((l) => l.weight));
    const maxCount = Math.max(1, ...simNodes.map((n) => n.count));

    // Scales
    const linkWidthScale = d3
      .scaleLinear()
      .domain([0, maxWeight])
      .range([1, 8]);

    const nodeRadiusScale = d3
      .scaleSqrt()
      .domain([0, maxCount])
      .range([8, 28]);

    // Simulation
    const simulation = d3
      .forceSimulation(simNodes)
      .force(
        "link",
        d3
          .forceLink<SimNode, SimLink>(simLinks)
          .id((d) => d.id)
          .distance(100),
      )
      .force("charge", d3.forceManyBody().strength(-200))
      .force("center", d3.forceCenter(width / 2, height / 2))
      .force("collision", d3.forceCollide().radius((d) => nodeRadiusScale((d as SimNode).count) + 4));

    const g = d3Svg.append("g");

    // Zoom
    const zoom = d3
      .zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.3, 4])
      .on("zoom", (event) => {
        g.attr("transform", event.transform);
      });
    d3Svg.call(zoom);

    // Links
    const link = g
      .append("g")
      .selectAll("line")
      .data(simLinks)
      .join("line")
      .attr("stroke", "#2a2a3a")
      .attr("stroke-opacity", 0.6)
      .attr("stroke-width", (d) => linkWidthScale(d.weight));

    // Nodes
    const node = g
      .append("g")
      .selectAll("circle")
      .data(simNodes)
      .join("circle")
      .attr("r", (d) => nodeRadiusScale(d.count))
      .attr("fill", (d) => getProfileColor(d.profile))
      .attr("stroke", "#0c0c14")
      .attr("stroke-width", 2)
      .attr("cursor", "grab")
      .call(
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        d3
          .drag<SVGCircleElement, SimNode>()
          .on("start", (event, d) => {
            if (!event.active) simulation.alphaTarget(0.3).restart();
            d.fx = d.x;
            d.fy = d.y;
          })
          .on("drag", (event, d) => {
            d.fx = event.x;
            d.fy = event.y;
          })
          .on("end", (event, d) => {
            if (!event.active) simulation.alphaTarget(0);
            d.fx = null;
            d.fy = null;
          // eslint-disable-next-line @typescript-eslint/no-explicit-any
          }) as any,
      );

    // Labels
    const label = g
      .append("g")
      .selectAll("text")
      .data(simNodes)
      .join("text")
      .text((d) => getProfileLabel(d.profile))
      .attr("font-size", 11)
      .attr("font-family", "Nunito Sans, sans-serif")
      .attr("fill", "#e2dfd8")
      .attr("text-anchor", "middle")
      .attr("dy", (d) => nodeRadiusScale(d.count) + 14)
      .attr("pointer-events", "none");

    // Hover interactions
    node
      .on("mouseenter", function (event, d) {
        // Highlight connected edges
        link
          .attr("stroke-opacity", (l) => {
            const src = typeof l.source === "object" ? (l.source as SimNode).id : l.source;
            const tgt = typeof l.target === "object" ? (l.target as SimNode).id : l.target;
            return src === d.id || tgt === d.id ? 1 : 0.1;
          })
          .attr("stroke", (l) => {
            const src = typeof l.source === "object" ? (l.source as SimNode).id : l.source;
            const tgt = typeof l.target === "object" ? (l.target as SimNode).id : l.target;
            return src === d.id || tgt === d.id
              ? getProfileColor(d.profile)
              : "#2a2a3a";
          });

        node.attr("opacity", (n) => (n.id === d.id ? 1 : 0.3));
        label.attr("opacity", (n) => (n.id === d.id ? 1 : 0.3));

        d3.select(this).attr("stroke", getProfileColor(d.profile)).attr("stroke-width", 3);

        setTooltip({
          x: event.offsetX,
          y: event.offsetY,
          content: `${getProfileLabel(d.profile)} — ${d.count} accusations`,
        });
      })
      .on("mouseleave", function () {
        link.attr("stroke-opacity", 0.6).attr("stroke", "#2a2a3a");
        node.attr("opacity", 1);
        label.attr("opacity", 1);
        d3.select(this).attr("stroke", "#0c0c14").attr("stroke-width", 2);
        setTooltip(null);
      });

    // Tick
    simulation.on("tick", () => {
      link
        .attr("x1", (d) => (d.source as SimNode).x!)
        .attr("y1", (d) => (d.source as SimNode).y!)
        .attr("x2", (d) => (d.target as SimNode).x!)
        .attr("y2", (d) => (d.target as SimNode).y!);

      node.attr("cx", (d) => d.x!).attr("cy", (d) => d.y!);
      label.attr("x", (d) => d.x!).attr("y", (d) => d.y!);
    });

    return () => {
      simulation.stop();
    };
  }, [nodes, edges]);

  useEffect(() => {
    const cleanup = render();
    return cleanup;
  }, [render]);

  // Resize observer
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    const observer = new ResizeObserver(() => render());
    observer.observe(svg);
    return () => observer.disconnect();
  }, [render]);

  return (
    <div className="relative w-full" style={{ minHeight: 400 }}>
      <svg
        ref={svgRef}
        className="w-full"
        style={{ height: 400, background: "transparent" }}
      />
      {tooltip && (
        <div
          className="pointer-events-none absolute z-tooltip rounded-md px-3 py-2 text-xs"
          style={{
            left: tooltip.x + 12,
            top: tooltip.y - 8,
            backgroundColor: "#181824",
            border: "1px solid #2a2a3a",
            color: "#e2dfd8",
          }}
        >
          {tooltip.content}
        </div>
      )}
    </div>
  );
}
