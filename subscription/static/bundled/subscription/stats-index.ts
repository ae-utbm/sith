import { BarController, BarElement, CategoryScale, Chart, LinearScale } from "chart.js";

Chart.register(BarController, BarElement, CategoryScale, LinearScale);

function getRandomColor() {
  const letters = "0123456789ABCDEF";
  let color = "#";
  for (let i = 0; i < 6; i++) {
    color += letters[Math.floor(Math.random() * 16)];
  }
  return color;
}
function getRandomColorUniq(list: string[]) {
  let color = getRandomColor();
  while (list.includes(color)) {
    color = getRandomColor();
  }
  return color;
}

type Rgb = { r: number; g: number; b: number };

function hexToRgb(hex: string): Rgb | null {
  // Expand shorthand form (e.g. "03F") to full form (e.g. "0033FF")
  const shorthandRegex = /^#?([a-f\d])([a-f\d])([a-f\d])$/i;
  const hexrgb = hex.replace(shorthandRegex, (_m, r, g, b) => {
    return r + r + g + g + b + b;
  });

  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hexrgb);
  return result
    ? {
        r: Number.parseInt(result[1], 16),
        g: Number.parseInt(result[2], 16),
        b: Number.parseInt(result[3], 16),
      }
    : null;
}

document.addEventListener("DOMContentLoaded", () => {
  const ctx = (document.getElementById("statsChart") as HTMLCanvasElement).getContext(
    "2d",
  ) as CanvasRenderingContext2D;
  const labels: string[] = [];
  const total: string[] = [];
  const colorStrings: string[] = [];
  const colorsDimmed: string[] = [];
  for (const element of Array.from(document.getElementsByClassName("types"))) {
    labels.push(element.childNodes[0].textContent as string);
  }
  for (const element of Array.from(document.getElementsByClassName("total"))) {
    total.push(element.childNodes[0].childNodes[0].textContent as string);
  }

  for (const _ of labels) {
    colorStrings.push(getRandomColorUniq(colorStrings));
  }
  const colors = colorStrings.map(hexToRgb) as Rgb[];

  for (const color of colors) {
    colorsDimmed.push(`rgba(${color.r}, ${color.g}, ${color.b}, 0.2)`);
  }

  for (const color of colors) {
    colorsDimmed.push(`rgba(${color.r}, ${color.g}, ${color.b}, 0.2)`);
  }

  new Chart(ctx, {
    type: "bar",
    data: {
      labels: labels,
      datasets: [
        {
          label: document.getElementById("graphLabel")?.childNodes[0]
            .textContent as string,
          data: total,
          backgroundColor: colorsDimmed,
          borderColor: colorStrings,
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
});
