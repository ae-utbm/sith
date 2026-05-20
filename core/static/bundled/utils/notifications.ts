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

function deleteNotifications() {
  Alpine.store("notifications", []);
}

function getNotifications() {
  return Alpine.store("notifications") as Notification[];
}

export function alpinePlugin(): NotificationPlugin {
  return {
    error: (message: string) => createNotification(message, NotificationLevel.Error),
    warning: (message: string) =>
      createNotification(message, NotificationLevel.Warning),
    success: (message: string) =>
      createNotification(message, NotificationLevel.Success),
    clear: () => deleteNotifications(),
    addMany: (notifs: Notification[]) =>
      notifs.forEach((n) => {
        createNotification(n.text, n.tag);
      }),
    getAll: () => getNotifications(),
  };
}
