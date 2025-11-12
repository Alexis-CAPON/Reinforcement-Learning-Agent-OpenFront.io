/**
 * Simple string-based EventBus for RL visualization
 * (Different from core/EventBus which uses typed events)
 */

type EventHandler = (data: any) => void;

export class EventBus {
  private listeners: Map<string, EventHandler[]> = new Map();

  on(eventName: string, handler: EventHandler): void {
    if (!this.listeners.has(eventName)) {
      this.listeners.set(eventName, []);
    }
    this.listeners.get(eventName)!.push(handler);
  }

  off(eventName: string, handler: EventHandler): void {
    const handlers = this.listeners.get(eventName);
    if (handlers) {
      const index = handlers.indexOf(handler);
      if (index > -1) {
        handlers.splice(index, 1);
      }
    }
  }

  emit(eventName: string, data?: any): void {
    const handlers = this.listeners.get(eventName);
    if (handlers) {
      for (const handler of handlers) {
        handler(data);
      }
    }
  }
}
