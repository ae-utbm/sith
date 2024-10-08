async function getGraphData(url, godfathersDepth, godchildrenDepth) {
  const data = await (
    await fetch(
      `${url}?godfathers_depth=${godfathersDepth}&godchildren_depth=${godchildrenDepth}`,
    )
  ).json();
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

function createGraph(container, data, activeUserId) {
  // biome-ignore lint/correctness/noUndeclaredVariables: imported by user_godphaters_tree.jinja
  const cy = cytoscape({
    boxSelectionEnabled: false,
    autounselectify: true,

    container,
    elements: data,
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
  const activeUser = cy.getElementById(activeUserId).style("shape", "rectangle");
  /* Reset graph */
  const resetGraph = () => {
    cy.elements((element) => {
      if (element.hasClass("traversed")) {
        element.removeClass("traversed");
      }
      if (element.hasClass("not-traversed")) {
        element.removeClass("not-traversed");
      }
    });
  };

  const onNodeTap = (el) => {
    resetGraph();
    /* Create path on graph if selected isn't the targeted user */
    if (el === activeUser) {
      return;
    }
    cy.elements((element) => {
      element.addClass("not-traversed");
    });

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
  cy.zoomingEnabled(false);

  /* Add context menu */
  if (cy.cxtmenu === undefined) {
    throw new Error("ctxmenu isn't loaded, context menu won't be available on graphs");
  }
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

document.addEventListener("alpine:init", () => {
  /*
    This needs some constants to be set before the document has been loaded

    apiUrl:     base url for fetching the tree as a string
    activeUser: id of the user to fetch the tree from
    depthMin:   minimum tree depth for godfathers and godchildren as an int
    depthMax:   maximum tree depth for godfathers and godchildren as an int
  */
  const defaultDepth = 2;

  if (
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
    typeof apiUrl === "undefined" ||
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
    typeof activeUser === "undefined" ||
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
    typeof depthMin === "undefined" ||
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
    typeof depthMax === "undefined"
  ) {
    throw new Error(
      "Some constants are not set before using the family_graph script, please look at the documentation",
    );
  }

  function getInitialDepth(prop) {
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by script.js
    const value = Number.parseInt(initialUrlParams.get(prop));
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
    if (Number.isNaN(value) || value < depthMin || value > depthMax) {
      return defaultDepth;
    }
    return value;
  }

  Alpine.data("graph", () => ({
    loading: false,
    godfathersDepth: getInitialDepth("godfathersDepth"),
    godchildrenDepth: getInitialDepth("godchildrenDepth"),
    // biome-ignore lint/correctness/noUndeclaredVariables: defined by script.js
    reverse: initialUrlParams.get("reverse")?.toLowerCase?.() === "true",
    graph: undefined,
    graphData: {},

    async init() {
      const delayedFetch = Alpine.debounce(async () => {
        await this.fetchGraphData();
      }, 100);
      for (const param of ["godfathersDepth", "godchildrenDepth"]) {
        this.$watch(param, async (value) => {
          // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
          if (value < depthMin || value > depthMax) {
            return;
          }
          // biome-ignore lint/correctness/noUndeclaredVariables: defined by script.js
          updateQueryString(param, value, History.REPLACE);
          await delayedFetch();
        });
      }
      this.$watch("reverse", async (value) => {
        // biome-ignore lint/correctness/noUndeclaredVariables: defined by script.js
        updateQueryString("reverse", value, History.REPLACE);
        await this.reverseGraph();
      });
      this.$watch("graphData", async () => {
        await this.generateGraph();
        if (this.reverse) {
          await this.reverseGraph();
        }
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
      this.graph.elements((el) => {
        el.position({ x: -el.position().x, y: -el.position().y });
      });
      this.graph.center(this.graph.elements());
    },

    async fetchGraphData() {
      this.graphData = await getGraphData(
        // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
        apiUrl,
        this.godfathersDepth,
        this.godchildrenDepth,
      );
    },

    async generateGraph() {
      this.loading = true;
      // biome-ignore lint/correctness/noUndeclaredVariables: defined by user_godfathers_tree.jinja
      this.graph = await createGraph($(this.$refs.graph), this.graphData, activeUser);
      this.loading = false;
    },
  }));
});
