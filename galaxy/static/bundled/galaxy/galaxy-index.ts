import { exportToHtml } from "#core:utils/globals";

import cytoscape from "cytoscape";
import d3Force, { type D3ForceLayoutOptions } from "cytoscape-d3-force";

cytoscape.use(d3Force);

interface GalaxyConfig {
  nodeId: number;
  dataUrl: string;
}

async function getGraphData(dataUrl: string) {
  const response = await fetch(dataUrl);
  if (!response.ok) {
    return [];
  }

  const content = await response.json();
  const nodes = content.nodes.map((node, i) => {
    return {
      group: "nodes",
      data: {
        id: node.id,
        name: node.name,
        mass: node.mass,
      },
    };
  });

  const edges = content.links.map((link) => {
    return {
      group: "edges",
      data: {
        id: `edge_${link.source}_${link.value}`,
        source: link.source,
        target: link.target,
        value: link.value,
      },
    };
  });

  return { nodes: nodes, edges: edges };
}

exportToHtml("loadGalaxy", async (config: GalaxyConfig) => {
  const graphDiv = document.getElementById("3d-graph");
  const elements = await getGraphData(config.dataUrl);
  const cy = cytoscape({
    container: graphDiv,
    elements: elements,
    style: [
      {
        selector: "node",
        style: {
          label: "data(name)",
          "background-color": "red",
        },
      },
      {
        selector: ".focused",
        style: {
          "border-width": "5px",
          "border-style": "solid",
          "border-color": "black",
          "target-arrow-color": "black",
          "line-color": "black",
        },
      },
      {
        selector: "edge",
        style: {
          width: 0.1,
        },
      },
      {
        selector: ".direct",
        style: {
          width: "5px",
          "line-color": "red",
        },
      },
    ],
    layout: {
      name: "d3-force",
      animate: true,
      fit: false,
      ungrabifyWhileSimulating: true,
      fixedAfterDragging: true,

      linkId: (node) => {
        return node.id;
      },

      linkDistance: (link) => {
        return elements.nodes.length * 10;
      },

      linkStrength: (link) => {
        return 1 / Math.max(1, link?.value);
      },

      linkIterations: 10,

      manyBodyStrength: (node) => {
        return node?.mass;
      },

      // manyBodyDistanceMin: 500,
      collideRadius: () => {
        return 50;
      },

      ready: (e) => {
        // Center on current user node at the start of the simulation
        // Color all direct paths from that citizen to it's neighbor
        const citizen = e.cy.nodes(`#${config.nodeId}`)[0];
        citizen.addClass("focused");
        citizen.connectedEdges().addClass("direct");
        e.cy.center(citizen);
      },

      tick: () => {
        // Center on current user node during simulation
        const citizen = cy.nodes(`#${config.nodeId}`)[0];
        cy.center(citizen);
      },

      stop: (e) => {
        // Disable user grabbing of nodes
        // This has to be disabled after the simulation is done
        // Otherwise the simulation can't move nodes
        e.cy.autolock(true);
      },
    } as D3ForceLayoutOptions,
  });
});
