# WebSocket Protocol Documentation

## Overview

This document describes the WebSocket protocol for real-time banking updates in the Banking Application. The protocol enables instant updates for account balances, transactions, fraud alerts, and notifications without requiring page refreshes.

## Connection Endpoints

### Banking WebSocket
```
ws://localhost:8000/ws/banking/
```
Handles real-time updates for:
- Account balances
- Transactions
- Account status changes
- Fraud alerts

### Notification WebSocket
```
ws://localhost:8000/ws/notifications/
```
Handles general notifications and system messages.

## Authentication

WebSocket connections require authentication via Django's session middleware. Users must be logged in to establish a WebSocket connection.

## Message Format

All messages are JSON formatted with the following structure:

```json
{
    "type": "message_type",
    "timestamp": "2023-01-01T00:00:00Z",
    "data": { ... }
}
```

## Client-to-Server Messages

### Connection Messages

#### Ping
Check connection status.

```json
{
    "type": "ping"
}
```

**Response:**
```json
{
    "type": "pong",
    "timestamp": "2023-01-01T00:00:00Z"
}
```

### Subscription Messages

#### Subscribe to Balance Updates
Subscribe to real-time balance updates for specific accounts.

```json
{
    "type": "subscribe_balances",
    "account_ids": [1, 2, 3]
}
```

If `account_ids` is empty or omitted, subscribes to all user's accounts.

