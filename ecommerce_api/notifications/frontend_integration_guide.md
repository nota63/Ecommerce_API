# Complete Frontend Integration Guide
## Real-time Order Status Notifications with Django Channels

*A comprehensive guide for recruiters and frontend developers*

---

## 📋 Table of Contents
1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Architecture Overview](#architecture-overview)
4. [Step-by-Step Implementation](#step-by-step-implementation)
5. [Framework-Specific Examples](#framework-specific-examples)
6. [Testing & Debugging](#testing--debugging)
7. [Production Considerations](#production-considerations)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This guide explains how to integrate real-time order status notifications into your frontend application. When an order status changes in the backend, users will receive instant notifications without refreshing the page.

**What you'll achieve:**
- ✅ Real-time notifications when order status changes
- ✅ Automatic reconnection on connection loss
- ✅ User-friendly notification display
- ✅ Browser notification support
- ✅ Mobile-responsive notifications

---

## 📚 Prerequisites

### Backend Requirements (Already Implemented)
- Django with Django REST Framework
- Django Channels configured
- Redis server running
- WebSocket endpoint: `ws://your-domain/ws/orders/`

### Frontend Requirements
- Modern browser with WebSocket support
- Basic JavaScript knowledge
- Authentication system (JWT tokens recommended)

### Tools You'll Need
- Code editor (VS Code, WebStorm, etc.)
- Browser developer tools
- Optional: Postman for API testing

---

## 🏗️ Architecture Overview

```
┌─────────────────┐    WebSocket     ┌─────────────────┐
│   Frontend      ├─────────────────►│   Django        │
│   Application   │                  │   Channels      │
└─────────────────┘                  └─────────────────┘
         │                                    │
         │ Real-time Notifications            │
         ▼                                    ▼
┌─────────────────┐                  ┌─────────────────┐
│   Notification  │                  │   Order Status  │
│   Display       │                  │   Change Signal │
└─────────────────┘                  └─────────────────┘
```

**Flow:**
1. User authenticates and connects to WebSocket
2. Backend detects order status change
3. Django signal triggers notification
4. Channels sends message to user's WebSocket group
5. Frontend receives and displays notification

---

## 🚀 Step-by-Step Implementation

### Step 1: Create the WebSocket Service

Create a reusable service to handle WebSocket connections:

```javascript
// services/NotificationService.js
class OrderNotificationService {
    constructor(config = {}) {
        this.wsUrl = config.wsUrl || 'ws://localhost:8000/ws/orders/';
        this.authToken = config.authToken || null;
        this.socket = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = config.maxReconnectAttempts || 5;
        this.reconnectInterval = config.reconnectInterval || 2000;
        this.callbacks = {
            onConnect: config.onConnect || (() => {}),
            onMessage: config.onMessage || (() => {}),
            onDisconnect: config.onDisconnect || (() => {}),
            onError: config.onError || (() => {})
        };
    }

    connect() {
        try {
            // Include auth token in WebSocket URL if available
            const wsUrl = this.authToken 
                ? `${this.wsUrl}?token=${this.authToken}`
                : this.wsUrl;

            this.socket = new WebSocket(wsUrl);

            this.socket.onopen = this.handleOpen.bind(this);
            this.socket.onmessage = this.handleMessage.bind(this);
            this.socket.onclose = this.handleClose.bind(this);
            this.socket.onerror = this.handleError.bind(this);

        } catch (error) {
            console.error('Failed to create WebSocket connection:', error);
            this.callbacks.onError(error);
        }
    }

    handleOpen(event) {
        console.log('✅ Connected to order notifications');
        this.reconnectAttempts = 0;
        this.callbacks.onConnect(event);
    }

    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('📨 Received notification:', data);
            this.callbacks.onMessage(data);
        } catch (error) {
            console.error('Failed to parse message:', error);
        }
    }

    handleClose(event) {
        console.log('❌ Disconnected from order notifications');
        this.callbacks.onDisconnect(event);
        
        if (!event.wasClean) {
            this.attemptReconnect();
        }
    }

    handleError(error) {
        console.error('🚨 WebSocket error:', error);
        this.callbacks.onError(error);
    }

    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnectAttempts++;
            const delay = this.reconnectInterval * this.reconnectAttempts;
            
            console.log(`🔄 Attempting to reconnect... (${this.reconnectAttempts}/${this.maxReconnectAttempts}) in ${delay}ms`);
            
            setTimeout(() => {
                this.connect();
            }, delay);
        } else {
            console.error('❌ Max reconnection attempts reached');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close(1000, 'User disconnected');
            this.socket = null;
        }
    }

    isConnected() {
        return this.socket && this.socket.readyState === WebSocket.OPEN;
    }
}

export default OrderNotificationService;
```

### Step 2: Create Notification Display Component

```javascript
// components/NotificationToast.js
class NotificationToast {
    constructor(container = document.body) {
        this.container = container;
        this.notifications = new Map();
        this.createStyles();
    }

    createStyles() {
        if (document.getElementById('notification-styles')) return;

        const style = document.createElement('style');
        style.id = 'notification-styles';
        style.textContent = `
            .notification-container {
                position: fixed;
                top: 20px;
                right: 20px;
                z-index: 10000;
                max-width: 400px;
            }

            .notification-toast {
                background: white;
                border-radius: 8px;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
                margin-bottom: 12px;
                padding: 16px;
                border-left: 4px solid #10b981;
                animation: slideIn 0.3s ease-out;
                cursor: pointer;
                transition: transform 0.2s ease;
            }

            .notification-toast:hover {
                transform: translateX(-4px);
            }

            .notification-toast.error {
                border-left-color: #ef4444;
            }

            .notification-toast.warning {
                border-left-color: #f59e0b;
            }

            .notification-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 8px;
            }

            .notification-title {
                font-weight: 600;
                color: #1f2937;
                margin: 0;
            }

            .notification-close {
                background: none;
                border: none;
                font-size: 18px;
                cursor: pointer;
                color: #6b7280;
                padding: 0;
                width: 20px;
                height: 20px;
                display: flex;
                align-items: center;
                justify-content: center;
            }

            .notification-message {
                color: #4b5563;
                margin: 0;
                font-size: 14px;
                line-height: 1.4;
            }

            .notification-meta {
                display: flex;
                justify-content: space-between;
                margin-top: 8px;
                font-size: 12px;
                color: #9ca3af;
            }

            @keyframes slideIn {
                from {
                    transform: translateX(100%);
                    opacity: 0;
                }
                to {
                    transform: translateX(0);
                    opacity: 1;
                }
            }

            @keyframes slideOut {
                from {
                    transform: translateX(0);
                    opacity: 1;
                }
                to {
                    transform: translateX(100%);
                    opacity: 0;
                }
            }

            @media (max-width: 480px) {
                .notification-container {
                    left: 20px;
                    right: 20px;
                    max-width: none;
                }
            }
        `;
        document.head.appendChild(style);

        // Create container
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.id = 'notification-container';
        document.body.appendChild(container);
    }

    show(notification) {
        const id = Date.now().toString();
        const toast = this.createToast(notification, id);
        
        const container = document.getElementById('notification-container');
        container.appendChild(toast);
        
        this.notifications.set(id, toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            this.hide(id);
        }, 5000);

        return id;
    }

    createToast(notification, id) {
        const toast = document.createElement('div');
        toast.className = `notification-toast ${notification.type || 'success'}`;
        toast.dataset.id = id;

        const statusEmojis = {
            confirmed: '✅',
            processing: '⚙️',
            shipped: '🚚',
            delivered: '📦',
            cancelled: '❌',
            refunded: '💰'
        };

        const emoji = statusEmojis[notification.status] || '📢';

        toast.innerHTML = `
            <div class="notification-header">
                <h4 class="notification-title">${emoji} ${notification.title}</h4>
                <button class="notification-close" onclick="window.notificationToast.hide('${id}')">&times;</button>
            </div>
            <p class="notification-message">${notification.message}</p>
            <div class="notification-meta">
                <span>Order: ${notification.orderNumber}</span>
                <span>${new Date(notification.timestamp).toLocaleTimeString()}</span>
            </div>
        `;

        // Click to dismiss
        toast.addEventListener('click', () => {
            this.hide(id);
        });

        return toast;
    }

    hide(id) {
        const toast = this.notifications.get(id);
        if (toast) {
            toast.style.animation = 'slideOut 0.3s ease-out';
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.parentNode.removeChild(toast);
                }
                this.notifications.delete(id);
            }, 300);
        }
    }

    clear() {
        this.notifications.forEach((toast, id) => {
            this.hide(id);
        });
    }
}

// Make it globally available
window.notificationToast = new NotificationToast();
export default NotificationToast;
```

### Step 3: Main Integration

```javascript
// main.js or your main application file
import OrderNotificationService from './services/NotificationService.js';
import NotificationToast from './components/NotificationToast.js';

class OrderNotificationManager {
    constructor() {
        this.notificationService = null;
        this.notificationToast = new NotificationToast();
        this.isInitialized = false;
    }

    async initialize(authToken) {
        if (this.isInitialized) return;

        try {
            // Request notification permission
            await this.requestNotificationPermission();

            // Initialize WebSocket service
            this.notificationService = new OrderNotificationService({
                wsUrl: this.getWebSocketUrl(),
                authToken: authToken,
                onConnect: this.handleConnect.bind(this),
                onMessage: this.handleMessage.bind(this),
                onDisconnect: this.handleDisconnect.bind(this),
                onError: this.handleError.bind(this)
            });

            // Connect to WebSocket
            this.notificationService.connect();
            this.isInitialized = true;

            console.log('✅ Order notification manager initialized');
        } catch (error) {
            console.error('❌ Failed to initialize notification manager:', error);
        }
    }

    getWebSocketUrl() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const host = window.location.host;
        return `${protocol}//${host}/ws/orders/`;
    }

    async requestNotificationPermission() {
        if ('Notification' in window) {
            if (Notification.permission === 'default') {
                const permission = await Notification.requestPermission();
                console.log('Notification permission:', permission);
            }
        }
    }

    handleConnect(event) {
        console.log('🔗 Connected to order notifications');
        this.showConnectionStatus('Connected', 'success');
    }

    handleMessage(data) {
        console.log('📨 Received notification:', data);

        switch (data.type) {
            case 'connection_established':
                console.log('✅ Connection established');
                break;

            case 'order_status_update':
                this.handleOrderStatusUpdate(data);
                break;

            default:
                console.log('Unknown message type:', data.type);
        }
    }

    handleOrderStatusUpdate(data) {
        // Show toast notification
        this.notificationToast.show({
            title: 'Order Update',
            message: data.message,
            orderNumber: data.order_number,
            status: data.new_status,
            timestamp: data.timestamp,
            type: this.getNotificationType(data.new_status)
        });

        // Show browser notification
        this.showBrowserNotification(data);

        // Update UI if order is currently displayed
        this.updateOrderInUI(data);

        // Trigger custom events for other parts of the app
        this.dispatchCustomEvent('orderStatusUpdate', data);
    }

    getNotificationType(status) {
        const typeMap = {
            'cancelled': 'error',
            'refunded': 'warning',
            'confirmed': 'success',
            'processing': 'info',
            'shipped': 'success',
            'delivered': 'success'
        };
        return typeMap[status] || 'info';
    }

    showBrowserNotification(data) {
        if (Notification.permission === 'granted') {
            const notification = new Notification('Order Update', {
                body: `${data.message} (Order: ${data.order_number})`,
                icon: '/static/images/notification-icon.png',
                badge: '/static/images/badge-icon.png',
                tag: `order-${data.order_id}`, // Prevents duplicate notifications
                requireInteraction: false,
                silent: false
            });

            // Auto-close after 5 seconds
            setTimeout(() => {
                notification.close();
            }, 5000);

            // Handle notification click
            notification.onclick = () => {
                window.focus();
                // Navigate to order details page
                this.navigateToOrder(data.order_id);
                notification.close();
            };
        }
    }

    updateOrderInUI(data) {
        // Update order status in any displayed order lists or details
        const orderElements = document.querySelectorAll(`[data-order-id="${data.order_id}"]`);
        orderElements.forEach(element => {
            const statusElement = element.querySelector('.order-status');
            if (statusElement) {
                statusElement.textContent = data.new_status.replace('_', ' ').toUpperCase();
                statusElement.className = `order-status status-${data.new_status}`;
            }
        });
    }

    dispatchCustomEvent(eventName, data) {
        const event = new CustomEvent(eventName, {
            detail: data,
            bubbles: true,
            cancelable: true
        });
        document.dispatchEvent(event);
    }

    navigateToOrder(orderId) {
        // Implement navigation to order details page
        // This depends on your routing system
        if (window.location.pathname.includes('/orders/')) {
            window.location.href = `/orders/${orderId}/`;
        } else {
            // Use your router (React Router, Vue Router, etc.)
            console.log('Navigate to order:', orderId);
        }
    }

    showConnectionStatus(message, type) {
        // Optional: Show connection status to user
        console.log(`Connection status: ${message}`);
    }

    handleDisconnect(event) {
        console.log('❌ Disconnected from order notifications');
        this.showConnectionStatus('Disconnected', 'error');
    }

    handleError(error) {
        console.error('🚨 Notification service error:', error);
        this.showConnectionStatus('Connection Error', 'error');
    }

    disconnect() {
        if (this.notificationService) {
            this.notificationService.disconnect();
        }
        this.isInitialized = false;
    }

    reconnect(authToken) {
        this.disconnect();
        setTimeout(() => {
            this.initialize(authToken);
        }, 1000);
    }
}

// Global instance
window.orderNotificationManager = new OrderNotificationManager();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Get auth token from your authentication system
    const authToken = localStorage.getItem('authToken') || null;
    
    if (authToken) {
        window.orderNotificationManager.initialize(authToken);
    }
});

