/**
 * WebSocket Client for Real-time Banking Updates
 * Handles connection to Django Channels WebSocket endpoints
 */

class BankingWebSocketClient {
    constructor(options = {}) {
        this.options = {
            bankingUrl: options.bankingUrl || 'ws://localhost:8000/ws/banking/',
            notificationUrl: options.notificationUrl || 'ws://localhost:8000/ws/notifications/',
            reconnectInterval: options.reconnectInterval || 5000,
            maxReconnectAttempts: options.maxReconnectAttempts || 10,
            ...options
        };
        
        this.bankingSocket = null;
        this.notificationSocket = null;
        this.reconnectAttempts = 0;
        this.isConnected = false;
        this.eventListeners = {};
        
        // Auto-connect by default
        if (options.autoConnect !== false) {
            this.connect();
        }
    }
    
    /**
     * Connect to WebSocket endpoints
     */
    connect() {
        this.connectBankingSocket();
        this.connectNotificationSocket();
    }
    
    /**
     * Connect to banking WebSocket
     */
    connectBankingSocket() {
        try {
            this.bankingSocket = new WebSocket(this.options.bankingUrl);
            
            this.bankingSocket.onopen = () => {
                console.log('Banking WebSocket connected');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.emit('connected', { type: 'banking' });
            };
            
            this.bankingSocket.onmessage = (event) => {
                this.handleMessage(event.data, 'banking');
            };
            
            this.bankingSocket.onclose = (event) => {
                console.log('Banking WebSocket disconnected:', event);
                this.isConnected = false;
                this.emit('disconnected', { type: 'banking', event });
                this.handleReconnect('banking');
            };
            
            this.bankingSocket.onerror = (error) => {
                console.error('Banking WebSocket error:', error);
                this.emit('error', { type: 'banking', error });
            };
            
        } catch (error) {
            console.error('Failed to connect to banking WebSocket:', error);
            this.emit('error', { type: 'banking', error });
        }
    }
    
    /**
     * Connect to notification WebSocket
     */
    connectNotificationSocket() {
        try {
            this.notificationSocket = new WebSocket(this.options.notificationUrl);
            
            this.notificationSocket.onopen = () => {
                console.log('Notification WebSocket connected');
                this.emit('connected', { type: 'notification' });
            };
            
            this.notificationSocket.onmessage = (event) => {
                this.handleMessage(event.data, 'notification');
            };
            
            this.notificationSocket.onclose = (event) => {
                console.log('Notification WebSocket disconnected:', event);
                this.emit('disconnected', { type: 'notification', event });
                this.handleReconnect('notification');
            };
            
            this.notificationSocket.onerror = (error) => {
                console.error('Notification WebSocket error:', error);
                this.emit('error', { type: 'notification', error });
            };
            
        } catch (error) {
            console.error('Failed to connect to notification WebSocket:', error);
            this.emit('error', { type: 'notification', error });
        }
    }
    
    /**
     * Handle incoming WebSocket messages
     */
    handleMessage(data, socketType) {
        try {
            const message = JSON.parse(data);
            console.log(`Received ${socketType} message:`, message);
            
            // Emit specific event based on message type
            this.emit(message.type, message);
            
            // Also emit generic message event
            this.emit('message', { type: socketType, data: message });
            
        } catch (error) {
            console.error('Failed to parse WebSocket message:', error);
            this.emit('error', { type: 'parse_error', error, data });
        }
    }
    
    /**
     * Handle reconnection logic
     */
    handleReconnect(socketType) {
        if (this.reconnectAttempts < this.options.maxReconnectAttempts) {
            this.reconnectAttempts++;
            console.log(`Attempting to reconnect ${socketType} socket (${this.reconnectAttempts}/${this.options.maxReconnectAttempts})`);
            
            setTimeout(() => {
                if (socketType === 'banking') {
                    this.connectBankingSocket();
                } else if (socketType === 'notification') {
                    this.connectNotificationSocket();
                }
            }, this.options.reconnectInterval);
        } else {
            console.error(`Max reconnection attempts reached for ${socketType} socket`);
            this.emit('reconnect_failed', { type: socketType });
        }
    }
    
    /**
     * Send message to banking WebSocket
     */
    sendBankingMessage(message) {
        if (this.bankingSocket && this.bankingSocket.readyState === WebSocket.OPEN) {
            this.bankingSocket.send(JSON.stringify(message));
        } else {
            console.warn('Banking WebSocket is not connected');
        }
    }
    
    /**
     * Send message to notification WebSocket
     */
    sendNotificationMessage(message) {
        if (this.notificationSocket && this.notificationSocket.readyState === WebSocket.OPEN) {
            this.notificationSocket.send(JSON.stringify(message));
        } else {
            console.warn('Notification WebSocket is not connected');
        }
    }
    
    /**
     * Subscribe to balance updates for specific accounts
     */
    subscribeToBalances(accountIds = []) {
        this.sendBankingMessage({
            type: 'subscribe_balances',
            account_ids: accountIds
        });
    }
    
    /**
     * Subscribe to transaction updates
     */
    subscribeToTransactions() {
        this.sendBankingMessage({
            type: 'subscribe_transactions'
        });
    }
    
    /**
     * Send ping to server
     */
    ping() {
        this.sendBankingMessage({ type: 'ping' });
        this.sendNotificationMessage({ type: 'ping' });
    }
    
    /**
     * Disconnect from WebSocket endpoints
     */
    disconnect() {
        if (this.bankingSocket) {
            this.bankingSocket.close();
            this.bankingSocket = null;
        }
        
        if (this.notificationSocket) {
            this.notificationSocket.close();
            this.notificationSocket = null;
        }
        
        this.isConnected = false;
    }
    
    /**
     * Event listener management
     */
    on(event, callback) {
        if (!this.eventListeners[event]) {
            this.eventListeners[event] = [];
        }
        this.eventListeners[event].push(callback);
    }
    
    off(event, callback) {
        if (this.eventListeners[event]) {
            this.eventListeners[event] = this.eventListeners[event].filter(cb => cb !== callback);
        }
    }
    
    emit(event, data) {
        if (this.eventListeners[event]) {
            this.eventListeners[event].forEach(callback => {
                try {
                    callback(data);
                } catch (error) {
                    console.error(`Error in event listener for ${event}:`, error);
                }
            });
        }
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = BankingWebSocketClient;
} else if (typeof window !== 'undefined') {
    window.BankingWebSocketClient = BankingWebSocketClient;
}