**Response:**
```json
{
    "type": "subscription_confirmed",
    "subscription": "balances",
    "account_ids": [1, 2, 3],
    "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Subscribe to Transaction Updates
Subscribe to real-time transaction updates.

```json
{
    "type": "subscribe_transactions"
}
```

**Response:**
```json
{
    "type": "subscription_confirmed",
    "subscription": "transactions",
    "timestamp": "2023-01-01T00:00:00Z"
}
```

## Server-to-Client Messages

### Connection Messages

#### Connection Established
Sent when WebSocket connection is successfully established.

```json
{
    "type": "connection_established",
    "message": "Connected to real-time updates",
    "user_id": 123,
    "timestamp": "2023-01-01T00:00:00Z"
}
```

### Real-time Events

#### Balance Updated
Sent when an account balance changes.

```json
{
    "type": "balance_updated",
    "account_id": 1,
    "balance": "1500.50",
    "currency": "USD",
    "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Transaction Updated
Sent when a transaction is created, updated, or status changes.

```json
{
    "type": "transaction_updated",
    "transaction": {
        "id": "uuid-string",
        "from_account": "1234567890",
        "to_account": "0987654321",
        "amount": "100.00",
        "currency": "USD",
        "status": "COMPLETED",
        "description": "Transfer to friend",
        "created_at": "2023-01-01T00:00:00Z",
        "updated_at": "2023-01-01T00:01:00Z"
    },
    "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Account Status Updated
Sent when an account status changes (active, frozen, closed).

```json
{
    "type": "account_status_updated",
    "account_id": 1,
    "status": "FROZEN",
    "timestamp": "2023-01-01T00:00:00Z"
}
```

#### Fraud Alert
Sent when a fraud event is triggered.

```json
{
    "type": "fraud_alert",
    "alert": {
        "id": 1,
        "transaction_id": "uuid-string",
        "risk_level": "HIGH",
        "decision": "REVIEW_PENDING",
        "description": "Suspicious transaction pattern detected",
        "metadata": {
            "ip_address": "192.168.1.1",
            "device_id": "device123"
        }
    },
    "timestamp": "2023-01-01T00:00:00Z"
}
```

#### General Notification
Sent for general system notifications.

```json
{
    "type": "notification",
    "notification": {
        "id": "notif_001",
        "title": "System Maintenance",
        "message": "Scheduled maintenance in 2 hours",
        "type": "info",
        "data": {
            "maintenance_time": "2023-01-01T02:00:00Z",
            "duration": "2 hours"
        }
    },
    "timestamp": "2023-01-01T00:00:00Z"
}
```

### Error Messages

#### Error Response
Sent when an error occurs.

```json
{
    "type": "error",
    "message": "Invalid message type",
    "timestamp": "2023-01-01T00:00:00Z"
}
```

## Event Types Reference

| Event Type | Description | Data Fields |
|-------------|-------------|-------------|
| `connection_established` | Connection successful | `message`, `user_id` |
| `balance_updated` | Account balance changed | `account_id`, `balance`, `currency` |
| `transaction_updated` | Transaction updated | `transaction` object |
| `account_status_updated` | Account status changed | `account_id`, `status` |
| `fraud_alert` | Fraud event triggered | `alert` object |
| `notification` | General notification | `notification` object |
| `subscription_confirmed` | Subscription successful | `subscription`, `account_ids` |
| `error` | Error occurred | `message` |
| `pong` | Response to ping | `timestamp` |

## Client Implementation

### JavaScript Example

```javascript
// Connect to WebSocket
const ws = new WebSocket('ws://localhost:8000/ws/banking/');

ws.onopen = function(event) {
    console.log('Connected to banking WebSocket');
    
    // Subscribe to balance updates
    ws.send(JSON.stringify({
        type: 'subscribe_balances',
        account_ids: [1, 2, 3]
    }));
    
    // Subscribe to transaction updates
    ws.send(JSON.stringify({
        type: 'subscribe_transactions'
    }));
};

ws.onmessage = function(event) {
    const message = JSON.parse(event.data);
    
    switch(message.type) {
        case 'balance_updated':
            updateBalanceDisplay(message.account_id, message.balance);
            break;
        case 'transaction_updated':
            updateTransactionList(message.transaction);
            break;
        case 'fraud_alert':
            showFraudAlert(message.alert);
            break;
        default:
            console.log('Received message:', message);
    }
};

ws.onclose = function(event) {
    console.log('WebSocket disconnected');
    // Implement reconnection logic
};

ws.onerror = function(error) {
    console.error('WebSocket error:', error);
};
```

### Using the BankingWebSocketClient

```javascript
// Initialize client
const client = new BankingWebSocketClient({
    bankingUrl: 'ws://localhost:8000/ws/banking/',
    notificationUrl: 'ws://localhost:8000/ws/notifications/'
});

// Listen for events
client.on('balance_updated', (data) => {
    console.log('Balance updated:', data);
    updateUI(data);
});

client.on('transaction_updated', (data) => {
    console.log('Transaction updated:', data);
    updateTransactionUI(data);
});

client.on('fraud_alert', (data) => {
    console.log('Fraud alert:', data);
    showAlert(data);
});

// Subscribe to updates
client.subscribeToBalances([1, 2, 3]);
client.subscribeToTransactions();
```

## Rate Limiting

WebSocket connections are subject to rate limiting:
- Connection attempts: 10 per minute per IP
- Message sending: 100 per minute per connection
- Subscriptions: 20 per minute per connection

## Security Considerations

1. **Authentication**: All WebSocket connections require authenticated user sessions
2. **Authorization**: Users only receive updates for their own accounts and transactions
3. **Origin Validation**: WebSocket connections validate the origin header
4. **Message Validation**: All incoming messages are validated and sanitized
5. **Rate Limiting**: Connections and messages are rate-limited to prevent abuse

## Reconnection Strategy

Clients should implement automatic reconnection with exponential backoff:

```javascript
class ReconnectingWebSocket {
    constructor(url, options = {}) {
        this.url = url;
        this.reconnectInterval = options.reconnectInterval || 5000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectAttempts = 0;
        this.connect();
    }
    
    connect() {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
            this.reconnectAttempts = 0;
        };
        
        this.ws.onclose = () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => this.connect(), this.reconnectInterval);
            }
        };
    }
}
```

## Testing

Use the provided demo HTML file (`frontend/realtime-demo.html`) to test WebSocket functionality:

1. Start the Django server with Channels: `python manage.py runserver`
2. Ensure Redis is running for channel layer
3. Open `frontend/realtime-demo.html` in a browser
4. Test connection and real-time updates

## Troubleshooting

### Common Issues

1. **Connection Failed**: Check Redis is running and accessible
2. **Authentication Error**: Ensure user is logged in before connecting
3. **No Updates**: Verify signal handlers are properly registered
4. **Performance Issues**: Monitor Redis connection and channel layer performance

### Debug Mode

Enable debug logging for Channels:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'channels': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

## Performance Considerations

1. **Connection Pooling**: Limit concurrent connections per user
2. **Message Batching**: Batch multiple updates when possible
3. **Memory Management**: Clean up unused channel groups
4. **Database Optimization**: Use select_related/prefetch_related for signal queries
5. **Redis Optimization**: Monitor Redis memory usage and connection count
