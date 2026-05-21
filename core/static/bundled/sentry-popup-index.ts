// biome-ignore lint/performance/noNamespaceImport: this is the recommended way from the documentation
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

const loadSentryPopup = (options: SentryOptions) => {
  Sentry.init({
    dsn: options.dsn,
  });
  Sentry.showReportDialog({
    eventId: options.eventId,
    ...(options.user ?? {}),
  });
};
Object.assign(window, { loadSentryPopup });
