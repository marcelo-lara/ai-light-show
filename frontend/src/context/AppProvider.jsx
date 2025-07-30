import { WebSocketProvider } from './WebSocketContext';
// Import other providers here in the future
// import { SongProvider } from './SongContext';

export const AppProvider = ({ children }) => {
    return (
        <WebSocketProvider>
            {children}
        </WebSocketProvider>
    );
};