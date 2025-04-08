import type { Alpine as AlpineType } from "alpinejs";

export function limitedChoices(Alpine: AlpineType) {
  /**
   * Directive to limit the number of elements
   * that can be selected in a group of checkboxes.
   *
   * When the max numbers of selectable elements is reached,
   * new elements will still be inserted, but oldest ones will be deselected.
   * For example, if checkboxes A, B and C have been selected and the max
   * number of selections is 3, then selecting D will result in having
   * B, C and D selected.
   *
   * # Example in template
   * ```html
   * <div x-data="{nbMax: 2}", x-limited-choices="nbMax">
   *   <button @click="nbMax += 1">Click me to increase the limit</button>
   *   <input type="checkbox" value="A" name="foo">
   *   <input type="checkbox" value="B" name="foo">
   *   <input type="checkbox" value="C" name="foo">
   *   <input type="checkbox" value="D" name="foo">
   * </div>
   * ```
   */
  Alpine.directive(
    "limited-choices",
    (el, { expression }, { evaluateLater, effect }) => {
      const getMaxChoices = evaluateLater(expression);
      let maxChoices: number;
      const inputs: HTMLInputElement[] = Array.from(
        el.querySelectorAll("input[type='checkbox']"),
      );
      const checked = [] as HTMLInputElement[];

      const manageDequeue = () => {
        if (checked.length <= maxChoices) {
          // There isn't too many checkboxes selected. Nothing to do
          return;
        }
        const popped = checked.splice(0, checked.length - maxChoices);
        for (const p of popped) {
          p.checked = false;
        }
      };

      for (const input of inputs) {
        input.addEventListener("change", (_e) => {
          if (input.checked) {
            checked.push(input);
          } else {
            checked.splice(checked.indexOf(input), 1);
          }
          manageDequeue();
        });
      }
      effect(() => {
        getMaxChoices((value: string) => {
          const previousValue = maxChoices;
          maxChoices = Number.parseInt(value);
          if (maxChoices < previousValue) {
            // The maximum number of selectable items has been lowered.
            // Some currently selected elements may need to be removed
            manageDequeue();
          }
        });
      });
    },
  );
}
