import { paginated } from "#core:utils/api";
import { exportToHtml } from "#core:utils/globals";
import { Chart } from "chart.js/auto";
import {
  type PermanencyFetchPermananciesData,
  permanencyFetchPermanancies,
} from "#openapi";

interface ActivityChartConfig {
  canvas: HTMLCanvasElement;
  startDate: Date;
  counterId: number;
}

// Get permanancies from the last week using the API

exportToHtml("loadChart", loadChart);

async function loadChart(options: ActivityChartConfig) {
  const permanancies = paginated(permanencyFetchPermanancies, {
    query: {
      counter: [options.counterId],
      // biome-ignore lint/style/useNamingConvention: backend API uses snake_case
      start_date: options.startDate.toISOString(),
    },
  } as PermanencyFetchPermananciesData).then((data) => {
    console.log(data);
  });
  const chart = new Chart(options.canvas, {
    type: "bar",
    data: {
      labels: ["Red", "Blue", "Yellow", "Green", "Purple", "Orange"],
      datasets: [
        {
          label: "# of Votes",
          data: [12, 19, 3, 5, 2, 3],
          borderWidth: 1,
        },
      ],
    },
    options: {
      scales: {
        y: {
          beginAtZero: true,
        },
      },
    },
  });
}

console.log("Hello from graph-index.ts");
