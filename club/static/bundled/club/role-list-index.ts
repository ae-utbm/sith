import type { AlpineComponent } from "alpinejs";

interface RoleGroupData {
  isBoard: boolean;
  isPresidency: boolean;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("clubRoleList", () => ({
    /**
     * Edit relevant item data after it has been moved by x-sort
     */
    reorder(item: AlpineComponent<RoleGroupData>, conf: RoleGroupData) {
      item.isBoard = conf.isBoard;
      item.isPresidency = conf.isPresidency;
      this.resetOrder();
    },
    /**
     * Reset the value of the ORDER input of all items in the list.
     * This is to be called after any reordering operation, in order to make sure
     * that the order that will be saved is coherent with what is displayed.
     */
    resetOrder() {
      // When moving items with x-sort, the only information we truly have is
      // the end position in the target group, not the previous position nor
      // the position in the global list.
      // To overcome this, we loop through an enumeration of all inputs
      // that are in the form `roles-X-ORDER` and sequentially set the value of the field.
      const inputs = document.querySelectorAll<HTMLInputElement>(
        "input[name^='roles'][name$='ORDER']",
      );
      for (const [i, elem] of inputs.entries()) {
        elem.value = (i + 1).toString();
      }
    },
  }));
});
