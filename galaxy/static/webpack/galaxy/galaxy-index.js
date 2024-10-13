import { default as ForceGraph3D } from "3d-force-graph";
import { forceX, forceY, forceZ } from "d3-force-3d";
// biome-ignore lint/style/noNamespaceImport: This is how it should be imported
import * as Three from "three";
import SpriteText from "three-spritetext";

/**
 * @typedef GalaxyConfig
 * @property {number} nodeId id of the current user node
 * @property {string} dataUrl url to fetch the galaxy data from
 **/

/**
 * Load the galaxy of an user
 * @param {GalaxyConfig} config
 **/
window.loadGalaxy = (config) => {
  window.getNodeFromId = (id) => {
    return Graph.graphData().nodes.find((n) => n.id === id);
  };

  window.getLinksFromNodeId = (id) => {
    return Graph.graphData().links.filter(
      (l) => l.source.id === id || l.target.id === id,
    );
  };

  window.focusNode = (node) => {
    highlightNodes.clear();
    highlightLinks.clear();

    hoverNode = node || null;
    if (node) {
      // collect neighbors and links for highlighting
      for (const link of window.getLinksFromNodeId(node.id)) {
        highlightLinks.add(link);
        highlightNodes.add(link.source);
        highlightNodes.add(link.target);
      }
    }

    // refresh node and link display
    Graph.nodeThreeObject(Graph.nodeThreeObject())
      .linkWidth(Graph.linkWidth())
      .linkDirectionalParticles(Graph.linkDirectionalParticles());

    // Aim at node from outside it
    const distance = 42;
    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

    const newPos =
      node.x || node.y || node.z
        ? { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }
        : { x: 0, y: 0, z: distance }; // special case if node is in (0,0,0)

    Graph.cameraPosition(
      newPos, // new position
      node, // lookAt ({ x, y, z })
      3000, // ms transition duration
    );
  };

  const highlightNodes = new Set();
  const highlightLinks = new Set();
  let hoverNode = null;

  const grpahDiv = document.getElementById("3d-graph");
  const Graph = ForceGraph3D();
  Graph(grpahDiv);
  Graph.jsonUrl(config.dataUrl)
    .width(
      grpahDiv.parentElement.clientWidth > 1200
        ? 1200
        : grpahDiv.parentElement.clientWidth,
    ) // Not perfect at all. JS-fu master from the future, please fix this :-)
    .height(1000)
    .enableNodeDrag(false) // allow easier navigation
    .onNodeClick((node) => {
      const camera = Graph.cameraPosition();
      const distance = Math.sqrt(
        (node.x - camera.x) ** 2 + (node.y - camera.y) ** 2 + (node.z - camera.z) ** 2,
      );
      if (distance < 120 || highlightNodes.has(node)) {
        window.focusNode(node);
      }
    })
    .linkWidth((link) => (highlightLinks.has(link) ? 0.4 : 0.0))
    .linkColor((link) =>
      highlightLinks.has(link) ? "rgba(255,160,0,1)" : "rgba(128,255,255,0.6)",
    )
    .linkVisibility((link) => highlightLinks.has(link))
    .nodeVisibility((node) => highlightNodes.has(node) || node.mass > 4)
    // .linkDirectionalParticles(link => highlightLinks.has(link) ? 3 : 1) // kinda buggy for now, and slows this a bit, but would be great to help visualize lanes
    .linkDirectionalParticleWidth(0.2)
    .linkDirectionalParticleSpeed(-0.006)
    .nodeThreeObject((node) => {
      const sprite = new SpriteText(node.name);
      sprite.material.depthWrite = false; // make sprite background transparent
      sprite.color = highlightNodes.has(node)
        ? node === hoverNode
          ? "rgba(200,0,0,1)"
          : "rgba(255,160,0,0.8)"
        : "rgba(0,255,255,0.2)";
      sprite.textHeight = 2;
      sprite.center = new Three.Vector2(1.2, 0.5);
      return sprite;
    })
    .onEngineStop(() => {
      window.focusNode(window.getNodeFromId(config.nodeId));
      Graph.onEngineStop(() => {
        /* nope */
      }); // don't call ourselves in a loop while moving the focus
    });

  // Set distance between stars
  Graph.d3Force("link").distance((link) => link.value);

  // Set high masses nearer the center of the galaxy
  // TODO: quick and dirty strength computation, this will need tuning.
  Graph.d3Force(
    "positionX",
    forceX().strength((node) => {
      return 1 - 1 / node.mass;
    }),
  );
  Graph.d3Force(
    "positionY",
    forceY().strength((node) => {
      return 1 - 1 / node.mass;
    }),
  );
  Graph.d3Force(
    "positionZ",
    forceZ().strength((node) => {
      return 1 - 1 / node.mass;
    }),
  );
};
