import { AutoCompleteSelectBase } from "#core:core/components/ajax-select-base";
import { registerComponent } from "#core:utils/web-components";
import type { RecursivePartial, TomSettings } from "tom-select/dist/types/types";

const productParsingRegex = /^(\d+x)?(.*)/i;

function parseProduct(query: string): [number, string] {
  const parsed = productParsingRegex.exec(query);
  return [Number.parseInt(parsed[1] || "1"), parsed[2]];
}

@registerComponent("counter-product-select")
export class CounterProductSelect extends AutoCompleteSelectBase {
  public getOperationCodes(): string[] {
    return ["FIN", "ANN"];
  }

  public getSelectedProduct(): [number, string] {
    return parseProduct(this.widget.getValue() as string);
  }

  protected attachBehaviors(): void {
    this.allowMultipleProducts();
  }

  private allowMultipleProducts(): void {
    const search = this.widget.search;
    const onOptionSelect = this.widget.onOptionSelect;
    this.widget.hook("instead", "search", (query: string) => {
      return search.call(this.widget, parseProduct(query)[1]);
    });
    this.widget.hook(
      "instead",
      "onOptionSelect",
      (evt: MouseEvent | KeyboardEvent, option: HTMLElement) => {
        const [quantity, _] = parseProduct(this.widget.inputValue());
        const originalValue = option.getAttribute("data-value") ?? option.innerText;

        if (quantity === 1 || this.getOperationCodes().includes(originalValue)) {
          return onOptionSelect.call(this.widget, evt, option);
        }

        const value = `${quantity}x${originalValue}`;
        const label = `${quantity}x${option.innerText}`;
        this.widget.addOption({ value: value, text: label }, true);
        return onOptionSelect.call(
          this.widget,
          evt,
          this.widget.getOption(value, true),
        );
      },
    );

    this.widget.hook("after", "onOptionSelect", () => {
      /* Focus the next element if it's an input */
      if (this.nextElementSibling.nodeName === "INPUT") {
        (this.nextElementSibling as HTMLInputElement).focus();
      }
    });
  }
  protected tomSelectSettings(): RecursivePartial<TomSettings> {
    /* We disable the dropdown on focus because we're going to always autofocus the widget */
    return { ...super.tomSelectSettings(), openOnFocus: false };
  }
}
