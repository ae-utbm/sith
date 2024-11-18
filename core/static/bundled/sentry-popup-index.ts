import { exportToHtml } from "#core:utils/globals";
// biome-ignore lint/style/noNamespaceImport: this is the recommended way from the documentation
import * as Sentry from "@sentry/browser";

interface LoggedUser {
  name: string;
  email: string;
}

interface SentryOptions {
  dsn: string;
  eventId: string;
  user?: LoggedUser;
}

exportToHtml("loadSentryPopup", (options: SentryOptions) => {
  Sentry.init({
    dsn: options.dsn,
  });
  Sentry.showReportDialog({
    eventId: options.eventId,
    ...(options.user ?? {}),
  });
});
