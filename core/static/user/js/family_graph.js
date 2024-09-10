async function get_graph_data(url, godfathers_depth, godchildren_depth) {
  let data = await (
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
  let cy = cytoscape({
    boxSelectionEnabled: false,
    autounselectify: true,

    container: container,
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
      name: "breadthfirst",
      directed: false,
      padding: 10,
      grid: true,
      circle: false,
      avoidOverlap: true,
      roots: `#${active_user_id}`,
    },
  });
  let active_user = cy
    .getElementById(active_user_id)
    .style("shape", "rectangle");
  /* Reset graph */
  let reset_graph = () => {
    cy.elements((element) => {
      if (element.hasClass("traversed")) {
        element.removeClass("traversed");
      }
      if (element.hasClass("not-traversed")) {
        element.removeClass("not-traversed");
      }
    });
  };

  let on_node_tap = (el) => {
    reset_graph();
    /* Create path on graph if selected isn't the targeted user */
    if (el === active_user) {
      return;
    }
    cy.elements((element) => {
      element.addClass("not-traversed");
    });

    cy.elements()
      .aStar({
        root: el,
        goal: active_user,
      })
      .path.forEach((el) => {
        el.removeClass("not-traversed");
        el.addClass("traversed");
      });
  };

  cy.on("tap", "node", (tapped) => {
    on_node_tap(tapped.target);
  });
  cy.zoomingEnabled(false);

  /* Add context menu */
  if (cy.cxtmenu === undefined) {
    console.error(
      "ctxmenu isn't loaded, context menu won't be available on graphs",
    );
    return cy;
  }
  cy.cxtmenu({
    selector: "node",

    commands: [
      {
        content: '<i class="fa fa-external-link fa-2x"></i>',
        select: function (el) {
          window.open(el.data().profile_url, "_blank").focus();
        },
      },

      {
        content: '<span class="fa fa-mouse-pointer fa-2x"></span>',
        select: function (el) {
          on_node_tap(el);
        },
      },

      {
        content: '<i class="fa fa-eraser fa-2x"></i>',
        select: function (el) {
          reset_graph();
        },
      },
    ],
  });

  return cy;
}

document.addEventListener("alpine:init", () => {
  const depth_min = 0;
  const depth_max = 10;
  const default_depth = 2;

  function get_initial_depth(prop) {
    let value = parseInt(initialUrlParams.get(prop));
    if (isNaN(value) || value < depth_min || value > depth_max) {
      return default_depth;
    }
    return value;
  }

  Alpine.data("graph", () => ({
    loading: false,
    godfathers_depth: get_initial_depth("godfathers_depth"),
    godchildren_depth: get_initial_depth("godchildren_depth"),
    reverse: !!initialUrlParams.get("reverse"),
    graph: undefined,
    graph_data: {},

    async init() {
      let delayed_fetch = Alpine.debounce(async () => {
        this.fetch_graph_data();
      }, 100);
      ["godfathers_depth", "godchildren_depth"].forEach((param) => {
        this.$watch(param, async (value) => {
          if (value < depth_min || value > depth_max) {
            return;
          }
          update_query_string(param, value, History.REPLACE);
          delayed_fetch();
        });
      });
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
      link.download = "output.jpg";
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    },

    async reset() {
      this.godfathers_depth = default_depth;
      this.godchildren_depth = default_depth;
    },

    async reverse_graph() {
      this.graph.elements((el) => {
        el.position(new Object({ x: -el.position().x, y: -el.position().y }));
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
      this.graph = create_graph(
        $(this.$refs.graph),
        this.graph_data,
        active_user,
      );
      this.loading = false;
    },
  }));
});
