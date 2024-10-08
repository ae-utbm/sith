async function get_graph_data(url, godfathers_depth, godchildren_depth) {
  const data = await (
    await fetch(
      `${url}?godfathers_depth=${godfathers_depth}&godchildren_depth=${godchildren_depth}`,
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

function create_graph(container, data, active_user_id) {
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
  const active_user = cy.getElementById(active_user_id).style("shape", "rectangle");
  /* Reset graph */
  const reset_graph = () => {
    cy.elements((element) => {
      if (element.hasClass("traversed")) {
        element.removeClass("traversed");
      }
      if (element.hasClass("not-traversed")) {
        element.removeClass("not-traversed");
      }
    });
  };

  const on_node_tap = (el) => {
    reset_graph();
    /* Create path on graph if selected isn't the targeted user */
    if (el === active_user) {
      return;
    }
    cy.elements((element) => {
      element.addClass("not-traversed");
    });

    for (const traversed of cy.elements().aStar({
      root: el,
      goal: active_user,
    }).path) {
      traversed.removeClass("not-traversed");
      traversed.addClass("traversed");
    }
  };

  cy.on("tap", "node", (tapped) => {
    on_node_tap(tapped.target);
  });
  cy.zoomingEnabled(false);

  /* Add context menu */
  if (cy.cxtmenu === undefined) {
    console.error("ctxmenu isn't loaded, context menu won't be available on graphs");
    return cy;
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
          on_node_tap(el);
        },
      },

      {
        content: '<i class="fa fa-eraser fa-2x"></i>',
        select: (el) => {
          reset_graph();
        },
      },
    ],
  });

  return cy;
}

/* global api_url, active_user, depth_min, depth_max */
document.addEventListener("alpine:init", () => {
  /*
    This needs some constants to be set before the document has been loaded

    api_url:     base url for fetching the tree as a string
    active_user: id of the user to fetch the tree from
    depth_min:   minimum tree depth for godfathers and godchildren as an int
    depth_max:   maximum tree depth for godfathers and godchildren as an int
  */
  const default_depth = 2;

  if (
    typeof api_url === "undefined" ||
    typeof active_user === "undefined" ||
    typeof depth_min === "undefined" ||
    typeof depth_max === "undefined"
  ) {
    console.error(
      "Some constants are not set before using the family_graph script, please look at the documentation",
    );
    return;
  }

  function get_initial_depth(prop) {
    const value = Number.parseInt(initialUrlParams.get(prop));
    if (Number.isNaN(value) || value < depth_min || value > depth_max) {
      return default_depth;
    }
    return value;
  }

  Alpine.data("graph", () => ({
    loading: false,
    godfathers_depth: get_initial_depth("godfathers_depth"),
    godchildren_depth: get_initial_depth("godchildren_depth"),
    reverse: initialUrlParams.get("reverse")?.toLowerCase?.() === "true",
    graph: undefined,
    graph_data: {},

    async init() {
      const delayed_fetch = Alpine.debounce(async () => {
        this.fetch_graph_data();
      }, 100);
      for (const param of ["godfathers_depth", "godchildren_depth"]) {
        this.$watch(param, async (value) => {
          if (value < depth_min || value > depth_max) {
            return;
          }
          update_query_string(param, value, History.REPLACE);
          delayed_fetch();
        });
      }
      this.$watch("reverse", async (value) => {
        update_query_string("reverse", value, History.REPLACE);
        this.reverse_graph();
      });
      this.$watch("graph_data", async () => {
        await this.generate_graph();
        if (this.reverse) {
          await this.reverse_graph();
        }
      });
      this.fetch_graph_data();
    },

    async screenshot() {
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

    async reset() {
      this.reverse = false;
      this.godfathers_depth = default_depth;
      this.godchildren_depth = default_depth;
    },

    async reverse_graph() {
      this.graph.elements((el) => {
        el.position({ x: -el.position().x, y: -el.position().y });
      });
      this.graph.center(this.graph.elements());
    },

    async fetch_graph_data() {
      this.graph_data = await get_graph_data(
        api_url,
        this.godfathers_depth,
        this.godchildren_depth,
      );
    },

    async generate_graph() {
      this.loading = true;
      this.graph = create_graph($(this.$refs.graph), this.graph_data, active_user);
      this.loading = false;
    },
  }));
});
