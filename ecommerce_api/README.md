# Ecommerce_API

A full-featured, production-ready e-commerce backend API built using Django, Django REST Framework, Django Channels, and Redis. This project is designed to serve as a robust foundation for any online store, providing real-time order notifications, multi-framework frontend support, advanced caching, and extensible, modular architecture.

---

## Table of Contents

1. [Features](#features)
2. [Architecture Overview](#architecture-overview)
3. [Tech Stack](#tech-stack)
4. [Getting Started](#getting-started)
    - [Prerequisites](#prerequisites)
    - [Installation](#installation)
    - [Configuration](#configuration)
5. [Running the Project](#running-the-project)
6. [Project Structure](#project-structure)
7. [Core Functionality](#core-functionality)
8. [Real-Time Notification System](#real-time-notification-system)
    - [Backend Implementation](#backend-implementation)
    - [Frontend Integration](#frontend-integration)
9. [Caching & Performance](#caching--performance)
    - [Manual Cache Warmup](#manual-cache-warmup)
    - [Automatic Cache Invalidation](#automatic-cache-invalidation)
    - [Cache Key Generation](#cache-key-generation)
10. [Testing & Debugging](#testing--debugging)
11. [Extending the API](#extending-the-api)
12. [Deployment](#deployment)
    - [Production Checklist](#production-checklist)
    - [Scaling & Performance](#scaling--performance)
13. [Security Best Practices](#security-best-practices)
14. [Contributing](#contributing)
15. [License](#license)
16. [Acknowledgements](#acknowledgements)
17. [FAQ](#faq)
18. [Further Reading](#further-reading)

---

## Features

- **User Authentication:** Secure JWT-based authentication system.
- **Product Management:** CRUD operations for products, categories, brands.
- **Order Processing:** Manage cart, checkout, and order statuses.
- **Real-Time Order Notifications:** WebSocket-based instant notifications when order status changes.
- **Advanced Caching:** Automatic and manual cache warmup, cache invalidation for products, categories, brands.
- **RESTful API:** Built with Django REST Framework for industry-standard API endpoints.
- **Frontend-Agnostic:** Detailed guides for React, Vue, Angular, and Vanilla JS integration.
- **Extensible & Modular:** Clean architecture, easy to add new features or endpoints.
- **Signals & Events:** Utilizes Django signals for reacting to model changes.
- **Testing Suite:** Built-in utilities for unit and integration testing.
- **API Documentation:** Swagger/OpenAPI integration (customize as needed).

---

## Architecture Overview

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
1. User authenticates and connects to WebSocket.
2. Backend detects order status change.
3. Django signal triggers notification.
4. Channels sends message to user's WebSocket group.
5. Frontend receives and displays notification.

---

## Tech Stack

- **Backend:** Python, Django, Django REST Framework
- **Real-time:** Django Channels, Redis
- **Cache:** Django cache framework (Redis backend)
- **Database:** (Configure as needed, e.g. PostgreSQL, SQLite)
- **Frontend:** Agnostic; integration guides for React, Vue, Angular, Vanilla JS
- **Testing:** pytest, Django TestCase, Postman, WebSocket test scripts

---

## Getting Started

### Prerequisites

- Python 3.8+
- pip
- Redis server (for channels & cache)
- Node.js and npm/yarn (for frontend, optional)
- Browser with WebSocket support

### Backend Requirements (Already Implemented)

- Django with Django REST Framework
- Django Channels configured
- Redis server running

### Frontend Requirements

- Modern browser with WebSocket support
- Basic JavaScript knowledge
- Authentication system (JWT tokens recommended)

### Tools You'll Need

- Code editor (VS Code, WebStorm, etc.)
- Browser developer tools
- Optional: Postman for API testing

---

### Installation

1. **Clone the Repository:**

    ```sh
    git clone https://github.com/nota63/Ecommerce_API.git
    cd Ecommerce_API
    ```

2. **Create a Virtual Environment:**

    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. **Install Dependencies:**

    ```sh
    pip install -r requirements.txt
    ```

4. **Start Redis Server:**
   - On Linux/macOS: `redis-server`
   - On Windows: Use Redis from [Microsoft archive](https://github.com/MicrosoftArchive/redis/releases)

5. **Apply Migrations:**

    ```sh
    python manage.py migrate
    ```

6. **Create Superuser:**

    ```sh
    python manage.py createsuperuser
    ```

---

## Configuration

- Copy `.env.example` to `.env` and configure database, Redis, secret key, etc.
- Set up Django Channels in `settings.py` (already configured).
- Adjust allowed hosts, CORS settings, and other environment variables as needed.

---

## Running the Project

1. **Start Django Development Server:**

    ```sh
    python manage.py runserver
    ```

2. **Run Channels Worker (if using Daphne):**

    ```sh
    daphne ecommerce_api.asgi:application
    ```

3. **(Optional) Warm Up Cache:**

    ```sh
    python manage.py cache_warmup
    ```

---

## Project Structure

```
ecommerce_api/
├── accounts/         # User authentication and profiles
├── notifications/    # Real-time notification backend & guides
├── product/          # Product, category, brand management
│   ├── cache_utils.py        # Cache utilities & invalidators
│   └── management/
│        └── commands/
│             └── cache_warmup.py    # Cache warmup command
├── manage.py         # Django management script
└── ...
```

---

## Core Functionality

### User Authentication

- JWT authentication for secure login/logout and API access.
- Endpoints for user registration, login, profile, and password management.

### Product Management

- CRUD endpoints for products, categories, brands.
- Featured products, filtering, and search.
- Caching for frequently accessed product and category data.

### Order Management

- Cart operations, checkout, and order status tracking.
- Signals for order status change to trigger notifications.

---

## Real-Time Notification System

### Backend Implementation

- Uses Django Channels for WebSocket support.
- Sends notifications to the frontend when an order status changes.
- JWT or session authentication supported for WebSocket connections.
- Notification group management via Django Channels.

### Frontend Integration

#### Framework-Agnostic Steps

1. **Create WebSocket Service:**  
   Write a reusable JS service class to handle auth, connection, reconnection, and incoming messages.

2. **Notification Display Component:**  
   Implement UI to show notifications (Toast, pop-up, etc.).

3. **Main Integration:**  
   Initialize service on app start, handle user authentication, and connect to WS endpoint.

#### Example: React

```jsx
import { useEffect, useRef, useState } from 'react';
import OrderNotificationService from '../services/NotificationService';

export const useOrderNotifications = (authToken) => {
    // ... see full code in notifications/frontend_integration_guide.md
};
```

#### Example: Vue.js

```js
// See detailed setup in notifications/frontend_integration_guide.md
```

#### Example: Angular

```ts
// See detailed setup in notifications/frontend_integration_guide.md
```

#### Testing WebSocket Integration

```js
class WebSocketTester {
    // ... see full code in notifications/frontend_integration_guide.md
}
```

See the `notifications/frontend_integration_guide.md` file for elaborate integration examples, best practices, and troubleshooting tips for each framework.

---

## Caching & Performance

### Manual Cache Warmup

Warm up cache for featured products, categories, brands:

```sh
python manage.py cache_warmup
```

### Automatic Cache Invalidation

Cache is invalidated on product/category/brand changes:

- Product detail cache
- Category/brand product lists
- Featured products, product list, categories list, brands list

See: `product/cache_utils.py` for all cache management utilities.

### Cache Key Generation

- Custom cache key generators for product lists, categories, brands, and details.
- Example from `cache_utils.py`:
    - `product_list_key(filters=None, ordering=None, page=1)`
    - `product_detail_key(product_slug)`
    - `category_products_key(category_slug, filters=None, page=1)`
    - `brand_products_key(brand_slug, filters=None, page=1)`
- Ensures cache consistency even with filtered/ordered queries.
- Supports cache decorators for API responses.

---

## Testing & Debugging

- Use `test-websocket.js` or browser console to inspect WebSocket events.
- Use Postman to test REST endpoints.
- Run Django test suite as needed:
    ```sh
    python manage.py test
    ```
- Add custom tests as required in each app's `tests.py`.

---

## Extending the API

- Add new apps for more features (e.g. payments, shipping, analytics).
- Create new API endpoints with Django REST Framework.
- Extend notification system for other events (e.g. inventory, user activity).
- Integrate third-party services (payment gateways, shipping APIs).
- Add more cache layers (per-user, per-session, etc.).
- Implement background tasks using Celery (optional).

---

## Deployment

### Production Checklist

- Set `DEBUG=False` in your environment.
- Configure allowed hosts.
- Use secure, random `SECRET_KEY`.
- Set up HTTPS (TLS/SSL).
- Use production-grade database (e.g. PostgreSQL).
- Ensure Redis and Channels layer is production-ready.
- Set up static and media file serving.
- Configure gunicorn/daphne/uvicorn as application server.
- Set up process managers (systemd, supervisor, etc.).

### Scaling & Performance

- Use Redis or Memcached for caching and channels.
- Load balance between multiple Daphne/gunicorn workers.
- Consider sharding or partitioning for large catalog/traffic.
- Enable connection pooling in database settings.
- Monitor application using Sentry, Prometheus, etc.

---

## Security Best Practices

- Use HTTPS for all requests (including WebSocket/WSS).
- Rotate JWT secrets and use short-lived tokens.
- Sanitize all user inputs.
- Enable Django security middleware (XSS, CSRF, HSTS, etc.).
- Restrict API access by permissions and throttling.
- Keep dependencies up-to-date and monitor for vulnerabilities.

---

## Contributing

1. Fork the repository.
2. Create a new branch (`git checkout -b feature-xyz`).
3. Commit your changes.
4. Push to your fork.
5. Open a Pull Request.

Please ensure code quality, testing, and documentation for all contributions.

---

## License

This project is released under the [MIT License](LICENSE).

---

## Acknowledgements

- Django, Django REST Framework, Django Channels, Redis
- Community guides and open-source inspiration

---

## FAQ

### Can I use this backend with any frontend framework?
**Yes!** The API is frontend-agnostic, with integration guides for React, Vue, Angular, and vanilla JavaScript.

### How do I add payment gateway support?
Create a new Django app (e.g., `payments`). Integrate with third-party APIs (Stripe, PayPal, Razorpay, etc.) and expose new endpoints as needed.

### How can I add more real-time events?
Extend Django signals and Channels consumers for new models/events. Update the frontend to listen for and display new notification types.

### Where do I find more integration examples?
See `ecommerce_api/notifications/frontend_integration_guide.md` for a comprehensive, step-by-step frontend integration manual.

---

## Further Reading

- [Django Documentation](https://docs.djangoproject.com/)
- [Django REST Framework](https://www.django-rest-framework.org/)
- [Django Channels](https://channels.readthedocs.io/)
- [Redis Documentation](https://redis.io/)
- [WebSockets for Real-time Apps](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
- [OpenAPI/Swagger for API Docs](https://swagger.io/)

---

**For detailed frontend integration code, troubleshooting, or advanced features, see [`ecommerce_api/notifications/frontend_integration_guide.md`](ecommerce_api/notifications/frontend_integration_guide.md) in the repository.**