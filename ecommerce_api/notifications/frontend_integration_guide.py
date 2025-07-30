


"""
// JavaScript code for frontend (React/Vue/vanilla JS)
class OrderNotificationService {
    constructor(userId) {
        this.userId = userId;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }

    connect() {
        // Replace with your actual WebSocket URL
        const wsUrl = `ws://localhost:8000/ws/orders/`;
        
        this.socket = new WebSocket(wsUrl);

        this.socket.onopen = (event) => {
            console.log('Connected to order notifications');
            this.reconnectAttempts = 0;
        };

        this.socket.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };

        this.socket.onclose = (event) => {
            console.log('Disconnected from order notifications');
            this.attemptReconnect();
        };

        this.socket.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    handleMessage(data) {
        if (data.type === 'order_status_update') {
            // Show notification to user
            this.showNotification({
                title: 'Order Update',
                message: data.message,
                orderNumber: data.order_number,
                status: data.new_status
            });
        }
    }

    showNotification(notification) {
        // Implement your notification display logic here
        // Could be a toast, modal, or browser notification
        console.log('New order notification:', notification);
        
        // Example: Browser notification
        if (Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: `${notification.message} (Order: ${notification.orderNumber})`,
                icon: '/path/to/icon.png'
            });
        }
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            setTimeout(() => {
                console.log(`Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts})`);
                this.connect();
            }, 2000 * this.reconnectAttempts);
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Usage
const notificationService = new OrderNotificationService();
notificationService.connect();

// Request notification permission
if (Notification.permission !== 'granted' && Notification.permission !== 'denied') {
    Notification.requestPermission();
}
"""