import { createContext } from 'preact';
import { useEffect, useRef, useState, useContext } from 'preact/hooks';

const WebSocketContext = createContext();

export const useWebSocket = () => useContext(WebSocketContext);

export const WebSocketProvider = ({ children }) => {
    const wsRef = useRef(null);
    const [wsConnected, setWsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);

    useEffect(() => {
        const connect = () => {
            const ws = new WebSocket(`ws://${window.location.host}/ws`);
            wsRef.current = ws;

            ws.onopen = () => {
                console.log("🎵 WebSocket connected");
                setWsConnected(true);
            };

            ws.onmessage = (event) => {
                try {
                    const msg = JSON.parse(event.data);
                    setLastMessage({ ...msg, timestamp: Date.now() }); // new object to trigger updates
                } catch (err) {
                    console.error("WebSocket message error:", err);
                }
            };

            ws.onerror = (e) => console.error("WebSocket error:", e);

            ws.onclose = () => {
                console.log("WebSocket closed. Reconnecting in 1s...");
                setWsConnected(false);
                setTimeout(connect, 1000); // Attempt to reconnect
            };
        };

        connect();

        return () => {
            wsRef.current?.close();
        };
    }, []);

    const wsSend = (cmd, data) => {
        if (wsRef.current?.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify({ type: cmd, ...data }));
        }
    };

    const value = { wsSend, wsConnected, lastMessage };

    return (
        <WebSocketContext.Provider value={value}>{children}</WebSocketContext.Provider>
    );
};