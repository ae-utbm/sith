interface Config {
  /**
   * The prefix of the formset, in case it has been changed.
   * See https://docs.djangoproject.com/fr/stable/topics/forms/formsets/#customizing-a-formset-s-prefix
   */
  prefix?: string;
}

// biome-ignore lint/style/useNamingConvention: It's the DOM API naming
type HTMLFormInputElement = HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement;

document.addEventListener("alpine:init", () => {
  /**
   * Alpine data element to allow the dynamic addition of forms to a formset.
   *
   * To use this, you need :
   * - an HTML element containing the existing forms, noted by `x-ref="formContainer"`
   * - a template containing the empty form
   *   (that you can obtain jinja-side with `{{ formset.empty_form }}`),
   *   noted by `x-ref="formTemplate"`
   * - a button with `@click="addForm"`
   * - you may also have one or more buttons with `@click="removeForm(element)"`,
   *   where `element` is the HTML element containing the form.
   */
  Alpine.data("dynamicFormSet", (config?: Config) => ({
    init() {
      this.formContainer = this.$refs.formContainer as HTMLElement;
      this.nbForms = this.formContainer.children.length as number;
      this.template = this.$refs.formTemplate as HTMLTemplateElement;
      const prefix = config?.prefix ?? "form";
      this.$root
        .querySelector(`#id_${prefix}-TOTAL_FORMS`)
        .setAttribute(":value", "nbForms");
    },

    addForm() {
      this.formContainer.appendChild(document.importNode(this.template.content, true));
      const newForm = this.formContainer.lastElementChild;
      const inputs: NodeListOf<HTMLFormInputElement> = newForm.querySelectorAll(
        "input, select, textarea",
      );
      for (const el of inputs) {
        el.name = el.name.replace("__prefix__", this.nbForms.toString());
        el.id = el.id.replace("__prefix__", this.nbForms.toString());
      }
      const labels: NodeListOf<HTMLLabelElement> = newForm.querySelectorAll("label");
      for (const el of labels) {
        el.htmlFor = el.htmlFor.replace("__prefix__", this.nbForms.toString());
      }
      inputs[0].focus();
      this.nbForms += 1;
    },

    removeForm(container: HTMLDivElement) {
      container.remove();
      this.nbForms -= 1;
      // adjust the id of remaining forms
      for (let i = 0; i < this.nbForms; i++) {
        const form: HTMLDivElement = this.formContainer.children[i];
        const inputs: NodeListOf<HTMLFormInputElement> = form.querySelectorAll(
          "input, select, textarea",
        );
        for (const el of inputs) {
          el.name = el.name.replace(/\d+/, i.toString());
          el.id = el.id.replace(/\d+/, i.toString());
        }
        const labels: NodeListOf<HTMLLabelElement> = form.querySelectorAll("label");
        for (const el of labels) {
          el.htmlFor = el.htmlFor.replace(/\d+/, i.toString());
        }
      }
    },
  }));
});
