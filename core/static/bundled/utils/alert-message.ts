interface AlertParams {
  success?: boolean;
  duration?: number;
}

export class AlertMessage {
  public open: boolean;
  public success: boolean;
  public content: string;
  private timeoutId?: number;
  private readonly defaultDuration: number;

  constructor(params?: { defaultDuration: number }) {
    this.open = false;
    this.content = "";
    this.timeoutId = null;
    this.defaultDuration = params?.defaultDuration ?? 2000;
  }

  public display(message: string, params: AlertParams) {
    this.clear();
    this.open = true;
    this.content = message;
    this.success = params.success ?? true;
    this.timeoutId = setTimeout(() => {
      this.open = false;
      this.timeoutId = null;
    }, params.duration ?? this.defaultDuration);
  }

  public clear() {
    if (this.timeoutId !== null) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    this.open = false;
  }
}
