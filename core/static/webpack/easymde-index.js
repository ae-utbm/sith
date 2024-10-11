// biome-ignore lint/correctness/noUndeclaredDependencies: shipped by easymde
import "codemirror/lib/codemirror.css";
import "easymde/src/css/easymde.css";
import easyMde from "easymde";
import { markdownRenderMarkdown } from "#openapi";

/**
 * Create a new easymde based textarea
 * @param {HTMLTextAreaElement} textarea to use
 **/
window.easymdeFactory = (textarea) => {
  const easymde = new easyMde({
    element: textarea,
    spellChecker: false,
    autoDownloadFontAwesome: false,
    previewRender: Alpine.debounce(async (plainText, preview) => {
      preview.innerHTML = (
        await markdownRenderMarkdown({ body: { text: plainText } })
      ).data;
      return null;
    }, 300),
    forceSync: true, // Avoid validation error on generic create view
    toolbar: [
      {
        name: "heading-smaller",
        action: easyMde.toggleHeadingSmaller,
        className: "fa fa-header",
        title: gettext("Heading"),
      },
      {
        name: "italic",
        action: easyMde.toggleItalic,
        className: "fa fa-italic",
        title: gettext("Italic"),
      },
      {
        name: "bold",
        action: easyMde.toggleBold,
        className: "fa fa-bold",
        title: gettext("Bold"),
      },
      {
        name: "strikethrough",
        action: easyMde.toggleStrikethrough,
        className: "fa fa-strikethrough",
        title: gettext("Strikethrough"),
      },
      {
        name: "underline",
        action: function customFunction(editor) {
          const cm = editor.codemirror;
          cm.replaceSelection(`__${cm.getSelection()}__`);
        },
        className: "fa fa-underline",
        title: gettext("Underline"),
      },
      {
        name: "superscript",
        action: function customFunction(editor) {
          const cm = editor.codemirror;
          cm.replaceSelection(`^${cm.getSelection()}^`);
        },
        className: "fa fa-superscript",
        title: gettext("Superscript"),
      },
      {
        name: "subscript",
        action: function customFunction(editor) {
          const cm = editor.codemirror;
          cm.replaceSelection(`~${cm.getSelection()}~`);
        },
        className: "fa fa-subscript",
        title: gettext("Subscript"),
      },
      {
        name: "code",
        action: easyMde.toggleCodeBlock,
        className: "fa fa-code",
        title: gettext("Code"),
      },
      "|",
      {
        name: "quote",
        action: easyMde.toggleBlockquote,
        className: "fa fa-quote-left",
        title: gettext("Quote"),
      },
      {
        name: "unordered-list",
        action: easyMde.toggleUnorderedList,
        className: "fa fa-list-ul",
        title: gettext("Unordered list"),
      },
      {
        name: "ordered-list",
        action: easyMde.toggleOrderedList,
        className: "fa fa-list-ol",
        title: gettext("Ordered list"),
      },
      "|",
      {
        name: "link",
        action: easyMde.drawLink,
        className: "fa fa-link",
        title: gettext("Insert link"),
      },
      {
        name: "image",
        action: easyMde.drawImage,
        className: "fa-regular fa-image",
        title: gettext("Insert image"),
      },
      {
        name: "table",
        action: easyMde.drawTable,
        className: "fa fa-table",
        title: gettext("Insert table"),
      },
      "|",
      {
        name: "clean-block",
        action: easyMde.cleanBlock,
        className: "fa fa-eraser fa-clean-block",
        title: gettext("Clean block"),
      },
      "|",
      {
        name: "preview",
        action: easyMde.togglePreview,
        className: "fa fa-eye no-disable",
        title: gettext("Toggle preview"),
      },
      {
        name: "side-by-side",
        action: easyMde.toggleSideBySide,
        className: "fa fa-columns no-disable no-mobile",
        title: gettext("Toggle side by side"),
      },
      {
        name: "fullscreen",
        action: easyMde.toggleFullScreen,
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

  const submits = textarea.closest("form").querySelectorAll('input[type="submit"]');
  const parentDiv = textarea.parentElement;
  let submitPressed = false;

  function checkMarkdownInput() {
    // an attribute is null if it does not exist, else a string
    const required = textarea.getAttribute("required") != null;
    const length = textarea.value.trim().length;

    if (required && length === 0) {
      parentDiv.style.boxShadow = "red 0px 0px 1.5px 1px";
    } else {
      parentDiv.style.boxShadow = "";
    }
  }

  function onSubmitClick(e) {
    if (!submitPressed) {
      easymde.codemirror.on("change", checkMarkdownInput);
    }
    submitPressed = true;
    checkMarkdownInput(e);
  }

  for (const submit of submits) {
    submit.addEventListener("click", onSubmitClick);
  }
};
