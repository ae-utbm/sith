import { Alpine } from "alpinejs";

export enum NotificationLevel {
  Error = "error",
  Warning = "warning",
  Success = "success",
}

export interface NotificationPlugin {
  /**
   * Add an error message to the notifications.
   */
  error: (message: string) => void;
  /**
   * Add a warning message to the notifications
   */
  warning: (message: string) => void;
  /**
   * Add a success message to the notifications
   */
  success: (message: string) => void;
  /**
   * Remove all notifications displayed on the page.
   */
  clear: () => void;
  /**
   * Add multiple notifications at once.
   * The added notifications can have different notification levels.
   */
  addMany: (notifs: Notification[]) => void;
  /**
   * Return all notifications displayed on the page.
   */
  getAll: () => Notification[];
}

export interface Notification {
  tag: NotificationLevel;
  text: string;
}

Alpine.store("notifications", [] as Notification[]);

function createNotification(message: string, level: NotificationLevel) {
  (Alpine.store("notifications") as Notification[]).push({ text: message, tag: level });
}
function createManyNotifications(notifs: Notification[]) {
  for (const notif of notifs) {
    createNotification(notif.text, notif.tag);
  }
}

export const notifications: NotificationPlugin = {
  error: (message: string) => createNotification(message, NotificationLevel.Error),
  warning: (message: string) => createNotification(message, NotificationLevel.Warning),
  success: (message: string) => createNotification(message, NotificationLevel.Success),
  clear: () => Alpine.store("notifications", []),
  addMany: (notifs: Notification[]) => createManyNotifications(notifs),
  getAll: () => Alpine.store("notifications") as Notification[],
};

export function notificationsPlugin(GlobalAlpine: Alpine) {
  GlobalAlpine.magic("notifications", () => ({ ...notifications }));
}
