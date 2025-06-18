import { History, initialUrlParams, updateQueryString } from "#core:utils/history";
import cytoscape, {
  type ElementDefinition,
  type NodeSingular,
  type Singular,
} from "cytoscape";
import cxtmenu from "cytoscape-cxtmenu";
import klay from "cytoscape-klay";
import { type UserProfileSchema, familyGetFamilyGraph } from "#openapi";

cytoscape.use(klay);
cytoscape.use(cxtmenu);

type GraphData = (
  | { data: UserProfileSchema }
  | { data: { source: number; target: number } }
)[];

function isMobile() {
  return window.innerWidth < 500;
}

async function getGraphData(
  userId: number,
  godfathersDepth: number,
  godchildrenDepth: number,
): Promise<GraphData> {
  const data = (
    await familyGetFamilyGraph({
      path: {
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        user_id: userId,
      },
      query: {
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        godfathers_depth: godfathersDepth,
        // biome-ignore lint/style/useNamingConvention: api is snake_case
        godchildren_depth: godchildrenDepth,
      },
    })
  ).data;
  return [
    ...data.users.map((user) => {
      return { data: user };
    }),
    ...data.relationships.map((rel) => {
      return {
        data: { source: rel.godfather, target: rel.godchild },
      };
    }),
  ];
}

function createGraph(container: HTMLDivElement, data: GraphData, activeUserId: number) {
  const cy = cytoscape({
    boxSelectionEnabled: false,
    autounselectify: true,

    container,
    elements: data as ElementDefinition[],
    minZoom: 0.5,

    style: [
      // the stylesheet for the graph
      {
        selector: "node",
        style: {
          label: "data(display_name)",
          "background-image": "data(profile_pict)",
          width: "100%",
          height: "100%",
          "background-fit": "cover",
          "background-repeat": "no-repeat",
          shape: "ellipse",
        },
      },

      {
        selector: "edge",
        style: {
          width: 5,
          "line-color": "#ccc",
          "target-arrow-color": "#ccc",
          "target-arrow-shape": "triangle",
          "curve-style": "bezier",
        },
      },

      {
        selector: ".traversed",
        style: {
          "border-width": "5px",
          "border-style": "solid",
          "border-color": "red",
          "target-arrow-color": "red",
          "line-color": "red",
        },
      },

      {
        selector: ".not-traversed",
        style: {
          "line-opacity": "0.5",
          "background-opacity": "0.5",
          "background-image-opacity": "0.5",
        },
      },
    ],
    layout: {
      name: "klay",
      nodeDimensionsIncludeLabels: true,
      fit: true,
      klay: {
        addUnnecessaryBendpoints: true,
        direction: "DOWN",
        nodePlacement: "INTERACTIVE",
        layoutHierarchy: true,
      },
    },
  });
  const activeUser = cy
    .getElementById(activeUserId.toString())
    .style("shape", "rectangle");
  /* Reset graph */
  const resetGraph = () => {
    cy.elements(((element: Singular) => {
      if (element.hasClass("traversed")) {
        element.removeClass("traversed");
      }
      if (element.hasClass("not-traversed")) {
        element.removeClass("not-traversed");
      }
    }) as unknown as string);
  };

  const onNodeTap = (el: Singular) => {
    resetGraph();
    /* Create path on graph if selected isn't the targeted user */
    if (el === activeUser) {
      return;
    }
    cy.elements(((element: Singular) => {
      element.addClass("not-traversed");
    }) as unknown as string);

    for (const traversed of cy.elements().aStar({
      root: el,
      goal: activeUser,
    }).path) {
      traversed.removeClass("not-traversed");
      traversed.addClass("traversed");
    }
  };

  cy.on("tap", "node", (tapped) => {
    onNodeTap(tapped.target);
  });

  /* Add context menu */
  cy.cxtmenu({
    selector: "node",

    commands: [
      {
        content: '<i class="fa fa-external-link fa-2x"></i>',
        select: (el) => {
          window.open(el.data().profile_url, "_blank").focus();
        },
      },

      {
        content: '<span class="fa fa-mouse-pointer fa-2x"></span>',
        select: (el) => {
          onNodeTap(el);
        },
      },

      {
        content: '<i class="fa fa-eraser fa-2x"></i>',
        select: (_) => {
          resetGraph();
        },
      },
    ],
  });

  return cy;
}

interface FamilyGraphConfig {
  activeUser: number; // activeUser Id of the user to fetch the tree from
  depthMin: number; // depthMin Minimum tree depth for godfathers and godchildren
  depthMax: number; // depthMax Maximum tree depth for godfathers and godchildren
}

document.addEventListener("alpine:init", () => {
  const defaultDepth = 2;

  Alpine.data("graph", (config: FamilyGraphConfig) => ({
    loading: false,
    godfathersDepth: 0,
    godchildrenDepth: 0,
    reverse: initialUrlParams.get("reverse")?.toLowerCase?.() === "true",
    graph: undefined as cytoscape.Core,
    graphData: {},
    isZoomEnabled: !isMobile(),

    getInitialDepth(prop: string) {
      const value = Number.parseInt(initialUrlParams.get(prop));
      if (Number.isNaN(value) || value < config.depthMin || value > config.depthMax) {
        return defaultDepth;
      }
      return value;
    },

    async init() {
      this.godfathersDepth = this.getInitialDepth("godfathersDepth");
      this.godchildrenDepth = this.getInitialDepth("godchildrenDepth");

      const delayedFetch = Alpine.debounce(async () => {
        await this.fetchGraphData();
      }, 100);
      for (const param of ["godfathersDepth", "godchildrenDepth"]) {
        this.$watch(param, async (value: number) => {
          if (value < config.depthMin || value > config.depthMax) {
            return;
          }
          updateQueryString(param, value.toString(), History.Replace);
          await delayedFetch();
        });
      }
      this.$watch("reverse", async (value: number) => {
        updateQueryString("reverse", value.toString(), History.Replace);
        await this.reverseGraph();
      });
      this.$watch("graphData", async () => {
        this.generateGraph();
        if (this.reverse) {
          await this.reverseGraph();
        }
      });
      this.$watch("isZoomEnabled", () => {
        this.graph.userZoomingEnabled(this.isZoomEnabled);
      });
      await this.fetchGraphData();
    },

    screenshot() {
      const link = document.createElement("a");
      link.href = this.graph.jpg();
      link.download = interpolate(
        gettext("family_tree.%(extension)s"),
        { extension: "jpg" },
        true,
      );
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    reset() {
      this.reverse = false;
      this.godfathersDepth = defaultDepth;
      this.godchildrenDepth = defaultDepth;
    },

    async reverseGraph() {
      this.graph.elements((el: NodeSingular) => {
        el.position({ x: -el.position().x, y: -el.position().y });
      });
      this.graph.center(this.graph.elements());
    },

    async fetchGraphData() {
      this.graphData = await getGraphData(
        config.activeUser,
        this.godfathersDepth,
        this.godchildrenDepth,
      );
    },

    generateGraph() {
      this.loading = true;
      this.graph = createGraph(
        this.$refs.graph as HTMLDivElement,
        this.graphData,
        config.activeUser,
      );
      this.graph.userZoomingEnabled(this.isZoomEnabled);
      this.loading = false;
    },
  }));
});
