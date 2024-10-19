// biome-ignore lint/correctness/noUndeclaredDependencies: shipped by easymde
import "codemirror/lib/codemirror.css";
import "easymde/src/css/easymde.css";
import { inheritHtmlElement, registerComponent } from "#core:utils/web-components";
// biome-ignore lint/correctness/noUndeclaredDependencies: Imported by EasyMDE
import type CodeMirror from "codemirror";
// biome-ignore lint/style/useNamingConvention: This is how they called their namespace
import EasyMDE from "easymde";
import { markdownRenderMarkdown } from "#openapi";

const loadEasyMde = (textarea: HTMLTextAreaElement) => {
  new EasyMDE({
    element: textarea,
    spellChecker: false,
    autoDownloadFontAwesome: false,
    previewRender: Alpine.debounce((plainText: string, preview: MarkdownInput) => {
      const func = async (plainText: string, preview: MarkdownInput): Promise<null> => {
        preview.innerHTML = (
          await markdownRenderMarkdown({ body: { text: plainText } })
        ).data as string;
        return null;
      };
      func(plainText, preview);
      return null;
    }, 300),
    forceSync: true, // Avoid validation error on generic create view
    toolbar: [
      {
        name: "heading-smaller",
        action: EasyMDE.toggleHeadingSmaller,
        className: "fa fa-header",
        title: gettext("Heading"),
      },
      {
        name: "italic",
        action: EasyMDE.toggleItalic,
        className: "fa fa-italic",
        title: gettext("Italic"),
      },
      {
        name: "bold",
        action: EasyMDE.toggleBold,
        className: "fa fa-bold",
        title: gettext("Bold"),
      },
      {
        name: "strikethrough",
        action: EasyMDE.toggleStrikethrough,
        className: "fa fa-strikethrough",
        title: gettext("Strikethrough"),
      },
      {
        name: "underline",
        action: function customFunction(editor: { codemirror: CodeMirror.Editor }) {
          const cm = editor.codemirror;
          cm.replaceSelection(`__${cm.getSelection()}__`);
        },
        className: "fa fa-underline",
        title: gettext("Underline"),
      },
      {
        name: "superscript",
        action: function customFunction(editor: { codemirror: CodeMirror.Editor }) {
          const cm = editor.codemirror;
          cm.replaceSelection(`^${cm.getSelection()}^`);
        },
        className: "fa fa-superscript",
        title: gettext("Superscript"),
      },
      {
        name: "subscript",
        action: function customFunction(editor: { codemirror: CodeMirror.Editor }) {
          const cm = editor.codemirror;
          cm.replaceSelection(`~${cm.getSelection()}~`);
        },
        className: "fa fa-subscript",
        title: gettext("Subscript"),
      },
      {
        name: "code",
        action: EasyMDE.toggleCodeBlock,
        className: "fa fa-code",
        title: gettext("Code"),
      },
      "|",
      {
        name: "quote",
        action: EasyMDE.toggleBlockquote,
        className: "fa fa-quote-left",
        title: gettext("Quote"),
      },
      {
        name: "unordered-list",
        action: EasyMDE.toggleUnorderedList,
        className: "fa fa-list-ul",
        title: gettext("Unordered list"),
      },
      {
        name: "ordered-list",
        action: EasyMDE.toggleOrderedList,
        className: "fa fa-list-ol",
        title: gettext("Ordered list"),
      },
      "|",
      {
        name: "link",
        action: EasyMDE.drawLink,
        className: "fa fa-link",
        title: gettext("Insert link"),
      },
      {
        name: "image",
        action: EasyMDE.drawImage,
        className: "fa-regular fa-image",
        title: gettext("Insert image"),
      },
      {
        name: "table",
        action: EasyMDE.drawTable,
        className: "fa fa-table",
        title: gettext("Insert table"),
      },
      "|",
      {
        name: "clean-block",
        action: EasyMDE.cleanBlock,
        className: "fa fa-eraser fa-clean-block",
        title: gettext("Clean block"),
      },
      "|",
      {
        name: "preview",
        action: EasyMDE.togglePreview,
        className: "fa fa-eye no-disable",
        title: gettext("Toggle preview"),
      },
      {
        name: "side-by-side",
        action: EasyMDE.toggleSideBySide,
        className: "fa fa-columns no-disable no-mobile",
        title: gettext("Toggle side by side"),
      },
      {
        name: "fullscreen",
        action: EasyMDE.toggleFullScreen,
        className: "fa fa-expand no-mobile",
        title: gettext("Toggle fullscreen"),
      },
      "|",
      {
        name: "guide",
        action: "/page/Aide_sur_la_syntaxe",
        className: "fa fa-question-circle",
        title: gettext("Markdown guide"),
      },
    ],
  });

  const submits: HTMLInputElement[] = Array.from(
    textarea.closest("form").querySelectorAll('input[type="submit"]'),
  );
  const parentDiv = textarea.parentElement.parentElement;

  function checkMarkdownInput(event: Event) {
    // an attribute is null if it does not exist, else a string
    const required = textarea.getAttribute("required") != null;
    const length = textarea.value.trim().length;

    if (required && length === 0) {
      parentDiv.style.boxShadow = "red 0px 0px 1.5px 1px";
      event.preventDefault();
    } else {
      parentDiv.style.boxShadow = "";
    }
  }

  function onSubmitClick(e: Event) {
    checkMarkdownInput(e);
  }

  for (const submit of submits) {
    submit.addEventListener("click", onSubmitClick);
  }
};

@registerComponent("markdown-input")
class MarkdownInput extends inheritHtmlElement("textarea") {
  connectedCallback() {
    super.connectedCallback();
    loadEasyMde(this.node);
  }
}
