import Cookies from "js-cookie";
import type { CreateClientConfig } from "#openapi";

export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  headers: {
    "X-CSRFToken": Cookies.get("csrftoken"),
  },
});
