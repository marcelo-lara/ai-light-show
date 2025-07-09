import { useRef, useState } from 'preact/hooks';
import { useEffect } from 'react';

export default function ChatAssistant({ wsSend, lastResponse }) {
  const [message, setMessage] = useState("");
  const [chat, setChat] = useState([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState("");

  // Expose streaming handlers globally
  window._chatAssistantStartStreaming = () => {
    setIsStreaming(true);
    setCurrentStreamingMessage("");
  };
  
  window._chatAssistantAppendChunk = (chunk) => {
    setCurrentStreamingMessage(prev => prev + chunk);
  };
  
  window._chatAssistantEndStreaming = () => {
    setChat(prev => [...prev, { sender: 'assistant', text: currentStreamingMessage }]);
    setCurrentStreamingMessage("");
    setIsStreaming(false);
  };

  const sendMessage = () => {
    if (!message.trim()) return;
    setChat((prev) => [...prev, { sender: 'user', text: message }]);
    if (wsSend) {
      wsSend('userPrompt', { prompt: message });
    }
    setMessage("");
  };

  useEffect(() => {
    if (lastResponse) {
      setChat((prev) => [...prev, { sender: 'assistant', text: lastResponse }]);
    }
  }, [lastResponse]);
  
  return (
    <div>
      <h2 className="text-lg mb-2 font-semibold">Assistant</h2>
      <div className="flex flex-col gap-2 mb-4">
        {chat.length === 0 && (
          <p className="text-sm text-gray-400">No messages yet.</p>
        )}
        {chat.map((msg, idx) => (
          <p
            key={idx}
            className={
              'max-w-[75%] px-4 py-2 rounded-lg text-sm ' +
              (msg.sender === 'user'
                ? 'bg-blue-600 text-white self-end ml-auto text-right'
                : 'bg-gray-200 text-gray-900 self-start mr-auto text-left')
            }
            style={{ alignSelf: msg.sender === 'user' ? 'flex-end' : 'flex-start' }}
          >
            {msg.text}
          </p>
        ))}
        {isStreaming && (
          <p
            className="max-w-[75%] px-4 py-2 rounded-lg text-sm bg-gray-200 text-gray-900 self-start mr-auto text-left"
            style={{ alignSelf: 'flex-start' }}
          >
            {currentStreamingMessage}<span className="animate-pulse">|</span>
          </p>
        )}
      </div>
      <div className="mt-4 flex gap-2 items-end">
        <textarea
          className="flex-1 min-h-[2.5rem] max-h-32 p-2 bg-gray-800 text-white rounded resize-none"
          placeholder="Type your message here..."
          rows="1"
          value={message}
          onInput={(e) => {
            e.target.style.height = 'auto';
            e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
            setMessage(e.target.value);
          }}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              sendMessage();
              setMessage("");
            }
          }}
        ></textarea>
        <button
          className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded whitespace-nowrap"
          onClick={sendMessage}
        >
          Send ➤
        </button>
      </div>
    </div>
  );
}
