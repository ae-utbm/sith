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
    ],
    layout: {
      name: "d3-force",
      animate: false,
      fit: false,
      ungrabifyWhileSimulating: true,
      fixedAfterDragging: true,
      linkId: (node) => {
        return node.id;
      },

      linkDistance: (link) => {
        return link?.value * 1000;
      },

      stop: () => {
        // Disable user grabbing of nodes
        // This has to be disabled after the simulation is done
        // Otherwise the simulation can't move nodes
        cy.autolock(true);

        // Center on current user node
        for (const node of cy.nodes()) {
          if (node.id() === `${config.nodeId}`) {
            node.addClass("focused");
            cy.center(node);
            break;
          }
        }
      },
    } as D3ForceLayoutOptions,
  });
});
