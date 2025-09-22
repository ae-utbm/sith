const INTERVAL = 10;

interface Poster {
  url: string; // URL of the poster
  displayTime: number; // Number of seconds to display that poster
}

document.addEventListener("alpine:init", () => {
  Alpine.data("slideshow", (posters: Poster[]) => ({
    posters: posters,
    progress: 0,
    elapsed: 0,

    current: 0,

    init() {
      this.$watch("elapsed", () => {
        const displayTime = this.posters[this.current].displayTime * 1000;
        if (this.elapsed > displayTime) {
          this.current = this.getNext();
          this.elapsed = 0;
        }
        if (displayTime === 0) {
          this.progress = 100;
        } else {
          this.progress = (100 * this.elapsed) / displayTime;
        }
      });
      setInterval(() => {
        this.elapsed += INTERVAL;
      }, INTERVAL);
    },

    getNext() {
      return (this.current + 1) % this.posters.length;
    },

    async toggleFullScreen(event: Event) {
      const target = event.target as HTMLElement;
      if (document.fullscreenElement) {
        await document.exitFullscreen();
        return;
      }
      await target.requestFullscreen();
    },
  }));
});
