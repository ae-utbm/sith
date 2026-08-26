interface CustomHtmxExtension {
  name: string;
  extension: any;
}

export const getErrorCallbacksExt = () => {
  const attrPrefix = "hx-callback-";
  let htmxApi: { attributeValue: (arg0: HTMLElement, arg1: string) => string | null };

  const getCallback = (elt: HTMLElement, responseCode: number) => {
    if (!elt || !responseCode) {
      return () => {};
    }

    const code = responseCode.toString();

    // '*' is the original syntax, as the obvious character for a wildcard.
    // The 'x' alternative was added for maximum compatibility with HTML
    // templating engines, due to ambiguity around which characters are
    // supported in HTML attributes.
    //
    // Start with the most specific possible attribute and generalize from
    // there.
    const suffixes = [
      code,

      `${code.substring(0, 2)}*`,
      `${code.substring(0, 2)}x`,

      `${code.substring(0, 1)}*`,
      `${code.substring(0, 1)}x`,
      `${code.substring(0, 1)}**`,
      `${code.substring(0, 1)}xx`,

      "*",
      "x",
      "***",
      "xxx",
    ];
    if (code.startsWith("4") || code.startsWith("5")) {
      suffixes.push("error");
    }

    for (const suffix of suffixes) {
      const attr = attrPrefix + suffix;
      const callback = htmxApi?.attributeValue(elt, attr);
      if (callback) {
        return Function("src", "target", callback);
      }
    }

    return () => {};
  };

  return {
    name: "error-callbacks",
    extension: {
      init: (api: any) => {
        htmxApi = api;
      },
      // biome-ignore lint/style/useNamingConvention: HTMX naming convention
      htmx_response_error: (
        elt: HTMLElement,
        event: { ctx: any; cancelled: boolean },
      ) => {
        if (event.cancelled) {
          return false;
        }
        getCallback(elt, event.ctx.response.status)(elt, event.ctx.target);
        return true;
      },
    },
  } as CustomHtmxExtension;
};
