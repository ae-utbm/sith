export enum NotificationLevel {
  Error = "error",
  Warning = "warning",
  Success = "success",
}

export function createNotification(message: string, level: NotificationLevel) {
  const element = document.getElementById("quick-notifications");
  if (element === null) {
    return false;
  }
  return element.dispatchEvent(
    new CustomEvent("quick-notification-add", {
      detail: { text: message, tag: level },
    }),
  );
}

export function deleteNotifications() {
  const element = document.getElementById("quick-notifications");
  if (element === null) {
    return false;
  }
  return element.dispatchEvent(new CustomEvent("quick-notification-delete"));
}

export function alpinePlugin() {
  return {
    error: (message: string) => createNotification(message, NotificationLevel.Error),
    warning: (message: string) =>
      createNotification(message, NotificationLevel.Warning),
    success: (message: string) =>
      createNotification(message, NotificationLevel.Success),
    clear: () => deleteNotifications(),
  };
}
