export enum NotificationLevel {
  Error = "error",
  Warning = "warning",
}

export function createNotification(message: string, level: NotificationLevel) {
  const element = document.getElementById("notifications");
  if (element === null) {
    return false;
  }
  return element.dispatchEvent(
    new CustomEvent("notification-add", {
      detail: { text: message, tag: level },
    }),
  );
}

export function deleteNotifications() {
  const element = document.getElementById("notifications");
  if (element === null) {
    return false;
  }
  return element.dispatchEvent(new CustomEvent("notification-delete"));
}
