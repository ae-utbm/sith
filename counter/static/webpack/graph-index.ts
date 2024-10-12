import Chart from 'chart.js/auto';
import {permanencyFetchPermanancies} from '#openapi'

async function main() {
    console.log((await permanencyFetchPermanancies()).data)
}

main()
console.log("Hello from graph-index.ts");
