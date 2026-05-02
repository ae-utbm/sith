import type { AlpineComponent } from "alpinejs";

interface RoleGroupData {
  isBoard: boolean;
  isPresidency: boolean;
  roleId: number;
}

document.addEventListener("alpine:init", () => {
  Alpine.data("clubRoleList", (config: { userRoleId: number | null }) => ({
    confirmOnSubmit: false,

    /**
     * Edit relevant item data after it has been moved by x-sort
     */
    reorder(item: AlpineComponent<RoleGroupData>, conf: RoleGroupData) {
      item.isBoard = conf.isBoard;
      item.isPresidency = conf.isPresidency;
      // if the user has moved its own role outside the presidency,
      // submitting the form will require a confirmation
      this.confirmOnSubmit = config.userRoleId === item.roleId && !item.isPresidency;
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

    /**
     * If the user moved its role out of the presidency, ask a confirmation
     * before submitting the form
     */
    confirmSubmission(event: SubmitEvent) {
      if (
        this.confirmOnSubmit &&
        !confirm(
          gettext(
            "You're going to remove your own role from the presidency. " +
              "You may lock yourself out of this page. Do you want to continue ? ",
          ),
        )
      ) {
        event.preventDefault();
      }
    },
  }));
});