export default OrderNotificationManager;
```

---

## 🎨 Framework-Specific Examples

### React Integration

```jsx
// hooks/useOrderNotifications.js
import { useEffect, useRef, useState } from 'react';
import OrderNotificationService from '../services/NotificationService';

export const useOrderNotifications = (authToken) => {
    const [isConnected, setIsConnected] = useState(false);
    const [notifications, setNotifications] = useState([]);
    const serviceRef = useRef(null);

    useEffect(() => {
        if (!authToken) return;

        const service = new OrderNotificationService({
            authToken,
            onConnect: () => setIsConnected(true),
            onDisconnect: () => setIsConnected(false),
            onMessage: (data) => {
                if (data.type === 'order_status_update') {
                    setNotifications(prev => [data, ...prev.slice(0, 9)]); // Keep last 10
                }
            }
        });

        service.connect();
        serviceRef.current = service;

        return () => {
            service.disconnect();
        };
    }, [authToken]);

    const clearNotifications = () => {
        setNotifications([]);
    };

    return {
        isConnected,
        notifications,
        clearNotifications
    };
};

// components/OrderNotifications.jsx
import React from 'react';
import { useOrderNotifications } from '../hooks/useOrderNotifications';
import { useAuth } from '../hooks/useAuth'; // Your auth hook

