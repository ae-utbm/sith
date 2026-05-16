import { Alpine } from "alpinejs";

export enum NotificationLevel {
  Error = "error",
  Warning = "warning",
  Success = "success",
}

export interface NotificationPlugin {
  error: (message: string) => void;
  warning: (message: string) => void;
  success: (message: string) => void;
  clear: () => void;
  addMany: (notifs: Notification[]) => void;
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