const OrderNotifications = () => {
    const { user, token } = useAuth();
    const { isConnected, notifications, clearNotifications } = useOrderNotifications(token);

    if (!user) return null;

    return (
        <div className="order-notifications">
            <div className="connection-status">
                <span className={`status-indicator ${isConnected ? 'connected' : 'disconnected'}`}>
                    {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
                </span>
            </div>

            {notifications.length > 0 && (
                <div className="notifications-list">
                    <div className="notifications-header">
                        <h3>Recent Order Updates</h3>
                        <button onClick={clearNotifications}>Clear All</button>
                    </div>
                    
                    {notifications.map((notification, index) => (
                        <div key={index} className="notification-item">
                            <div className="notification-content">
                                <strong>{notification.message}</strong>
                                <p>Order: {notification.order_number}</p>
                                <small>{new Date(notification.timestamp).toLocaleString()}</small>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default OrderNotifications;
```

### Vue.js Integration

```vue
<!-- components/OrderNotifications.vue -->
<template>
  <div class="order-notifications">
    <div class="connection-status">
      <span :class="['status-indicator', isConnected ? 'connected' : 'disconnected']">
        {{ isConnected ? '🟢 Connected' : '🔴 Disconnected' }}
      </span>
    </div>

    <div v-if="notifications.length > 0" class="notifications-list">
      <div class="notifications-header">
        <h3>Recent Order Updates</h3>
        <button @click="clearNotifications">Clear All</button>
      </div>
      
      <div 
        v-for="(notification, index) in notifications" 
        :key="index" 
        class="notification-item"
      >
        <div class="notification-content">
          <strong>{{ notification.message }}</strong>
          <p>Order: {{ notification.order_number }}</p>
          <small>{{ formatDate(notification.timestamp) }}</small>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import { useAuthStore } from '../stores/auth'; // Your auth store
import OrderNotificationService from '../services/NotificationService';

export default {
  name: 'OrderNotifications',
  setup() {
    const authStore = useAuthStore();
    const isConnected = ref(false);
    const notifications = ref([]);
    let notificationService = null;

    const initializeService = (token) => {
      if (!token) return;

      notificationService = new OrderNotificationService({
        authToken: token,
        onConnect: () => { isConnected.value = true; },
        onDisconnect: () => { isConnected.value = false; },
        onMessage: (data) => {
          if (data.type === 'order_status_update') {
            notifications.value.unshift(data);
            // Keep only last 10 notifications
            if (notifications.value.length > 10) {
              notifications.value = notifications.value.slice(0, 10);
            }
          }
        }
      });

      notificationService.connect();
    };

    const clearNotifications = () => {
      notifications.value = [];
    };

    const formatDate = (dateString) => {
      return new Date(dateString).toLocaleString();
    };

    // Watch for auth token changes
    watch(() => authStore.token, (newToken, oldToken) => {
      if (notificationService) {
        notificationService.disconnect();
      }
      if (newToken) {
        initializeService(newToken);
      }
    }, { immediate: true });

    onMounted(() => {
      if (authStore.token) {
        initializeService(authStore.token);
      }
    });

    onUnmounted(() => {
      if (notificationService) {
        notificationService.disconnect();
      }
    });

    return {
      isConnected,
      notifications,
      clearNotifications,
      formatDate
    };
  }
};
</script>
```

### Angular Integration

```typescript
// services/order-notification.service.ts
import { Injectable } from '@angular/core';
import { BehaviorSubject, Observable } from 'rxjs';
import OrderNotificationService from './NotificationService';

export interface OrderNotification {
  type: string;
  order_id: string;
  order_number: string;
  old_status: string;
  new_status: string;
  message: string;
  timestamp: string;
}

@Injectable({
  providedIn: 'root'
})
export class OrderNotificationAngularService {
  private isConnectedSubject = new BehaviorSubject<boolean>(false);
  private notificationsSubject = new BehaviorSubject<OrderNotification[]>([]);
  private notificationService: any = null;

  public isConnected$: Observable<boolean> = this.isConnectedSubject.asObservable();
  public notifications$: Observable<OrderNotification[]> = this.notificationsSubject.asObservable();

  initialize(authToken: string) {
    if (this.notificationService) {
      this.notificationService.disconnect();
    }

    this.notificationService = new OrderNotificationService({
      authToken,
      onConnect: () => {
        this.isConnectedSubject.next(true);
      },
      onDisconnect: () => {
        this.isConnectedSubject.next(false);
      },
      onMessage: (data: any) => {
        if (data.type === 'order_status_update') {
          const currentNotifications = this.notificationsSubject.value;
          const updatedNotifications = [data, ...currentNotifications.slice(0, 9)];
          this.notificationsSubject.next(updatedNotifications);
        }
      }
    });

    this.notificationService.connect();
  }

  clearNotifications() {
    this.notificationsSubject.next([]);
  }

  disconnect() {
    if (this.notificationService) {
      this.notificationService.disconnect();
      this.isConnectedSubject.next(false);
    }
  }
}

// components/order-notifications.component.ts
import { Component, OnInit, OnDestroy } from '@angular/core';
import { OrderNotificationAngularService, OrderNotification } from '../services/order-notification.service';
import { AuthService } from '../services/auth.service'; // Your auth service
import { Observable } from 'rxjs';

@Component({
  selector: 'app-order-notifications',
  template: `
    <div class="order-notifications">
      <div class="connection-status">
        <span [class]="'status-indicator ' + (isConnected$ | async ? 'connected' : 'disconnected')">
          {{ (isConnected$ | async) ? '🟢 Connected' : '🔴 Disconnected' }}
        </span>
      </div>

      <div *ngIf="(notifications$ | async)?.length > 0" class="notifications-list">
        <div class="notifications-header">
          <h3>Recent Order Updates</h3>
          <button (click)="clearNotifications()">Clear All</button>
        </div>
        
        <div *ngFor="let notification of notifications$ | async" class="notification-item">
          <div class="notification-content">
            <strong>{{ notification.message }}</strong>
            <p>Order: {{ notification.order_number }}</p>
            <small>{{ notification.timestamp | date:'medium' }}</small>
          </div>
        </div>
      </div>
    </div>
  `
})
export class OrderNotificationsComponent implements OnInit, OnDestroy {
  isConnected$: Observable<boolean>;
  notifications$: Observable<OrderNotification[]>;

  constructor(
    private orderNotificationService: OrderNotificationAngularService,
    private authService: AuthService
  ) {
    this.isConnected$ = this.orderNotificationService.isConnected$;
    this.notifications$ = this.orderNotificationService.notifications$;
  }

  ngOnInit() {
    const token = this.authService.getToken();
    if (token) {
      this.orderNotificationService.initialize(token);
    }
  }

  ngOnDestroy() {
    this.orderNotificationService.disconnect();
  }

  clearNotifications() {
    this.orderNotificationService.clearNotifications();
  }
}
```

---

## 🧪 Testing & Debugging

### Testing the WebSocket Connection

```javascript
// test-websocket.js
class WebSocketTester {
    constructor(wsUrl, authToken) {
        this.wsUrl = wsUrl;
        this.authToken = authToken;
        this.socket = null;
    }

    connect() {
        console.log('🔌 Connecting to:', this.wsUrl);
        
        const url = this.authToken 
            ? `${this.wsUrl}?token=${this.authToken}`
            : this.wsUrl;
            
        this.socket = new WebSocket(url);

        this.socket.onopen = (event) => {
            console.log('✅ Connected successfully');
            console.log('Connection event:', event);
        };

        this.socket.onmessage = (event) => {
            console.log('📨 Received message:', JSON.parse(event.data));
        };

        this.socket.onclose = (event) => {
            console.log('❌ Connection closed');
            console.log('Close event:', event);
            console.log('Code:', event.code, 'Reason:', event.reason);
        };

        this.socket.onerror = (error) => {
            console.error('🚨 WebSocket error:', error);
        };
    }

    sendTestMessage() {
        if (this.socket && this.socket.readyState === WebSocket.OPEN) {
            const testMessage = { type: 'ping', timestamp: new Date().toISOString() };
            this.socket.send(JSON.stringify(testMessage));
            console.log('📤 Sent test message:', testMessage);
        } else {
            console.error('❌ WebSocket not connected');
        }
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
        }
    }
}

// Usage
const tester = new WebSocketTester('ws://localhost:8000/ws/orders/', 'your-auth-token');
tester.connect();

// Test after connection is established
setTimeout(() => {
    tester.sendTestMessage();
}, 2000);
```

### Backend Testing Script

```python
# test_order_notifications.py
from django.test import TestCase
from django.contrib.auth.models import User
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from myapp.consumers import OrderNotificationConsumer
from myapp.models import Order
import json

class OrderNotificationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
    async def test_order_status_notification(self):
        # Create WebSocket communicator
        application = URLRouter([
            path('ws/orders/', OrderNotificationConsumer.as_asgi()),
        ])
        
        communicator = WebsocketCommunicator(application, "ws/orders/")
        communicator.scope["user"] = self.user
        
        # Connect
        connected, subprotocol = await communicator.connect()
        self.assertTrue(connected)
        
        # Create an order
        order = Order.objects.create(
            customer=self.user,
            subtotal=100.00,
            total_amount=100.00,
            billing_address={"address": "123 Test St"},
            shipping_address={"address": "123 Test St"},
            status='pending'
        )
        
        # Update order status (this should trigger notification)
        order.status = 'confirmed'
        order.save()
        
        # Receive notification
        response = await communicator.receive_json_from()
        
        # Verify notification content
        self.assertEqual(response['type'], 'order_status_update')
        self.assertEqual(response['order_id'], str(order.id))
        self.assertEqual(response['new_status'], 'confirmed')
        self.assertEqual(response['old_status'], 'pending')
        
        # Disconnect
        await communicator.disconnect()

# Manual testing script
def test_order_notification():
    """
    Run this script to manually test order notifications
    python manage.py shell < test_order_notifications.py
    """
    from myapp.models import Order
    from django.contrib.auth.models import User
    
    # Get a test user and order
    user = User.objects.first()
    if not user:
        print("No users found. Please create a user first.")
        return
        
    order = Order.objects.filter(customer=user).first()
    if not order:
        print("No orders found for user. Please create an order first.")
        return
    
    print(f"Testing notification for Order: {order.order_number}")
    print(f"Current status: {order.status}")
    
    # Change status to trigger notification
    old_status = order.status
    new_status = 'shipped' if old_status != 'shipped' else 'delivered'
    
    order.status = new_status
    order.save()
    
    print(f"Status changed from {old_status} to {new_status}")
    print("Check your frontend for the notification!")